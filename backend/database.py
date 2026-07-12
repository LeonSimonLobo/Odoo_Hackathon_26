import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
loaded = load_dotenv(dotenv_path=env_path)

# Default to SQLite file inside the backend directory, but allow postgres/mysql config
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///assetflow.db")

engine = create_engine(
    DATABASE_URL,
    # connect_args={"check_same_thread": False} is only required for SQLite
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
