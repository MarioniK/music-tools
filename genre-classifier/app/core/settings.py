import os
from pathlib import Path


MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "tmp"
MODELS_DIR = BASE_DIR / "models"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

MODEL_PB = MODELS_DIR / "msd-musicnn-1.pb"
MODEL_JSON = MODELS_DIR / "msd-musicnn-1.json"
GENRE_PROVIDER_LEGACY = "legacy_musicnn"
GENRE_PROVIDER_LLM = "llm"
DEFAULT_GENRE_PROVIDER = "legacy_musicnn"
SUPPORTED_GENRE_PROVIDERS = (
    GENRE_PROVIDER_LEGACY,
    GENRE_PROVIDER_LLM,
    "stub",
)
LLM_CLIENT_STUB = "stub"
LLM_CLIENT_LOCAL_HTTP = "local_http"
DEFAULT_LLM_CLIENT = LLM_CLIENT_STUB
DEFAULT_LLM_LOCAL_HTTP_TIMEOUT_SECONDS = 5.0
DEFAULT_LLM_GENRE_PROMPT_MAX_LABELS = 8
DEFAULT_LLM_GENRE_POSTPROCESS_TOP_N = 8
DEFAULT_LLM_GENRE_SCORE_THRESHOLD = 0.4
LLM_GENRE_PROMPT_ROLE = "genre-inference-engine"
LLM_GENRE_PROMPT_VERSION = "baseline-v1"
DEFAULT_SHADOW_ENABLED = False
DEFAULT_SHADOW_PROVIDER = GENRE_PROVIDER_LLM
DEFAULT_SHADOW_SAMPLE_RATE = 0.0
DEFAULT_SHADOW_TIMEOUT_SECONDS = 2.0
DEFAULT_SHADOW_ARTIFACTS_ENABLED = False
DEFAULT_SHADOW_ARTIFACTS_DIR = "evaluation/artifacts/runtime_shadow"
DEFAULT_SHADOW_MAX_CONCURRENT = 1

TMP_DIR.mkdir(exist_ok=True)


def get_configured_genre_provider_name():
    value = os.getenv("GENRE_PROVIDER", DEFAULT_GENRE_PROVIDER)
    return (value or DEFAULT_GENRE_PROVIDER).strip() or DEFAULT_GENRE_PROVIDER


def get_configured_llm_client_name():
    value = os.getenv("LLM_CLIENT", DEFAULT_LLM_CLIENT)
    return (value or DEFAULT_LLM_CLIENT).strip() or DEFAULT_LLM_CLIENT


def get_configured_llm_local_http_endpoint():
    return (os.getenv("LLM_LOCAL_HTTP_ENDPOINT", "") or "").strip()


def get_configured_llm_local_http_timeout_seconds():
    value = (os.getenv("LLM_LOCAL_HTTP_TIMEOUT_SECONDS", "") or "").strip()
    if not value:
        return DEFAULT_LLM_LOCAL_HTTP_TIMEOUT_SECONDS

    return float(value)


def _get_configured_bool(env_name, default):
    value = (os.getenv(env_name, "") or "").strip().lower()
    if not value:
        return default

    if value in ("1", "true", "yes", "on"):
        return True

    if value in ("0", "false", "no", "off"):
        return False

    raise ValueError("{} must be a boolean value".format(env_name))


def get_configured_shadow_enabled():
    return _get_configured_bool(
        "GENRE_CLASSIFIER_SHADOW_ENABLED",
        DEFAULT_SHADOW_ENABLED,
    )


def get_configured_shadow_provider():
    value = os.getenv("GENRE_CLASSIFIER_SHADOW_PROVIDER", DEFAULT_SHADOW_PROVIDER)
    return (value or DEFAULT_SHADOW_PROVIDER).strip() or DEFAULT_SHADOW_PROVIDER


def get_configured_shadow_sample_rate():
    value = (os.getenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", "") or "").strip()
    if not value:
        return DEFAULT_SHADOW_SAMPLE_RATE

    sample_rate = float(value)
    if sample_rate < 0.0 or sample_rate > 1.0:
        raise ValueError("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE must be between 0.0 and 1.0")

    return sample_rate


def get_configured_shadow_timeout_seconds():
    value = (os.getenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", "") or "").strip()
    if not value:
        return DEFAULT_SHADOW_TIMEOUT_SECONDS

    timeout_seconds = float(value)
    if timeout_seconds <= 0.0:
        raise ValueError("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS must be positive")

    return timeout_seconds


def get_configured_shadow_artifacts_enabled():
    return _get_configured_bool(
        "GENRE_CLASSIFIER_SHADOW_ARTIFACTS_ENABLED",
        DEFAULT_SHADOW_ARTIFACTS_ENABLED,
    )


def get_configured_shadow_artifacts_dir():
    value = os.getenv(
        "GENRE_CLASSIFIER_SHADOW_ARTIFACTS_DIR",
        DEFAULT_SHADOW_ARTIFACTS_DIR,
    )
    return (value or DEFAULT_SHADOW_ARTIFACTS_DIR).strip() or DEFAULT_SHADOW_ARTIFACTS_DIR


def get_configured_shadow_max_concurrent():
    value = (os.getenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", "") or "").strip()
    if not value:
        return DEFAULT_SHADOW_MAX_CONCURRENT

    max_concurrent = int(value)
    if max_concurrent <= 0:
        raise ValueError("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT must be positive")

    return max_concurrent
