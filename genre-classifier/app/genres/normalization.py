from dataclasses import dataclass
from typing import Iterable, List, Optional

from app.genre_normalization import normalize_genre_value
from app.genres.vocabulary import CANONICAL_ALLOWED_GENRES, GENRE_ALIAS_TO_CANONICAL


@dataclass(frozen=True)
class CanonicalGenreScore:
    tag: str
    score: float


def normalize_genre_label(value) -> Optional[str]:
    normalized = normalize_genre_value(value)
    if not normalized:
        return None

    canonical = GENRE_ALIAS_TO_CANONICAL.get(normalized, normalized)
    if canonical not in CANONICAL_ALLOWED_GENRES:
        return None

    return canonical


def canonicalize_genre_scores(items: Iterable) -> List[CanonicalGenreScore]:
    best_scores_by_tag = {}

    for item in items:
        canonical_tag = normalize_genre_label(getattr(item, "tag", None))
        if not canonical_tag:
            continue

        score = getattr(item, "score", None)
        existing_score = best_scores_by_tag.get(canonical_tag)
        if _should_replace_score(existing_score, score):
            best_scores_by_tag[canonical_tag] = score

    return [
        CanonicalGenreScore(tag=tag, score=score)
        for tag, score in best_scores_by_tag.items()
    ]


def _should_replace_score(existing_score, new_score) -> bool:
    if existing_score is None:
        return True

    if new_score is None:
        return False

    return new_score > existing_score
