from app.main import parse_tidal_metadata_from_html


def test_parse_tidal_metadata_from_html_valid_json_ld_dict():
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@type": "MusicRecording",
        "name": "Track Title",
        "byArtist": {"@type": "MusicGroup", "name": "Artist Name"},
        "inAlbum": {"@type": "MusicAlbum", "name": "Album Name"}
      }
      </script>
      <meta property="og:title" content="Wrong Title by Wrong Artist on TIDAL" />
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "Track Title",
        "artist": "Artist Name",
        "album": "Album Name",
    }


def test_parse_tidal_metadata_from_html_valid_json_ld_list():
    html = """
    <html><head>
      <script type="application/ld+json">
      [
        {"@type": "BreadcrumbList", "name": "Ignore me"},
        {
          "@type": "MusicAlbum",
          "name": "Album Title",
          "byArtist": {"name": "Artist Name"}
        }
      ]
      </script>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "album")

    assert result == {
        "title": "Album Title",
        "artist": "Artist Name",
        "album": "Album Title",
    }


def test_parse_tidal_metadata_from_html_json_ld_graph():
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@graph": [
          {"@type": "WebSite", "name": "TIDAL"},
          {
            "@type": "MusicRecording",
            "name": "Graph Track",
            "byArtist": {"name": "Graph Artist"},
            "inAlbum": {"name": "Graph Album"}
          }
        ]
      }
      </script>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "Graph Track",
        "artist": "Graph Artist",
        "album": "Graph Album",
    }


def test_parse_tidal_metadata_from_html_multiple_json_ld_blocks_prefers_relevant_candidate():
    html = """
    <html><head>
      <script type="application/ld+json">
      {"@type": "WebSite", "name": "TIDAL"}
      </script>
      <script type="application/ld+json">
      {"@type": "MusicRecording", "name": "Track Title", "byArtist": {"name": "Artist Name"}}
      </script>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result["title"] == "Track Title"
    assert result["artist"] == "Artist Name"


def test_parse_tidal_metadata_from_html_ignores_broken_json_ld_block_if_valid_exists():
    html = """
    <html><head>
      <script type="application/ld+json">{bad json</script>
      <script type="application/ld+json">
      {"@type": "MusicRecording", "name": "Track Title", "byArtist": {"name": "Artist Name"}}
      </script>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result["title"] == "Track Title"
    assert result["artist"] == "Artist Name"


def test_parse_tidal_metadata_from_html_falls_back_to_og_title_without_json_ld():
    html = """
    <html><head>
      <meta property="og:title" content="Track Title by Artist Name on TIDAL" />
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "Track Title",
        "artist": "Artist Name",
        "album": None,
    }


def test_parse_tidal_metadata_from_html_falls_back_to_twitter_title_without_json_ld():
    html = """
    <html><head>
      <meta name="twitter:title" content="Twitter Track by Twitter Artist on TIDAL" />
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "Twitter Track",
        "artist": "Twitter Artist",
        "album": None,
    }


def test_parse_tidal_metadata_from_html_falls_back_to_title_tag_without_json_ld():
    html = """
    <html><head>
      <title>Title Tag Track by Title Tag Artist on TIDAL</title>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "Title Tag Track",
        "artist": "Title Tag Artist",
        "album": None,
    }


def test_parse_tidal_metadata_from_html_handles_malformed_html():
    html = '<html><head><meta property="og:title" content="Track Title by Artist Name on TIDAL"><body><div>'

    result = parse_tidal_metadata_from_html(html, "track")

    assert result["title"] == "Track Title"
    assert result["artist"] == "Artist Name"


def test_parse_tidal_metadata_from_html_handles_empty_html():
    result = parse_tidal_metadata_from_html("", "track")

    assert result == {"title": None, "artist": None, "album": None}


def test_parse_tidal_metadata_from_html_handles_whitespace_html():
    result = parse_tidal_metadata_from_html("   \n\t   ", "track")

    assert result == {"title": None, "artist": None, "album": None}


def test_parse_tidal_metadata_from_html_fallback_does_not_overwrite_stronger_data():
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@type": "MusicRecording",
        "name": "Strong Title",
        "byArtist": {"name": "Strong Artist"},
        "inAlbum": {"name": "Strong Album"}
      }
      </script>
      <meta property="og:title" content="Weak Title by Weak Artist on TIDAL" />
      <meta name="twitter:title" content="Another Weak Title by Another Weak Artist on TIDAL" />
      <title>Fallback Title by Fallback Artist on TIDAL</title>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "Strong Title",
        "artist": "Strong Artist",
        "album": "Strong Album",
    }


def test_parse_tidal_metadata_from_html_supports_by_artist_list_of_dicts():
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@type": "MusicRecording",
        "name": "List Track",
        "byArtist": [
          {"@type": "MusicGroup", "name": "Primary Artist"},
          {"@type": "MusicGroup", "name": "Secondary Artist"}
        ],
        "inAlbum": {"name": "List Album"}
      }
      </script>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result == {
        "title": "List Track",
        "artist": "Primary Artist",
        "album": "List Album",
    }


def test_parse_tidal_metadata_from_html_happy_path_regression():
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@type": "MusicRecording",
        "name": "Track Title",
        "byArtist": {"name": "Artist Name"},
        "inAlbum": {"name": "Album Name"}
      }
      </script>
    </head></html>
    """

    result = parse_tidal_metadata_from_html(html, "track")

    assert result["title"] == "Track Title"
    assert result["artist"] == "Artist Name"
    assert result["album"] == "Album Name"
