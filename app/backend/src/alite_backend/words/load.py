# load.py
import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.models import (
    EnumAdjectiveType,
    EnumConjGender,
    EnumConjPerson,
    EnumGramNumber,
    EnumGramTense,
    EnumParticipleType,
    EnumParticipleVoice,
    EnumPartOfSpeech,
    EnumSubstCase,
    EnumVerbAspect,
    EnumVerbMood,
    EnumVerbTransRefl,
    EnumVerbType
)
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
            "imperfective": {"verb_aspect": EnumVerbAspect},
            "perfective": {"verb_aspect": EnumVerbAspect},
            # verb_conj - taking as string
            # verb_type
            "type-I": {"verb_type": EnumVerbType},
            "type-II": {"verb_type": EnumVerbType},
            # verb_mood
            "indicative": {"verb_mood": EnumVerbMood},
            "imperative": {"verb_mood": EnumVerbMood},
            # verb_trans_refl
            "transitive": {"verb_trans_refl": EnumVerbTransRefl},
            "reflexive": {"verb_trans_refl": EnumVerbTransRefl},
            "neither-tnr": {"verb_trans_refl": EnumVerbTransRefl},  # not in data
            # conj_person
            "first-person": {"conj_person": EnumConjPerson},
            "second-person": {"conj_person": EnumConjPerson},
            "third-person": {"conj_person": EnumConjPerson},
            # verb_infinitive
            "infinitive": {"verb_infinitive": True},
            # part_type
            "adjectival": {"part_type": EnumParticipleType},  # not in data
            "adverbial": {"part_type": EnumParticipleType},
            # part_voice
            "active": {"part_voice": EnumParticipleVoice},
            "passive": {"part_voice": EnumParticipleVoice},
            # subst_case
            "nominative": {"subst_case": EnumSubstCase},
            "genitive": {"subst_case": EnumSubstCase},
            "accusative": {"subst_case": EnumSubstCase},
            "dative": {"subst_case": EnumSubstCase},
            "instrumental": {"subst_case": EnumSubstCase},
            "prepositional": {"subst_case": EnumSubstCase},
            "vocative": {"subst_case": EnumSubstCase},
            "locative": {"subst_case": EnumSubstCase},
            "partitive": {"subst_case": EnumSubstCase},
            # subst_animacy
            "animate": {"subst_animacy": True},
            # adjv_comp_type
            "comparative": {"adjv_comp_type": EnumAdjectiveType},
            "superlative": {"adjv_comp_type": EnumAdjectiveType},
            # adjv_short
            "short-form": {"adjv_short": True},
            # diminutive - also in definitions
            "diminutive": {"diminutive": True},
            # conj_gender
            "masculine": {"conj_gender": EnumConjGender},
            "neuter": {"conj_gender": EnumConjGender},
            "feminine": {"conj_gender": EnumConjGender},
            # gram_number
            "singular": {"gram_number": EnumGramNumber},
            "plural": {"gram_number": EnumGramNumber},
            "dual": {"gram_number": EnumGramNumber},
            # gram_tense
            "past": {"gram_tense": EnumGramTense},
            "present": {"gram_tense": EnumGramTense},
            "future": {"gram_tense": EnumGramTense},
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
                new_gram_prop = word_crud.goc_gramprop(db=self.db, incoming_props=junc_props)
                v["gram_id"] = new_gram_prop.id

        logger.debug("gram_props mapped junction_map: %s", junction_map.items())

        # create word_forms with link (and link them)
        for k, v in junction_map.items():
            del v["props"]
            logger.debug("v: %s", v)
            new_word_form = word_crud.goc_wordform(db=self.db, form_ids=v)
            #logger.debug("new_word_form.id: %d", new_word_form.id)

        # # create definitions with link
        # create def_examples
        # create pronunciations
        # create word_relations with link
