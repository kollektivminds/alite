# app/backend/services/exercise_router.py
import logging
from .items.nouns import NounCaseStrategy
#from .items.verbs import 
#from .items.participles import 
from alite_backend.db import schemas, models 

logger = logging.getLogger(__name__)

def get_exercise_generator(db, context, exercise_type):
    strategies = {
        "noun_cases": NounCaseStrategy,
        #"verb_conjugations": VerbConjugationStrategy,
        #"participle_id": ParticipleTypeStrategy,
    }
    
    StrategyClass = strategies.get(exercise_type)
    if not StrategyClass:
        raise ValueError("Unknown exercise type")
        
    return StrategyClass(db, context)

# Usage in API endpoint:
# generator = get_exercise_generator(db, request.context, request.type)
# exercise_data = generator.generate(request.criteria, request.context)