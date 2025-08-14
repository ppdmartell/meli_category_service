from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config.env import Settings

Settings.load()
DB_URL = Settings.DB_URL
engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

# This is THE Base for the whole app
Base = declarative_base()

def get_session():
    return SessionLocal()
