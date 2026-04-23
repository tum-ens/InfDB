import json
import os
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape

# Internal URLs for pygeoapi and PostgREST services
PYGEOAPI_URL = os.getenv("PYGEOAPI_INTERNAL")
POSTGREST_URL = os.getenv("POSTGREST_INTERNAL")
if PYGEOAPI_URL is None:
    raise ValueError("Environment variable PYGEOAPI_INTERNAL is not set.")

if POSTGREST_URL is None:
    raise ValueError("Environment variable POSTGREST_INTERNAL is not set.")
POSTGREST_URL_STRING = str(POSTGREST_URL)

# FastAPI app setup
app = FastAPI(title="infDB API Gateway", version="1.0.0")
app.add_middleware(GZipMiddleware, minimum_size=500)  # Enable gzip compression for large responses


# Root endpoint for basic API status
@app.get("/")
async def root():
    """Returns a basic status message indicating the API is running."""
    return {"message": "INFDB API is running."}


# Health check endpoint
@app.get("/health")
async def health():
    """Returns the health status of the API gateway."""
    return {"status": "ok"}


# Health check for PostgREST service
@app.get("/postgrest/health")
async def postgrest_health():
    """Checks the health of the downstream PostgREST service.

    Returns:
        A dictionary containing the status code and a boolean 'ok' flag.

    Raises:
        HTTPException: If PostgREST is unreachable.
    """
    timeout = httpx.Timeout(5.0, read=5.0)
    url = POSTGREST_URL
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
        return {"ok": r.status_code < 400, "status_code": r.status_code}
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"PostgREST unreachable at {url}: {e}") from e


# Helper to proxy HTTP responses, preserving headers except for hop-by-hop headers
def _proxy_response(resp: httpx.Response) -> Response:
    """Proxies an HTTP response, preserving headers except for hop-by-hop headers.

    Args:
        resp: The original httpx response.

    Returns:
        A FastAPI Response object.
    """
    media = resp.headers.get("content-type", "application/json")
    r = Response(content=resp.content, status_code=resp.status_code, media_type=media)
    hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-encoding",
    }
    for k, v in resp.headers.items():
        lk = k.lower()
        if lk not in hop and lk not in {"content-length", "content-type"}:
            r.headers[k] = v
    return r


# Helper to proxy requests to another service
async def _proxy(
    req: Request, base_url: str, subpath: str, *, override_params: Optional[Iterable[Tuple[str, str]]] = None
) -> httpx.Response:
    """Proxies a request to another service.

    Args:
        req: The incoming FastAPI request.
        base_url: The base URL of the target service.
        subpath: The path to append to the base URL.
        override_params: Optional query parameters to use instead of the request's params.

    Returns:
        The httpx response from the target service.
    """
    method = req.method
    target = urljoin(base_url, subpath)
    body = await req.body()
    headers = {k: v for k, v in req.headers.items() if k.lower() != "host"}
    timeout = httpx.Timeout(30.0, read=60.0)
    # type check has issues with restriction to type: list[tuple[str, str]]
    params: List[tuple[str, str | int | float | bool | None]] = (
        list(override_params) if override_params is not None else list(req.query_params.items())
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, target, params=params, content=body, headers=headers)
    return resp


# ---- PostgREST Endpoints ----


