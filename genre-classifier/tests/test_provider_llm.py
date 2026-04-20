from app.providers.base import ProviderResult
from app.providers.llm import LlmGenreProvider
from app.providers.schema import ValidatedProviderResult
from app.providers.validation import validate_and_normalize_provider_result


def test_llm_provider_returns_expected_provider_result_shape():
    provider = LlmGenreProvider()

    result = provider.classify("/tmp/audio.wav")

    assert isinstance(result, ProviderResult)
    assert result.provider_name == "llm"
    assert result.model_name == "llm-scaffold-v1"
    assert [(item.tag, item.score) for item in result.genres] == [
        ("indie rock", 0.91),
        ("dream pop", 0.73),
        ("ambient", 0.41),
    ]


def test_llm_provider_output_passes_existing_validation_pipeline():
    provider = LlmGenreProvider()

    provider_result = provider.classify("/tmp/audio.wav")
    validated_result = validate_and_normalize_provider_result(provider_result)

    assert isinstance(validated_result, ValidatedProviderResult)
    assert validated_result.provider_name == "llm"
    assert validated_result.model_name == "llm-scaffold-v1"
    assert [(item.tag, item.score) for item in validated_result.genres] == [
        ("indie rock", 0.91),
        ("dream pop", 0.73),
        ("ambient", 0.41),
    ]
    assert validated_result.total_items_received == 3
    assert validated_result.total_items_kept == 3
    assert validated_result.dropped_items_count == 0
