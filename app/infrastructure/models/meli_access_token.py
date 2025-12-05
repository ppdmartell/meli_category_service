from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from app.infrastructure.database import Base


class MeliAccessToken(Base):
    __tablename__ = "meli_access_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    singleton_key = Column(Integer, nullable=False, default=1)     # This allows to have only one row
    access_token = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_in_seconds = Column(Integer, nullable=False)
    access_token_expires_at = Column(DateTime, nullable=False)
    refresh_token_expires_at = Column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint("singleton_key", name="uix_singleton_key"),) # Also enforces 1-row
