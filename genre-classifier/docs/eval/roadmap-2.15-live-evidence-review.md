# Roadmap 2.15 Live Evidence Review

## Purpose

This document records the results of controlled runtime shadow evidence collection for Roadmap 2.15.

It captures manual live evidence for enabled runtime shadow scenarios after:

- `554906b` - `docs/eval: add roadmap 2.15 controlled shadow evidence plan`
- `b05233a` - `docs/eval: add roadmap 2.15 live evidence review template`
- `12074a3` - `fix/runtime: support Python 3.6 event loop fallback`

This review does not approve canary serving, provider cutover, API changes, response shape changes, or committed runtime behavior changes.

## Scope

- `genre-classifier` only;
- no `tidal-parser` changes;
- no runtime behavior changes committed during this review;
- no `/classify` API changes;
- no response shape changes;
- no canary;
- no cutover.

## Environment Snapshot

- date: 2026-04-29 / 2026-04-30 review session
- git commit: `12074a359624254ca7ea93525653f0d36078bd04`
- runtime provider: `legacy_musicnn`
- shadow enabled: temporary review-only one-off containers
- shadow sample rate: scenario-specific, `0.0` or `1.0`
- shadow timeout: scenario-specific, `0.001`, `2.0`, or `10.0`
- shadow max concurrency: `1`
- local LLM/provider endpoint if used: `http://127.0.0.1:9/infer` and `http://172.25.0.1:9999/infer`
- audio fixture: `app/tmp/upload.mp3`
- `/classify` request: `POST` multipart form, file field `file`
- notes: normal committed/default service config was restored after review; default service showed `genre_classifier.shadow.skipped` with status `skipped_by_config`.

## Baseline Blocker And Resolution

Initial baseline review found that `/classify` failed in the container runtime:

```text
module 'asyncio' has no attribute 'get_running_loop'
```

Cause:

- the `genre-classifier` container uses Python 3.6.9;
- Python 3.6 does not provide `asyncio.get_running_loop`.

Resolution:

- commit `12074a3` added a minimal compatibility fallback;
- after rebuild, `/health` returned `{"ok": true}`;
- `/classify` returned a legacy-only response;
- response keys were `ok`, `message`, `genres`, `genres_pretty`;
- forbidden fields were absent: `shadow`, `llm`, `comparison`, `diagnostics`, `debug`, `canary`.

## Production Response Immutability Baseline

- [x] HTTP status controlled by legacy path;
- [x] response shape unchanged;
- [x] no shadow fields;
- [x] no llm fields;
- [x] no comparison fields;
- [x] no diagnostics/debug fields;
- [x] `genres` legacy-derived;
- [x] `genres_pretty` legacy-derived.

Baseline evidence after hotfix:

- `/health`: `{"ok": true}`
- `/classify` response keys: `ok`, `message`, `genres`, `genres_pretty`
- forbidden fields: none
- default service log after restore: `event=genre_classifier.shadow.skipped status=skipped_by_config`
- result: pass
- note: this confirms committed/default service config does not execute shadow.

## Scenario Review Matrix

| scenario | runtime config used | manual trigger | expected log event/status | observed log event/status | production response immutable | result | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| completed/success | shadow enabled, `sample_rate=1.0`, `timeout=2.0`, `max_concurrent=1`, `LLM_CLIENT=stub` | one `POST /classify` with `app/tmp/upload.mp3` | `genre_classifier.shadow.completed` / `success` | `genre_classifier.shadow.completed` / `success` | yes | pass | provider selected `llm`, stub client returned 3 labels |
| skipped_by_sampling | shadow enabled, `sample_rate=0.0`, `timeout=2.0`, `max_concurrent=1`, `LLM_CLIENT=stub` | one-off runtime container and `POST /classify` | `genre_classifier.shadow.skipped` / `skipped_by_sampling` | `genre_classifier.shadow.skipped` / `skipped_by_sampling` | yes | pass | one-off stdout contained evidence; compose logs also had older default-service entries |
| skipped_by_concurrency | shadow enabled, `sample_rate=1.0`, `timeout=10.0`, `max_concurrent=1`, `LLM_CLIENT=local_http`, slow endpoint | two overlapping `POST /classify` requests | `genre_classifier.shadow.skipped` / `skipped_by_concurrency` | `genre_classifier.shadow.skipped` / `skipped_by_concurrency` | yes | pass | both production responses returned `200 OK` |
| timeout | shadow enabled, `sample_rate=1.0`, `timeout=0.001`, `max_concurrent=1`, `LLM_CLIENT=local_http`, slow endpoint | one `POST /classify` against reachable slow endpoint | `genre_classifier.shadow.timeout` / `timeout` | `genre_classifier.shadow.timeout` / `timeout` | yes | pass | delayed provider validation logs appeared after timeout as background noise |
| provider_error | shadow enabled, `sample_rate=1.0`, `timeout=2.0`, `max_concurrent=1`, `LLM_CLIENT=local_http`, bad endpoint | one `POST /classify` to closed local port | `genre_classifier.shadow.failed` / `provider_error` | `genre_classifier.shadow.failed` / `provider_error` | yes | pass | transport refusal isolated from production response |
| invalid_output | not safely live-reproducible through current `/classify` runtime path | not run as live scenario | `genre_classifier.shadow.failed` / `invalid_output` | not observed | not applicable | gap documented | malformed local HTTP responses surface as provider/client validation errors |

