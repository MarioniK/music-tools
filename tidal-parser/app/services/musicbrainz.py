import html
import re

import httpx


MUSICBRAINZ_USER_AGENT = "tidal-parser/1.0 (local-app@example.com)"

COUNTRY_TAG_MAP = {
    "US": "american",
    "USA": "american",
    "UNITED STATES": "american",
    "GB": "british",
    "UK": "british",
    "UNITED KINGDOM": "british",
    "ENGLAND": "british",
    "SCOTLAND": "british",
    "WALES": "british",
    "NORTHERN IRELAND": "british",
    "IE": "irish",
    "IRELAND": "irish",
    "CA": "canadian",
    "CANADA": "canadian",
    "AU": "australian",
    "AUSTRALIA": "australian",
    "NZ": "newzealand",
    "NEW ZEALAND": "newzealand",
    "DE": "german",
    "GERMANY": "german",
    "FR": "french",
    "FRANCE": "french",
    "IT": "italian",
    "ITALY": "italian",
    "ES": "spanish",
    "SPAIN": "spanish",
    "SE": "swedish",
    "SWEDEN": "swedish",
    "NO": "norwegian",
    "NORWAY": "norwegian",
    "DK": "danish",
    "DENMARK": "danish",
    "FI": "finnish",
    "FINLAND": "finnish",
    "IS": "icelandic",
    "ICELAND": "icelandic",
    "NL": "dutch",
    "NETHERLANDS": "dutch",
    "BE": "belgian",
    "BELGIUM": "belgian",
    "CH": "swiss",
    "SWITZERLAND": "swiss",
    "AT": "austrian",
    "AUSTRIA": "austrian",
    "PL": "polish",
    "POLAND": "polish",
    "CZ": "czech",
    "CZECHIA": "czech",
    "CZECH REPUBLIC": "czech",
    "SK": "slovak",
    "SLOVAKIA": "slovak",
    "HU": "hungarian",
    "HUNGARY": "hungarian",
    "RO": "romanian",
    "ROMANIA": "romanian",
    "BG": "bulgarian",
    "BULGARIA": "bulgarian",
    "GR": "greek",
    "GREECE": "greek",
    "TR": "turkish",
    "TURKEY": "turkish",
    "UA": "ukrainian",
    "UKRAINE": "ukrainian",
    "BY": "belarusian",
    "BELARUS": "belarusian",
    "RU": "russian",
    "RUSSIA": "russian",
    "JP": "japanese",
    "JAPAN": "japanese",
    "KR": "korean",
    "SOUTH KOREA": "korean",
    "KOREA, REPUBLIC OF": "korean",
    "CN": "chinese",
    "CHINA": "chinese",
    "TW": "taiwanese",
    "TAIWAN": "taiwanese",
    "HK": "hongkong",
    "HONG KONG": "hongkong",
    "SG": "singaporean",
    "SINGAPORE": "singaporean",
    "BR": "brazilian",
    "BRAZIL": "brazilian",
    "AR": "argentinian",
    "ARGENTINA": "argentinian",
    "MX": "mexican",
    "MEXICO": "mexican",
    "CL": "chilean",
    "CHILE": "chilean",
    "CO": "colombian",
    "COLOMBIA": "colombian",
    "PE": "peruvian",
    "PERU": "peruvian",
    "PT": "portuguese",
    "PORTUGAL": "portuguese",
    "ZA": "southafrican",
    "SOUTH AFRICA": "southafrican",
}


def clean_text(value):
    if not value:
        return None
    value = html.unescape(str(value)).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def score_similarity(a, b):
    a = (clean_text(a) or "").lower()
    b = (clean_text(b) or "").lower()

    if not a or not b:
        return 0

    if a == b:
        return 100

    if a in b or b in a:
        return 70

    a_words = set(re.findall(r"[a-z0-9]+", a))
    b_words = set(re.findall(r"[a-z0-9]+", b))
    if not a_words or not b_words:
        return 0

    overlap = len(a_words & b_words)
    total = len(a_words | b_words)
    return int((overlap / float(total)) * 100)


def infer_mb_release_kind(primary_type, secondary_types, entity_type):
    pt = (primary_type or "").lower()
    st = set([str(x).lower() for x in (secondary_types or [])])

    if "ep" in st:
        return "ep"
    if pt == "album":
        return "album"
    if pt == "single":
        return "single"

    return "album" if entity_type == "album" else "single"


