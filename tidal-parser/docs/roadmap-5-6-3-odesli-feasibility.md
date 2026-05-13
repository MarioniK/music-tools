# Roadmap 5.6.3 — Odesli feasibility for Yandex / provider link mapping

**Status:** completed / docs-only  
**Scope:** tidal-parser only  
**Baseline:** `3c06ea2 tidal-parser: add Spotify metadata extractor`

## Goal

Проверить, можно ли использовать Odesli/Songlink как bridge:

- Yandex/Spotify/Apple URL → TIDAL URL;
- Yandex/Spotify/Apple URL → normalized metadata;
- существующий TIDAL parse flow без изменений.

## Endpoint

`https://api.song.link/v1-alpha.1/links?url=<encoded_provider_url>`

## Findings

### Yandex

- feasible via Odesli;
- Yandex track URLs returned direct TIDAL track URLs;
- Yandex album test returned metadata but no TIDAL mapping;
- direct Yandex HTML remains blocked by captcha.

### Spotify

- feasible via Odesli;
- Odesli returns TIDAL URL and metadata for album/track;
- direct Spotify extractor remains preferred primary path.

### Apple

- feasible via Odesli;
- Odesli returns TIDAL URL and metadata for album/song;
- direct Apple extractor remains preferred primary path.

## Decision

Use Odesli first only for Yandex.
Keep Apple and Spotify on direct extractor path as primary.

## Recommended implementation

### Roadmap 5.6.4 — Odesli bridge adapter for Yandex only

- Yandex track:
  - Yandex URL → Odesli → TIDAL URL → existing TIDAL parse flow.
- Yandex album:
  - Yandex URL → Odesli metadata → existing TIDAL candidates/scoring → safe handoff or Yandex identity fallback.

## Non-goals

- no OAuth/login;
- no paid API;
- no headless browser;
- no Apple/Spotify migration to Odesli in this slice;
- no direct Yandex HTML parser.

## Risks

- Yandex album may not have TIDAL URL from Odesli.
- Odesli responses did not include reliable `isrc` in tested cases.
- Odesli metadata did not include release date/year in tested cases.
- External bridge availability/rate limits should degrade safely.

## Test URLs

- `https://music.yandex.ru/album/31774859?lang=en`
- `https://music.yandex.ru/album/33932468/track/132723441?lang=uz`
- `https://music.yandex.ru/album/14453277/track/76359080?lang=uz&play=1`
- `https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj`
- `https://open.spotify.com/track/4jBfUB4kQJCWOrjGLQqhO0`
- `https://music.apple.com/us/album/older/412453578`
- `https://music.apple.com/us/song/412453589`

## Confirmations

- AGENTS.md read and followed: yes
- service scope: tidal-parser only
- genre-classifier untouched: yes
- Odesli feasibility documented: yes
- Yandex via Odesli tested: yes
- Spotify via Odesli tested: yes
- Apple via Odesli tested: yes
- paid API used: no
- OAuth/login used: no
- headless browser used: no
- runtime code changed: no
- templates changed: no
- tests changed: no
- Docker run/rebuild: no
- commit/tag/push: no
