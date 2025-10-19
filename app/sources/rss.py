from typing import Iterable
from datetime import timezone

from bs4 import BeautifulSoup
from dateutil import parser as dateparser
import feedparser

from app.sources.base import BaseSource, FetchedItem


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    # remove scripts/styles
    for s in soup(["script", "style"]):
        s.decompose()
    # 不传参数给 get_text，避免类型检查器误报；之后合并空白
    text = soup.get_text().strip()
    return " ".join(text.split())


class RSSSource(BaseSource):
    def __init__(self, name: str, url: str):
        super().__init__(name, url)

    def fetch(self) -> Iterable[FetchedItem]:
        """从 RSS/Atom feed 拉取并产生 FetchedItem（不做持久化）。"""
        feed = feedparser.parse(self.base_url)
        for e in feed.entries:
            url = e.get("link")
            title = e.get("title", "")
            published = e.get("published") or e.get("updated") or e.get("published_parsed")
            published_date = None
            if published:
                try:
                    published_date = dateparser.parse(str(published))
                except Exception:
                    published_date = None
            if published_date and published_date.tzinfo is None:
                published_date = published_date.replace(tzinfo=timezone.utc)

            raw_content = e.get("summary", "")

            # 解析作者字段，兼容 authors 列表或单一 author 字符串
            authors = None
            if e.get("authors"):
                try:
                    authors = [a.get("name") if isinstance(a, dict) else str(a) for a in e.get("authors")]
                except Exception:
                    authors = [str(a) for a in e.get("authors")]
            elif e.get("author"):
                authors = [e.get("author")]

            content = _clean_html(raw_content)
            yield FetchedItem(
                url=url,
                title=title,
                content=content,
                raw_content=raw_content,
                authors=authors,
                source=self.name,
                published_date=published_date,
                meta={}
            )


if __name__ == '__main__':
    rss_source = RSSSource("IT之家", "https://www.ithome.com/rss")
    fetch_items_list = [item for item in rss_source.fetch()]
    print(fetch_items_list)
