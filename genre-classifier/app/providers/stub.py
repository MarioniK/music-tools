from app.providers.base import ProviderGenreScore, ProviderResult


class StubGenreProvider:
    def classify(self, audio_path: str) -> ProviderResult:
        return ProviderResult(
            genres=[ProviderGenreScore(tag="stub genre", score=1.0)],
            provider_name="stub",
            model_name="stub-v1",
        )
