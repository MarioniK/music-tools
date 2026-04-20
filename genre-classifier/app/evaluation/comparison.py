import math

from app.core import settings


def extract_canonical_tag_sequence(result):
    return [item["tag"] for item in _extract_canonical_items(result)]


def compare_provider_results(
    legacy_result,
    llm_result,
    weak_score_threshold: float = settings.DEFAULT_LLM_GENRE_SCORE_THRESHOLD,
):
    legacy_items = _extract_canonical_items(legacy_result)
    llm_items = _extract_canonical_items(llm_result)

    legacy_tags = [item["tag"] for item in legacy_items]
    llm_tags = [item["tag"] for item in llm_items]

    legacy_rank_by_tag = {tag: index + 1 for index, tag in enumerate(legacy_tags)}
    llm_rank_by_tag = {tag: index + 1 for index, tag in enumerate(llm_tags)}

    shared_tags = [tag for tag in legacy_tags if tag in llm_rank_by_tag]
    legacy_only_tags = [tag for tag in legacy_tags if tag not in llm_rank_by_tag]
    llm_only_tags = [tag for tag in llm_tags if tag not in legacy_rank_by_tag]

    overlap_count = len(shared_tags)
    legacy_count = len(legacy_tags)
    llm_count = len(llm_tags)
    union_count = len(set(legacy_tags) | set(llm_tags))

    warning_flags = _build_warning_flags(
        legacy_items=legacy_items,
        llm_items=llm_items,
        shared_tags=shared_tags,
        weak_score_threshold=weak_score_threshold,
    )

    return {
        "legacy_provider_name": _read_attr_or_key(legacy_result, "provider_name"),
        "llm_provider_name": _read_attr_or_key(llm_result, "provider_name"),
        "legacy_model_name": _read_attr_or_key(legacy_result, "model_name"),
        "llm_model_name": _read_attr_or_key(llm_result, "model_name"),
        "legacy_tags": legacy_tags,
        "llm_tags": llm_tags,
        "shared_tags": shared_tags,
        "legacy_only_tags": legacy_only_tags,
        "llm_only_tags": llm_only_tags,
        "overlap_summary": {
            "legacy_tag_count": legacy_count,
            "llm_tag_count": llm_count,
            "shared_tag_count": overlap_count,
            "legacy_only_tag_count": len(legacy_only_tags),
            "llm_only_tag_count": len(llm_only_tags),
            "overlap_ratio_vs_legacy": _safe_ratio(overlap_count, legacy_count),
            "overlap_ratio_vs_llm": _safe_ratio(overlap_count, llm_count),
            "jaccard_similarity": _safe_ratio(overlap_count, union_count),
        },
        "ranking_drift": [
            {
                "tag": tag,
                "legacy_rank": legacy_rank_by_tag[tag],
                "llm_rank": llm_rank_by_tag[tag],
                "rank_delta": llm_rank_by_tag[tag] - legacy_rank_by_tag[tag],
                "absolute_rank_delta": abs(llm_rank_by_tag[tag] - legacy_rank_by_tag[tag]),
            }
            for tag in shared_tags
        ],
        "warning_flags": warning_flags,
        "warning_cases": [name for name, enabled in warning_flags.items() if enabled],
    }


def _extract_canonical_items(result):
    genres = _read_attr_or_key(result, "genres")
    if not isinstance(genres, list):
        raise RuntimeError("invalid comparison result genres")

    items_by_tag = {}
    ordered_tags = []

    for item in genres:
        tag = _normalize_tag(_read_attr_or_key(item, "tag"))
        if not tag:
            continue

        score = _coerce_numeric_score(_read_attr_or_key(item, "score"))

        if tag not in items_by_tag:
            items_by_tag[tag] = {"tag": tag, "score": score}
            ordered_tags.append(tag)
            continue

        if _should_replace_score(items_by_tag[tag]["score"], score):
            items_by_tag[tag]["score"] = score

    return [items_by_tag[tag] for tag in ordered_tags]


def _build_warning_flags(legacy_items, llm_items, shared_tags, weak_score_threshold: float):
    llm_scores = [item["score"] for item in llm_items if item["score"] is not None]

    legacy_count = len(legacy_items)
    llm_count = len(llm_items)

    # Partial-output warnings in this baseline are intentionally heuristic.
    # They use only relative tag counts and do not attempt a fuller semantic
    # judgment about output quality, confidence, or compatibility impact.
    return {
        "legacy_empty_output": legacy_count == 0,
        "llm_empty_output": llm_count == 0,
        "legacy_partial_output": legacy_count > 0 and llm_count > 0 and legacy_count < llm_count,
        "llm_partial_output": legacy_count > 0 and llm_count > 0 and llm_count < legacy_count,
        "llm_weak_top_score": bool(llm_scores) and max(llm_scores) < float(weak_score_threshold),
        "no_shared_tags": legacy_count > 0 and llm_count > 0 and not shared_tags,
    }


def _read_attr_or_key(value, name):
    if hasattr(value, name):
        return getattr(value, name)
    if isinstance(value, dict):
        return value.get(name)
    return None


def _normalize_tag(tag) -> str:
    normalized = str(tag or "").strip().lower()
    normalized = normalized.replace("-", " ").replace("_", " ")
    return " ".join(normalized.split())


def _coerce_numeric_score(score):
    if score is None:
        return None

    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numeric_score):
        return None

    return numeric_score


def _should_replace_score(existing_score, new_score) -> bool:
    if existing_score is None:
        return new_score is not None
    if new_score is None:
        return False
    return new_score > existing_score


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)
