from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LlmClientGenreScore:
    tag: str
    score: float


@dataclass(frozen=True)
class LlmInferenceResult:
    genres: List[LlmClientGenreScore]
    model_name: str


class LlmInferenceClient(object):
    def infer_genres(self, audio_path: str) -> LlmInferenceResult:
        raise NotImplementedError


class StubLlmInferenceClient(LlmInferenceClient):
    def infer_genres(self, audio_path: str) -> LlmInferenceResult:
        _ = audio_path

        return LlmInferenceResult(
            genres=[
                LlmClientGenreScore(tag="indie rock", score=0.91),
                LlmClientGenreScore(tag="dream pop", score=0.73),
                LlmClientGenreScore(tag="ambient", score=0.41),
            ],
            model_name="llm-scaffold-v1",
        )


def get_default_llm_inference_client() -> LlmInferenceClient:
    return StubLlmInferenceClient()
