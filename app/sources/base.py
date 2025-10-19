from abc import ABC, abstractmethod
from typing import Iterable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FetchedItem:
    url: str
    title: str
    content: str | None
    raw_content: str | None
    authors: list[str] | None
    source: str | None
    published_date: datetime | None
    meta: dict

class BaseSource(ABC):
    def __init__(self, name: str, url: str):
        self.name = name
        self.base_url = url

    @abstractmethod
    def fetch(self) -> Iterable[FetchedItem]:
        """Yield FetchedItem objects."""
        raise NotImplementedError

