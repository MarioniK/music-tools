import math

import pytest

from app.clients.llm import LlmClientGenreScore, LlmInferenceResult
from app.providers.compat import map_validated_result_to_legacy_genres
from app.providers.llm import LlmGenreProvider
from app.providers.validation import validate_and_normalize_provider_result


def _build_provider_result(runtime_genres):
    class _GoldenCaseClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            assert audio_path == "/tmp/audio.wav"
            return LlmInferenceResult(
                genres=runtime_genres,
                model_name="golden-llm",
            )

    provider = LlmGenreProvider(client=_GoldenCaseClient())
    return provider.classify("/tmp/audio.wav")


@pytest.mark.parametrize(
    ("case_name", "runtime_genres", "expected_provider", "expected_validated", "validation_error"),
    [
        (
            "canonical_success",
            [
                LlmClientGenreScore(tag="indie rock", score=0.91),
                LlmClientGenreScore(tag="dream pop", score=0.73),
                LlmClientGenreScore(tag="ambient", score=0.41),
            ],
            [
                ("indie rock", 0.91),
                ("dream pop", 0.73),
                ("ambient", 0.41),
            ],
            [
                ("indie rock", 0.91),
                ("dream pop", 0.73),
                ("ambient", 0.41),
            ],
            None,
        ),
        (
            "alias_heavy_output",
            [
                LlmClientGenreScore(tag=" Dream Pop ", score=0.81),
                LlmClientGenreScore(tag="dream-pop", score=0.77),
                LlmClientGenreScore(tag="left field", score=0.65),
                LlmClientGenreScore(tag="leftfield", score=0.61),
            ],
            [
                ("dream pop", 0.81),
                ("leftfield", 0.65),
            ],
            [
                ("dream pop", 0.81),
                ("leftfield", 0.65),
            ],
            None,
        ),
        (
            "mixed_canonical_and_unknown",
            [
                LlmClientGenreScore(tag="indie rock", score=0.91),
                LlmClientGenreScore(tag="space yacht metal", score=0.89),
                LlmClientGenreScore(tag="dream pop", score=0.41),
            ],
            [
                ("indie rock", 0.91),
                ("dream pop", 0.41),
            ],
            [
                ("indie rock", 0.91),
                ("dream pop", 0.41),
            ],
            None,
        ),
        (
            "all_unknown_oov",
            [
                LlmClientGenreScore(tag="space yacht metal", score=0.81),
                LlmClientGenreScore(tag="cosmic whalewave", score=0.65),
            ],
            [],
            None,
            "no valid provider genres",
        ),
        (
            "weak_scored_output_below_threshold",
            [
                LlmClientGenreScore(tag="dream pop", score=0.39),
                LlmClientGenreScore(tag="ambient", score=0.2),
            ],
            [],
            None,
            "no valid provider genres",
        ),
        (
            "mixed_strong_and_weak",
            [
                LlmClientGenreScore(tag="indie rock", score=0.91),
                LlmClientGenreScore(tag="dream pop", score=0.39),
                LlmClientGenreScore(tag="ambient", score=0.41),
            ],
            [
                ("indie rock", 0.91),
                ("ambient", 0.41),
            ],
            [
                ("indie rock", 0.91),
                ("ambient", 0.41),
            ],
            None,
        ),
        (
            "partial_output_one_surviving_strong_tag",
            [
                LlmClientGenreScore(tag="space yacht metal", score=0.99),
                LlmClientGenreScore(tag="indie rock", score=0.9),
                LlmClientGenreScore(tag="dream pop", score=0.2),
            ],
            [
                ("indie rock", 0.9),
            ],
            [
                ("indie rock", 0.9),
            ],
            None,
        ),
        (
            "unscored_survival_case",
            [
                LlmClientGenreScore(tag="trip hop", score=None),
                LlmClientGenreScore(tag="indie rock", score=0.39),
                LlmClientGenreScore(tag="leftfield", score=None),
            ],
            [
                ("trip hop", None),
                ("leftfield", None),
            ],
            None,
            "no valid provider genres",
        ),
        (
            "invalid_scored_values_do_not_leak",
            [
                LlmClientGenreScore(tag="indie rock", score="0.91"),
                LlmClientGenreScore(tag="dream pop", score=math.nan),
                LlmClientGenreScore(tag="ambient", score=math.inf),
                LlmClientGenreScore(tag="trip hop", score=None),
                LlmClientGenreScore(tag="leftfield", score=0.65),
            ],
            [
                ("leftfield", 0.65),
                ("trip hop", None),
            ],
            [
                ("leftfield", 0.65),
            ],
            None,
        ),
    ],
)
def test_llm_golden_cases(case_name, runtime_genres, expected_provider, expected_validated, validation_error):
    provider_result = _build_provider_result(runtime_genres)

    assert [(item.tag, item.score) for item in provider_result.genres] == expected_provider, case_name

    if validation_error is not None:
        with pytest.raises(RuntimeError, match=validation_error):
            validate_and_normalize_provider_result(provider_result)
        return

    validated_result = validate_and_normalize_provider_result(provider_result)

    assert [(item.tag, item.score) for item in validated_result.genres] == expected_validated, case_name


def test_llm_golden_case_alias_heavy_output_preserves_existing_compatibility_shape():
    provider_result = _build_provider_result(
        [
            LlmClientGenreScore(tag=" Dream Pop ", score=0.81),
            LlmClientGenreScore(tag="dream-pop", score=0.77),
            LlmClientGenreScore(tag="left field", score=0.65),
            LlmClientGenreScore(tag="leftfield", score=0.61),
        ]
    )

    validated_result = validate_and_normalize_provider_result(provider_result)

    assert map_validated_result_to_legacy_genres(validated_result) == [
        {"tag": "dream pop", "prob": 0.81},
        {"tag": "leftfield", "prob": 0.65},
    ]
