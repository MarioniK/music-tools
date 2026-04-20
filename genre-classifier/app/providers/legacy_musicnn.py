from app.core import settings
from app.providers.base import ProviderGenreScore, ProviderResult


def _run_legacy_musicnn_classification(audio_path: str):
    from app.services.classify import run_genre_classification

    return run_genre_classification(audio_path)


class LegacyMusiCNNProvider:
    def classify(self, audio_path: str) -> ProviderResult:
        genres = _run_legacy_musicnn_classification(audio_path)
        return ProviderResult(
            genres=[
                ProviderGenreScore(tag=item["tag"], score=float(item["prob"]))
                for item in genres
            ],
            provider_name="legacy_musicnn",
            model_name=settings.MODEL_PB.stem,
        )
