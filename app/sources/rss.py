from typing import Iterable

from bs4 import BeautifulSoup
from dateutil import parser as dateparser
import feedparser

from app.sources.base import BaseSource, FetchedItem

def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    # remove scripts/styles
    for s in soup(["script", "style"]):
        s.decompose()
    return soup.get_text(separator=" ", strip=True)


class RSSSource(BaseSource):
    def __init__(self, name: str, url: str):
        super().__init__(name, url)

    def fetch(self) -> Iterable[FetchedItem]:
        feed = feedparser.parse(self.base_url)
        for e in feed.entries:
            url = e.get("link")
            title = e.get("title", "")
            published = e.get("published") or e.get("updated")
            published_date = dateparser.parse(published) if published else None
            summary = e.get("summary", "")
            author = e.get("author", [])    # not all rss pages have authors value
            content = _clean_html(summary)
            yield FetchedItem(
                url=url,
                title=title,
                content=content,
                raw_content=summary,
                authors=author,
                source=self.name,
                published_date=published_date,
                meta={}
            )


if __name__ == '__main__':
    rss_source = RSSSource("IT之家", "https://www.ithome.com/rss")
    fetch_items_list = [item for item in rss_source.fetch()]
    print(fetch_items_list)

