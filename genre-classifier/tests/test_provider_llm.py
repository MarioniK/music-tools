import pytest
from urllib import error
import json

from app.clients.llm import (
    LOCAL_HTTP_UNKNOWN_MODEL_NAME,
    LlmClientGenreScore,
    LlmInferenceResult,
    LocalHttpLlmInferenceClient,
    LocalLlmRuntimeHttpError,
    LocalLlmRuntimeTransportError,
    StubLlmInferenceClient,
    get_default_llm_inference_client,
)
from app.clients.llm_prompt_builder import build_genre_inference_prompt
from app.clients.llm_runtime_contract import (
    LocalLlmRuntimeValidationError,
    parse_local_llm_runtime_response,
)
from app.core import settings
from app.providers.base import ProviderResult
from app.providers.compat import (
    map_validated_result_to_legacy_genres,
    map_validated_result_to_legacy_genres_pretty,
)
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
            return b'{"ok":true,"model":"local-llm-v1","labels":[{"name":"indie rock","score":0.82},{"name":"dream pop","score":0.51}]}'

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

    request_payload = json.loads(captured["body"].decode("utf-8"))

    assert captured["url"] == "http://127.0.0.1:11434/infer"
    assert captured["method"] == "POST"
    assert captured["timeout"] == 4.0
    assert request_payload == {
        "input": {"text": "/tmp/audio.wav"},
        "options": {},
    }
    assert isinstance(result, LlmInferenceResult)
    assert result.model_name == "local-llm-v1"
    assert [(item.tag, item.score) for item in result.genres] == [
        ("indie rock", 0.82),
        ("dream pop", 0.51),
    ]


@pytest.mark.parametrize(
    "response_body",
    [
        b'{"ok":true,"labels":[{"name":"indie rock","score":0.82}]}',
        b'{"ok":true,"model":"","labels":[{"name":"indie rock","score":0.82}]}',
        b'{"ok":true,"model":"   ","labels":[{"name":"indie rock","score":0.82}]}',
    ],
)
def test_local_http_client_uses_non_empty_model_fallback(monkeypatch, response_body):
    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return response_body

    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: _FakeResponse(),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    result = client.infer_genres("/tmp/audio.wav")

    assert result.model_name == LOCAL_HTTP_UNKNOWN_MODEL_NAME


def test_local_http_client_maps_timeout_to_transport_error(monkeypatch):
    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: (_ for _ in ()).throw(TimeoutError("deadline exceeded")),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    with pytest.raises(LocalLlmRuntimeTransportError, match="timed out"):
        client.infer_genres("/tmp/audio.wav")


def test_local_http_client_maps_urlerror_to_transport_error(monkeypatch):
    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: (_ for _ in ()).throw(error.URLError("connection refused")),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    with pytest.raises(LocalLlmRuntimeTransportError, match="transport request failed"):
        client.infer_genres("/tmp/audio.wav")


def test_local_http_client_maps_http_error_to_http_error(monkeypatch):
    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: (_ for _ in ()).throw(
            error.HTTPError(
                url="http://127.0.0.1:11434/infer",
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=None,
            )
        ),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    with pytest.raises(LocalLlmRuntimeHttpError, match="status=503"):
        client.infer_genres("/tmp/audio.wav")


def test_local_http_client_rejects_invalid_json_response(monkeypatch):
    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok":true,"model":"local-llm-v1","labels":'

    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: _FakeResponse(),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    with pytest.raises(LocalLlmRuntimeValidationError, match="invalid local llm runtime json response"):
        client.infer_genres("/tmp/audio.wav")


def test_local_http_client_rejects_invalid_runtime_payload(monkeypatch):
    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok":true,"model":"local-llm-v1","labels":"not-a-list"}'

    monkeypatch.setattr(
        "app.clients.llm.request.urlopen",
        lambda http_request, timeout: _FakeResponse(),
    )

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    with pytest.raises(LocalLlmRuntimeValidationError, match="invalid local llm runtime response"):
        client.infer_genres("/tmp/audio.wav")


