from app.providers.base import GenreProvider, ProviderGenreScore, ProviderResult


class LlmGenreProvider(GenreProvider):
    def classify(self, audio_path: str) -> ProviderResult:
        # Scaffold-only deterministic output until the real LLM runtime is wired in.
        _ = audio_path

        return ProviderResult(
            genres=[
                ProviderGenreScore(tag="indie rock", score=0.91),
                ProviderGenreScore(tag="dream pop", score=0.73),
                ProviderGenreScore(tag="ambient", score=0.41),
            ],
            provider_name="llm",
            model_name="llm-scaffold-v1",
        )
