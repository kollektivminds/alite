from fastapi import APIRouter

from alite_backend.api.routes import (
    analytics,
    documents,
    exercises,
    lemmas,
    lesslists,
    modules,
    sentences,
    users,
)

api_router = APIRouter()
api_router.include_router(lemmas.router)
api_router.include_router(lesslists.router)
api_router.include_router(modules.router)
api_router.include_router(users.router)
api_router.include_router(exercises.router)
api_router.include_router(sentences.router)
api_router.include_router(documents.router)
api_router.include_router(analytics.router)
