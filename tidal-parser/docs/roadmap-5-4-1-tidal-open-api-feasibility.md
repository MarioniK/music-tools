# Roadmap 5.4.1 — TIDAL Open API feasibility

**Status:** feasible / contract confirmed

**Scope:** tidal-parser only

## Background

Roadmap 5.4 нужен для universal normalized metadata → TIDAL resolver.
Ранее HTML scraping `tidal.com/search` был rejected из-за `403` и JS/captcha challenge.

## Credentials

`TIDAL_CLIENT_ID` и `TIDAL_CLIENT_SECRET` берутся из environment.
Локальный `tidal-parser/.env` игнорируется git.
Credentials и access token нельзя логировать или коммитить.

## Confirmed

- Client credentials flow работает.
- `token_type`: `Bearer`.
- `expires_in`: `14400`.
- Для этих запросов нужен `Accept: application/vnd.api+json`.
- Catalog endpoint работает с `application/vnd.api+json`.
- Search candidates нужно получать не через root `/searchResults/{id}`, а через relationship endpoints.

## Working endpoints

- `/v2/searchResults/{query}/relationships/albums`
- `/v2/searchResults/{query}/relationships/tracks`

## Required params observed

- `countryCode=US`
- `include=albums` или `include=tracks`
- `explicitFilter=INCLUDE`

## Rejected / incorrect

- `application/vnd.tidal.v1+json` для этих probes давал `404`.
- Root `/searchResults/{id}` давал `404`.
- Backend scraping `tidal.com/search` был rejected ранее.

## Candidate shape

JSON:API `data` содержит resource identifiers.
`included` содержит candidate objects.

Observed fields:

- `id`
- `type`
- `title`
- `releaseDate`

`artist` и `url` могут отсутствовать inline.

Safe TIDAL URL derivation:

- albums → `https://tidal.com/album/{id}`
- tracks → `https://tidal.com/track/{id}`

## Decision

TIDAL Open API is feasible as a resolver source candidate.
Runtime integration allowed only as the next safe slice.
Auto-parse and auto-resolve remain forbidden until candidate scoring is implemented and approved.

## Next safe slice

Roadmap 5.4.2 — read-only TIDAL Open API candidates adapter.

## Non-goals

- no auto-parse
- no auto-resolve
- no cache changes
- no TIDAL success response shape changes
- no new dependencies unless explicitly approved
