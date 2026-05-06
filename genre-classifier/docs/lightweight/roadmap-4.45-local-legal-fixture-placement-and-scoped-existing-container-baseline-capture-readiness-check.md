# Roadmap 4.45 - Local legal fixture placement and scoped existing-container baseline capture readiness check

## Goal

Roadmap 4.45 records post-4.44 manual legal fixture placement and checks readiness for a future scoped existing-container baseline capture.

Roadmap 4.44 remains historically correct as `blocked_missing_fixtures`: at that time the external audio fixtures were unavailable. Roadmap 4.45 does not rewrite that decision; it records the later manual placement of legal CC0 fixtures outside the repository.

## Fixture Placement

The fixtures remain outside the repository. No audio files, model files, venv contents, or provenance note files from the external workspace are committed.

The committed report is sanitized and contains only:

- `fixture_id`
- `sha256`
- `file_size_bytes`
- `audio_format`
- `source_artist`
- `license_status`
- `usage_permission`

No full local fixture paths are included in the committed report.

## Scope Boundaries

This is not a production decision. It is not full numeric parity, not TensorFlow vs ONNX comparison, not ONNX model execution, not TensorFlow model output capture, and not provider implementation.

The default provider remains `legacy_musicnn`. The `/classify` contract and response shape remain unchanged. No `/classify` calls were made.

`tidal-parser` is untouched.

## Scoped Existing-Container Readiness

The selected baseline runtime strategy is `existing_container_local_only`. Compose inspection was scoped to the `genre-classifier` service directory and limited to existing-container discovery. No Docker rebuild, Dockerfile change, Compose change, dependency change, provider change, or model execution was performed.

The existing `genre-classifier` service was present and running, and import-only checks for TensorFlow and Essentia succeeded inside the existing container. These checks do not execute the model and do not capture TensorFlow output.

## Decision

`decision_status`: `ready_for_scoped_baseline_capture`

`approved_for_scoped_baseline_capture`: `true`

Blockers: none.

This approval is limited to a future scoped existing-container baseline capture. It does not approve full numeric parity, TensorFlow vs ONNX comparison, ONNX model execution, provider implementation, default provider switch, production migration, tag, or release.

## Next Step

The next step is scoped existing-container baseline capture only if readiness is approved and the same constraints remain in force.
