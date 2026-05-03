# Lightweight Evaluation Artifacts

## Purpose

This directory contains example documentation and sample artifact skeletons for a future offline evaluation harness for lightweight genre-classifier candidates.

The files here are examples only. They define the intended shape of manifests, baseline outputs, candidate outputs, and human-readable reports. They do not run inference, create a provider implementation, connect to production code, or change runtime behavior.

No audio fixtures, model files, captured inference outputs, or executable harness code are included in this directory.

## Baseline and Contract

`legacy_musicnn` remains the production baseline.

The default provider remains `legacy_musicnn`.

The `/classify` contract is unchanged.

The production response shape remains:

- `ok`
- `message`
- `genres`
- `genres_pretty`

Future offline artifacts must preserve these fields when representing provider outputs, then add evaluation-only fields such as normalized genres, warnings, and metrics outside the production contract.

## Directory Structure

```text
docs/lightweight/evaluation/
├── README.md
├── manifests/
│   └── example-manifest.yaml
├── outputs/
│   ├── example-legacy-baseline-output.json
│   └── example-candidate-output.json
└── reports/
    └── example-evaluation-report.md
```

## Schema and Versioning Conventions

- `schema_version` identifies the artifact schema, not the service version.
- Example artifacts use `schema_version: "0.1"` while the harness is still unimplemented.
- Schema changes should be additive where practical and documented in this README or a future changelog.
- Artifacts should include stable identifiers such as `manifest_id`, `run_id`, provider name, and artifact type.
- Example-only artifacts must state that values are illustrative and not captured from a real run.
- Future captured artifacts should include code revision, runtime identity, fixture manifest metadata, and generation timestamp.

## Future Artifact Expectations

A future offline harness may generate:

- versioned manifests with fixture identity, category, path, provenance, licensing, duration, tags, and expected quality notes
- baseline output artifacts captured from `legacy_musicnn`
- candidate output artifacts with model metadata, provenance, licensing, warnings, and resource metrics
- normalized comparison data for controlled vocabulary hits, OOV terms, top-N overlap, failures, and resource deltas
- markdown reports that summarize evidence and keep approval gates explicit

Generated artifacts should remain offline evidence until separately approved. They should support baseline parity review, rollback planning, and production contract preservation before any provider implementation or runtime migration work.

## Non-Goals

- no production code changes
- no runtime changes
- no dependency changes
- no Dockerfile or Docker Compose changes
- no provider implementation
- no default-provider switch
- no `/classify` contract change
- no response shape change
- no audio fixtures
- no model files
- no actual inference harness
- no shadow execution
- no canary rollout
- no production migration
- no LLM adoption decision

