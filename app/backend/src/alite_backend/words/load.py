# load.py
import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from psycopg2.errors import UniqueViolation
from alite_backend.db import schemas
from alite_backend.db.models import (
    EnumAltAdjvType,
    EnumAltNounType,
    EnumGender,
    EnumConjPerson,
    EnumGramTense,
    EnumGramNum,
    EnumParticipleType,
    EnumParticipleVoice,
    EnumPartOfSpeech,
    EnumSubstCase,
    EnumVerbAspect,
    EnumVerbMood,
    EnumVerbTransRefl,
    EnumVerbType,≠
)
import alite_backend.db.crud.word_crud as word_crud
from alite_backend.db.crud.word_crud import (
    crud_lemma,
    crud_lexicon,
    crud_gram_prop,
    crud_word_form,
    crud_definition,
    crud_example,
    crud_pronunciation,
)

logger = logging.getLogger(__name__)


class Loader:
    """_summary_"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _map_grammar_tags(self, payload_tags: list[str]) -> dict:

        grammar_tag_map = {
            # gram_tense
            "past": {"gram_tense": EnumGramTense.PAST},
            "present": {"gram_tense": EnumGramTense.PRESENT},
            "future": {"gram_tense": EnumGramTense.FUTURE},
            # irregular
            "irregular": {"irregular": True},
            # gram_num
            "singular": {"gram_num": EnumGramNum.SINGULAR},
            "plural": {"gram_num": EnumGramNum.PLURAL},
            # conj_gender
            "masculine": {"conj_gender": EnumGender.MASCULINE},
            "neuter": {"conj_gender": EnumGender.NEUTER},
            "feminine": {"conj_gender": EnumGender.FEMININE},
            # conj_person
            "first-person": {"conj_person": EnumConjPerson.FIRST},
            "second-person": {"conj_person": EnumConjPerson.SECOND},
            "third-person": {"conj_person": EnumConjPerson.THIRD},
            # verb_mood
            "indicative": {"verb_mood": EnumVerbMood.INDICATIVE},
            "imperative": {"verb_mood": EnumVerbMood.IMPERATIVE},
            # subst_case
            "nominative": {"subst_case": EnumSubstCase.NOMINATIVE},
            "genitive": {"subst_case": EnumSubstCase.GENITIVE},
            "accusative": {"subst_case": EnumSubstCase.ACCUSATIVE},
            "dative": {"subst_case": EnumSubstCase.DATIVE},
            "instrumental": {"subst_case": EnumSubstCase.INSTRUMENTAL},
            "prepositional": {"subst_case": EnumSubstCase.PREPOSITIONAL},
            "locative": {"subst_case": EnumSubstCase.LOCATIVE},
            "vocative": {"subst_case": EnumSubstCase.VOCATIVE},
            "partitive": {"subst_case": EnumSubstCase.PARTITIVE},
            # alt_adjv_type
            "comparative": {"alt_adjv_type": EnumAltAdjvType.COMPARATIVE},
            "superlative": {"alt_adjv_type": EnumAltAdjvType.SUPERLATIVE},
            "short-form": {"alt_adjv_type": EnumAltAdjvType.SHORT},
            # alt_noun_type
            "augmentative": {"alt_noun_type": EnumAltNounType.AUGMENTATIVE},
            "diminutive": {"alt_noun_type": EnumAltNounType.DIMINUTIVE},
            "collective": {"alt_noun_type": EnumAltNounType.COLLECTIVE},
            "paucal": {"alt_noun_type": EnumAltNounType.PAUCAL},
            "pejorative": {"alt_noun_type": EnumAltNounType.PEJORATIVE},
            # part_type
            "participle": {
                "part_type": EnumParticipleType.ADJECTIVAL
            },  # in data as "participle"
            "adverbial": {"part_type": EnumParticipleType.ADVERBIAL},
            # part_voice
            "active": {"part_voice": EnumParticipleVoice.ACTIVE},
            "passive": {"part_voice": EnumParticipleVoice.PASSIVE},
        }

        return_props = {}

        for tag in payload_tags:
            # tag = tag.lower()
            # logger.debug("_map_grammar_tags tag: %s", tag)
            if tag in grammar_tag_map:
                # logger.debug("matching _map_grammar_tags tag: %s", tag)
                return_props.update(grammar_tag_map[tag])
        # logger.debug("_map_grammar_tags props: %s", return_props)
        return return_props

    def load_payload(self, payload: schemas.ProcessedPayload):
        # logger.debug(payload.lemmas)

        lemma_id_map = {}
        gram_prop_groups = defaultdict(list)
        junction_map = {}
        lem_def_map = {}
        current_run_lexemes = {}
        form_list = []

        # create lemma
        for lem in payload.lemmas:  # type: ignore
            # logger.debug(lem.entry_key)
            
            # validate
            lem_in = schemas.LemmaCreate(**lem)
            #new_lemma = word_crud.goc_lemma(db=self.db, lemma_record=lem)
            new_lemma = crud_lemma.get_or_create(
                db=self.db,
                obj_in=lem_in,
                filter_kwargs=lem
            )
            # confirm_lemma = word_crud.get_lemmas(db=db, clean_lemma=word_lemma)
            # logger.debug([(x.id, x.lem_canon) for x in confirm_lemma])
            lemma_id_map[lem.entry_key] = new_lemma.id  # type: ignore

        # map and create lexemes
        for lex in payload.lexicon:

            # get parent id from map
            lemma_db_id = lemma_id_map[lex.entry_key]

            lex_in = schemas.LexemeCreate(**lex)
            # create lexicon row
            #new_lexeme = word_crud.goc_lexeme(db=self.db, word_form=lex.form)
            new_lex = word_crud.crud_lexicon.get_or_create(
                db=self.db,
                obj_in=lex_in,
                filter_kwargs=lex
            )
            # create link between lemma and lexeme
            junction_map[lex.temp_form_id] = {
                "lem_id": lemma_db_id,
                "lex_id": new_lex.id,
                "props": [],
            }

        # logger.debug("lexicon junction_map: %s", junction_map)

        # group gram_props by temp_form_id
        for prop in payload.gram_props:
            # logger.debug(prop)
            junction_map[prop.temp_form_id]["props"].append(prop.prop_name)

        # logger.debug("gram_props junction_map: %s", junction_map)

        # create create gram_props
        for k, v in junction_map.items():
            # logger.debug("k: %s, v: %s", k, v)
            # logger.debug("v.props: %s", v["props"])
            junc_props = self._map_grammar_tags(v["props"])
            # if len(junc_props.items()) > 0:
            # logger.debug("junc_props: %d", len(junc_props.items()))
            if len(junc_props.items()) > 0:
                # validate
                gram_prop_in = schemas.GramPropCreate(**junc_props)
                # new_gram_prop = word_crud.goc_gramprop(
                #     db=self.db, incoming_props=junc_props
                # )
                
                new_gram_prop = crud_gram_prop.get_or_create(
                    db = self.db,
                    obj_in=gram_prop_in,
                    filter_kwargs=junc_props
                )
                v["gram_id"] = new_gram_prop.id

        logger.debug("gram_props mapped junction_map: %s", junction_map.items())

        # create word_forms with link (and link them)
        for k, v in junction_map.items():
            del v["props"]
            # logger.debug("v: %s", v)
            # validate
            word_form_in = schemas.WordFormCreate(**v)
            #new_word_form = word_crud.goc_wordform(db=self.db, form_ids=v)
            new_word_form = crud_word_form.get_or_create(
                db=self.db,
                obj_in=word_form_in,
                filter_kwargs=v
            )
            #logger.debug("new_word_form.id: %d", new_word_form.id)

        # create definitions with link
        for definition in payload.definitions:
            logger.debug("Load definition: %s", definition)
            def_in = schemas.DefinitionCreate(**definition)

            filters = {
                "def_text": definition.def_text,
                "tags": definition.tags
            }
            
            new_def = crud_definition.get_or_create(
                db=self.db,
                obj_in=def_in,
                filter_kwargs=filters
            )
            lem_def_map[definition.temp_def_id] = {
                "def_id": new_def.id,
                "lem_id": definition.entry_key
            }

        # create def_examples
        for example in payload.def_examples:
            logger.debug("Load examples: %s", example)
            
            example_in = schemas.ExampleCreate(**example)
            
            # Examples are unique based on their text and the definition they belong to
            filters = {
                "definition_id": example_in.definition_id,
                "text": example_in.text
            }
            
            crud_example.get_or_create(
                db=self.db,
                obj_in=example_in,
                filter_kwargs=filters
            )

        # create pronunciations
        for pron in payload.pronunciations:
            logger.debug("Load pronunciation: %s", pron)
            
            pron_in = schemas.PronunciationCreate(**pron)
            
            # Pronunciations are unique to a lemma and their audio_url/file
            filters = {
                "lemma_id": pron_in.lemma_id,
                "audio_url": pron_in.audio_url # Or whatever column stores the audio path
            }
            
            crud_pronunciation.get_or_create(
                db=self.db,
                obj_in=pron_in,
                filter_kwargs=filters
            )
            
        # create related lemmas
        for relation in payload.related_lemmas:
            # relation might look like: {"lemma_id": 5, "related_lemma_id": 12, "relation_type": "synonym"}
            
            relation_in = schemas.LemmaRelationCreate(**relation)
            
            filters = {
                "lemma_id": relation_in.lemma_id,
                "related_lemma_id": relation_in.related_lemma_id,
                "relation_type": relation_in.relation_type
            }
            
            crud_lemma_relation.get_or_create(
                db=self.db,
                obj_in=relation_in,
                filter_kwargs=filters
            )