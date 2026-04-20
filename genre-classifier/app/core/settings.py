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

TMP_DIR.mkdir(exist_ok=True)


def get_configured_genre_provider_name():
    value = os.getenv("GENRE_PROVIDER", DEFAULT_GENRE_PROVIDER)
    return (value or DEFAULT_GENRE_PROVIDER).strip() or DEFAULT_GENRE_PROVIDER