## Detailed Scenario Notes

### completed/success

- runtime config:
  - `GENRE_PROVIDER=legacy_musicnn`
  - `GENRE_CLASSIFIER_SHADOW_ENABLED=true`
  - `GENRE_CLASSIFIER_SHADOW_PROVIDER=llm`
  - `GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0`
  - `GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS=2.0`
  - `GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT=1`
  - `LLM_CLIENT=stub`
- command/request: `POST /classify` multipart form with `file=@app/tmp/upload.mp3`
- relevant log evidence:
  - `2026-04-29 22:22:08,332 INFO genre_classifier event=genre_classifier.shadow.started status=started`
  - `2026-04-29 22:22:08,332 INFO genre_classifier event=genre_provider_selected provider_name=llm provider_class=LlmGenreProvider`
  - `2026-04-29 22:22:08,332 INFO genre_classifier event=llm_provider_started provider_name=llm client_name=StubLlmInferenceClient`
  - `2026-04-29 22:22:08,333 INFO genre_classifier event=llm_provider_succeeded provider_name=llm client_name=StubLlmInferenceClient model_name=llm-scaffold-v1 genres_count=3`
  - `2026-04-29 22:22:08,333 INFO genre_classifier event=genre_classifier.shadow.completed status=success`
- response immutability check: keys were `ok`, `message`, `genres`, `genres_pretty`; forbidden fields absent.
- observed result: pass.
- blockers/gaps: none for this scenario.

### skipped_by_sampling

- runtime config:
  - `GENRE_PROVIDER=legacy_musicnn`
  - `GENRE_CLASSIFIER_SHADOW_ENABLED=true`
  - `GENRE_CLASSIFIER_SHADOW_PROVIDER=llm`
  - `GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=0.0`
  - `GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS=2.0`
  - `GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT=1`
  - `LLM_CLIENT=stub`
- command/request: `POST /classify` multipart form with `file=@app/tmp/upload.mp3`
- relevant log evidence:
  - `2026-04-29 22:17:11,266 INFO genre_classifier event=genre_classifier.shadow.skipped status=skipped_by_sampling`
  - `2026-04-29 22:17:53,000 INFO genre_classifier event=genre_classifier.shadow.skipped status=skipped_by_sampling`
- response immutability check: keys were `ok`, `message`, `genres`, `genres_pretty`; forbidden fields absent.
- observed result: pass.
- blockers/gaps: `docker compose logs` showed older `skipped_by_config` entries from the normal service container; actual one-off evidence was captured from `docker compose run` stdout.

### skipped_by_concurrency

- runtime config:
  - `GENRE_PROVIDER=legacy_musicnn`
  - `GENRE_CLASSIFIER_SHADOW_ENABLED=true`
  - `GENRE_CLASSIFIER_SHADOW_PROVIDER=llm`
  - `GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0`
  - `GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS=10.0`
  - `GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT=1`
  - `LLM_CLIENT=local_http`
  - `LLM_LOCAL_HTTP_ENDPOINT=http://172.25.0.1:9999/infer`
  - `LLM_LOCAL_HTTP_TIMEOUT_SECONDS=10.0`
- command/request: two overlapping `POST /classify` requests with `file=@app/tmp/upload.mp3`.
- relevant log evidence:
  - `2026-04-29 22:34:54,367 INFO genre_classifier event=file_processing_started filename=upload.mp3 size_bytes=7470185`
  - `2026-04-29 22:34:54,387 INFO genre_classifier event=file_processing_started filename=upload.mp3 size_bytes=7470185`
  - `2026-04-29 22:35:00,801 INFO genre_classifier event=genre_classifier.shadow.started status=started`
  - `2026-04-29 22:35:00,803 INFO genre_classifier event=local_llm_http_request_started endpoint=http://172.25.0.1:9999/infer timeout_seconds=10.0`
  - `2026-04-29 22:35:06,461 INFO genre_classifier event=genre_classifier.shadow.skipped status=skipped_by_concurrency`
- response immutability check:
  - request 1 keys: `ok`, `message`, `genres`, `genres_pretty`; forbidden fields absent;
  - request 2 keys: `ok`, `message`, `genres`, `genres_pretty`; forbidden fields absent;
  - both `POST /classify` requests returned `200 OK`.
- observed result: pass.
- blockers/gaps: first shadow request later timed out and emitted delayed `invalid_payload` / `validation_error` logs from the slow endpoint; this did not affect either production response.

### timeout

- runtime config:
  - `GENRE_PROVIDER=legacy_musicnn`
  - `GENRE_CLASSIFIER_SHADOW_ENABLED=true`
  - `GENRE_CLASSIFIER_SHADOW_PROVIDER=llm`
  - `GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0`
  - `GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS=0.001`
  - `GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT=1`
  - `LLM_CLIENT=local_http`
  - `LLM_LOCAL_HTTP_ENDPOINT=http://172.25.0.1:9999/infer`
  - `LLM_LOCAL_HTTP_TIMEOUT_SECONDS=5.0`
