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
from cytoolz import concat
from alite_backend.config import settings
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from alite_backend.db.db_session import engine, SessionLocal
from alite_backend.db.models import Base
from alite_backend.words import funcs
from alite_backend.words.pipeline import feed_data

load_dotenv()

VOCAB_LIST_LOC = os.getenv("VOCAB_LIST_LOC")
APP_DIR = os.getenv("APP_DIR")
INIT_DB_LOC = APP_DIR + "backend/src/alite_backend/db/init_db.sql"  # type:ignore

bodyLibDfLoc = "../syntagrus/bodyLibDf.json"
bodyTextDfLoc = "../syntagrus/bodyTextDf.json"
infDictLoc = "../syntagrus/infDict.json"

def load_org_tables(db: Session, org_data: dict):
    for row in org_data:
        mod_id = goc_module(db, row['module'])
        lesslist_id = goc_lesslist(db, row['chapter'], row['topic'])

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
        for pos, words in vocab_section.items() if pos != "topic"
        for word in (words if isinstance(words, list) else [words])
    ]
    
def get_all_words(vocab_list_loc: str = VOCAB_LIST_LOC):
    # Load the JSON file
    with open(vocab_list_loc, "r", encoding="utf-8") as f:  # type: ignore
        data = json.load(f)

    chapter_gen = (
    (mod, chap, cont) 
    for mod, chaps in data.items() 
    for chap, cont in chaps.items()
    )

    rows = list(concat(get_rows(*item) for item in chapter_gen))
    return [x['lemma'] for x in rows]


def make_tables(init_db_loc: str = INIT_DB_LOC):
    # logging.debug("Attempting to execute SQL from %s...", init_db_loc)

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
                        logging.error("An error was raised while executing init_db SQL commands: %s", e)
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
    
    problem_words = [
        "день",
        "ладно",
        "летом",
        "граница",
        "ухо",
        "рыжий"
    ]
    print(
        f"a total of {str(len(all_words))} words, of which\
            {str(len(set(all_words)))} are unique"
    )

    rand_samp = random.sample(all_words, 3)

    logging.debug("trying %d words: %s", len(rand_samp), rand_samp)

    with SessionLocal() as db:
        try:
            feed_data(db=db, word_s=rand_samp)

            db.commit()
            logging.info("Data loaded and committed successfully")

        except Exception as e:
            db.rollback()
            logging.error("Error while loading data: %s", e)
            raise e


if __name__ == "__main__":
    init_database()
