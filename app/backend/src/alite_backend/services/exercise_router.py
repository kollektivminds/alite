# app/backend/services/exercise_router.py
import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from .items.nouns import NounCaseStrategy
#from .items.verbs import 
#from .items.participles import 
from alite_backend.db import schemas, models
from alite_backend.db.schemas import EnumWordItemType

logger = logging.getLogger(__name__)

STRATEGY_MAP = {}

def get_exercise_generator(db, context: schemas.ExerciseRequest, exercise_type, prompt_criteria):
    
    StrategyClass = STRATEGY_MAP.get(exercise_type)
    if not StrategyClass:
        raise ValueError("Unknown exercise type")
        
    return StrategyClass.generate_exercise(user_id=Depends(deps.get_current_user))

# Usage in API endpoint:
# generator = get_exercise_generator(db, request.context, request.type)
# exercise_data = generator.generate(request.criteria, request.context)