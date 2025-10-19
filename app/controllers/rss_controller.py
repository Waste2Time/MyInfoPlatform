from typing import List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from app.utils.logger import logger


class ArticleSummary(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    fetched_at: Optional[datetime] = None
    source_name: Optional[str] = None
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None


class ArticleDetail(BaseModel):
    id: str
    title: str
    content: str
    published_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    url: Optional[str] = None
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None


class FlagsUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None


class RSSController:
    """负责返回 RSS 文章相关的 API。构造时注入一个 RSSService（或具有等价方法的对象）。

    service 必须实现：
      - list_summaries(limit, offset, status) -> List[dict]
      - get_article(item_id) -> dict | None
      - update_flags(item_id, is_read=None, is_starred=None) -> bool

    使用方法：
        from app.controllers.rss_controller import RSSController
        router = RSSController(rss_service).router
        app.include_router(router, prefix="/rss")
    """

    def __init__(self, service: Any, prefix: str = ""):
        self.service = service
        self.router = APIRouter(prefix=prefix)
        self._register_routes()

    def _register_routes(self):
        self.router.get("/", response_model=List[ArticleSummary])(self.list_articles)
        self.router.get("/{item_id}", response_model=ArticleDetail)(self.get_article)
        self.router.patch("/{item_id}/flags")(self.update_flags)

    async def list_articles(self, limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), status: str = Query("all")):
        try:
            items = self.service.list_summaries(limit=limit, offset=offset, status=status)
            results: List[ArticleSummary] = []
            for it in items:
                results.append(ArticleSummary(
                    id=str(it.get("id")),
                    title=it.get("title") or "",
                    summary=it.get("summary"),
                    fetched_at=it.get("fetched_at"),
                    source_name=it.get("source_name"),
                    is_read=it.get("is_read"),
                    is_starred=it.get("is_starred"),
                ))
            return results
        except Exception:
            logger.exception("RSSController: failed to list articles")
            raise HTTPException(status_code=500, detail="无法获取文章列表")

    async def get_article(self, item_id: str):
        try:
            it = self.service.get_article(item_id)
            if not it:
                raise HTTPException(status_code=404, detail="文章未找到")
            return ArticleDetail(
                id=str(it.get("id")),
                title=it.get("title") or "",
                content=it.get("content") or "",
                published_at=it.get("published_at"),
                fetched_at=it.get("fetched_at"),
                source_id=it.get("source_id"),
                source_name=it.get("source_name"),
                url=it.get("url"),
                is_read=it.get("is_read"),
                is_starred=it.get("is_starred"),
            )
        except HTTPException:
            raise
        except Exception:
            logger.exception("RSSController: failed to get article %s", item_id)
            raise HTTPException(status_code=500, detail="无法获取文章详情")

    async def update_flags(self, item_id: str, flags: FlagsUpdate):
        try:
            ok = self.service.update_flags(item_id, is_read=flags.is_read, is_starred=flags.is_starred)
            if not ok:
                raise HTTPException(status_code=404, detail="文章未找到或未更新")
            return {"ok": True}
        except HTTPException:
            raise
        except Exception:
            logger.exception("RSSController: failed to update flags for %s", item_id)
            raise HTTPException(status_code=500, detail="无法更新文章标记")
