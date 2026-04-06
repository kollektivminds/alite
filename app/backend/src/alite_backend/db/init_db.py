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
from alite_backend.config import settings
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


def get_all_words(data):
    """
    This function extracts all vocabulary words from the provided JSON data.

    Args:
        data: The loaded JSON data.

    Returns:
        A list of all the words found in the "vocab" sections.
    """
    all_words = []
    textbook = data.get("textbook", {})

    for module in textbook.values():
        for lesson in module.values():
            vocab = lesson.get("vocab", {})
            for pos_words in vocab.values():
                all_words.extend(pos_words)

    return all_words


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

    # Load the JSON file
    with open(VOCAB_LIST_LOC, "r", encoding="utf-8") as f:  # type: ignore
        vocab_data = json.load(f)

    # Get all the words
    words = get_all_words(vocab_data)

    print(
        f"a total of {str(len(words))} words, of which\
            {str(len(set(words)))} are unique"
    )

    rand_samp = random.sample(words, 2)

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
