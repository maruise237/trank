"""FastAPI entrypoint. Full routers come in Plan 2; here we expose /health."""
import logging
from fastapi import FastAPI
from .config import get_settings

_s = get_settings()
logging.basicConfig(level=_s.log_level)

app = FastAPI(title="trank API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "trank-api"}
