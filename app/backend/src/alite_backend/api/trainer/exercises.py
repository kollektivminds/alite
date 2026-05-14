from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from alite_backend.services import exercise_generator, flashcard_generator
from alite_backend.db import models, schemas
from alite_backend.api import deps

router = APIRouter()

@router.post("/generate-exercise")
def create_custom_exercise(
    request: schemas.ExerciseRequest, 
    db: Session = Depends(deps.get_db)
):
    if request.exercise_type == "grammar_forms":
        return exercise_generator.generate_grammar_exercise(db, request)
        
    # elif request.exercise_type == "definitions":
    #     return exercise_generator.generate_definition_exercise(db, request)
        
    else:
        raise HTTPException(status_code=400, detail="Unknown exercise type")