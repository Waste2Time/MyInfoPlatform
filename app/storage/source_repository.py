from typing import Optional, List
from datetime import datetime
import uuid

from .db import SessionLocal
from .models import Source


class SourceRepository:
    def __init__(self, session=None):
        self._session = session or SessionLocal()

    def create(self, name: str, base_url: str, type: Optional[str] = None, config: Optional[dict] = None) -> str:
        s = Source(
            id=str(uuid.uuid4()),
            name=name,
            base_url=base_url,
            type=type,
            config=config or {},
            enabled=True,
        )
        session = self._session
        session.add(s)
        session.commit()
        session.refresh(s)
        return s.id

    def get(self, source_id: str) -> Optional[dict]:
        session = self._session
        s = session.query(Source).filter(Source.id == source_id).one_or_none()
        if not s:
            return None
        return {
            "id": s.id,
            "name": s.name,
            "base_url": s.base_url,
            "type": s.type,
            "config": s.config,
            "last_fetch_at": s.last_fetch_at,
            "enabled": s.enabled,
        }

    def list(self, enabled_only: bool = False) -> List[dict]:
        session = self._session
        q = session.query(Source)
        if enabled_only:
            q = q.filter(Source.enabled == True)
        rows = q.order_by(Source.name).all()
        return [{"id": r.id, "name": r.name, "base_url": r.base_url, "type": r.type, "enabled": r.enabled} for r in rows]

    def update_last_fetch(self, source_id: str, when: Optional[datetime]):
        session = self._session
        s = session.query(Source).filter(Source.id == source_id).one_or_none()
        if not s:
            return False
        s.last_fetch_at = when
        session.add(s)
        session.commit()
        return True