def test_runtime_response_validator_accepts_valid_payload():
    result = parse_local_llm_runtime_response(
        {
            "ok": True,
            "model": "local-llm-v1",
            "labels": [
                {"name": "indie rock", "score": 0.82},
                {"name": "dream pop", "score": None},
            ],
            "meta": {"source": "test"},
        }
    )

    assert result.ok is True
    assert result.model == "local-llm-v1"
    assert [(item.name, item.score) for item in result.labels] == [
        ("indie rock", 0.82),
        ("dream pop", None),
    ]
    assert result.meta == {"source": "test"}


def test_runtime_response_validator_rejects_missing_labels():
    with pytest.raises(LocalLlmRuntimeValidationError, match="labels are required"):
        parse_local_llm_runtime_response({"ok": True, "model": "local-llm-v1"})


def test_runtime_response_validator_rejects_empty_label_name():
    with pytest.raises(LocalLlmRuntimeValidationError, match="name must be a non-empty string"):
        parse_local_llm_runtime_response(
            {
                "ok": True,
                "labels": [{"name": " ", "score": 0.82}],
            }
        )


def test_runtime_response_validator_rejects_non_numeric_score():
    with pytest.raises(LocalLlmRuntimeValidationError, match="score must be numeric or null"):
        parse_local_llm_runtime_response(
            {
                "ok": True,
                "labels": [{"name": "indie rock", "score": "high"}],
            }
        )


def test_runtime_response_validator_allows_unknown_fields():
    result = parse_local_llm_runtime_response(
        {
            "ok": True,
            "labels": [
                {"name": "indie rock", "score": 0.82, "extra": "kept-ignored"},
            ],
            "unexpected_top_level": {"safe": True},
        }
    )

    assert [(item.name, item.score) for item in result.labels] == [("indie rock", 0.82)]


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
    assert "event=llm_provider_started provider_name=llm client_name=StubLlmInferenceClient" in caplog.text
    assert "event=llm_provider_succeeded provider_name=llm client_name=StubLlmInferenceClient model_name=llm-scaffold-v1 genres_count=3" in caplog.text


def test_llm_provider_logs_transport_failure(caplog):
    class _FailingLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            raise LocalLlmRuntimeTransportError("connection dropped")

    provider = LlmGenreProvider(client=_FailingLlmClient())

    with caplog.at_level("INFO", logger="genre_classifier"):
        with pytest.raises(LocalLlmRuntimeTransportError, match="connection dropped"):
            provider.classify("/tmp/audio.wav")

    assert "event=llm_provider_started provider_name=llm client_name=_FailingLlmClient" in caplog.text
    assert "event=llm_provider_failed provider_name=llm client_name=_FailingLlmClient failure_category=transport_error error=connection dropped" in caplog.text


def test_llm_provider_logs_http_failure(caplog):
    class _FailingLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            raise LocalLlmRuntimeHttpError("status=503")

    provider = LlmGenreProvider(client=_FailingLlmClient())

    with caplog.at_level("INFO", logger="genre_classifier"):
        with pytest.raises(LocalLlmRuntimeHttpError, match="status=503"):
            provider.classify("/tmp/audio.wav")

    assert "event=llm_provider_failed provider_name=llm client_name=_FailingLlmClient failure_category=http_error error=status=503" in caplog.text


def test_llm_provider_logs_validation_failure(caplog):
    class _FailingLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            raise LocalLlmRuntimeValidationError("invalid runtime payload")

    provider = LlmGenreProvider(client=_FailingLlmClient())

    with caplog.at_level("INFO", logger="genre_classifier"):
        with pytest.raises(LocalLlmRuntimeValidationError, match="invalid runtime payload"):
            provider.classify("/tmp/audio.wav")

    assert "event=llm_provider_failed provider_name=llm client_name=_FailingLlmClient failure_category=validation_error error=invalid runtime payload" in caplog.text


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


