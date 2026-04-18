import os


DEFAULT_AUDIO_CLASSIFIER_URL = "http://genre-classifier:8021/classify"
DEFAULT_DISCOGS_USER_AGENT = "TIDALParser/1.0 (+local app)"
DEFAULT_MUSICBRAINZ_APP_NAME = "tidal-parser/1.0"
DEFAULT_MUSICBRAINZ_MAX_ATTEMPTS = 3
DEFAULT_MUSICBRAINZ_RETRY_DELAY_S = 0.2
DEFAULT_MUSICBRAINZ_MIN_INTERVAL_S = 1.1


def _get_env_str(name, default=""):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _get_env_float(name, default):
    raw_value = _get_env_str(name, "")
    if not raw_value:
        return default

    try:
        parsed = float(raw_value)
    except ValueError:
        return default

    if parsed <= 0:
        return default

    return parsed


def get_audio_classifier_url():
    return _get_env_str("AUDIO_CLASSIFIER_URL", DEFAULT_AUDIO_CLASSIFIER_URL)


def get_discogs_token():
    return _get_env_str("DISCOGS_TOKEN", "")


def get_discogs_user_agent():
    return DEFAULT_DISCOGS_USER_AGENT


def get_musicbrainz_contact_email():
    return _get_env_str("MUSICBRAINZ_CONTACT_EMAIL", "")


def get_musicbrainz_min_interval_s():
    return _get_env_float(
        "MUSICBRAINZ_MIN_INTERVAL_S",
        DEFAULT_MUSICBRAINZ_MIN_INTERVAL_S,
    )


def get_musicbrainz_app_name():
    return DEFAULT_MUSICBRAINZ_APP_NAME


def get_musicbrainz_max_attempts():
    return DEFAULT_MUSICBRAINZ_MAX_ATTEMPTS


def get_musicbrainz_retry_delay_s():
    return DEFAULT_MUSICBRAINZ_RETRY_DELAY_S
