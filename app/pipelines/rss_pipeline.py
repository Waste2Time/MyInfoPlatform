import logging
from datetime import datetime, timezone
from typing import List, Tuple

from app.pipelines.base_pipeline import BasePipeline
from app.sources.rss import RSSSource
from app.storage.fetched_item_repository import FetchedItemRepository
from app.storage.source_repository import SourceRepository

logger = logging.getLogger(__name__)


class RSSPipeline(BasePipeline):
    """Service/pipeline to pull RSS feeds and save items.

    Usage:
        svc = RSSPipeline()
        svc.run_for_source(source_id)
        svc.run_all_enabled()
    """

    def __init__(self, source_repo: SourceRepository | None = None, item_repo: FetchedItemRepository | None = None):
        super().__init__(source_repo=source_repo, item_repo=item_repo)

    def run_for_source(self, source_id: str) -> List[Tuple[str, bool]]:
        """Fetch a single source by id, save items and update last_fetch_at.

        Returns list of (item_id, created) tuples saved from this source.
        Raises if source not found or on unexpected errors.
        """
        src = self.source_repo.get(source_id)
        if not src:
            raise ValueError(f"Source not found: {source_id}")

        if not src.get("enabled", True):
            logger.info("Source %s is disabled, skipping", source_id)
            return []

        url = src.get("base_url")
        name = src.get("name") or "unknown"

        logger.info("Fetching source %s (%s)", name, url)
        rss = RSSSource(name, url)
        results: List[Tuple[str, bool]] = []
        try:
            # iterate fetch() and use repository to persist — keep source layer decoupled from storage
            for it in rss.fetch():
                fp = self._calc_fingerprint(it.url, it.title, it.content, it.raw_content)
                data = {
                    "url": it.url,
                    "title": it.title,
                    "content": it.content,
                    "raw_content": it.raw_content,
                    "authors": it.authors,
                    "source": it.source,
                    "published_date": it.published_date,
                    "meta": it.meta or {},
                }
                try:
                    item_id, created = self.item_repo.upsert_by_fingerprint(fp, data)
                    results.append((item_id, created))
                except Exception:
                    logger.exception("Failed to persist item from source %s", name)
            # update last_fetch_at to now (UTC)
            self.source_repo.update_last_fetch(source_id, datetime.now(timezone.utc))
            logger.info("Finished fetching %s: %d items processed", name, len(results))
        except Exception:
            logger.exception("Failed to fetch source %s (%s)", name, url)
            raise
        return results


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    svc = RSSPipeline()
    # 示例：对所有启用的 source 执行一次拉取（基类实现）
    svc.run_all_enabled()
