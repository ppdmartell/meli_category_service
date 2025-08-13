from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.env import Settings

Settings.load()
DB_URL = Settings.DB_URL
engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

def get_session():
    return SessionLocal()
