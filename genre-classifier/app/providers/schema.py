from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ValidatedGenreItem:
    tag: str
    score: float


@dataclass(frozen=True)
class ValidatedProviderResult:
    genres: List[ValidatedGenreItem]
    provider_name: str
    model_name: Optional[str] = None
    total_items_received: int = 0
    total_items_kept: int = 0
    dropped_items_count: int = 0
