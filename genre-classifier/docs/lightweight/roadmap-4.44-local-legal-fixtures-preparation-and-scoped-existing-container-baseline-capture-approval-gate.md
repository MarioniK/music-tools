# Roadmap 4.44 - Local legal fixtures preparation and scoped existing-container baseline capture approval gate

## Goal

Roadmap 4.44 prepares an approval artifact for two prerequisites of a future Roadmap 4.45 scoped baseline capture:

- legal local audio fixtures outside the repository;
- scoped existing-container baseline capture readiness.

This is a preparation gate only. It is not a numeric parity run, production migration, provider implementation, default-provider switch, release, or tag.

## Checked

- Existing Roadmap 4.35-4.43 parity scaffold artifacts and validator coverage.
- The allowed external fixture workspace policy.
- Whether fixture files were available for sanitized metadata capture.
- Whether Docker Compose discovery was necessary for this gate.

## Fixture Policy

Allowed fixture workspace:

```text
/tmp/music-tools-onnx-parity/fixtures/
```

Fixtures must remain outside the repository and outside git-tracked paths. Audio fixtures must not be copied into the repo root, `docs/`, `tests/`, `app/`, any path under `genre-classifier`, or any other tracked path.

The committed report may include only sanitized metadata. It must not include audio bytes, private full fixture paths, fake fixtures, fake readiness, model binaries, or venv contents.

## Container Policy

The selected future strategy is `existing_container_local_only` with `scope: scoped_baseline_capture_only`.

Docker Compose commands were not needed for this gate because fixtures are missing. Service name and container availability remain unconfirmed. Any future discovery must run only from `/opt/music-tools/genre-classifier` and must be limited to:

```text
docker compose config --services
docker compose ps
```

No rebuild, `up`, provider execution, inference exec, `/classify` call, or Compose file edit is allowed by this gate.

## Decision

`decision_status`: `blocked_missing_fixtures`

`approved_for_scoped_baseline_capture`: `false`

`ready_for_scoped_baseline_capture`: `false`

Blockers:

- `FIXTURE_FILES_MISSING`

The allowed external workspace exists, but it contains no audio fixture files. No fake audio or invented provenance was created.

## Explicitly Not Executed

- No numeric parity run.
- No TensorFlow model execution.
- No ONNX model execution.
- No TensorFlow vs ONNX comparison.
- No ONNX parity execution.
- No `/classify` calls.
- No Docker rebuild.
- No Dockerfile or Docker Compose changes.
- No production dependency changes.
- No provider factory or default-provider changes.
- No `/classify` contract or response-shape changes.
- No cache changes.
- No audio or model binaries added.
- No venv committed.
- No `tidal-parser` changes.
- No commit, push, tag, or release.

## Roadmap 4.45 Next Step

Roadmap 4.45 may perform scoped existing-container baseline capture only after legal fixtures, fixture provenance, service discovery, and container readiness are confirmed. Until then, baseline capture remains blocked.
