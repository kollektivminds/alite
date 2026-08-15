"""
set up database
1. load vocab JSON file
2. load words and feed to db
3. CREATE module
"""

import logging

# from ..words.funcs import load_json
import os
import random

# import json
from collections import defaultdict
from pathlib import Path

import alite_backend.db.schemas as schemas
from alembic import command
from alembic.config import Config
from alite_backend.config import settings
from alite_backend.db.crud.user_crud import (
    crud_user,
    get_password_hash,
    verify_password,
)
from alite_backend.db.crud.word_crud import (
    crud_lem_in_less_list,
    crud_less_list,
    crud_less_list_in_mod,
    crud_module,
)
from alite_backend.db.db_session import SessionLocal, engine
from alite_backend.db.models import Base, EnumUserRole
from alite_backend.logging_config import setup_logging
from alite_backend.sentences.write_sentences_parallel import (
    run_parallel_sentence_pipeline,
)
from alite_backend.words.funcs import load_json, save_json
from alite_backend.words.pipeline import load_words
from alite_backend.words.process_queue import process_lookup_queue
from cytoolz import concat
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

setup_logging()

logger = logging.getLogger(__name__)

load_dotenv()

VOCAB_LIST_LOC = os.getenv("VOCAB_LIST_LOC")
APP_DIR = os.getenv("APP_DIR")
INIT_DB_LOC = APP_DIR + "/app/src/alite_backend/db/init_db.sql"  # type: ignore
corpus_location = "/app/src/alite_backend/sentences/raw/SynTagRus2022/"  # type: ignore
# bodyLibDfLoc = "../syntagrus/bodyLibDf.json"
# bodyTextDfLoc = "../syntagrus/bodyTextDf.json"
# infDictLoc = "../syntagrus/infDict.json"

if settings.ENV_MODE == "dev":
    DATABASE_URL = settings.DEV_DATABASE_URL
elif settings.ENV_MODE == "test":
    DATABASE_URL = settings.TEST_DATABASE_URL
elif settings.ENV_MODE == "prod":
    DATABASE_URL = settings.PROD_DATABASE_URL


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


def seed_superuser(db: Session) -> None:
    """
    Idempotent database seeding routine.
    Ensures essential roles, system defaults, and initial admin accounts exist.

    Args:
        db (Session): Active SQLAlchemy database session.
    """
    logger.info("Verifying initial database state...")

    # query the database to check if the superuser account already exists
    user = crud_user.get_by_email(db=db, email_input=settings.FIRST_SUPERUSER_EMAIL)

    # provision the user only if no existing matching record is found
    if not user:
        logger.info(
            "First superuser (%s) not found. Seeding initial admin account...",
            settings.FIRST_SUPERUSER_EMAIL,
        )

        # Build user creation payload using the validated Pydantic schema
        user_in = schemas.UserCreate(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            user_role=EnumUserRole.ADMIN,
            alias=None,
        )

        # Persist through the CRUD layer to ensure password hashing executed
        user = crud_user.create(db=db, obj_in=user_in)
        logger.info("Superuser '%s' successfully created.", user.username)
    else:
        logger.info("Superuser '%s' already exists. Skipping seed.", user.username)


def migrate_schema() -> None:
    """
    Executes Alembic migrations programmatically up to 'head'.

    Using programmatic migrations during container initialization guarantees
    that schema updates apply before any seeding or API logic executes,
    preventing race conditions between SQLModel and Alembic.
    """
    logger.info("Running programmatic database migrations...")

    engine.dispose()

    # locate the alembic.ini configuration file relative to the project root
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    alembic_cfg_path = base_dir / "alembic.ini"

    if not alembic_cfg_path.exists():
        logger.error("alembic.ini not found at path: %s", alembic_cfg_path)
        raise FileNotFoundError(f"Missing alembic.ini at {alembic_cfg_path}")

    # load Alembic configuration and override the database URL dynamically
    alembic_cfg = Config(str(alembic_cfg_path))
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    # apply all pending migrations safely
    try:
        logger.info("Acquiring Alembic migration context and applying upgrades...")

        command.upgrade(alembic_cfg, "head")

        logger.info("Database schema successfully synchronized to 'head'.")

    except OperationalError as op_err:
        logger.error(
            "Database operational error during migration (possible lock timeout): %s",
            op_err,
        )
        raise
    except Exception as exc:
        logger.exception("Unexpected failure during programmatic migration: %s", exc)
        raise