def test_llm_provider_optional_score_path_is_filtered_by_existing_validation_pipeline():
    class _FakeLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            return LlmInferenceResult(
                genres=[
                    LlmClientGenreScore(tag="indie rock", score=0.91),
                    LlmClientGenreScore(tag="dream pop", score=None),
                    LlmClientGenreScore(tag="ambient", score=0.41),
                ],
                model_name="runtime-backed-llm",
            )

    provider = LlmGenreProvider(client=_FakeLlmClient())

    provider_result = provider.classify("/tmp/audio.wav")
    validated_result = validate_and_normalize_provider_result(provider_result)

    assert isinstance(validated_result, ValidatedProviderResult)
    assert validated_result.provider_name == "llm"
    assert validated_result.model_name == "runtime-backed-llm"
    assert [(item.tag, item.score) for item in validated_result.genres] == [
        ("indie rock", 0.91),
        ("ambient", 0.41),
    ]
    assert validated_result.total_items_received == 3
    assert validated_result.total_items_kept == 2
    assert validated_result.dropped_items_count == 1


def test_llm_provider_filters_unknown_genres_before_existing_validation_pipeline():
    class _FakeLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            return LlmInferenceResult(
                genres=[
                    LlmClientGenreScore(tag="indie rock", score=0.91),
                    LlmClientGenreScore(tag="space yacht metal", score=0.89),
                    LlmClientGenreScore(tag="dream pop", score=0.41),
                ],
                model_name="runtime-backed-llm",
            )

    provider = LlmGenreProvider(client=_FakeLlmClient())

    provider_result = provider.classify("/tmp/audio.wav")
    validated_result = validate_and_normalize_provider_result(provider_result)

    assert [(item.tag, item.score) for item in provider_result.genres] == [
        ("indie rock", 0.91),
        ("dream pop", 0.41),
    ]
    assert [(item.tag, item.score) for item in validated_result.genres] == [
        ("indie rock", 0.91),
        ("dream pop", 0.41),
    ]


def test_llm_provider_alias_heavy_output_is_canonicalized_and_deduped():
    class _FakeLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            return LlmInferenceResult(
                genres=[
                    LlmClientGenreScore(tag=" Dream Pop ", score=0.81),
                    LlmClientGenreScore(tag="dream-pop", score=0.77),
                    LlmClientGenreScore(tag="left field", score=0.65),
                    LlmClientGenreScore(tag="leftfield", score=0.61),
                ],
                model_name="runtime-backed-llm",
            )

    provider = LlmGenreProvider(client=_FakeLlmClient())

    provider_result = provider.classify("/tmp/audio.wav")
    validated_result = validate_and_normalize_provider_result(provider_result)
    legacy_genres = map_validated_result_to_legacy_genres(validated_result)

    assert [(item.tag, item.score) for item in provider_result.genres] == [
        ("dream pop", 0.81),
        ("leftfield", 0.65),
    ]
    assert legacy_genres == [
        {"tag": "dream pop", "prob": 0.81},
        {"tag": "leftfield", "prob": 0.65},
    ]


def test_llm_provider_raises_when_all_runtime_labels_are_out_of_vocabulary():
    class _FakeLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            return LlmInferenceResult(
                genres=[
                    LlmClientGenreScore(tag="space yacht metal", score=0.81),
                    LlmClientGenreScore(tag="cosmic whalewave", score=0.65),
                ],
                model_name="runtime-backed-llm",
            )

    provider = LlmGenreProvider(client=_FakeLlmClient())

    provider_result = provider.classify("/tmp/audio.wav")

    assert provider_result.genres == []
    with pytest.raises(RuntimeError, match="no valid provider genres"):
        validate_and_normalize_provider_result(provider_result)


