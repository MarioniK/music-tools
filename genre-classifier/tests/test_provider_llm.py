import pytest

from app.clients.llm import (
    LlmClientGenreScore,
    LlmInferenceResult,
    LocalHttpLlmInferenceClient,
    StubLlmInferenceClient,
    get_default_llm_inference_client,
)
from app.providers.base import ProviderResult
from app.providers.llm import LlmGenreProvider
from app.providers.schema import ValidatedProviderResult
from app.providers.validation import validate_and_normalize_provider_result


def test_stub_llm_client_returns_expected_structured_result():
    client = StubLlmInferenceClient()

    result = client.infer_genres("/tmp/audio.wav")

    assert isinstance(result, LlmInferenceResult)
    assert result.model_name == "llm-scaffold-v1"
    assert [(item.tag, item.score) for item in result.genres] == [
        ("indie rock", 0.91),
        ("dream pop", 0.73),
        ("ambient", 0.41),
    ]


def test_default_llm_client_remains_stub():
    class _Settings:
        LLM_CLIENT_STUB = "stub"
        LLM_CLIENT_LOCAL_HTTP = "local_http"

        @staticmethod
        def get_configured_llm_client_name():
            return "stub"

    client = get_default_llm_inference_client(settings_module=_Settings)

    assert isinstance(client, StubLlmInferenceClient)


def test_explicit_local_http_config_selects_real_client_boundary():
    class _Settings:
        LLM_CLIENT_STUB = "stub"
        LLM_CLIENT_LOCAL_HTTP = "local_http"

        @staticmethod
        def get_configured_llm_client_name():
            return "local_http"

        @staticmethod
        def get_configured_llm_local_http_endpoint():
            return "http://127.0.0.1:11434/infer"

        @staticmethod
        def get_configured_llm_local_http_timeout_seconds():
            return 3.5

    client = get_default_llm_inference_client(settings_module=_Settings)

    assert isinstance(client, LocalHttpLlmInferenceClient)
    assert client._endpoint == "http://127.0.0.1:11434/infer"
    assert client._timeout_seconds == 3.5


def test_local_http_client_requires_endpoint():
    class _Settings:
        LLM_CLIENT_STUB = "stub"
        LLM_CLIENT_LOCAL_HTTP = "local_http"

        @staticmethod
        def get_configured_llm_client_name():
            return "local_http"

        @staticmethod
        def get_configured_llm_local_http_endpoint():
            return ""

        @staticmethod
        def get_configured_llm_local_http_timeout_seconds():
            return 5.0

    with pytest.raises(ValueError, match="LLM_LOCAL_HTTP_ENDPOINT is required for local_http client"):
        get_default_llm_inference_client(settings_module=_Settings)


def test_local_http_client_parses_valid_response(monkeypatch):
    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"model_name":"local-llm-v1","genres":[{"tag":"indie rock","score":0.82},{"tag":"dream pop","score":0.51}]}'

    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["method"] = http_request.get_method()
        captured["body"] = http_request.data
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("app.clients.llm.request.urlopen", fake_urlopen)

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    result = client.infer_genres("/tmp/audio.wav")

    assert captured["url"] == "http://127.0.0.1:11434/infer"
    assert captured["method"] == "POST"
    assert captured["body"] == b'{"audio_path": "/tmp/audio.wav"}'
    assert captured["timeout"] == 4.0
    assert isinstance(result, LlmInferenceResult)
    assert result.model_name == "local-llm-v1"
    assert [(item.tag, item.score) for item in result.genres] == [
        ("indie rock", 0.82),
        ("dream pop", 0.51),
    ]


def test_local_http_client_rejects_invalid_response(monkeypatch):
    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"model_name":"local-llm-v1","genres":"not-a-list"}'

    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: _FakeResponse(),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    with pytest.raises(RuntimeError, match="invalid local llm runtime response"):
        client.infer_genres("/tmp/audio.wav")


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


def test_llm_provider_uses_client_boundary():
    client_calls = []

    class _FakeLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            client_calls.append(audio_path)
            return LlmInferenceResult(
                genres=[
                    LlmClientGenreScore(tag="leftfield", score=0.88),
                    LlmClientGenreScore(tag="trip hop", score=0.67),
                ],
                model_name="fake-llm-client",
            )

    provider = LlmGenreProvider(client=_FakeLlmClient())

    result = provider.classify("/tmp/audio.wav")

    assert client_calls == ["/tmp/audio.wav"]
    assert result.provider_name == "llm"
    assert result.model_name == "fake-llm-client"
    assert [(item.tag, item.score) for item in result.genres] == [
        ("leftfield", 0.88),
        ("trip hop", 0.67),
    ]


def test_llm_provider_logs_inference_start_and_success(caplog):
    provider = LlmGenreProvider()

    with caplog.at_level("INFO", logger="genre_classifier"):
        result = provider.classify("/tmp/audio.wav")

    assert result.provider_name == "llm"
    assert "event=llm_inference_started provider_name=llm client_name=StubLlmInferenceClient" in caplog.text
    assert "event=llm_inference_succeeded provider_name=llm client_name=StubLlmInferenceClient model_name=llm-scaffold-v1 genres_count=3" in caplog.text


def test_llm_provider_logs_inference_failure(caplog):
    class _FailingLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            raise RuntimeError("stub client failure")

    provider = LlmGenreProvider(client=_FailingLlmClient())

    with caplog.at_level("INFO", logger="genre_classifier"):
        with pytest.raises(RuntimeError, match="stub client failure"):
            provider.classify("/tmp/audio.wav")

    assert "event=llm_inference_started provider_name=llm client_name=_FailingLlmClient" in caplog.text
    assert "event=llm_inference_failed provider_name=llm client_name=_FailingLlmClient error=stub client failure" in caplog.text


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
