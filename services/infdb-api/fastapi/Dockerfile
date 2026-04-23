FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /workspaces/fastapi
COPY pyproject.toml /workspaces/fastapi/pyproject.toml

RUN uv sync

COPY main.py /workspaces/fastapi/main.py
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ,"--log-level", "debug"]