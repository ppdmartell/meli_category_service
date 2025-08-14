from app.infrastructure.database import engine, Base # imports all models via __init__.py
from app.infrastructure import models # # This runs __init__.py, importing all models

def initialize_database():
    """
    Ensure all tables exist at app startup.
    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)