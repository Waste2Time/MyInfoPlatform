import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple, Optional

from app.storage.source_repository import SourceRepository
from app.storage.fetched_item_repository import FetchedItemRepository

logger = logging.getLogger(__name__)


class BasePipeline(ABC):
    """Pipeline 基类，提供通用的源/项仓库注入与批量执行逻辑。

    子类需要实现 run_for_source(source_id) 来完成单个 source 的处理。
    提供 run_all_enabled() 的默认实现，会遍历启用的 sources 并调用 run_for_source。
    """

    def __init__(self, source_repo: Optional[SourceRepository] = None, item_repo: Optional[FetchedItemRepository] = None):
        self.source_repo = source_repo or SourceRepository()
        self.item_repo = item_repo or FetchedItemRepository()

    @abstractmethod
    def run_for_source(self, source_id: str) -> List[Tuple[str, bool]]:
        """处理单个 source，返回保存结果列表 (item_id, created)。"""
        raise NotImplementedError

    def run_all_enabled(self) -> None:
        """遍历所有启用的 source 并调用 run_for_source，单个 source 错误不会中断整个流程。"""
        sources = self.source_repo.list(enabled_only=True)
        for s in sources:
            sid = s.get("id")
            try:
                self.run_for_source(sid)
            except Exception:
                logger.exception("Error processing source %s", sid)

    def update_last_fetch(self, source_id: str, when: Optional[datetime]) -> bool:
        """更新 source 的 last_fetch_at 字段（委托给 SourceRepository）。"""
        return self.source_repo.update_last_fetch(source_id, when)

    def _calc_fingerprint(self, url: str | None, title: str | None, content: str | None, raw_content: str | None) -> str:
        parts = [url or "", title or "", content or raw_content or ""]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
