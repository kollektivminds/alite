# load.py
import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from psycopg2.errors import UniqueViolation
from alite_backend.words.funcs import remove_accents
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
    EnumVerbType,
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
    crud_lem_rel,
    crud_lem_def,
    crud_def_ex,
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
        form_list = []

        # create lemma
        for lem in payload.lemmas:  # type: ignore
            # logger.debug(lem.entry_key)

            # validate
            lemma_in = schemas.LemmaCreate(**lem.model_dump())
            # new_lemma = word_crud.goc_lemma(db=self.db, lemma_record=lem)
            new_lemma = crud_lemma.get_or_create(
                db=self.db, obj_in=lemma_in, filter_kwargs=lem.model_dump()
            )
            # confirm_lemma = word_crud.get_lemmas(db=db, lem_text=word_lemma)
            # logger.debug([(x.id, x.lem_canon) for x in confirm_lemma])
            lemma_id_map[lem.entry_key] = new_lemma.id  # type: ignore

        # map and create lexemes
        for lex in payload.lexicon:

            # get parent id from map
            lemma_db_id = lemma_id_map[lex.entry_key]
            new_lex_in = {
                "lex_text": lex.lex_text,
                "lex_text_clean": remove_accents(lex.lex_text),
            }
            lex_in = schemas.LexemeCreate(**new_lex_in)
            # create lexicon row
            # new_lexeme = word_crud.goc_lexeme(db=self.db, word_form=lex.form)
            new_lex = word_crud.crud_lexicon.get_or_create(
                db=self.db, obj_in=lex_in, filter_kwargs=new_lex_in
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
                    db=self.db, obj_in=gram_prop_in, filter_kwargs=junc_props
                )
                v["gram_id"] = new_gram_prop.id

        # logger.debug("gram_props mapped junction_map: %s", junction_map.items())

        # create word_forms with link (and link them)
        for k, v in junction_map.items():
            del v["props"]
            # logger.debug("v: %s", v)
            # validate
            word_form_in = schemas.WordFormCreate(**v)
            # new_word_form = word_crud.goc_wordform(db=self.db, form_ids=v)
            new_word_form = crud_word_form.get_or_create(
                db=self.db, obj_in=word_form_in, filter_kwargs=v
            )
            # logger.debug("new_word_form.id: %d", new_word_form.id)

        # create definitions with link
        for definition in payload.definitions:
            # logger.debug("Load definition: %s", definition)

            filters = {"def_text": definition.def_text, "def_tags": definition.def_tags}

            def_in = schemas.DefinitionCreate(**filters)

            new_def = crud_definition.get_or_create(
                db=self.db,
                obj_in=def_in,
                filter_kwargs={"def_text": definition.def_text},
            )
            lem_def_map[definition.temp_def_id] = {
                "def_id": new_def.id,
                "lem_id": lemma_id_map[definition.entry_key],
                "ex_ids": [],
            }

        # logger.debug("After definition Lem_def_map: %s", lem_def_map)

        # create def_examples
        for example in payload.def_examples:
            # logger.debug("Load examples: %s", example)

            # Examples are unique based on their text and the definition they belong to
            filters = {"ex_text": example.ex_text}

            example_in = schemas.ExampleCreate(**filters)

            new_ex = crud_example.get_or_create(
                db=self.db, obj_in=example_in, filter_kwargs=filters
            )
            # logger.debug("New example id: %d", new_ex.id)
            lem_def_map[example.temp_def_id]["ex_ids"].append(new_ex.id)

        # logger.debug("After examples Lem_def_map: %s", lem_def_map)

        for temp_def_id, rels in lem_def_map.items():
            lem_def = {"lem_id": rels["lem_id"], "def_id": rels["def_id"]}
            lem_def_in = schemas.LemDefCreate(**lem_def)
            new_lem_def = crud_lem_def.get_or_create(
                db=self.db, obj_in=lem_def_in, filter_kwargs=lem_def
            )
            # logger.debug("new_lem_def id: (%d, %d)", new_lem_def.lem_id, new_lem_def.def_id)
            if len(rels["ex_ids"]) > 0:
                for ex_id in rels["ex_ids"]:
                    def_ex = {"def_id": rels["def_id"], "ex_id": ex_id}
                    def_ex_in = schemas.DefExCreate(**def_ex)
                    new_def_ex = crud_def_ex.get_or_create(
                        db=self.db, obj_in=def_ex_in, filter_kwargs=def_ex
                    )
                    # logger.debug("new_def_ex id: (%d, %d)", new_def_ex.def_id, new_def_ex.ex_id)

        # create pronunciations
        for pron in payload.pronunciations:
            # logger.debug("Load pronunciation: %s", pron)
            pron_in = schemas.PronunciationCreate(**pron.model_dump())

            filters = {"pron_text": pron_in.pron_text, "pron_type": pron_in.pron_type}

            new_pron = crud_pronunciation.get_or_create(
                db=self.db, obj_in=pron_in, filter_kwargs=filters
            )

            # logger.debug("New pron id: %d", new_pron.id)

        # create related lemmas
        # for relation in payload.rel_lems:
        #     logger.debug("related lem: %s", relation)

        #     other_rel_params = {"lem_text": relation.rel_form}

        #     other_rel_params = schemas.LemmaSearchParams(**other_rel_params)

        #     other_rel = crud_lemma.search(db=self.db, params=other_rel_params)
        #     logger.debug("other rel: %s", other_rel)
        #     relation_in = schemas.LemRelCreate(**relation.model_dump())

        #     filters = {
        #         "source_id": relation_in.source_id,
        #         "target_id": relation_in.target_id,
        #         "rel_type": relation_in.rel_type,
        #     }

        #     new_lem_rel = crud_lem_rel.get_or_create(
        #         db=self.db, obj_in=relation_in, filter_kwargs=filters
        #     )