def test_llm_provider_validated_output_preserves_existing_compatibility_shape(monkeypatch):
    class _FakeLlmClient:
        def infer_genres(self, audio_path: str) -> LlmInferenceResult:
            return LlmInferenceResult(
                genres=[
                    LlmClientGenreScore(tag="Indie Rock", score=0.91234),
                    LlmClientGenreScore(tag="Dream Pop", score=0.50789),
                ],
                model_name="runtime-backed-llm",
            )

    pretty_calls = []

    def fake_normalize_audio_prediction_genres(raw_genres, min_prob=0.05):
        pretty_calls.append((raw_genres, min_prob))
        return raw_genres

    monkeypatch.setattr(
        "app.providers.compat.normalize_audio_prediction_genres",
        fake_normalize_audio_prediction_genres,
    )

    provider = LlmGenreProvider(client=_FakeLlmClient())

    provider_result = provider.classify("/tmp/audio.wav")
    validated_result = validate_and_normalize_provider_result(provider_result)
    legacy_genres = map_validated_result_to_legacy_genres(validated_result)
    pretty_genres = map_validated_result_to_legacy_genres_pretty(validated_result)

    assert legacy_genres == [
        {"tag": "indie rock", "prob": 0.9123},
        {"tag": "dream pop", "prob": 0.5079},
    ]
    assert pretty_genres == legacy_genres
    assert pretty_calls == [(legacy_genres, 0.05)]


def test_genre_inference_prompt_is_not_empty():
    prompt = build_genre_inference_prompt("/tmp/audio.wav")

    assert isinstance(prompt, str)
    assert prompt.strip()


def test_genre_inference_prompt_requires_json_only_output():
    prompt = build_genre_inference_prompt("/tmp/audio.wav")

    assert "OUTPUT_MODE: JSON_ONLY" in prompt
    assert 'OUTPUT_SHAPE: {"genres":[{"tag":"string","score":0.0}]}' in prompt


def test_genre_inference_prompt_forbids_explanations_and_markdown():
    prompt = build_genre_inference_prompt("/tmp/audio.wav")

    assert "do not return explanations, prose, markdown, code fences, or commentary" in prompt


def test_genre_inference_prompt_includes_max_n_rule():
    prompt = build_genre_inference_prompt("/tmp/audio.wav", max_genres=5)

    assert "never return more than 5 genres" in prompt
    assert "max_genres=5" in prompt


def test_genre_inference_prompt_requires_empty_list_for_weak_output():
    prompt = build_genre_inference_prompt("/tmp/audio.wav")

    assert 'return {"genres":[]} if nothing reliable can be inferred' in prompt
    assert "return fewer tags instead of inventing genres" in prompt


def test_genre_inference_prompt_shape_is_stable_and_machine_oriented():
    prompt = build_genre_inference_prompt(
        "/tmp/audio.wav",
        max_genres=4,
        candidate_genres=["indie rock", " dream pop ", "", None],
    )

    assert prompt.startswith("PROMPT_VERSION: baseline-v1\nROLE: genre-inference-engine\nTASK:")
    assert "CONTROLLED_VOCABULARY_HINT:" in prompt
    assert 'candidate_genres=["indie rock", "dream pop"]' in prompt
    assert 'audio_reference="/tmp/audio.wav"' in prompt


def test_local_http_client_preserves_existing_runtime_input_contract(monkeypatch):
    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok":true,"model":"local-llm-v1","labels":[{"name":"indie rock","score":0.82}]}'

    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["body"] = http_request.data
        return _FakeResponse()

    monkeypatch.setattr("app.clients.llm.request.urlopen", fake_urlopen)

    client = LocalHttpLlmInferenceClient(
        endpoint="http://127.0.0.1:11434/infer",
        timeout_seconds=4.0,
    )

    client.infer_genres("/tmp/audio.wav")

    assert json.loads(captured["body"].decode("utf-8")) == {
        "input": {"text": "/tmp/audio.wav"},
        "options": {},
    }
