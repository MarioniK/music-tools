# Roadmap 4.13 - ONNX Candidate Offline Evaluation Report Generation

Status: offline-only tooling safe slice.

## Purpose

Roadmap 4.13 adds a stdlib-only report generator for comparing an existing
baseline output artifact with an existing ONNX candidate output artifact. The
report uses the Roadmap 4.3-4.5 evaluation artifact contract and preserves the
required markdown sections used by the existing lightweight evaluation report
validator.

The report is review evidence only. It is an offline-only static artifact
comparison, not a production decision.

## Scope

This slice is limited to:

- reading baseline output JSON from a supplied path;
- reading candidate output JSON from a supplied path;
- reading the fixture manifest as text and shallow metadata;
- comparing available `genres[].tag` values;
- preserving warning categories already documented by Roadmap 4.5;
- writing a markdown report with the required sections.

The generator does not run inference, call `/classify`, import production
provider/runtime modules, load models, process audio, use Docker, or access the
network.

## Non-Goals

Roadmap 4.13 does not:

- run real ONNX inference;
- run `legacy_musicnn` inference;
- call `/classify`;
- import `app`, service, provider, or runtime modules;
- add a production provider implementation;
- connect an ONNX candidate to the provider factory;
- change the default provider from `legacy_musicnn`;
- change the production classifier path;
- change the production response shape;
- add model or audio files;
- add dependencies;
- change requirements, pyproject, lock files, Dockerfile, or Docker Compose;
- perform shadow execution, canary rollout, or production migration.

`tidal-parser` is unchanged.

## Input Artifacts

The generator accepts:

- `--baseline-output`: existing baseline JSON output artifact;
- `--candidate-output`: existing candidate JSON output artifact;
- `--manifest`: existing fixture manifest path;
- `--candidate-name`: optional display name override for the candidate;
- `--decision`: optional report decision text.

The JSON artifacts are expected to follow the existing evaluation output shape:

- top-level metadata such as `provider`, `warnings`, and `aggregate_metrics`;
- `fixture_results`;
- per-fixture production-compatible fields `ok`, `message`, `genres`, and
  `genres_pretty`;
- evaluation-only fields such as `normalized_genres`, `warnings`, and
  `metrics` when present.

The manifest is read as UTF-8 text. The generator extracts only shallow
metadata such as schema version, manifest id, fixture count, and fixture
categories. It does not require PyYAML and does not access fixture files.

## Output Report

`scripts/lightweight/generate_evaluation_report.py` writes a markdown report to
`--output-report`.

Required markers in generated reports:

- offline-only static artifact comparison;
- not production decision;
- inference executed: no;
- `/classify` called: no;
- production provider/runtime imports: no;
- default provider changed: no;
- approval gate: not approved for production.

The report states that synthetic/example artifacts are not real quality
evaluation and must not be treated as production readiness evidence.

## Report Sections

Generated reports include the Roadmap 4.5 required sections:

- summary;
- scope;
- baseline provider;
- candidate provider;
- manifest;
- fixture coverage;
- aggregate comparison;
- controlled vocabulary results;
- OOV results;
- top-N overlap;
- resource metrics;
- failures and warnings;
- known gaps;
- decision;
- approval gate status;
- appendix / per-fixture results.

The report also keeps the production contract visible: `legacy_musicnn` remains
the production baseline and default provider, and the `/classify` response shape
remains `ok`, `message`, `genres`, and `genres_pretty`.

## Comparison Calculations

The generator parses `genres[].tag` values from baseline and candidate fixture
results. Tags are compared case-insensitively while preserving original display
values in the report.

Calculations include:

- unique baseline tag count;
- unique candidate tag count;
- unique tag overlap count and ratio;
- per-fixture top-1, top-3, and top-5 overlap;
- average top-1, top-3, and top-5 overlap across comparable fixtures;
- empty baseline or candidate outputs.

The denominator for an overlap ratio is the larger available tag set for that
comparison. Empty outputs produce warnings instead of tracebacks.

## Warning And No-Go Handling

The generator preserves existing artifact warnings and adds review warnings
where static comparison evidence is incomplete.

Important Roadmap 4.13 warning categories:

- `empty_output`;
- `comparison_incomplete`;
- `runtime_metric_missing`;
- `model_provenance_unknown`;
- `license_unknown`.

The report also lists the broader Roadmap 4.5 warning vocabulary for review
compatibility:

- `fixture_missing`;
- `fixture_unreadable`;
- `baseline_failed`;
- `candidate_failed`;
- `empty_output`;
- `oov_terms_detected`;
- `major_genre_shift`;
- `license_unknown`;
- `model_provenance_unknown`;
- `runtime_metric_missing`;
- `comparison_incomplete`.

Any warning is carried into the report as evidence. The generator does not hide
warning categories in logs and does not turn missing evidence into approval.

## Offline-Only And Not-Production Markers

Roadmap 4.13 is explicitly offline-only:

- inference executed: no;
- `/classify` called: no;
- production provider/runtime imports: no;
- default provider changed: no;
- approval gate: not approved for production.

Generated reports are not approval for provider implementation, shadow
execution, canary rollout, default-provider switch, production migration, or
production ONNX use.

## Test Plan

Run from `/opt/music-tools/genre-classifier`:

```bash
python3 -m pytest tests/lightweight -q

python3 scripts/lightweight/generate_evaluation_report.py \
  --baseline-output docs/lightweight/evaluation/outputs/example-legacy-baseline-output.json \
  --candidate-output docs/lightweight/evaluation/outputs/example-candidate-output.json \
  --manifest docs/lightweight/evaluation/manifests/example-manifest.yaml \
  --output-report /tmp/roadmap-4.13-generated-evaluation-report.md \
  --candidate-name onnx_candidate \
  --decision "no production decision"

python3 scripts/lightweight/validate_evaluation_artifacts.py
```

Targeted tests cover:

- CLI report creation from existing example artifacts;
- required report sections;
- offline-only / not-production-decision markers;
- top-N overlap with small temp JSON fixtures;
- empty baseline or candidate output warning behavior;
- controlled failure for invalid or missing JSON;
- operation without ONNX Runtime, model files, Docker, or `/classify`.

## Rollback Considerations

Rollback is limited to removing:

- this documentation artifact;
- `scripts/lightweight/generate_evaluation_report.py`;
- `tests/lightweight/test_generate_evaluation_report.py`.

No production runtime code, provider factory wiring, default provider, Docker
configuration, dependency files, model/audio artifacts, or `/classify` behavior
are changed, so rollback does not require a service migration.
