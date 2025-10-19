"""SQLAlchemy ORM models for MyInfoPlatform.
Designed to work with PostgreSQL (JSON/UUID) but falls back to SQLite types where necessary.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, func, UniqueConstraint, ForeignKey
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from app.storage.db import Base
import uuid
import typing as t


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    name = Column(String(255), nullable=False)
    base_url = Column(Text, nullable=False)
    type = Column(String(50), nullable=True)
    config = Column(JSON, nullable=True)
    last_fetch_at = Column(DateTime(timezone=True), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationship
    items = relationship("Item", back_populates="source_obj")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Source id={self.id} name={self.name} url={self.base_url}>"


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_items_fingerprint"),
    )

    id = Column(String(36), primary_key=True, default=_new_uuid)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=True)
    url = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)

    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    fingerprint = Column(String(255), nullable=True, index=True)
    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    source_obj = relationship("Source", back_populates="items")

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "raw_content": self.raw_content,
            "authors": self.authors,
            "published_at": self.published_at,
            "fetched_at": self.fetched_at,
            "fingerprint": self.fingerprint,
            "meta": self.meta,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Item id={self.id} title={self.title!r}>"
