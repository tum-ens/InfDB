import os
from fastapi import FastAPI, Request, HTTPException, Response
import httpx
from urllib.parse import urljoin
from typing import Optional, Mapping, Iterable, Tuple, List
from db.models.common_data import create_common_data_table
from db.models.energy_assets import energy_assets

def _env(key: str, default: str) -> str:
    v = os.getenv(key, default)
    if (key.upper().startswith("PYGEOAPI") or key.upper().startswith("POSTGREST")) and not v.endswith("/"):
        v = v + "/"
    return v

PYGEOAPI_URL = _env("PYGEOAPI_INTERNAL", os.getenv("PYGEOAPI_URL", "http://cityapi-pygeoapi:5000/"))
POSTGREST_URL = _env("POSTGREST_INTERNAL", os.getenv("POSTGREST_URL", "http://cityapi-postgrest:3000/"))


schema = "our_schema"  # <-- Replace with our schema name
create_common_data_table(schema)
energy_assets(schema)


app = FastAPI(title="cityAPI Gateway", version="1.0.0")

# Root
@app.get("/")
async def root():
    return {"message": "INFDB API is running"}

# Health
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/postgrest/health")
async def postgrest_health():
    timeout = httpx.Timeout(5.0, read=5.0)
    url = POSTGREST_URL
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
        return {"ok": r.status_code < 400, "status_code": r.status_code}
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"PostgREST unreachable at {url}: {e}")

def _proxy_response(resp: httpx.Response) -> Response:
    media = resp.headers.get("content-type", "application/json")
    r = Response(content=resp.content, status_code=resp.status_code, media_type=media)
    hop = {"connection","keep-alive","proxy-authenticate","proxy-authorization","te",
           "trailers","transfer-encoding","upgrade","content-encoding"}
    for k, v in resp.headers.items():
        lk = k.lower()
        if lk not in hop and lk not in {"content-length","content-type"}:
            r.headers[k] = v
    return r

async def _proxy(
    req: Request,
    base_url: str,
    subpath: str,
    *,
    override_params: Optional[Iterable[Tuple[str, str]]] = None
) -> httpx.Response:
    method = req.method
    target = urljoin(base_url, subpath)
    body = await req.body()
    headers = {k: v for k, v in req.headers.items() if k.lower() != "host"}
    timeout = httpx.Timeout(30.0, read=60.0)
    params = list(override_params) if override_params is not None else dict(req.query_params)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, target, params=params, content=body, headers=headers)
    return resp

# ---- PygeoAPI ----
@app.get("/get-pygeoapi")
async def get_pygeoapi(
    request: Request,
    table: str,
    limit: int = 100,
    crs: str = "EPSG:25832",
):
    py_path = f"collections/{table}/items"

    bbox = None
    filter_expr = None

    params: List[Tuple[str, str]] = [("limit", str(limit)), ("offset", "0")]
    if bbox:
        params.append(("bbox", bbox))
        params.append(("crs", crs))
    if filter_expr:
        params.append(("filter", filter_expr))

    try:
        resp = await _proxy(request, PYGEOAPI_URL, py_path, override_params=params)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach pygeoapi at {PYGEOAPI_URL}: {e.__class__.__name__}: {e}"
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"pygeoapi error: {resp.text}")

    return resp.json()

# ---- PostgREST ----
@app.get("/get-postgrest")
async def get_postgrest(
    request: Request,
    table: str,
    limit: int = 100,
):
    table = (table or "").strip()
    if not table or "/" in table:
        raise HTTPException(status_code=400, detail="Invalid table name.")

    if limit < 1:
        limit = 1
    offset = 0
    if offset < 0:
        offset = 0

    passthrough = [
        (k, v) for k, v in request.query_params.multi_items()
        if k not in {"table", "limit", "offset"}
    ]
    passthrough.append(("limit", str(limit)))
    passthrough.append(("offset", str(offset)))

    try:
        resp = await _proxy(request, POSTGREST_URL, table, override_params=passthrough)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach PostgREST at {POSTGREST_URL} -> {table}: {e.__class__.__name__}: {e}",
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return _proxy_response(resp)
