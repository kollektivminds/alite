"""initializes FastAPI, mounts app root, handles errors
    
    This module...
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from alite_backend.config import settings

app = FastAPI()

if settings.ENV_MODE == "dev":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
else:
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

@app.exception_handler(IntegrityError)
async def db_integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Database integrity error", "error": str(exc)}
    )

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
