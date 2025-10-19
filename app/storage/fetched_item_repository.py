from typing import Optional, Tuple, List
from datetime import datetime, timezone
import uuid

from .db import get_session
from .models import Item


class FetchedItemRepository:
    """Repository for storing and querying fetched items using SQLAlchemy.

    Methods accept and return primitive Python types (dicts/strings) to keep the repository
    decoupled from domain dataclasses in app.sources.base.FetchedItem.
    """

    def __init__(self, session=None):
        # session param kept for compatibility, but prefer context-managed sessions via get_session
        self._session = session

    def upsert_by_fingerprint(self, fingerprint: Optional[str], data: dict) -> Tuple[str, bool]:
        """Insert a new item or update an existing one based on fingerprint.

        Args:
            fingerprint: content fingerprint or None
            data: dict with keys: url, title, content, raw_content, authors (list), source (name or id),
                  published_date (datetime), meta (dict), source_id (optional)

        Returns:
            (item_id, created) - created True if a new DB row was created.
        """
        # prefer using the context-managed session if none provided
        if self._session is None:
            with get_session() as session:
                return self._upsert(session, fingerprint, data)
        else:
            return self._upsert(self._session, fingerprint, data)

    def _upsert(self, session, fingerprint: Optional[str], data: dict) -> Tuple[str, bool]:
        # Try to find by fingerprint when available
        if fingerprint:
            existing = session.query(Item).filter(Item.fingerprint == fingerprint).one_or_none()
            if existing:
                # merge basic fields and meta
                if data.get("title"):
                    existing.title = data["title"]
                if data.get("content") is not None:
                    existing.content = data["content"]
                if data.get("raw_content") is not None:
                    existing.raw_content = data["raw_content"]
                if data.get("authors") is not None:
                    existing.authors = data["authors"]
                if data.get("published_date") is not None:
                    existing.published_at = data["published_date"]
                # merge meta dicts
                new_meta = (existing.meta or {})
                if data.get("meta"):
                    new_meta.update(data.get("meta") or {})
                existing.meta = new_meta
                # use timezone-aware UTC now
                existing.fetched_at = datetime.now(timezone.utc)
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing.id, False

        # Not found by fingerprint (or fingerprint was None) -> insert
        item = Item(
            id=str(uuid.uuid4()),
            source_id=data.get("source_id"),
            url=data.get("url"),
            title=data.get("title"),
            content=data.get("content"),
            raw_content=data.get("raw_content"),
            authors=data.get("authors"),
            published_at=data.get("published_date"),
            fetched_at=data.get("fetched_at") or datetime.now(timezone.utc),
            fingerprint=fingerprint,
            meta=data.get("meta") or {},
        )
        session.add(item)
        try:
            session.commit()
            session.refresh(item)
            return item.id, True
        except Exception:
            session.rollback()
            # race condition or unique constraint -> try to fetch existing by fingerprint
            if fingerprint:
                existing = session.query(Item).filter(Item.fingerprint == fingerprint).one_or_none()
                if existing:
                    return existing.id, False
            raise

    def get(self, item_id: str) -> Optional[dict]:
        if self._session is None:
            with get_session() as session:
                item = session.query(Item).filter(Item.id == item_id).one_or_none()
        else:
            item = self._session.query(Item).filter(Item.id == item_id).one_or_none()
        if not item:
            return None
        return item.to_dict()

    def list(self, limit: int = 100, offset: int = 0) -> List[dict]:
        if self._session is None:
            with get_session() as session:
                rows = session.query(Item).order_by(Item.published_at.desc().nulls_last(), Item.fetched_at.desc()).offset(offset).limit(limit).all()
        else:
            rows = self._session.query(Item).order_by(Item.published_at.desc().nulls_last(), Item.fetched_at.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in rows]
