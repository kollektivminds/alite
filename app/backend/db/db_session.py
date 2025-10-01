import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PW = os.getenv("DB_PW")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# --- 1. Define the Database URL ---
# This is the connection string for your database.
# It's critical to load this from an environment variable for security.
# Format: postgresql://<user>:<password>@<host>:<port>/<dbname>
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- 2. Create the SQLAlchemy Engine ---
# The engine is the starting point for any SQLAlchemy application.
# It establishes the connection pool to the database.
engine = create_engine(DATABASE_URL)

# --- 3. Create a Session Factory ---
# This is a factory that will generate new Session objects (database connections).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 4. Create a Dependency for your API ---
# This function will be used by your FastAPI endpoints to get a database session.
# It ensures that the database connection is opened when the request starts
# and closed when the request is finished.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()