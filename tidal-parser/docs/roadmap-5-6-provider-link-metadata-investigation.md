# Roadmap 5.6.0 — Provider link metadata investigation

## Status

completed / docs-only

## Scope

tidal-parser only

## Goal

Проверить, можно ли из Apple Music, Spotify и Yandex Music ссылок получить normalized metadata:
artist, title, year / release date, release_type, canonical URL, provider id.

## Baseline

`7e612e7 tidal-parser: add manual release type selector`

## Findings

### Apple Music

- feasible
- metadata available from HTML without JS / headless / OAuth
- useful fields:
  - canonical
  - `og:title`
  - `og:url`
  - `og:type`
  - `twitter:title`
  - JSON-LD
  - `datePublished` / `releaseDate`
  - `byArtist` / `name`
- album vs song distinguishable via `og:type`, URL path, JSON-LD type
- provider id available in URL path

### Spotify

- feasible
- metadata available from HTML without JS / headless / OAuth
- useful fields:
  - canonical
  - `og:title`
  - `og:url`
  - `og:type`
  - `og:description`
  - JSON-LD
  - `datePublished`
  - `music:*` fields
- album vs track distinguishable via `og:type`, URL path, JSON-LD type
- provider id available in URL path
- track artist extraction may require more careful parsing than album extraction

### Yandex Music

- blocked in current environment
- public pages redirected to captcha
- no reliable release metadata extracted
- only URL ids are visible from the original path, not confirmed through page metadata

## Decision

Implement providers one per safe slice:

1. Apple Music first
2. Spotify second
3. Yandex Music later as a separate blocked/risky track

## Non-goals

- no paid APIs
- no OAuth / login
- no headless browser
- no private API scraping
- no runtime changes in 5.6.0

## Next safe slice

Roadmap 5.6.1 — Apple Music metadata extractor:

Apple Music URL
→ normalized provider identity
→ existing TIDAL candidates/scoring/handoff

## Risks

- Apple Music track pages should prefer canonical song URLs, not album URLs with `?i=...`, unless separately validated.
- Spotify track artist metadata needs careful extraction.
- Yandex remains blocked by captcha.