- command/request:
  - temporary manual Python HTTP server on host port `9999`;
  - container reachability verified by `GET` returning `HTTP/1.0 501 Unsupported method`;
  - one `POST /classify` with `file=@app/tmp/upload.mp3`.
- relevant log evidence:
  - `2026-04-29 22:32:12,400 INFO genre_classifier event=genre_classifier.shadow.started status=started`
  - `2026-04-29 22:32:12,401 INFO genre_classifier event=local_llm_http_request_started endpoint=http://172.25.0.1:9999/infer timeout_seconds=5.0`
  - `2026-04-29 22:32:12,402 INFO genre_classifier event=genre_classifier.shadow.timeout status=timeout`
  - `POST /classify returned 200 OK`
- response immutability check: keys were `ok`, `message`, `genres`, `genres_pretty`; forbidden fields absent.
- observed result: pass.
- blockers/gaps: delayed local HTTP `invalid_payload` / validation error logs appeared after timeout from the timed-out provider path; recorded as post-timeout background noise, not as production response impact.

### provider_error

- runtime config:
  - `GENRE_PROVIDER=legacy_musicnn`
  - `GENRE_CLASSIFIER_SHADOW_ENABLED=true`
  - `GENRE_CLASSIFIER_SHADOW_PROVIDER=llm`
  - `GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0`
  - `GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS=2.0`
  - `GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT=1`
  - `LLM_CLIENT=local_http`
  - `LLM_LOCAL_HTTP_ENDPOINT=http://127.0.0.1:9/infer`
  - `LLM_LOCAL_HTTP_TIMEOUT_SECONDS=1.0`
- command/request: `POST /classify` multipart form with `file=@app/tmp/upload.mp3`.
- relevant log evidence:
  - `2026-04-29 22:26:01,676 INFO genre_classifier event=genre_classifier.shadow.started status=started`
  - `2026-04-29 22:26:01,677 INFO genre_classifier event=genre_provider_selected provider_name=llm provider_class=LlmGenreProvider`
  - `2026-04-29 22:26:01,677 INFO genre_classifier event=llm_provider_started provider_name=llm client_name=LocalHttpLlmInferenceClient`
  - `2026-04-29 22:26:01,677 INFO genre_classifier event=local_llm_http_request_started endpoint=http://127.0.0.1:9/infer timeout_seconds=1.0`
  - `2026-04-29 22:26:01,678 ERROR genre_classifier event=local_llm_http_request_failed category=transport endpoint=http://127.0.0.1:9/infer timeout_seconds=1.0 reason=[Errno 111] Connection refused`
  - `2026-04-29 22:26:01,678 ERROR genre_classifier event=llm_provider_failed provider_name=llm client_name=LocalHttpLlmInferenceClient failure_category=transport_error error=local llm runtime transport request failed`
  - `2026-04-29 22:26:01,678 INFO genre_classifier event=genre_classifier.shadow.failed status=provider_error`
- response immutability check: keys were `ok`, `message`, `genres`, `genres_pretty`; forbidden fields absent.
- observed result: pass.
- blockers/gaps: none for this scenario.

### invalid_output

- runtime config: not safely live-reproducible through current `/classify` runtime path without adding helper/change.
- command/request: not run as a live scenario.
- relevant log evidence: not observed.
- response immutability check: not applicable.
- observed result: documented live evidence gap.
- blockers/gaps:
  - malformed local HTTP responses are mapped through provider/client validation;
  - they surface as provider/local HTTP validation errors, not cleanly as runtime observer `invalid_output`;
  - recommended follow-up is to keep this out of Roadmap 2.15 runtime scope;
  - consider a tiny test/stub helper or runtime evidence artifact baseline in a later step only if needed.

## Stop Conditions Review

- [x] no production response mutation;
- [x] no shadow result exposed externally;
- [x] no response shape change;
- [x] no shadow failure affected HTTP response;
- [x] no sampling guard failure;
- [x] no concurrency guard failure;
- [x] no timeout isolation failure;
- [x] logs sufficient for safety-oriented review;
- [x] no committed defaults changed;
- [x] no canary appeared;
- [x] no cutover appeared.

## Evidence Sufficiency Assessment

- logs sufficient for safety review: yes.
- logs insufficient areas: durable artifact trail, detailed genre-level disagreement review, clean live `invalid_output` reproduction.
- artifact writing needed now: no.
- recommended follow-up: create Roadmap 2.15 decision artifact; optionally consider runtime evidence artifacts baseline later.

## Decision

- [x] evidence sufficient for v0.2.15 release discussion, with `invalid_output` gap documented;
- [x] no immediate runtime shadow hardening blocker identified;
- [x] runtime evidence artifacts baseline is optional follow-up, not an immediate blocker;
- [x] canary remains not approved;
- [x] cutover remains not approved.
