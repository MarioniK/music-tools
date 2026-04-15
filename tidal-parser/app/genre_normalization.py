import re
import unicodedata

NON_GENRE_DESCRIPTORS = {
    "female vocalists",
    "male vocalists",
}


def _to_text(value):
    if value is None:
        return None
    return str(value)


def normalize_genre_value(value):
    text = _to_text(value)
    if text is None:
        return None

    text = text.strip().lower()
    text = re.sub(r"[-_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text or None


def _iter_genre_tokens(value):
    if value is None:
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            for token in _iter_genre_tokens(item):
                yield token
        return

    text = _to_text(value)
    if text is None:
        return

    parts = re.split(r"\s*[,;/]\s*", text)
    for part in parts:
        normalized = normalize_genre_value(part)
        if normalized:
            yield normalized


def normalize_genres(value):
    result = []
    seen = set()

    for token in _iter_genre_tokens(value):
        if token not in seen:
            seen.add(token)
            result.append(token)

    return result


def genre_to_blog_tag(value):
    normalized = normalize_genre_value(value)
    if not normalized:
        return None

    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized or None


def is_allowed_final_genre(value):
    normalized = normalize_genre_value(value)
    if not normalized:
        return False
    return normalized not in NON_GENRE_DESCRIPTORS


def normalize_audio_prediction_genres(raw_genres, min_prob=0.05):
    filtered = [g for g in raw_genres if g.get("prob", 0) >= min_prob]
    tags = normalize_genres([g.get("tag") for g in filtered if g.get("tag")])
    tag_set = set(tags)

    result = []

    def add(tag):
        normalized = normalize_genre_value(tag)
        if normalized and is_allowed_final_genre(normalized) and normalized not in result:
            result.append(normalized)

    if "indie rock" in tag_set:
        add("indie rock")
    elif "indie" in tag_set and "rock" in tag_set:
        add("indie rock")

    if "experimental rock" in tag_set:
        add("experimental rock")
    elif "experimental" in tag_set and "rock" in tag_set:
        add("experimental rock")

    if "jazz rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "instrumental" in tag_set and "experimental" in tag_set:
        add("avant jazz")

    if "alternative rock" in tag_set:
        add("alternative rock")
    elif "alternative" in tag_set and "rock" in tag_set:
        add("alternative rock")

    if "instrumental rock" in tag_set:
        add("instrumental rock")
    elif "instrumental" in tag_set and "rock" in tag_set:
        add("instrumental rock")

    if "electronic" in tag_set:
        add("electronic")

    for tag in tags:
        add(tag)

    return result[:8]
