"""initializes FastAPI, mounts app root, handles errors

This module...
"""

from pathlib import Path

from alite_backend.api.admin.admin_auth import admin_auth
from alite_backend.api.admin.admin_views import (
    DefinitionAdminView,
    DocumentAdminView,
    ExampleAdminView,
    GramPropAdminView,
    ItemAdminView,
    LemmaAdminView,
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
from alite_backend.api.admin.analytics import AnalyticsDashboardView
from alite_backend.api.router import api_router
from alite_backend.config import settings
from alite_backend.db.db_session import engine
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from sqlalchemy.exc import IntegrityError

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
admin_dashboard.add_view(ItemAdminView)

admin_dashboard.add_view(AnalyticsDashboardView)

origins = [settings.VITE_API_BASE_URL, "http://localhost:5173", "http://127.0.0.1:5173"]

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
