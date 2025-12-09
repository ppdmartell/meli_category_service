from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DateTime, Index
)
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base

class Category(Base):
    """
    Represents one MercadoLibre category node.
    This table holds the full tree (all nodes).
    """

    __tablename__ = "meli_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tree_id = Column(
        Integer,
        ForeignKey("meli_category_trees.id", ondelete="CASCADE"),
        nullable=False
    )

    # Also store site_id explicitly for easier filtering
    site_id = Column(String(10), nullable=False)

    # MeLi-provided fields
    category_id = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    parent_id = Column(String(50), nullable=True)  # MeLi parent category_id
    fragile = Column(Boolean, nullable=True, default=False)

    # Self-referencing DB FKs
    parent_db_id = Column(
        Integer,
        ForeignKey("meli_categories.id", ondelete="SET NULL"),
        nullable=True
    )

    # Helper fields to speed up queries
    status = Column(String(50), nullable=False, default="completed")  # completed, pending, in_progress
    depth = Column(Integer, nullable=False, default=0)
    total_items_in_this_category = Column(Integer, nullable=False, default=0)
    full_path = Column(String(1000), nullable=True)
    has_children = Column(Boolean, nullable=False, default=False)
    total_children = Column(Integer, nullable=False, default=0)

    persisted_at = Column(DateTime, nullable=False)
    created_in_meli_at = Column(DateTime, nullable=False)    # Could be old or a new category

    # Backref to tree metadata
    tree = relationship("CategoryTree", back_populates="meli_categories")

    # Parent/children relations inside this table
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
        uselist=False
    )

    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
