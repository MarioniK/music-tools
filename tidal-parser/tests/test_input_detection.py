import pytest

from app.input_detection import detect_music_input


@pytest.mark.parametrize(
    "raw_input, expected_provider",
    [
        ("https://tidal.com/album/478338199/u", "tidal"),
        ("https://www.qobuz.com/us-en/album/example/abc", "qobuz"),
        ("https://open.spotify.com/album/abc", "spotify"),
        ("https://music.apple.com/us/album/example/123", "apple_music"),
        ("https://music.yandex.ru/album/123", "yandex_music"),
    ],
)
def test_detect_music_input_url_providers(raw_input, expected_provider):
    result = detect_music_input(raw_input)

    assert result["input_type"] == "url"
    assert result["provider"] == expected_provider
    assert result["normalized_input"] == raw_input
    assert result["confidence"] in {"medium", "high"}


@pytest.mark.parametrize(
    "raw_input, expected_artist, expected_title, expected_year",
    [
        ('Lykke Li — «The Afterparty» (2026)', "Lykke Li", "The Afterparty", 2026),
        ('Blue — "All Rise" (2001)', "Blue", "All Rise", 2001),
    ],
)
def test_detect_music_input_manual_release_line(raw_input, expected_artist, expected_title, expected_year):
    result = detect_music_input(raw_input)

    assert result["input_type"] == "manual_release_line"
    assert result["provider"] == "manual"
    assert result["artist"] == expected_artist
    assert result["title"] == expected_title
    assert result["year"] == expected_year
    assert result["confidence"] == "high"
    assert result["warnings"] == []


def test_detect_music_input_unknown_text():
    result = detect_music_input("hello world")

    assert result["input_type"] == "unknown"
    assert result["provider"] == "unknown"
    assert result["confidence"] == "low"
    assert result["warnings"]


def test_detect_music_input_unknown_url():
    result = detect_music_input("https://example.com/music")

    assert result["input_type"] == "url"
    assert result["provider"] == "unknown"
    assert result["confidence"] == "low"
    assert result["warnings"]
