# Roadmap 4.37 - Local legal fixture manifest approval gate

## Purpose

Roadmap 4.37 creates an explicit approval gate before preparing a local-only audio fixture manifest for future MusiCNN TensorFlow vs ONNX parity evaluation.

This gate exists because Roadmap 4.35 and Roadmap 4.36 stopped at metadata-only scaffold validation. Moving from recorded metadata into audio fixtures is a separate legal, provenance, and technical boundary.

Roadmap 4.37 does not create the fixture manifest and does not run inference.

## Current state after Roadmap 4.36

- The local-only scaffold exists.
- The dry-run evidence artifact exists and validates.
- No inference is approved.
- No ONNX Runtime execution is approved.
- No TensorFlow baseline inference is approved.
- No model output comparison is approved.
- No provider implementation is approved.
- `legacy_musicnn` remains the production baseline.

## Future fixture manifest purpose

A future fixture manifest would record a local-only set of audio fixtures for a future MusiCNN TensorFlow vs ONNX parity evaluation.

The manifest would provide reproducible comparison context while keeping audio files outside the repository. It must not claim inference approval, parity approval, production approval, or provider readiness.

## Future manifest location

Potential future metadata-only artifact:

```text
docs/lightweight/evaluation/fixtures/local-musicnn-onnx-parity-fixture-manifest.json
```

Roadmap 4.37 does not create this file. Future manifest creation requires a later approved step.

## Local-only fixture path policy

Recommended future local fixture path:

```text
/tmp/music-tools-onnx-parity/fixtures/
```

Forbidden fixture paths:

- repository root;
- `docs/`;
- `tests/`;
- `app/`;
- any git-tracked path;
- any location under `/opt/music-tools/genre-classifier`.

## Future fixture metadata fields

Required or expected fields for a future metadata-only fixture manifest:

- `fixture_id`;
- `local_path`;
- `local_only`;
- `artifact_in_repo`;
- `committed_to_repo`;
- `duration_seconds`;
- `file_size_bytes`;
- `sha256`;
- `audio_format`;
- `sample_rate_hz`;
- `channels`;
- `source_type`;
- `license_status`;
- `usage_permission`;
- `provenance_notes`;
- `expected_quality_notes`;
- `category`;
- `tags`;
- `approved_for_local_parity_evaluation`;
- `approved_for_repo_inclusion`.

Expected safe defaults:

- `local_only: true`;
- `artifact_in_repo: false`;
- `committed_to_repo: false`;
- `approved_for_repo_inclusion: false`.

## Fixture categories

Possible future fixture categories:

- clear mainstream genre sample;
- ambiguous or overlapping genre sample;
- low-confidence or edge sample;
- short sample;
- production-relevant sample;
- silence, corrupt, or unreadable negative sample, only if appropriate and safe.

## Legal/provenance policy

Future audio fixtures must be local files with explicit permission or safe internal test material.

Policy requirements:

- no copyrighted audio committed to the repository;
- no redistributable assumption without evidence;
- no audio fixture upload to GitHub;
- no raw audio in `docs/`, `tests/`, or `app/`;
- no derived model output until inference approval;
- license and provenance notes are required;
- unknown usage permission blocks approval.

## Approval boundaries

Approval to create a metadata-only fixture manifest is not approval to:

- add audio files to the repository;
- run TensorFlow inference;
- run ONNX inference;
- compare model outputs;
- call `/classify`;
- add dependencies;
- add `onnxruntime`;
- change provider, default provider, or runtime behavior;
- change Dockerfile or Docker Compose;
- start shadow execution;
- start canary rollout;
- start production migration.

## Future validation expectations

Future manifest validation should check:

- JSON readability;
- required fields;
- `local_path` outside the repository;
- `artifact_in_repo: false`;
- `committed_to_repo: false`;
- `approved_for_repo_inclusion: false`;
- `approved_for_local_parity_evaluation` only after explicit review;
- no inference approval flags;
- no production approval flags;
- legal and provenance fields present;
- unknown usage permission blocks approval.

## No-go checklist

- Audio file in the repository.
- Copyrighted audio committed to the repository.
- Missing license or provenance notes.
- Unknown usage permission.
- Fixture path inside the repository.
- Fixture manifest claims inference approval.
- Manifest used to call `/classify`.
- Manifest used to trigger TensorFlow or ONNX execution.
- Production provider changes.
- Dependency or runtime changes.
- Dockerfile or Docker Compose changes.
- `tidal-parser` changes.

## Decision options

- Approve future creation of a metadata-only local fixture manifest.
- Approve only a sample or template manifest first.
- Require legal/provenance review before a real manifest.
- Block until local legal audio fixtures are identified.
- Block until fixture storage path is confirmed.
- Keep `legacy_musicnn` as the only production path.

## Recommended decision

Recommended default decision:

- approve only future metadata-only fixture manifest preparation;
- do not approve audio files in the repository;
- do not approve inference;
- do not approve TensorFlow baseline capture;
- do not approve ONNX execution;
- do not approve model output comparison;
- keep `legacy_musicnn` as the production baseline.

## Explicit non-goals

- No fixture manifest creation.
- No audio files.
- No model files.
- No inference.
- No TensorFlow inference.
- No ONNX Runtime execution.
- No model output comparison.
- No `/classify` calls.
- No provider implementation.
- No provider factory changes.
- No dependency changes.
- No `onnxruntime`.
- No network or download logic.
- No controlled vocabulary changes.
- No runtime changes.
- No Dockerfile or Docker Compose changes.
- No default provider switch.
- No `/classify` contract changes.
- No response shape changes.
- No cache semantics changes.
- No `tidal-parser` changes.
- No shadow execution.
- No canary rollout.
- No production migration.
- No tag or release.
