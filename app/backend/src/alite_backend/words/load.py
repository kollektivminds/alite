# load.py
import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.crud import word_crud
from psycopg2.errors import UniqueViolation

logger = logging.getLogger(__name__)


class Loader:
    """_summary_"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _map_grammar_tags(self, payload_tags: list[str]) -> dict:

        grammar_tag_map = {
            # verb_aspect
            "imperfective": {"verb_aspect": 0},
            "perfective": {"verb_aspect": 1},
            # verb_conj - taking as string
            # verb_type
            "type-I": {"verb_type": 1},
            "type-II": {"verb_type": 2},
            # verb_mood
            "indicative": {"verb_mood": 0},
            "imperative": {"verb_mood": 1},
            # verb_trans_refl
            "transitive": {"verb_trans_refl": 0},
            "reflexive": {"verb_trans_refl": 1},
            "neither-tnr": {"verb_trans_refl": 2},  # not in data
            # verb_person
            "first-person": {"verb_person": 1},
            "second-person": {"verb_person": 2},
            "third-person": {"verb_person": 3},
            # verb_infinitive
            "infinitive": {"verb_infinitive": True},
            # part_type
            "adjectival": {"part_type": 0},  # not in data
            "adverbial": {"part_type": 1},
            # part_voice
            "active": {"part_voice": 0},
            "passive": {"part_voice": 1},
            # subst_case
            "nominative": {"subst_case": 0},
            "genitive": {"subst_case": 1},
            "accusative": {"subst_case": 2},
            "dative": {"subst_case": 3},
            "instrumental": {"subst_case": 4},
            "prepositional": {"subst_case": 5},
            "vocative": {"subst_case": 6},
            "locative": {"subst_case": 7},
            "partitive": {"subst_case": 8},
            # subst_animacy
            "animate": {"subst_animacy": True},
            # adjv_short
            "short-form": {"adjv_short": True},
            # diminutive - also in definitions
            "diminutive": {"diminutive": True},
            # gram_gender
            "masculine": {"gram_gender": 0},
            "neuter": {"gram_gender": 1},
            "feminine": {"gram_gender": 2},
            "dual": {"gram_gender": 3},
            # gram_number
            "singular": {"gram_number": 0},
            "plural": {"gram_number": 1},
            "dual": {"gram_number": 2},
            # gram_tense
            "past": {"gram_tense": 0},
            "present": {"gram_tense": 1},
            "future": {"gram_tense": 2},
            # irregular
            "irregular": {"irregular": True},
        }

        return_props = {}

        for tag in payload_tags:
            # tag = tag.lower()
            #logger.debug("_map_grammar_tags tag: %s", tag)
            if tag in grammar_tag_map:
                return_props.update(grammar_tag_map[tag])
        #logger.debug("_map_grammar_tags props: %s", return_props)
        return return_props

    def load_payload(self, payload: schemas.ProcessedPayload):
        # logger.debug(payload.lemmas)

        lemma_id_map = {}
        gram_prop_groups = defaultdict(list)
        junction_map = {}
        current_run_lexemes = {}
        form_list = []

        # create lemma
        for lem in payload.lemmas:  # type: ignore
            # logger.debug(lem.entry_key)
            new_lemma = word_crud.goc_lemma(db=self.db, lemma_record=lem)
            # confirm_lemma = word_crud.get_lemmas(db=db, clean_lemma=word_lemma)
            # logger.debug([(x.id, x.lem_canon) for x in confirm_lemma])
            lemma_id_map[lem.entry_key] = new_lemma.id

        # map and create lexemes
        for lex in payload.lexicon:

            # get parent id from map
            lemma_db_id = lemma_id_map[lex.entry_key]

            # create lexicon row
            new_lexeme = word_crud.goc_lexeme(db=self.db, word_form=lex.form)

            # create link between lemma and lexeme
            junction_map[lex.temp_form_id] = {
                "lem_id": lemma_db_id,
                "lex_id": new_lexeme.id,
                "props": [],
            }

        #logger.debug("lexicon junction_map: %s", junction_map)

        # group gram_props by temp_form_id
        for prop in payload.gram_props:
            # logger.debug(prop)
            junction_map[prop.temp_form_id]["props"].append(prop.prop_name)

        #logger.debug("gram_props junction_map: %s", junction_map)

        # create create gram_props
        for k, v in junction_map.items():
            #logger.debug("k: %s, v: %s", k, v)
            #logger.debug("v.props: %s", v["props"])
            junc_props = self._map_grammar_tags(v["props"])
            #if len(junc_props.items()) > 0:
                #logger.debug("junc_props: %d", len(junc_props.items()))
            if len(junc_props.items()) > 0:
                new_gram_prop = word_crud.goc_gram_prop(db=self.db, incoming_props=junc_props)
                v["props"] = new_gram_prop.id

        logger.debug("gram_props mapped junction_map: %s", junction_map.values())

        # create word_forms with link (and link them)

        # # create definitions with link
        # create def_examples
        # create pronunciations
        # create word_relations with link
