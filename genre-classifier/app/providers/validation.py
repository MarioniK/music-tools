import math

from app.providers.base import ProviderGenreScore, ProviderResult
from app.providers.schema import ValidatedGenreItem, ValidatedProviderResult


def _normalize_tag(tag) -> str:
    normalized = str(tag).strip().lower()
    normalized = normalized.replace("-", " ").replace("_", " ")
    return " ".join(normalized.split())


def validate_and_normalize_provider_result(provider_result, top_n=8) -> ValidatedProviderResult:
    if not isinstance(top_n, int) or top_n <= 0:
        raise RuntimeError("invalid top_n")

    if not isinstance(provider_result, ProviderResult):
        raise RuntimeError("invalid provider result")

    if not isinstance(provider_result.genres, list):
        raise RuntimeError("invalid provider genres")

    total_items_received = len(provider_result.genres)
    best_scores_by_tag = {}

    for item in provider_result.genres:
        if not isinstance(item, ProviderGenreScore):
            continue

        tag = _normalize_tag(item.tag)
        if not tag:
            continue

        try:
            score = float(item.score)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(score):
            continue

        existing_score = best_scores_by_tag.get(tag)
        if existing_score is None or score > existing_score:
            best_scores_by_tag[tag] = score

    validated_genres = [
        ValidatedGenreItem(tag=tag, score=score)
        for tag, score in best_scores_by_tag.items()
    ]
    validated_genres.sort(key=lambda item: (-item.score, item.tag))
    validated_genres = validated_genres[:top_n]

    if not validated_genres:
        raise RuntimeError("no valid provider genres")

    total_items_kept = len(validated_genres)

    return ValidatedProviderResult(
        genres=validated_genres,
        provider_name=provider_result.provider_name,
        model_name=provider_result.model_name,
        total_items_received=total_items_received,
        total_items_kept=total_items_kept,
        dropped_items_count=total_items_received - total_items_kept,
    )
