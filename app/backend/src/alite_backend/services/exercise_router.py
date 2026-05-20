# app/backend/services/exercise_router.py
import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from .items.substantives import FormLemToGncStrategy
#from .items.nouns import NounCaseStrategy
#from .items.verbs import 
#from .items.participles import 
from alite_backend.db import schemas, models
from alite_backend.db.schemas import EnumWordItemType
from alite_backend.api.deps import get

logger = logging.getLogger(__name__)

STRATEGY_MAP = {
    EnumWordItemType.FORM_LEM_TO_GNC: FormLemToGncStrategy
}

def get_exercise_generator(db, context: schemas.ExerciseRequest, exercise_type: EnumWordItemType, prompt_criteria):
    
    StrategyClass = STRATEGY_MAP.get(exercise_type)
    if not StrategyClass:
        raise ValueError("Unknown exercise type")
        
    return StrategyClass.generate_exercise( #type: ignore
        user_id=Depends(),
        prompt_criteria=prompt_criteria,
        item_count=context.num_items,
        key_count=context.max_keys,
        distractor_count=context.max_distractors
    )

# Usage in API endpoint:
# generator = get_exercise_generator(db, request.context, request.type)
# exercise_data = generator.generate(request.criteria, request.context)