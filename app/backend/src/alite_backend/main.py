"""initializes FastAPI, mounts app root, handles errors

This module...
"""

import logging
import traceback
from pathlib import Path

# from alite_backend.api.admin.analytics import AnalyticsDashboardView
from alite_backend.api.admin.auth import admin_auth
from alite_backend.api.admin.views import (
    DefinitionAdminView,
    DocumentAdminView,
    ExampleAdminView,
    ExerciseAdminView,
    GramPropAdminView,
    ItemAdminView,
    LemmaAdminView,
    LemmaDefinitionAdminView,
    LemmaRelationAdminView,
    LessListAdminView,
    LexemeAdminView,
    LookupQueueAdminView,
    ModuleAdminView,
    PronunciationAdminView,
    SentenceAdminView,
    SentenceTokenAdminView,
    UserAdminView,
    WordFormAdminView,
)
from alite_backend.api.router import api_router
from alite_backend.config import settings
from alite_backend.db.db_session import engine
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ALITE Backend API",
    description="Autonomous Learning and Informed Teaching Engine - Statistical & Item Analytics Core",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

admin_dashboard = Admin(
    app=app,
    engine=engine,
    authentication_backend=admin_auth,
    title="ALITE admin",
    base_url="/admin",
    templates_dir=str(TEMPLATES_DIR),
)

admin_dashboard.add_view(LemmaAdminView)
admin_dashboard.add_view(LexemeAdminView)
admin_dashboard.add_view(GramPropAdminView)
admin_dashboard.add_view(WordFormAdminView)
admin_dashboard.add_view(DefinitionAdminView)
admin_dashboard.add_view(ExampleAdminView)
admin_dashboard.add_view(PronunciationAdminView)
admin_dashboard.add_view(LemmaRelationAdminView)
admin_dashboard.add_view(LookupQueueAdminView)
admin_dashboard.add_view(ExampleAdminView)
admin_dashboard.add_view(ModuleAdminView)
admin_dashboard.add_view(LessListAdminView)
admin_dashboard.add_view(UserAdminView)
admin_dashboard.add_view(DocumentAdminView)
admin_dashboard.add_view(SentenceAdminView)
admin_dashboard.add_view(SentenceTokenAdminView)
admin_dashboard.add_view(ExerciseAdminView)
admin_dashboard.add_view(ItemAdminView)
admin_dashboard.add_view(LemmaDefinitionAdminView)

# admin_dashboard.add_view(AnalyticsDashboardView)

origins = [settings.VITE_API_BASE_URL, "http://localhost:5173", "http://127.0.0.1:5173"]


@app.middleware("http")
async def catch_exceptions_and_log_middleware(request: Request, call_next):
    """
    Global exception-handling middleware.
    Intercepts unhandled runtime exceptions, logs the exact traceback
    with file paths and line numbers, and returns a structured 500 payload
    to assist frontend debugging.
    """
    try:
        # Proceed with the request lifecycle
        return await call_next(request)
    except Exception as exc:
        # Capture the complete traceback stack
        tb_str = traceback.format_exc()

        # Log the error heavily to the terminal running Uvicorn
        logger.error(
            f"CRITICAL UNHANDLED EXCEPTION on {request.method} {request.url.path}:\n{tb_str}"
        )

        # Return a structured JSON response to the browser / DevTools network tab
        # Rationale: Exposing tracebacks in development accelerates debugging.
        # (In production, you would replace 'traceback' with a unique correlation ID).
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal Server Error captured by ALITE middleware.",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": tb_str.splitlines(),  # Breaks lines for clean inspection in console
            },
        )


if settings.ENV_MODE == "dev":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
