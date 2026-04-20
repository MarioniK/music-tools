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
