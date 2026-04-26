# Roadmap 2.10 Decision Artifact Summary

## Stage Goal

Roadmap 2.10 moves the offline evaluation infrastructure from a baseline comparison scaffold into a curated, review-friendly, threshold-interpretable evaluation stage.

The goal of this stage is to make evaluation runs easier to select, review, and interpret before any later migration step is considered.

Current baseline assumptions:

- The default provider remains `legacy_musicnn`.
- The `llm` path is evaluated only through offline artifacts.
- No rollout, canary, shadow execution, or provider selection change is part of this stage.
- The external `/classify` contract remains unchanged.

## Achieved Result

Roadmap 2.10 adds a curated evaluation layer on top of the Roadmap 2.9 offline baseline.

The stage adds:

- a documented curated corpus and quality-gate framework
- versioned Roadmap 2.10 subset manifests
- manifest validation and subset-invariant tests
- subset-aware offline run selection
- review-friendly report metadata
- category-level summaries
- warning rollups
- review queue generation
- conservative readiness buckets
- decision summary output

These changes make evaluation artifacts more useful for engineering review.
They do not change production behavior.

## Evaluation Artifacts

Roadmap 2.10 defines three versioned offline manifest inputs:

- `evaluation/manifests/roadmap_2_10/curated_v1.json`
- `evaluation/manifests/roadmap_2_10/golden_v1.json`
- `evaluation/manifests/roadmap_2_10/repeat_run_v1.json`

The manifests are offline metadata only.
They define reviewable sample membership and per-sample context for curated evaluation runs.
They are not runtime data sources and do not affect provider selection.

Roadmap 2.10 runs can produce review artifacts that include:

- manifest metadata
- run summary
- warning summary
- per-sample comparison results
- category summary
- warning rollups
- review queue
- readiness bucket
- decision summary

The artifact shape is intended to be deterministic and diff-friendly.

## Review Capabilities

Roadmap 2.10 artifacts support explicit review of:

- curated, golden, and repeat-run subset behavior
- missing sample inputs
- warning case counts at run level
- warning case counts by category
- warning sample ids and warning details
- samples requiring manual review
- conservative readiness interpretation

The review queue is intentionally simple.
It includes samples with warnings and missing sample ids.
It does not attempt to rank samples or replace reviewer judgment.

## Readiness Semantics

The readiness output is an offline evaluation-governance signal.

Readiness buckets are:

- `ready`
- `limited-ready`
- `not-ready`

`ready` means the artifact is clean enough for the next safe offline evaluation or migration-preparation step.
It does not mean cutover approval.
It does not approve a production rollout.
It does not change the default provider.

`limited-ready` means the artifact is complete enough to interpret, but warnings or review queue items still need follow-up before broader migration planning.

`not-ready` means blocking findings must be resolved before the next roadmap step.

`limited-ready` and `not-ready` are evaluation-governance signals only.
They are not runtime control flow and are not rollout gates in production code.

## Non-Goals

Roadmap 2.10 does not include:

- provider cutover
- default provider changes
- legacy path removal
- runtime shadow execution
- rollout or canary mechanics
- provider selection changes
- response schema changes
- `/classify` API changes
- runtime request handling changes
- compatibility semantics changes
- taxonomy redesign
- production SLO changes

## Migration-Safe Boundary

Roadmap 2.10 preserves the migration-safe boundary established by Roadmap 2.9.

The stage is limited to offline evaluation metadata, offline execution usability, report aggregation, and interpretation of offline artifacts.

It does not require:

- changing the default provider
- changing runtime provider selection
- modifying the external contract
- introducing rollout state
- introducing shadow or canary behavior
- removing the legacy path

## Safe Next Step

After Roadmap 2.10, the safe next step is to use the curated evaluation artifacts to review concrete findings and decide whether additional offline corpus refinement or targeted compatibility fixes are needed.

Only after those review findings are understood should later roadmap work consider a separate shadow-oriented or rollout-oriented stage.

Any such later stage must remain separate from Roadmap 2.10 and must preserve the explicit distinction between offline evaluation readiness and production cutover approval.

## Relation To Prior Evaluation Work

This document closes the Roadmap 2.10 evaluation stage that builds on [docs/roadmap_2_9_evaluation_baseline.md](./roadmap_2_9_evaluation_baseline.md) and [docs/roadmap_2_10_curated_evaluation_quality_gates.md](./roadmap_2_10_curated_evaluation_quality_gates.md).

Roadmap 2.9 established executable offline comparison infrastructure.
Roadmap 2.10 makes that infrastructure curated, review-friendly, and conservatively interpretable before any runtime migration step is considered.
