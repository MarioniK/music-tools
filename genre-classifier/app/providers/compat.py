from app.genre_normalization import normalize_audio_prediction_genres
from app.providers.schema import ValidatedProviderResult


def map_validated_result_to_legacy_genres(validated_result):
    if not isinstance(validated_result, ValidatedProviderResult):
        raise RuntimeError("invalid validated result")

    return [
        {
            "tag": item.tag,
            "prob": round(item.score, 4),
        }
        for item in validated_result.genres
    ]


def map_validated_result_to_legacy_genres_pretty(validated_result):
    if not isinstance(validated_result, ValidatedProviderResult):
        raise RuntimeError("invalid validated result")

    raw_genres = map_validated_result_to_legacy_genres(validated_result)
    return normalize_audio_prediction_genres(raw_genres, min_prob=0.05)
