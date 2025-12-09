# load.py
from sqlalchemy.orm import Session
from app.backend.db import schemas
from app.backend.db.crud import word_data as crud_words
import logging

logger=logging.getLogger(__name__)
class Loader:
    def __init__(self, db_session: Session):
        self.db = db_session

    def load_to_db(self, payload: schemas.ProcessedPayload):
        logger.debug(payload.lemma.lemma_text)

        # 1. get or create lemma (with pos) for lemma.id

        # 2. create Definitions, Definition_Sentences records, connect them
         
        # 3. FOR ALL ENTRIES:
            # check/create lexeme,
            # check/create link to lemma in word_forms,
            # create GramProps record,
            # link in WordForms
            
            # if pos == verb: ADD to verb pair table, lookup pair word(s)

        # 4. 
