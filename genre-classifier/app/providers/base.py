from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderGenreScore:
    tag: str
    score: float


@dataclass(frozen=True)
class ProviderResult:
    genres: list[ProviderGenreScore]
    provider_name: str
    model_name: str | None = None


class GenreProvider(Protocol):
    def classify(self, audio_path: str) -> ProviderResult:
        ...
