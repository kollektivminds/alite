"""initializes FastAPI, mounts app root, handles errors

This module...
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from .config import settings
from .api.router import api_router

app = FastAPI(
    title="ALITE Backend API",
    description="Autonomous Learning and Informed Teaching Engine - Statistical & Item Analytics Core",
    version="0.1.0",
)

origins = [
    settings.VITE_API_BASE_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

if settings.ENV_MODE == "dev":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")


app.include_router(api_router, prefix="/api/v1")


@app.get("/", summary="Root Telemetry Check")
def read_root() -> dict[str, str]:
    """
    Root endpoint verifying that the FastAPI server is active and responding.
    """
    return {
        "status": "online",
        "service": "ALITE Core Analytics Engine",
        "target_language": "ru",
    }


@app.exception_handler(IntegrityError)
async def db_integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Database integrity error", "error": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "error": str(exc)}
    )
