# Roadmap 5.4 — TIDAL resolver source decision

Status: decision / rejected spike

Scope: tidal-parser only

## Background

Qobuz identity now extracts `artist`, `title`, `year`, and `type`, and it already shows copy helpers plus the manual TIDAL search helper.

## Tested rejected approach

Backend fetch of `https://tidal.com/search?...` followed by HTML parsing of the TIDAL search page.

## Evidence

- Live validation received `403 Forbidden`.
- TIDAL returned a JS/captcha challenge instead of usable search results.
- No candidates were obtained.
- Unit tests with mocked HTML are not enough to make this approach production-safe.

## Decision

Do not use backend HTML scraping of TIDAL search pages as a resolver source.

## Current safe baseline

Qobuz canonical URL -> Qobuz identity -> Copy release line / Copy Music prompt -> manual TIDAL search helper -> user selects TIDAL URL -> existing TIDAL parse flow.

## Future options

1. Reuse an official/stable TIDAL API/client only if one is available and explicitly approved.
2. Use an external search backend such as Brave Search API only as a separate architecture decision.
3. Keep the manual helper as the default baseline.

## Non-goals

- no auto-parse
- no auto-resolve
- no scraping/headless browser
- no new dependencies
- no cache/pipeline changes
- no TIDAL success response shape changes