def run_isolated_migrations() -> None:
    """
    Executes Alembic migrations in an isolated process boundary.

    Engineering Principle:
    By instantiating a dedicated, single-use SQLAlchemy engine just for migrations
    and disposing of it immediately, we prevent connection pool sharing and eliminate
    lingering table locks that cause silent application freezes.
    """
    logger.info("Initializing isolated migration engine...")

    # 1. Create a dedicated, non-pooled engine for migrations to prevent lock contention
    migration_engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

    try:
        # 2. Test database connectivity and clear any stale transactions
        with migration_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
            logger.info("Database connection verified. Executing Alembic upgrade...")

        # 3. Locate alembic.ini configuration file
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        alembic_ini_path = base_dir / "alembic.ini"

        if not alembic_ini_path.exists():
            raise FileNotFoundError(
                f"Missing alembic.ini configuration at {alembic_ini_path}"
            )

        # 4. Configure Alembic programmatically
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

        # 5. Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema successfully synchronized to 'head'.")

    except Exception as exc:
        logger.exception(
            "Migration execution failed due to lock or connection error: %s", exc
        )
        raise exc
    finally:
        # CRITICAL: Always dispose of the temporary engine to release file descriptors and sockets
        migration_engine.dispose()
        logger.info("Migration engine successfully disposed.")


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


def make_tables(db: Session, init_db_loc: str = INIT_DB_LOC):
    # logger.debug("Attempting to execute SQL from %s...", init_db_loc)

    try:
        # read all commands from the SQL file
        with open(init_db_loc, "r") as f:
            # split commands by semicolon for more robust execution
            sql_commands = [cmd.strip() for cmd in f.read().split(";") if cmd.strip()]

        # connect to the database and execute commands within a transaction
        with db as connection:
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
        # dispose of the engine connection pool
        print("Engine disposed.")


def create_tables_from_models():
    """
    Replaces the raw SQL file execution with SQLAlchemy's native schema generation.
    This guarantees your database tables perfectly match models.py.
    """
    try:
        logger.info("Dropping all existing tables...")
        # completely wipes the database, taking the place of your manual DROP statements
        Base.metadata.drop_all(bind=engine)

        logger.info("Creating tables from models.py...")
        # reads models.py and issues the CREATE TABLE commands automatically
        Base.metadata.create_all(bind=engine)

        logger.info("Database schema successfully synchronized with models.")

    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")
        raise e
    finally:
        # dispose of the engine connection pool
        engine.dispose()
        logger.info("Engine disposed.")


def init_database():

    # get all words from curriculum
    all_words = get_all_words()

    print(
        f"gathered a total of {str(len(all_words))} words,"
        f"of which {str(len(set(all_words)))} are unique"
    )

    # rand_samp = random.sample(all_words, 11)

    # logger.debug("trying %d words: %s", len(rand_samp), rand_samp)

    # migrate_schema()
    run_isolated_migrations()

    with SessionLocal() as db:
        try:
            # create tables in db
            # make_tables(db=db)
            # create_tables_from_models()
            seed_superuser(db=db)
            load_org_tables(db=db)
            db.commit()
            logger.info("Database tables loaded and committed successfully")

        except Exception as e:
            db.rollback()
            logger.error("Error while loading tables data: %s", e)
            raise e

        try:
            load_words(db=db, word_s=all_words)
            # process_lookup_queue(db=db)
            db.commit()
            logger.info("Lemma data loaded and committed successfully")

        except Exception as e:
            db.rollback()
            logger.error("Error while loading lemma data: %s", e)
            raise e

        try:
            run_parallel_sentence_pipeline(db=db, corpus_directory=corpus_location)
            db.commit()
            logger.info("Sentences data loaded and committed successfully")

        except Exception as e:
            db.rollback()
            logger.error("Error while loading sentence data: %s", e)
            raise e


if __name__ == "__main__":
    init_database()
