from sqlalchemy import Column, String, DateTime
from app.infrastructure.database import Base

class MeliSite(Base):
    __tablename__ = "meli_sites"

    default_currency_id = Column(String, nullable=False)
    id = Column(String, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def to_dict(self):
        return {
            "default_currency_id": self.default_currency_id,
            "id": self.id,
            "name": self.name,
            "updated_at": self.updated_at
        }