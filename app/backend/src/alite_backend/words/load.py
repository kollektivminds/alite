# load.py
import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.crud import word_crud

logger=logging.getLogger(__name__)
class Loader:
    """ _summary_
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def load_payload(self, payload: schemas.ProcessedPayload):
        #logger.debug(payload.lemmas)
        
        lemma_id_map = {}
        gram_prop_groups = defaultdict(list)
        junction_map = {}
        form_list = []
        
        # create lemma
        for lem in payload.lemmas: #type: ignore
            #logger.debug(lem.entry_key)
            new_lemma = word_crud.cog_lemma(db=self.db, lemma_record=lem)
            #confirm_lemma = word_crud.get_lemmas(db=db, clean_lemma=word_lemma)
            #logger.debug([(x.id, x.lem_canon) for x in confirm_lemma])
            lemma_id_map[lem.entry_key] = new_lemma.id
        
        # map and create lexemes
        for lex in payload.lexicon:
            
            # get parent id from map
            lemma_db_id = lemma_id_map[lex.entry_key]
            
            # create lexicon row
            new_lexeme = word_crud.cog_lexeme(
                db=self.db,
                word_form=lex.form,
            )

            # create link between lemma and lexeme
            junction_map[lex.temp_form_id] = {
                "lem_id": lemma_db_id,
                "lex_id": new_lexeme.id
            }

        # group gram_props by temp_form_id
        
        # create create gram_props with link
        
        # create word_forms with link (and link them)
        for form in form_list:
            new_form = word_crud.cog_word_form(
                db = self.db,
                lem_id = form.lem_id,
                lex_id = form.lex_id,
                gram_id = form.gram_id
            )
        # create definitions with link
        # create def_examples
        # create pronunciations
        # create word_relations with link
        