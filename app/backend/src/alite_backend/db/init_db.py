"""
set up database
1. load vocab JSON file
2. load words and feed to db
3. CREATE module
"""

# from ..words.funcs import load_json
import os
import random
import logging
import json
from collections import defaultdict
from cytoolz import concat
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from alite_backend.db.db_session import SessionLocal
from alite_backend.words.pipeline import load_words
from alite_backend.words.queue import process_lookup_queue
from alite_backend.words.funcs import load_json, save_json
from alite_backend.logging_config import setup_logging
from alite_backend.config import settings
import alite_backend.db.schemas as schemas
from alite_backend.db.crud.word_crud import (
    crud_module,
    crud_less_list,
    crud_lem_in_less_list,
    crud_less_list_in_mod,
)

setup_logging()

logger = logging.getLogger(__name__)

load_dotenv()

VOCAB_LIST_LOC = os.getenv("VOCAB_LIST_LOC")
APP_DIR = os.getenv("APP_DIR")
INIT_DB_LOC = APP_DIR + "backend/src/alite_backend/db/init_db.sql"  # type: ignore

bodyLibDfLoc = "../syntagrus/bodyLibDf.json"
bodyTextDfLoc = "../syntagrus/bodyTextDf.json"
infDictLoc = "../syntagrus/infDict.json"


def load_org_tables(db: Session, vocab_list_path: str = VOCAB_LIST_LOC):  # type: ignore
    data = load_json(vocab_list_path)
    # logger.debug("data: %s", data)
    lists_in_mods = []
    lems_in_lists = {}
    for mod in data:  # type: ignore
        # logger.debug("mod: %s", mod)
        filters = {"module_name": mod}
        module_in = schemas.ModuleCreate(**filters)
        new_module = crud_module.get_or_create(
            db=db, obj_in=module_in, filter_kwargs=filters
        )
        # logger.debug("new mod id: %d", new_module.id)
        # logger.debug("data[mod]: %s", data[mod]) #type: ignore
        for less_list in data[mod]:  # type: ignore
            # logger.debug("less_list: %s", less_list)
            less_list_data = data[mod][less_list]  # type: ignore
            # logger.debug("data[mod][less_list]: %s", less_list_data)  # type: ignore
            # list_lems = [lemma for pos_list in less_list_data["vocab"] for lemma in pos_list]
            filters = {"title": less_list, "topic": None, "owner_id": None}
            if mod in ["ales", "other"]:
                # list of ales or "other" words
                list_lems = [x for x in data[mod][less_list]]  # type: ignore
                # logger.debug("list_lems: %s", list_lems)
            else:
                # try:  # type: ignore
                #     logger.debug("data[mod][less_list]['topic']: %s", less_list_data["topic"])  # type: ignore
                # except:
                #     logger.debug("no topic found")
                filters["topic"] = less_list_data["topic"]  # type: ignore
                list_vocab = data[mod][less_list]["vocab"]  # type: ignore
                # logger.debug("List vocab: %s", list_vocab)
                list_lems = [lem for pos, lems in list_vocab.items() for lem in lems]  # type: ignore
                # logger.debug("list_lems: %s", list_lems)

            less_list_in = schemas.LessonListCreate(**filters)  # type: ignore
            new_less_list = crud_less_list.get_or_create(
                db=db, obj_in=less_list_in, filter_kwargs=filters
            )
            # logger.debug("new less_list id: %d", new_less_list.id)
            lists_in_mods.append(
                {"mod_id": new_module.id, "less_list_id": new_less_list.id}
            )
            if len(list_lems) > 0:
                lems_in_lists[new_less_list.id] = list_lems

    for llim in lists_in_mods:
        # logger.debug("less_list_in_mod: %s", llim)
        filters = llim
        llim_in = schemas.LessListInModCreate(**filters)
        new_llim = crud_less_list_in_mod.get_or_create(
            db=db, obj_in=llim_in, filter_kwargs=filters
        )
        # logger.debug("new less_list_in_mod id: (%d, %d)", new_llim.mod_id, new_llim.less_list_id)

    # logger.debug("Lems in lists: %s", lems_in_lists)
    # create reverse lookup for which lems are in what lists
    lists_with_lems = defaultdict(list)
    for id, lems in lems_in_lists.items():
        for lem in lems:
            lists_with_lems[lem].append(id)
    # logger.debug("Lists with lems: %s", lists_with_lems)


def get_rows(module, chapter, content):
    # Logic for modules with simplified structures
    if module in ["ales", "other"]:
        return [
            {"module": module, "chapter": chapter, "topic": None, "lemma": v}
            for v in content
        ]

    # Logic for standard modules
    topic = content.get("topic")
    vocab_section = content.get("vocab", content) if "vocab" in content else content

    # We use a nested list comprehension here, which concat will later flatten
    return [
        {"module": module, "chapter": chapter, "topic": topic, "lemma": word}
        for pos, words in vocab_section.items()
        if pos != "topic"
        for word in (words if isinstance(words, list) else [words])
    ]


def get_all_words(vocab_list_path: str = VOCAB_LIST_LOC):  # type: ignore
    # Load the JSON file
    data = load_json(vocab_list_path)

    chapter_gen = (
        (mod, chap, cont) for mod, chaps in data.items() for chap, cont in chaps.items()  # type: ignore
    )

    rows = list(concat(get_rows(*item) for item in chapter_gen))  # type: ignore
    return [x["lemma"] for x in rows]


def make_tables(init_db_loc: str = INIT_DB_LOC):
    # logger.debug("Attempting to execute SQL from %s...", init_db_loc)

    try:
        # Read all commands from the SQL file
        with open(init_db_loc, "r") as f:
            # Split commands by semicolon for more robust execution
            sql_commands = [cmd.strip() for cmd in f.read().split(";") if cmd.strip()]

        # Connect to the database and execute commands within a transaction
        with SessionLocal() as connection:
            with connection.begin():
                print(f"Executing {len(sql_commands)} commands...")
                for command in sql_commands:
                    try:
                        connection.execute(text(command))
                    except Exception as e:
                        logger.error(
                            "An error was raised while executing init_db SQL commands: %s",
                            e,
                        )
                        pass

        print(f"Successfully executed all SQL commands.")

    except FileNotFoundError as fnfe:
        print(f"Error: SQL file not found at {init_db_loc}: {fnfe}")
        raise fnfe
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
        raise e
    finally:
        # Dispose of the engine connection pool
        print("Engine disposed.")


def init_database():
    # Create tables in db
    make_tables()

    all_words = get_all_words()

    print(f"a total of {str(len(all_words))} words, of which\
            {str(len(set(all_words)))} are unique")

    rand_samp = random.sample(all_words, 7)

    logger.debug("trying %d words: %s", len(rand_samp), rand_samp)

    with SessionLocal() as db:
        try:
            load_org_tables(db=db)
            load_words(db=db, word_s=rand_samp)
            process_lookup_queue(db=db)
            db.commit()
            logger.info("Data loaded and committed successfully")

        except Exception as e:
            db.rollback()
            logger.error("Error while loading data: %s", e)
            raise e


if __name__ == "__main__":
    init_database()
