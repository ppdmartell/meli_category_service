from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base

class CategoryTree(Base):
    """
    Represents ONE category tree per MercadoLibre site.
    (Example: MLU for Uruguay, MLA for Argentina)
    
    Stores only metadata. Category nodes stored in Category table (see meli_category.py file).
    """
    __tablename__ = "meli_category_trees"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # One tree per site_id (MLU, MLA, MLB, etc.)
    site_id = Column(String(10), nullable=False, unique=True)

    # Auto-updated whenever the tree is refreshed
    updated_at = Column(DateTime, nullable=False)

    # The top category_id ("All categories" root)
    root_category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationship: connects to all categories in this tree
    categories = relationship(
        "Category",
        back_populates="tree",
        cascade="all, delete-orphan"
    )
