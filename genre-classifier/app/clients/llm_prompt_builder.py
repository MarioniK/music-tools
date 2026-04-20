import json
from typing import Optional, Sequence

from app.core import settings


def build_genre_inference_prompt(
    audio_reference: str,
    max_genres: int = settings.DEFAULT_LLM_GENRE_PROMPT_MAX_LABELS,
    candidate_genres: Optional[Sequence[str]] = None,
) -> str:
    if not isinstance(audio_reference, str) or not audio_reference.strip():
        raise ValueError("audio_reference must be a non-empty string")

    if not isinstance(max_genres, int) or max_genres <= 0:
        raise ValueError("max_genres must be a positive integer")

    normalized_candidates = _normalize_candidate_genres(candidate_genres)

    return "\n".join(
        [
            "PROMPT_VERSION: {}".format(settings.LLM_GENRE_PROMPT_VERSION),
            "ROLE: {}".format(settings.LLM_GENRE_PROMPT_ROLE),
            "TASK: infer music genres for the provided audio reference.",
            "OUTPUT_MODE: JSON_ONLY",
            'OUTPUT_SHAPE: {"genres":[{"tag":"string","score":0.0}]}',
            "OUTPUT_RULES:",
            '- return exactly one JSON object with a top-level "genres" list',
            '- each "genres" item must include "tag"; "score" is optional',
            "- do not return explanations, prose, markdown, code fences, or commentary",
            "- return fewer tags instead of inventing genres",
            '- return {"genres":[]} if nothing reliable can be inferred',
            "- never return more than {} genres".format(max_genres),
            "CONTROLLED_VOCABULARY_HINT:",
            "- if candidate genres are supplied, prefer them over inventing new labels",
            "INPUT:",
            "audio_reference={}".format(json.dumps(audio_reference)),
            "max_genres={}".format(max_genres),
            "candidate_genres={}".format(json.dumps(normalized_candidates)),
        ]
    )


def _normalize_candidate_genres(candidate_genres: Optional[Sequence[str]]) -> Optional[list]:
    if candidate_genres is None:
        return None

    normalized = []
    for item in candidate_genres:
        if isinstance(item, str):
            value = item.strip()
            if value:
                normalized.append(value)

    return normalized
