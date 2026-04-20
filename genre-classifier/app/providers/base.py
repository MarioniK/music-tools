from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ProviderGenreScore:
    tag: str
    score: float


@dataclass(frozen=True)
class ProviderResult:
    genres: List[ProviderGenreScore]
    provider_name: str
    model_name: Optional[str] = None


class GenreProvider(object):
    def classify(self, audio_path: str) -> ProviderResult:
        raise NotImplementedError
