# Example Lightweight Evaluation Report

Status: example skeleton only

## Summary

This report is an example format for a future offline lightweight classifier evaluation. No real inference was run, no provider was implemented, no production code was changed, and no production decision is made.

## Scope

This skeleton covers artifact shape only:

- example manifest structure
- example baseline output structure
- example candidate output structure
- example comparison report structure
- approval gate visibility

It does not include audio fixtures, model files, runtime changes, dependency changes, shadow execution, canary rollout, or migration work.

## Production Contract

`legacy_musicnn` remains the production baseline and default provider.

The `/classify` contract is unchanged. Provider output examples preserve:

- `ok`
- `message`
- `genres`
- `genres_pretty`

Evaluation-only fields such as `normalized_genres`, `warnings`, and `metrics` are not part of the production response shape.

## Fixture Coverage

Example fixture categories:

- `clear_mainstream_genres`
- `adjacent_overlapping_genres`
- `hybrid_material`
- `ambiguous_low_confidence_audio`
- `negative_edge_fixtures`

Coverage is illustrative. Real fixtures must be approved for licensing, provenance, duration, and local offline evaluation before any run.

## Aggregate Comparison

No aggregate comparison exists. The example baseline and candidate artifacts contain illustrative values only and were not captured from real runs.

Expected future comparison dimensions:

- baseline success/failure parity
- candidate-only failures
- normalized genre agreement
- major genre shifts
- resource deltas
- warning categories

## Controlled Vocabulary Results

Not measured. A future report should include controlled vocabulary hit rate, mapped terms, unmapped terms, and mapping-version metadata.

## OOV Results

Not measured. A future report should list out-of-vocabulary terms, affected fixtures, and whether OOV terms block the next approval gate.

## Top-N Overlap

Not measured. A future report should compare top-1, top-3, and top-5 normalized genre overlap when ranked outputs are available.

## Resource Metrics

Not measured. Future resource evidence should capture:

- cold startup/import time
- warm latency
- p95 latency
- peak memory
- model size
- dependency/runtime weight
- Docker image size impact if applicable

Missing resource evidence should be reported as `runtime_metric_missing`.

## Warnings and Failures

Current skeleton warnings:

- `example_only`
- `not_captured_from_real_run`
- `runtime_metric_missing`
- `license_unknown` for candidate model metadata
- `model_not_used` for candidate output

Future reports should preserve warnings and failures as review evidence rather than hiding them in logs.

## Known Gaps

- no real fixture files
- no captured `legacy_musicnn` baseline run
- no captured candidate run
- no model provenance review
- no license review
- no controlled vocabulary measurement
- no OOV measurement
- no top-N overlap measurement
- no resource measurements
- no rollback exercise beyond documentation removal

## Decision

No production decision is made.

This skeleton does not approve offline spike implementation, provider implementation, shadow execution, canary rollout, default-provider switch, production migration, or LLM adoption.

## Approval Gate Status

| Gate | Status | Notes |
| --- | --- | --- |
| offline spike implementation | not_started | Requires explicit approval before executable harness work. |
| provider implementation | not_started | No provider code exists or is approved. |
| shadow execution | not_started | No shadow path is implemented or approved. |
| canary rollout | not_started | No traffic exposure is implemented or approved. |
| default provider switch | not_started | `legacy_musicnn` remains the default provider. |
| production migration | not_started | No migration decision is made. |
| LLM adoption | not_started | Requires a separate explicit approval path. |

## Appendix: Per-Fixture Results

Per-fixture rows below are placeholders. They illustrate the future report layout only.

| Fixture ID | Category | Baseline normalized genres | Candidate normalized genres | Warnings | Result |
| --- | --- | --- | --- | --- | --- |
| fixture_clear_pop_001 | clear_mainstream_genres | pop, electronic | pop, electronic | none | example_only |
| fixture_clear_rock_001 | clear_mainstream_genres | rock | rock | none | example_only |
| fixture_indie_alt_overlap_001 | adjacent_overlapping_genres | rock | rock | adjacent_genre_overlap_expected | example_only |
| fixture_house_techno_overlap_001 | adjacent_overlapping_genres | electronic | electronic | adjacent_genre_overlap_expected | example_only |
| fixture_hiphop_jazz_hybrid_001 | hybrid_material | hip_hop, jazz | hip_hop, jazz | hybrid_material_expected | example_only |
| fixture_sparse_low_confidence_001 | ambiguous_low_confidence_audio | electronic | electronic | low_confidence_fixture | example_only |
| fixture_silence_edge_001 | negative_edge_fixtures | none | none | empty_output | example_only |
| fixture_unsupported_format_edge_001 | negative_edge_fixtures | none | none | fixture_unreadable | example_only |

