# Roadmap 2.13 Decision Artifact

## Summary

Roadmap 2.13 connects the runtime shadow observer to the real `genre-classifier` classify flow.

The shadow observer runs after production legacy response values are built. The production response remains legacy-only, and the shadow path is diagnostic-only.

This stage does not change provider routing, external API behavior, response shape, serving mode, or production classification decisions.

## Implemented

Roadmap 2.13 implemented:

- disabled-by-default runtime shadow execution guard;
- config gate for runtime shadow execution;
- sample-rate based request selection;
- timeout budget for the full shadow observer execution;
- max concurrency limit;
- no queueing: concurrency saturation skips shadow execution;
- classify wiring after production `genres` / `genres_pretty` values are built;
- runtime structured diagnostics logging;
- runtime shadow execution baseline documentation.

Commit trail:

- `ae8ec99` - `feat/shadow: add runtime execution guard`
- `2e80d16` - `feat/classify: run shadow observer after legacy response`
- `786c5cb` - `feat/shadow: add runtime diagnostics logging`
- `2545e26` - `docs/shadow: document runtime shadow execution baseline`

## Unchanged Invariants

The following invariants remain unchanged:

- default provider remains `legacy_musicnn`;
- `/classify` API is unchanged;
- response shape is unchanged;
- LLM/shadow result is not returned externally;
- no canary serving;
- no provider cutover;
- no `tidal-parser` changes;
- no artifact writing in this stage.

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

Diagnostics are expected to stay low-noise and must not include raw audio, prompts, raw LLM responses, full tag arrays, secrets, or large payload dumps.

## Evidence

### Automated Tests

Command:

```bash
cd /opt/music-tools/genre-classifier
PYTHONPATH=. pytest
```

Result:

```text
238 passed in 0.51s
```

### Container Smoke

Commands:

```bash
cd /opt/music-tools/genre-classifier
docker compose build
docker compose up -d
curl -s http://localhost:8021/health
docker compose logs --tail=120 genre-classifier
```

Evidence:

- `docker compose build` completed successfully;
- `docker compose up -d` completed successfully;
- `/health` on `localhost:8021` returned `{"ok":true}`;
- logs show Uvicorn running on `http://0.0.0.0:8021`;
- logs show `GET /health` returned `200 OK`.

## Known Notes

- TensorFlow CUDA/libcuda warnings were observed during container smoke testing.
- These warnings are pre-existing and expected for the current legacy TensorFlow base.
- They are not caused by Roadmap 2.13.
- Runtime shadow execution is still disabled by default.

## Deferred

The following work remains deferred:

- JSONL/evidence artifact writing;
- limited canary serving;
- provider cutover;
- deferred compatibility candidates from Roadmap 2.11 remain diagnostic context only.

## Stop Conditions Before Future Limited Canary

Do not proceed to a future limited canary if any of these are observed:

- any `/classify` response shape change;
- shadow execution affects response status code;
- shadow execution affects production payload;
- shadow timeout or failure affects the request;
- concurrency is uncontrolled;
- logs are noisy or unsafe;
- shadow output is invalid or unstable;
- rollback is unclear or untested.

## Decision

Roadmap 2.13 is complete as a runtime shadow execution baseline.

The system is ready for continued observation and later planning of artifact capture or limited canary work, but this artifact does not approve canary serving, provider cutover, default provider changes, or API changes.
