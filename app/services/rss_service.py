from typing import List, Optional, Any, Dict
from app.utils.logger import logger


class RSSService:
    """Service 层：为 Controller 提供主页面列表与文章详情数据。

    注入：
      - fetched_repo: 提供 list(limit, offset) 和 get(item_id)，返回 dict（包含 fetched_at 和 source_id 等）。
      - source_repo: 提供 get(source_id) 返回包含 name 的 dict。

    返回的数据为纯 Python dict，便于 Controller 将其映射到 Pydantic 模型。
    """

    def __init__(self, fetched_repo: Any, source_repo: Any):
        self.fetched_repo = fetched_repo
        self.source_repo = source_repo

    def list_summaries(self, limit: int = 20, offset: int = 0, status: str = "all") -> List[Dict[str, Any]]:
        """返回文章摘要列表：每项包含 id, title, summary, fetched_at, source_name

        status: "all" | "unread" | "read" | "starred"
        """
        try:
            items = self.fetched_repo.list(limit=limit, offset=offset)
        except Exception:
            logger.exception("RSSService: failed to list items from fetched_repo")
            raise

        results: List[Dict[str, Any]] = []
        # 缓存 source_name，避免重复查询
        source_name_cache: Dict[Optional[str], Optional[str]] = {}

        for it in items:
            # 过滤逻辑
            is_read = bool(it.get("is_read"))
            is_starred = bool(it.get("is_starred"))
            if status == "unread" and is_read:
                continue
            if status == "read" and not is_read:
                continue
            if status == "starred" and not is_starred:
                continue

            source_id = it.get("source_id")
            if source_id not in source_name_cache:
                try:
                    src = self.source_repo.get(source_id) if source_id else None
                    source_name_cache[source_id] = src.get("name") if src else None
                except Exception:
                    logger.exception("RSSService: failed to get source for id %s", source_id)
                    source_name_cache[source_id] = None

            summary = it.get("summary") or ( (it.get("content") or "")[:200] )
            results.append({
                "id": it.get("id"),
                "title": it.get("title") or "",
                "summary": summary,
                "fetched_at": it.get("fetched_at"),
                "source_name": source_name_cache.get(source_id),
                "is_read": is_read,
                "is_starred": is_starred,
            })
        return results

    def get_article(self, item_id: str) -> Optional[Dict[str, Any]]:
        """返回单篇文章详情：包含 id, title, content, published_at, fetched_at, source_id, source_name, url"""
        try:
            it = self.fetched_repo.get(item_id)
        except Exception:
            logger.exception("RSSService: failed to get item %s from fetched_repo", item_id)
            raise

        if not it:
            return None

        source_id = it.get("source_id")
        source_name = None
        if source_id:
            try:
                src = self.source_repo.get(source_id)
                source_name = src.get("name") if src else None
            except Exception:
                logger.exception("RSSService: failed to get source for id %s", source_id)

        return {
            "id": it.get("id"),
            "title": it.get("title") or "",
            "content": it.get("content") or "",
            "published_at": it.get("published_at"),
            "fetched_at": it.get("fetched_at"),
            "source_id": source_id,
            "source_name": source_name,
            "url": it.get("url"),
            "is_read": bool(it.get("is_read")),
            "is_starred": bool(it.get("is_starred")),
        }

    def update_flags(self, item_id: str, is_read: Optional[bool] = None, is_starred: Optional[bool] = None) -> bool:
        """更新指定文章的 is_read / is_starred 标记，返回是否成功。"""
        fields = {}
        if is_read is not None:
            fields["is_read"] = bool(is_read)
        if is_starred is not None:
            fields["is_starred"] = bool(is_starred)
        if not fields:
            return False
        try:
            return bool(self.fetched_repo.update_flags(item_id, fields))
        except Exception:
            logger.exception("RSSService: failed to update flags for %s", item_id)
            raise
