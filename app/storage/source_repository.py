from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .db import SessionLocal
from .models import Source


class SourceRepository:
    def __init__(self, session=None):
        self._session = session or SessionLocal()

    def create(self, name: str, base_url: str, type: Optional[str] = None, config: Optional[dict] = None, fetch_interval_seconds: Optional[int] = None) -> str:
        s = Source(
            id=str(uuid.uuid4()),
            name=name,
            base_url=base_url,
            type=type,
            config=config or {},
            enabled=True,
            fetch_interval_seconds=fetch_interval_seconds,
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
            "fetch_interval_seconds": s.fetch_interval_seconds,
        }

    def list(self, enabled_only: bool = False) -> List[dict]:
        session = self._session
        q = session.query(Source)
        if enabled_only:
            q = q.filter(Source.enabled == True)
        rows = q.order_by(Source.name).all()
        return [{"id": r.id, "name": r.name, "base_url": r.base_url, "type": r.type, "enabled": r.enabled, "fetch_interval_seconds": r.fetch_interval_seconds} for r in rows]

    def update_last_fetch(self, source_id: str, when: Optional[datetime]):
        session = self._session
        s = session.query(Source).filter(Source.id == source_id).one_or_none()
        if not s:
            return False
        s.last_fetch_at = when
        session.add(s)
        session.commit()
        return True

    def update(self, source_id: str, fields: Dict[str, Any]) -> bool:
        """更新指定 source 的多个字段。只允许更新除 id 外的字段：name, base_url, type, config, enabled, fetch_interval_seconds, last_fetch_at。

        fields: dict 中可包含上述键。返回 True 表示成功，False 表示未找到 source。
        """
        allowed = {"name", "base_url", "type", "config", "enabled", "fetch_interval_seconds", "last_fetch_at"}
        session = self._session
        s = session.query(Source).filter(Source.id == source_id).one_or_none()
        if not s:
            return False
        for k, v in fields.items():
            if k in allowed:
                setattr(s, k, v)
        session.add(s)
        session.commit()
        return True

    def list_due_sources(self, now: datetime, default_interval_seconds: Optional[int] = None) -> List[dict]:
        """返回当前已到期需要拉取的 sources 列表。

        逻辑：只考虑 enabled 的 sources；优先使用 source.fetch_interval_seconds，若为 None 则使用传入的 default_interval_seconds；
        若最终间隔为 None 则忽略该 source（表示由外部/手动调度）。
        如果 last_fetch_at 为 None 则视为到期。
        """
        session = self._session
        rows = session.query(Source).filter(Source.enabled == True).all()
        due: List[dict] = []
        for r in rows:
            interval = r.fetch_interval_seconds if r.fetch_interval_seconds is not None else default_interval_seconds
            if interval is None:
                # no automatic schedule for this source
                continue
            if r.last_fetch_at is None:
                due.append({"id": r.id, "name": r.name, "base_url": r.base_url, "type": r.type, "fetch_interval_seconds": interval})
                continue
            elapsed = (now - r.last_fetch_at).total_seconds()
            if elapsed >= interval:
                due.append({"id": r.id, "name": r.name, "base_url": r.base_url, "type": r.type, "fetch_interval_seconds": interval})
        return due
