# load.py
import os
import json
import logging
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from psycopg2.errors import UniqueViolation
from alite_backend.words.funcs import remove_accents, load_json
from alite_backend.db import schemas
from alite_backend.db.models import (
    EnumAltAdjvType,
    EnumAltNounType,
    EnumGramGender,
    EnumConjPerson,
    EnumGramTense,
    EnumGramNum,
    EnumPartType,
    EnumPartVoice,
    EnumSubstCase,
    EnumVerbMood
)
from alite_backend.db.crud.word_crud import (
    crud_lemma,
    crud_lexicon,
    crud_gram_prop,
    crud_word_form,
    crud_definition,
    crud_example,
    crud_pronunciation,
    crud_lem_rel,
    crud_lookup_queue,
    crud_lem_def,
    crud_def_ex,
)
from alite_backend.db.crud.orgi_crud import crud_less_list, crud_lem_in_less_list

logger = logging.getLogger(__name__)

load_dotenv()

# make lemma-in-lesson lookup item
_CURRICULUM_CACHE = None


def _get_curriculum_cache(db: Session) -> dict:
    """Builds the curriculum map in memory exactly ONCE."""
    global _CURRICULUM_CACHE

    if _CURRICULUM_CACHE is not None:
        return _CURRICULUM_CACHE  # Instant return!

    logger.info("First lookup detected! Building curriculum cache in memory...")
    lems_in_lists = defaultdict(list)

    try:
        VOCAB_LIST_LOC = os.getenv("VOCAB_LIST_LOC")
        data = load_json(VOCAB_LIST_LOC)
        # logger.debug("data: %s", data)
        for mod in data:  # type: ignore
            # logger.debug("mod: %s", mod)
            for less_list in data[mod]:  # type: ignore
                # logger.debug("less_list: %s", less_list)
                if mod in ["ales", "other"]:
                    # list of ales or "other" words
                    list_lems = [x for x in data[mod][less_list]]  # type: ignore
                else:
                    list_vocab = data[mod][less_list]["vocab"]  # type: ignore
                    # logger.debug("List vocab: %s", list_vocab)
                    list_lems = [lem for pos, lems in list_vocab.items() for lem in lems]  # type: ignore
                    # logger.debug("list_lems: %s", list_lems)

                less_list_id = crud_less_list.get_id_by_name(
                    db=db, less_list_name=less_list
                )
                if less_list_id:
                    for word in list_lems:
                        lems_in_lists[word].append(less_list_id)
        # Save it to the global variable
        _CURRICULUM_CACHE = dict(lems_in_lists)
        logger.info("Curriculum cache successfully built!")

    except FileNotFoundError:
        logger.error(
            "curriculum.json not found! Creating empty cache to prevent retries."
        )
        _CURRICULUM_CACHE = {}

    return _CURRICULUM_CACHE


# ==========================================
# 2. THE LOADER CLASS
# ==========================================
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
            # gram_gender
            "masculine": {"gram_gender": EnumGramGender.MASCULINE},
            "neuter": {"gram_gender": EnumGramGender.NEUTER},
            "feminine": {"gram_gender": EnumGramGender.FEMININE},
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
                "part_type": EnumPartType.ADJECTIVAL
            },  # in data as "participle"
            "adverbial": {"part_type": EnumPartType.ADVERBIAL},
            # part_voice
            "active": {"part_voice": EnumPartVoice.ACTIVE},
            "passive": {"part_voice": EnumPartVoice.PASSIVE},
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
            new_lex = crud_lexicon.get_or_create(
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
        for relation in payload.rel_lems:
            # logger.debug("related lem: %s", relation)
            rel_form = relation.rel_form
            # logger.debug("rel form: %s", rel_form)
            # relation source id
            source_id = lemma_id_map[relation.entry_key]
            # logger.debug("related lemma source id: %d", source_id)

            # new relation
            target_rel_params = {"lem_text": rel_form}
            target_rel_params = schemas.LemmaSearchParams(**target_rel_params) #type: ignore
            target_rel = crud_lemma.search(db=self.db, params=target_rel_params)
            # logger.debug("target rel: %s", target_rel)
            filters = {"rel_type": relation.rel_type, "source_id": source_id}

            if target_rel:
                # logger.debug("target rel found: %s", target_rel)

                filters["target_id"] = target_rel[0].id
                relation_in = schemas.LemRelCreate(**filters)

                new_lem_rel = crud_lem_rel.get_or_create(
                    db=self.db, obj_in=relation_in, filter_kwargs=filters
                )
                logger.debug("New lem rel id: %d", new_lem_rel.id)
            else:
                # logger.debug("adding related lemma to lookup queue")
                filters["target_lem"] = rel_form

                lookup_in = schemas.LookupQueueCreate(**filters)

                new_lookup_queue = crud_lookup_queue.get_or_create(
                    db=self.db, obj_in=lookup_in, filter_kwargs=filters
                )
                logger.debug("New lookup queue id: %d", new_lookup_queue.id)

        # set up Lemma-In-Lesson junction

        # get the cache (will be instant for 99% of requests)
        target_map = _get_curriculum_cache(self.db)

        for lem in payload.lemmas:
            db_lemma_id = lemma_id_map[lem.entry_key]
            # logger.debug("db_lemma_id: %s", db_lemma_id)
            # Is this word in our curriculum?
            if lem.lem_text in target_map:
                lesson_ids = target_map[lem.lem_text]
                # logger.debug(
                #     "Linking newly fetched word '%s' to lessons: %s",
                #     lem.lem_text,
                #     lesson_ids,
                # )

                for l_id in lesson_ids:
                    link_in = schemas.LemInLessListCreate(
                        lem_id=db_lemma_id, less_list_id=l_id
                    )
                    crud_lem_in_less_list.get_or_create(
                        db=self.db,
                        obj_in=link_in,
                        filter_kwargs={"less_list_id": l_id, "lem_id": db_lemma_id},
                    )