# GET endpoint to fetch data from PostgREST, with geometry simplification
@app.get("/postgrest/{schema}/{table}")
async def get_postgrest(
    request: Request,
    schema: str,
    table: str,
    limit: int = 100,
    tolerance: float = Query(100, description="Geometry simplification tolerance (units match your data)"),
):
    """Fetches data from PostgREST with optional geometry simplification.

    Args:
        request: The incoming request.
        schema: The database schema.
        table: The table name.
        limit: Max number of records to return.
        tolerance: Tolerance for geometry simplification.

    Returns:
        JSON response with (optionally) simplified geometries.

    Raises:
        HTTPException: If PostgREST returns an error or is unreachable.
    """
    # Only pass allowed params to PostgREST, filter out internal params
    # type check has issues with restriction to type: list[tuple[str, str]]
    passthrough: List[tuple[str, str | int | float | bool | None]] = [
        (k, v)
        for k, v in request.query_params.multi_items()
        if k not in {"schema", "table", "limit", "offset", "tolerance"}
    ]
    passthrough.append(("limit", str(limit)))
    passthrough.append(("offset", str(0)))

    headers = dict(request.headers)
    headers["Accept-Profile"] = schema  # Specify schema for PostgREST
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(urljoin(POSTGREST_URL_STRING, table), params=passthrough, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach PostgREST at {POSTGREST_URL_STRING} -> {table}: {e.__class__.__name__}: {e}",
        ) from e

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    # Simplify geometry in the response if present
    def _simplify_geometry(obj, tolerance=100):
        for key in ["geometry", "geom"]:
            if key in obj and isinstance(obj[key], dict) and "coordinates" in obj[key]:
                try:
                    geom = shape(obj[key])
                    simple_geom = geom.simplify(tolerance, preserve_topology=True)
                    obj[key] = mapping(simple_geom)
                except ShapelyError:
                    pass
        return obj

    if resp.headers.get("content-type", "").startswith("application/json"):
        data = resp.json()
        if isinstance(data, list):
            data = [_simplify_geometry(item, tolerance=tolerance) for item in data]
        elif isinstance(data, dict):
            data = _simplify_geometry(data, tolerance=tolerance)
        return Response(content=json.dumps(data), status_code=resp.status_code, media_type="application/json")
    else:
        return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


# POST endpoint to insert a new row into a table via PostgREST
@app.post("/postgrest/{schema}/{table}")
async def post_postgrest(schema: str, table: str, row: dict):
    """Inserts a new row into a table via PostgREST.

    Args:
        schema: The database schema.
        table: The table name.
        row: The dictionary representing the row to insert.

    Returns:
        The PostgREST response (JSON or success message).

    Raises:
        HTTPException: If PostgREST returns an error or is unreachable.
    """
    headers = {"Content-Type": "application/json", "Content-Profile": schema}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(urljoin(POSTGREST_URL_STRING, table), json=row, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Cannot reach PostgREST at {POSTGREST_URL_STRING}: {e.__class__.__name__}: {e}"
        ) from e
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=f"PostgREST error: {resp.text}")
    if resp.content:
        return resp.json()
    else:
        return {"status": "success"}


# PUT endpoint to update an existing row in a table via PostgREST
@app.put("/postgrest/{schema}/{table}/{item_id}")
async def put_postgrest(
    schema: str,
    table: str,
    item_id: str,
    row: dict,
    key_column: str = Query("id", description="Primary key column name"),
):
    """Updates an existing row in a table via PostgREST.

    Args:
        schema: The database schema.
        table: The table name.
        item_id: The ID of the item to update.
        row: The new data for the row.
        key_column: The name of the primary key column.

    Returns:
        The PostgREST response (JSON or update status).

    Raises:
        HTTPException: If PostgREST returns an error or is unreachable.
    """
    headers = {"Content-Type": "application/json", "Content-Profile": schema}
    params = {key_column: f"eq.{item_id}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(urljoin(POSTGREST_URL_STRING, table), params=params, json=row, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Cannot reach PostgREST at {POSTGREST_URL_STRING}: {e.__class__.__name__}: {e}"
        ) from e
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=f"PostgREST error: {resp.text}")
    if resp.content:
        return resp.json()
    else:
        return {"status": "updated"}


# DELETE endpoint to remove a row from a table via PostgREST
@app.delete("/postgrest/{schema}/{table}/{item_id}")
async def delete_postgrest(
    schema: str, table: str, item_id: str, key_column: str = Query("id", description="Primary key column name")
):
    """Removes a row from a table via PostgREST.

    Args:
        schema: The database schema.
        table: The table name.
        item_id: The ID of the item to delete.
        key_column: The name of the primary key column.

    Returns:
        A success status message.

    Raises:
        HTTPException: If PostgREST returns an error or is unreachable.
    """
    headers = {"Content-Type": "application/json", "Content-Profile": schema}
    params = {key_column: f"eq.{item_id}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(urljoin(POSTGREST_URL_STRING, table), params=params, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Cannot reach PostgREST at {POSTGREST_URL_STRING}: {e.__class__.__name__}: {e}"
        ) from e
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=f"PostgREST error: {resp.text}")
    return {"status": "deleted"}
