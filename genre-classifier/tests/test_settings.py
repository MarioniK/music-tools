import pytest

from app.core import settings


def test_get_configured_genre_provider_name_defaults_to_onnx(monkeypatch):
    monkeypatch.delenv("GENRE_PROVIDER", raising=False)

    assert settings.get_configured_genre_provider_name() == settings.GENRE_PROVIDER_ONNX


def test_get_configured_genre_provider_name_accepts_explicit_llm(monkeypatch):
    monkeypatch.setenv("GENRE_PROVIDER", settings.GENRE_PROVIDER_LLM)

    assert settings.get_configured_genre_provider_name() == settings.GENRE_PROVIDER_LLM


def test_supported_genre_providers_include_disabled_by_default_onnx():
    assert settings.GENRE_PROVIDER_ONNX == "onnx_musicnn"
    assert settings.GENRE_PROVIDER_ONNX in settings.SUPPORTED_GENRE_PROVIDERS
    assert settings.DEFAULT_GENRE_PROVIDER == settings.GENRE_PROVIDER_ONNX


def test_onnx_musicnn_artifact_paths_default_to_unset(monkeypatch):
    monkeypatch.delenv("ONNX_MUSICNN_MODEL_PATH", raising=False)
    monkeypatch.delenv("ONNX_MUSICNN_METADATA_PATH", raising=False)

    assert settings.DEFAULT_ONNX_MUSICNN_MODEL_PATH is None
    assert settings.DEFAULT_ONNX_MUSICNN_METADATA_PATH is None
    assert settings.get_configured_onnx_musicnn_model_path() is None
    assert settings.get_configured_onnx_musicnn_metadata_path() is None


def test_onnx_musicnn_artifact_paths_accept_explicit_values(monkeypatch):
    monkeypatch.setenv("ONNX_MUSICNN_MODEL_PATH", "/opt/music-tools/models/msd-musicnn-1.onnx")
    monkeypatch.setenv("ONNX_MUSICNN_METADATA_PATH", "/opt/music-tools/models/msd-musicnn-1.json")

    assert str(settings.get_configured_onnx_musicnn_model_path()) == "/opt/music-tools/models/msd-musicnn-1.onnx"
    assert str(settings.get_configured_onnx_musicnn_metadata_path()) == "/opt/music-tools/models/msd-musicnn-1.json"


def test_onnx_musicnn_artifact_paths_do_not_default_to_tmp_locations(monkeypatch):
    monkeypatch.delenv("ONNX_MUSICNN_MODEL_PATH", raising=False)
    monkeypatch.delenv("ONNX_MUSICNN_METADATA_PATH", raising=False)

    assert settings.get_configured_onnx_musicnn_model_path() is None
    assert settings.get_configured_onnx_musicnn_metadata_path() is None


def test_get_configured_genre_provider_name_falls_back_to_default_for_blank_value(monkeypatch):
    monkeypatch.setenv("GENRE_PROVIDER", "   ")

    assert settings.get_configured_genre_provider_name() == settings.GENRE_PROVIDER_ONNX


def test_get_configured_llm_client_name_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("LLM_CLIENT", raising=False)

    assert settings.get_configured_llm_client_name() == settings.LLM_CLIENT_STUB


def test_get_configured_llm_client_name_accepts_explicit_local_http(monkeypatch):
    monkeypatch.setenv("LLM_CLIENT", settings.LLM_CLIENT_LOCAL_HTTP)

    assert settings.get_configured_llm_client_name() == settings.LLM_CLIENT_LOCAL_HTTP


def test_get_configured_llm_local_http_timeout_seconds_defaults(monkeypatch):
    monkeypatch.delenv("LLM_LOCAL_HTTP_TIMEOUT_SECONDS", raising=False)

    assert settings.get_configured_llm_local_http_timeout_seconds() == settings.DEFAULT_LLM_LOCAL_HTTP_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1:11434/infer",
        "https://localhost/infer",
    ],
)
def test_validate_llm_local_http_endpoint_accepts_http_and_https(endpoint):
    assert settings.validate_llm_local_http_endpoint(endpoint) == endpoint


@pytest.mark.parametrize(
    "endpoint",
    [
        "file:///tmp/genre-classifier",
        "ftp://127.0.0.1:11434/infer",
        "http:///infer",
        "",
    ],
)
def test_validate_llm_local_http_endpoint_rejects_unsafe_or_invalid_urls(endpoint):
    with pytest.raises(ValueError, match="LLM_LOCAL_HTTP_ENDPOINT"):
        settings.validate_llm_local_http_endpoint(endpoint)


def test_shadow_settings_defaults_are_safe(monkeypatch):
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_PROVIDER", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_ARTIFACTS_ENABLED", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_ARTIFACTS_DIR", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", raising=False)

    assert settings.get_configured_shadow_enabled() is False
    assert settings.get_configured_shadow_sample_rate() == 0.0
    assert settings.get_configured_shadow_artifacts_enabled() is False
    assert settings.get_configured_shadow_provider() == "llm"
    assert settings.get_configured_shadow_timeout_seconds() == 2.0
    assert settings.get_configured_shadow_max_concurrent() == 1
    assert (
        settings.get_configured_shadow_artifacts_dir()
        == "evaluation/artifacts/runtime_shadow"
    )


def test_shadow_settings_env_overrides(monkeypatch):
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_PROVIDER", "stub")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "0.25")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", "3.5")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ARTIFACTS_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ARTIFACTS_DIR", "/tmp/shadow-artifacts")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", "2")

    assert settings.get_configured_shadow_enabled() is True
    assert settings.get_configured_shadow_provider() == "stub"
    assert settings.get_configured_shadow_sample_rate() == 0.25
    assert settings.get_configured_shadow_timeout_seconds() == 3.5
    assert settings.get_configured_shadow_artifacts_enabled() is True
    assert settings.get_configured_shadow_artifacts_dir() == "/tmp/shadow-artifacts"
    assert settings.get_configured_shadow_max_concurrent() == 2


@pytest.mark.parametrize("sample_rate", ["-0.1", "1.1"])
def test_shadow_sample_rate_rejects_out_of_range_values(monkeypatch, sample_rate):
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", sample_rate)

    with pytest.raises(ValueError):
        settings.get_configured_shadow_sample_rate()


@pytest.mark.parametrize("timeout_seconds", ["0", "-1"])
def test_shadow_timeout_seconds_rejects_non_positive_values(
    monkeypatch,
    timeout_seconds,
):
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", timeout_seconds)

    with pytest.raises(ValueError):
        settings.get_configured_shadow_timeout_seconds()


@pytest.mark.parametrize("max_concurrent", ["0", "-1"])
def test_shadow_max_concurrent_rejects_non_positive_values(monkeypatch, max_concurrent):
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", max_concurrent)

    with pytest.raises(ValueError):
        settings.get_configured_shadow_max_concurrent()
