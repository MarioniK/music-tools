# Roadmap 4.38 - Local-only fixture manifest template / metadata schema preparation

## Purpose

Roadmap 4.38 follows Roadmap 4.37 by converting the legal fixture approval gate into a schema-only template for future local-only audio fixture metadata.

Roadmap 4.37 established that audio fixtures need explicit legal, provenance, and storage review before any real manifest can exist. Roadmap 4.38 keeps that boundary intact while making the future metadata shape reviewable.

## Why this is template-only

This step prepares field names, storage policy, categories, and safe default flags. It does not identify real audio, record real local paths, record hashes, record file sizes, run inference, or compare model outputs.

A real fixture manifest would imply that specific local audio material has passed provenance review and is ready for a later local parity workflow. That approval does not exist yet, so the repository only gets a template with null placeholder values.

## Why audio stays out of the repository

Audio files must remain outside the repository because fixture material can carry copyright, redistribution, privacy, size, and provenance risks. The safe storage direction is a local path outside the service tree:

```text
/tmp/music-tools-onnx-parity/fixtures/
```

The repository must not contain audio fixtures in `docs/`, `tests/`, `app/`, the service tree, or any git-tracked path.

## Approval boundary

Template approval is not inference approval. The template documents the shape of metadata that a later local-only fixture manifest may use, but it does not approve TensorFlow inference, ONNX Runtime execution, output comparison, `/classify` calls, provider wiring, or production rollout.

The template also does not approve adding audio to the repository. `approved_for_local_parity_evaluation`, `approved_for_repo_inclusion`, `approved_for_inference`, and `approved_for_production` all remain false.

## Safe defaults over structure

Safe defaults matter more than a polished schema because the failure mode is not ugly metadata; it is accidentally treating unreviewed fixtures as executable parity evidence. The template therefore defaults to:

- local-only storage outside the repository;
- no committed audio artifacts;
- no hashes, sizes, durations, or local paths until real review;
- no inference, parity, repository, or production approval.

## Production baseline

`legacy_musicnn` remains the production baseline and default provider. Roadmap 4.38 does not change production runtime, provider factory behavior, Docker configuration, cache behavior, response shape, or the `/classify` contract.

## Recommended design

The future manifest should remain a metadata artifact that records local-only fixture identity, provenance, permission status, technical audio metadata, category coverage, and review flags. Real local paths should only point outside the repository after approval. Hashes, sizes, and durations should only be recorded after the real local files are reviewed and measured.

The template lives at:

```text
docs/lightweight/evaluation/fixtures/template-local-musicnn-onnx-parity-fixture-manifest.json
```

## Safe implementation summary

- Added a schema-only fixture manifest template.
- Added fixture storage policy and forbidden path markers.
- Added required fixture field list and planned fixture categories.
- Added one sample fixture object with only null or safe placeholder values.
- Added validator coverage for the template shape and non-approval defaults.
- Added no audio files, model files, real fixture metadata, dependency changes, provider changes, or runtime changes.

## Validation and review plan

Review should confirm:

- JSON parses successfully;
- validator recognizes exactly one fixture manifest template;
- required fixture fields are listed;
- sample fixture has no real local path, hash, size, or duration;
- storage policy points to `/tmp/music-tools-onnx-parity/fixtures/`;
- forbidden paths include repository, docs, tests, app, git-tracked paths, and the service tree boundary;
- no inference, parity, repository inclusion, or production approval is claimed.

## Rollback considerations

Rollback is low risk because the change is documentation and validation only. Removing the markdown file, template JSON, and validator/test additions restores the previous state without touching runtime code or production behavior.

## Explicit non-goals

- No real fixture manifest.
- No audio files.
- No model files.
- No real local audio paths.
- No fake hashes, sizes, or durations.
- No copyrighted audio references.
- No inference.
- No TensorFlow execution.
- No ONNX Runtime execution.
- No model output comparison.
- No `/classify` calls.
- No provider implementation or provider factory changes.
- No default provider changes.
- No dependency changes.
- No `onnxruntime`.
- No network or artifact retrieval logic.
- No Dockerfile or Docker Compose changes.
- No production runtime changes.
- No cache semantics changes.
- No response shape changes.
- No `tidal-parser` changes.
- No commit, tag, release, or push.

## Recommended next step

Roadmap 4.39 - real local-only fixture metadata manifest approval/preparation.
