# Roadmap 2.13 Runtime Shadow Execution Baseline

This document records the Roadmap 2.13 runtime shadow execution baseline for `genre-classifier`.

Roadmap 2.13 introduces a controlled runtime shadow observer path for diagnostics only. It does not change the external `/classify` API, response shape, default provider, serving mode, or production decision path.

## Implemented Baseline

Roadmap 2.13 currently includes:

- disabled-by-default runtime shadow execution guard;
- config-gated execution;
- sample-rate based request selection;
- timeout budget for the full shadow observer execution;
- max concurrency limit;
- no queueing: concurrency saturation skips shadow execution;
- classify wiring after the production legacy response values are built;
- runtime diagnostics logging;
- no artifact writing in this slice.

The runtime commits covered by this baseline are:

- `ae8ec99` - `feat/shadow: add runtime execution guard`
- `2e80d16` - `feat/classify: run shadow observer after legacy response`
- `786c5cb` - `feat/shadow: add runtime diagnostics logging`

## Runtime Wiring

The shadow observer is wired into the classify orchestration after the production legacy path has already produced:

- `genres`
- `genres_pretty`

The production response remains legacy-only. Shadow output is not returned to callers and is not added to the response payload.

The `/classify` response shape remains unchanged:

```json
{
  "ok": true,
  "message": "Аудио проанализировано",
  "genres": [],
  "genres_pretty": []
}
```

No `shadow`, `llm`, `comparison`, `diagnostics`, or `canary` fields are exposed externally.

## Execution Safeguards

Runtime shadow execution is protected by these safeguards:

- shadow execution is disabled by default;
- config controls whether shadow execution is allowed;
- `sample_rate=0.0` skips shadow execution;
- `sample_rate=1.0` runs shadow when enabled and capacity is available;
- `0.0 < sample_rate < 1.0` uses probabilistic sampling;
- timeout is isolated from the production response path;
- concurrency saturation skips shadow execution instead of queueing;
- observer exceptions are swallowed and converted into internal diagnostic outcomes;
- comparison failures are swallowed and converted into internal diagnostic outcomes;
- logging failures are swallowed;
- no canary serving is implemented;
- no provider cutover is implemented.

Shadow execution must not affect:

- response status code;
- production `genres`;
- production `genres_pretty`;
- response shape;
- default provider selection.

## Observability

Runtime shadow diagnostics use the existing `genre_classifier` logger.

Lifecycle events:

- `genre_classifier.shadow.skipped`
- `genre_classifier.shadow.started`
- `genre_classifier.shadow.completed`
- `genre_classifier.shadow.timeout`
- `genre_classifier.shadow.failed`

Safe diagnostic fields:

- `status`
- `duration_ms`
- `legacy_tags_count`
- `shadow_tags_count`
- `overlap_count`
- `missing_from_shadow_count`
- `extra_in_shadow_count`
- `error_type`

Diagnostics may also include low-noise runtime metadata such as whether shadow execution was enabled and the configured sample rate.

The diagnostics must not log:

- raw audio;
- prompts;
- raw LLM responses;
- full tag arrays;
- secrets;
- large payload dumps.

## Manual Smoke Check

Run all commands from:

```bash
cd /opt/music-tools/genre-classifier
```

### Unit Test Baseline

```bash
PYTHONPATH=. pytest
```

Expected result: all tests pass.

### Build And Run

```bash
docker compose build
docker compose up
```

In another shell:

```bash
cd /opt/music-tools/genre-classifier
curl -s http://localhost:8021/health
```

Expected response:

```json
{"ok":true}
```

Use the configured service port if local compose overrides differ.

### Scenario: Shadow Disabled

Start the service with shadow disabled or unset:

```bash
GENRE_CLASSIFIER_SHADOW_ENABLED=false docker compose up
```

Expected behavior:

- `/classify` response shape remains unchanged;
- shadow observer does not run;
- diagnostics may record `genre_classifier.shadow.skipped` with `skipped_by_config`;
- no shadow output appears in API responses.

### Scenario: Shadow Enabled With Sample Rate 0.0

```bash
GENRE_CLASSIFIER_SHADOW_ENABLED=true \
GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=0.0 \
docker compose up
```

Expected behavior:

- production response remains legacy-only;
- shadow observer does not run;
- diagnostics may record `genre_classifier.shadow.skipped` with `skipped_by_sampling`;
- no shadow output appears in API responses.

### Scenario: Shadow Enabled With Sample Rate 1.0

```bash
GENRE_CLASSIFIER_SHADOW_ENABLED=true \
GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0 \
docker compose up
```

Expected behavior:

- production response remains legacy-only;
- shadow observer runs after production response values are built;
- diagnostics may record `genre_classifier.shadow.started`;
- diagnostics may record `genre_classifier.shadow.completed`, `genre_classifier.shadow.timeout`, or `genre_classifier.shadow.failed`;
- no shadow output appears in API responses.

### Scenario: Shadow Timeout Or Failure

Use a very small timeout to exercise timeout handling:

```bash
GENRE_CLASSIFIER_SHADOW_ENABLED=true \
GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0 \
GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS=0.001 \
docker compose up
```

Expected behavior:

- `/classify` status and payload remain controlled by the production legacy path;
- shadow timeout/failure does not fail the request;
- diagnostics may record `genre_classifier.shadow.timeout` or `genre_classifier.shadow.failed`;
- no shadow output appears in API responses.

### Scenario: Concurrency Saturation

If convenient, set max concurrency to `1` and issue overlapping classification requests:

```bash
GENRE_CLASSIFIER_SHADOW_ENABLED=true \
GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE=1.0 \
GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT=1 \
docker compose up
```

Expected behavior:

- at most one shadow execution runs at a time;
- saturated shadow executions skip instead of queueing;
- diagnostics may record `genre_classifier.shadow.skipped` with `skipped_by_concurrency`;
- production responses remain unchanged.

## Stop Conditions Before Future Limited Canary

Do not proceed to a future limited canary if any of these are observed:

- `/classify` response shape changes;
- shadow execution affects response status code;
- shadow execution affects production payload;
- shadow timeout or failure affects the request;
- evidence logs are missing;
- concurrency is uncontrolled;
- logs are noisy or include large payloads;
- logs expose raw audio, prompts, raw LLM responses, full tag arrays, or secrets;
- shadow output is invalid or unstable;
- rollback story is unclear or untested.

## Non-Goals

This baseline explicitly does not include:

- default provider change;
- LLM serving enablement;
- canary serving;
- provider cutover;
- external API changes;
- response shape changes;
- artifact writing in this docs slice;
- `tidal-parser` changes.

## Future Work

Future slices may add artifact capture or limited canary behavior only after this baseline remains stable and the stop conditions above are cleared. Any future serving change should remain independently gated, reversible, and supported by a clear rollback plan.
