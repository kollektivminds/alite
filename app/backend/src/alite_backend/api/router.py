from alite_backend.api.trainer import (
    documents,
    exercises,
    lemmas,
    lesslists,
    modules,
    sentences,
    users,
)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(lemmas.router, prefix="/lemmas", tags=["lemmas"])
api_router.include_router(lesslists.router, prefix="/lesslists", tags=["lesslists"])
api_router.include_router(modules.router, prefix="/modules", tags=["modules"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(sentences.router, prefix="/sentences", tags=["sentences"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
