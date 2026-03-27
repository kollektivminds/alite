"""
set up database
1. load vocab JSON file
2. load words and feed to db
3. CREATE module
"""
#from ..words.funcs import load_json
import os
import random
import logging
import json
from alite_backend.config import settings
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from alite_backend.db.db_session import engine
import alite_backend
from alite_backend.db.models import Base
from alite_backend.words import funcs
#from .. words.ews import *
from alite_backend.words.pipeline import feed_data

load_dotenv()

DB_URL = settings.DATABASE_URL
VOCAB_LIST_LOC = os.getenv("VOCAB_LIST_LOC")
APP_DIR = os.getenv("APP_DIR")
INIT_DB_LOC = APP_DIR+"backend/src/alite_backend/db/init_db.sql"

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

# Load the JSON file
with open(VOCAB_LIST_LOC, 'r', encoding='utf-8') as f: #type: ignore
    vocab_data = json.load(f)

# Get all the words
words = get_all_words(vocab_data)

# Print the list of words
print(
    f"a total of {str(len(words))} words, of which,\
        {str(len(set(words)))} words are unique"
    )

rand_samp = random.sample(words, 2)

logging.debug("trying %d words: %s", len(rand_samp), rand_samp)

feed_data(rand_samp)

# --- Create the SQLAlchemy Engine ---
engine = create_engine(DB_URL)  # type: ignore
print(f"Attempting to execute SQL from {INIT_DB_LOC}...")

try:
    # Read all commands from the SQL file
    with open(INIT_DB_LOC, "r") as f:
        # Split commands by semicolon for more robust execution
        sql_commands = [cmd.strip() for cmd in f.read().split(";") if cmd.strip()]

    # Connect to the database and execute commands within a transaction
    with engine.connect() as connection:
        # Begin a transaction explicitly
        with connection.begin():
            print(f"Executing {len(sql_commands)} commands...")
            for command in sql_commands:
                connection.execute(text(command))

    print(f"Successfully executed all SQL commands.")

except FileNotFoundError:
    print(f"Error: SQL file not found at {INIT_DB_LOC}")
except Exception as e:
    print(f"An error occurred during database initialization: {e}")
finally:
    # Dispose of the engine connection pool
    engine.dispose()
    print("Engine disposed.")
