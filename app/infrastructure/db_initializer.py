from app.infrastructure.models import Base
from app.infrastructure.database import engine

def initialize_database():
    """
    Ensure all tables exist at app startup.
    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)