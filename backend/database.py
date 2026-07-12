import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

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
