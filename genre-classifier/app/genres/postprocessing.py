import math
from dataclasses import dataclass
from typing import Iterable, List

from app.core import settings
from app.genres.normalization import canonicalize_genre_scores


@dataclass(frozen=True)
class PostprocessedGenreScore:
    tag: str
    score: float


def postprocess_llm_genre_scores(
    items: Iterable,
    top_n: int = settings.DEFAULT_LLM_GENRE_POSTPROCESS_TOP_N,
    score_threshold: float = settings.DEFAULT_LLM_GENRE_SCORE_THRESHOLD,
) -> List[PostprocessedGenreScore]:
    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    canonical_items = canonicalize_genre_scores(items)
    valid_items = _filter_invalid_scored_items(canonical_items)
    ranked_items = _rank_postprocessed_items(valid_items)
    truncated_items = ranked_items[:top_n]
    filtered_items = _filter_items_below_threshold(truncated_items, score_threshold)

    return [
        PostprocessedGenreScore(tag=item.tag, score=item.score)
        for item in filtered_items
    ]


def _filter_invalid_scored_items(items: Iterable) -> List:
    result = []

    for item in items:
        score = getattr(item, "score", None)
        if _is_missing_score(score) or _has_numeric_score(score):
            result.append(item)

    return result


def _rank_postprocessed_items(items: Iterable) -> List:
    scored_items = []
    unscored_items = []

    for index, item in enumerate(items):
        score = getattr(item, "score", None)
        if _has_numeric_score(score):
            scored_items.append((index, item))
        else:
            unscored_items.append((index, item))

    scored_items.sort(key=lambda pair: (-float(pair[1].score), pair[0]))

    return [item for _, item in scored_items] + [item for _, item in unscored_items]


def _filter_items_below_threshold(items: Iterable, score_threshold: float) -> List:
    result = []

    for item in items:
        score = getattr(item, "score", None)
        if _has_numeric_score(score) and float(score) < float(score_threshold):
            continue

        result.append(item)

    return result


def _has_numeric_score(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _is_missing_score(value) -> bool:
    return value is None