async def fetch_musicbrainz_json(url, params):
    headers = {
        "User-Agent": MUSICBRAINZ_USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.json()


async def get_artist_country_by_mbid(artist_id):
    if not artist_id:
        return None

    try:
        data = await fetch_musicbrainz_json(
            "https://musicbrainz.org/ws/2/artist/{}".format(artist_id),
            {"fmt": "json"},
        )
    except Exception:
        return None

    candidates = []

    if data.get("country"):
        candidates.append(str(data["country"]).upper())

    area = data.get("area")
    if isinstance(area, dict) and area.get("name"):
        candidates.append(str(area["name"]).upper())

    begin_area = data.get("begin-area")
    if isinstance(begin_area, dict) and begin_area.get("name"):
        candidates.append(str(begin_area["name"]).upper())

    for value in candidates:
        if value in COUNTRY_TAG_MAP:
            return COUNTRY_TAG_MAP[value]

    return None


async def search_musicbrainz_release_info(artist, title, album, entity_type):
    try:
        if entity_type == "album":
            query = 'release:"{}" AND artist:"{}"'.format(title, artist)
            data = await fetch_musicbrainz_json(
                "https://musicbrainz.org/ws/2/release/",
                {
                    "query": query,
                    "fmt": "json",
                    "limit": 10,
                },
            )

            releases = data.get("releases", [])
            if not releases:
                return {
                    "release_year": None,
                    "release_date": None,
                    "release_kind": None,
                    "artist_id": None,
                    "confidence": 0.0,
                }

            scored = []
            for rel in releases:
                rel_title = rel.get("title")
                title_score = score_similarity(title, rel_title)
                artist_score = 0
                artist_id = None

                credits = rel.get("artist-credit", [])
                if credits:
                    first = credits[0]
                    if isinstance(first, dict):
                        artist_score = score_similarity(artist, first.get("name"))
                        artist_obj = first.get("artist") or {}
                        artist_id = artist_obj.get("id")

                date = rel.get("date")
                year_score = 10 if date and re.match(r"^\d{4}", date) else 0

                total = title_score + artist_score + year_score
                scored.append((total, rel, artist_id))

            scored.sort(key=lambda x: x[0], reverse=True)
            best_score, best, artist_id = scored[0]

            date = best.get("date")
            year = int(date[:4]) if date and re.match(r"^\d{4}", date) else None
            group = best.get("release-group", {})
            release_kind = infer_mb_release_kind(
                group.get("primary-type"),
                group.get("secondary-types", []),
                entity_type,
            )

            confidence = min(best_score / 200.0, 0.95)

            return {
                "release_year": year,
                "release_date": date,
                "release_kind": release_kind,
                "artist_id": artist_id,
                "confidence": confidence,
            }

        query = 'recording:"{}" AND artist:"{}"'.format(title, artist)
        data = await fetch_musicbrainz_json(
            "https://musicbrainz.org/ws/2/recording/",
            {
                "query": query,
                "fmt": "json",
                "inc": "releases+artist-credits",
                "limit": 10,
            },
        )

        recordings = data.get("recordings", [])
        if not recordings:
            return {
                "release_year": None,
                "release_date": None,
                "release_kind": None,
                "artist_id": None,
                "confidence": 0.0,
            }

        scored_recordings = []

        for rec in recordings:
            title_score = score_similarity(title, rec.get("title"))
            artist_score = 0
            artist_id = None

            credits = rec.get("artist-credit", [])
            if credits:
                first = credits[0]
                if isinstance(first, dict):
                    artist_score = score_similarity(artist, first.get("name"))
                    artist_obj = first.get("artist") or {}
                    artist_id = artist_obj.get("id")

            album_bonus = 0
            best_release = None
            best_release_score = -1

            for rel in rec.get("releases", []):
                rel_title = rel.get("title")
                rel_score = 0

                if album:
                    rel_score += score_similarity(album, rel_title)
                else:
                    rel_score += 20 if rel_title else 0

                date = rel.get("date")
                if date and re.match(r"^\d{4}", date):
                    rel_score += 10

                if rel_score > best_release_score:
                    best_release_score = rel_score
                    best_release = rel

            if best_release_score > 0:
                album_bonus = best_release_score

            total = title_score + artist_score + album_bonus
            scored_recordings.append((total, rec, best_release, artist_id))

        scored_recordings.sort(key=lambda x: x[0], reverse=True)
        best_score, best_rec, best_release, artist_id = scored_recordings[0]

        if not best_release:
            return {
                "release_year": None,
                "release_date": None,
                "release_kind": "single",
                "artist_id": artist_id,
                "confidence": min(best_score / 200.0, 0.6),
            }

        date = best_release.get("date")
        year = int(date[:4]) if date and re.match(r"^\d{4}", date) else None
        group = best_release.get("release-group", {})
        release_kind = infer_mb_release_kind(
            group.get("primary-type"),
            group.get("secondary-types", []),
            entity_type,
        )

        confidence = min(best_score / 220.0, 0.95)

        if confidence < 0.65:
            release_kind = "single"

        return {
            "release_year": year,
            "release_date": date,
            "release_kind": release_kind,
            "artist_id": artist_id,
            "confidence": confidence,
        }

    except Exception:
        return {
            "release_year": None,
            "release_date": None,
            "release_kind": None,
            "artist_id": None,
            "confidence": 0.0,
        }


async def search_artist_country_tag(artist, artist_id=None):
    if artist_id:
        country = await get_artist_country_by_mbid(artist_id)
        if country:
            return country

    if not artist:
        return None

    try:
        data = await fetch_musicbrainz_json(
            "https://musicbrainz.org/ws/2/artist/",
            {
                "query": 'artist:"{}"'.format(artist),
                "fmt": "json",
                "limit": 5,
            },
        )
    except Exception:
        return None

    artists = data.get("artists", [])
    if not artists:
        return None

    best = None
    best_score = -1

    for item in artists:
        score = score_similarity(artist, item.get("name"))
        if score > best_score:
            best_score = score
            best = item

    if not best or best_score < 90:
        return None

    candidates = []

    if best.get("country"):
        candidates.append(str(best["country"]).upper())

    area = best.get("area")
    if isinstance(area, dict) and area.get("name"):
        candidates.append(str(area["name"]).upper())

    begin_area = best.get("begin-area")
    if isinstance(begin_area, dict) and begin_area.get("name"):
        candidates.append(str(begin_area["name"]).upper())

    for value in candidates:
        if value in COUNTRY_TAG_MAP:
            return COUNTRY_TAG_MAP[value]

    return None
