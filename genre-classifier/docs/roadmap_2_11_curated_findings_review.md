# Roadmap 2.11 Curated Findings Review

## Stage Goal

Roadmap 2.11 reviews the curated evaluation findings produced by Roadmap 2.10 and turns well-supported findings into narrow, migration-safe compatibility fix candidates.

The goal is to identify recurring LLM mismatch patterns, separate acceptable drift from risky incompatibility, and prepare targeted fixes without changing production routing or the public contract.

Current baseline assumptions:

- The default provider remains `legacy_musicnn`.
- The legacy path remains available and unchanged by this stage.
- The `llm` path is reviewed through offline evaluation artifacts.
- No cutover, rollout, runtime shadow execution, canary, or provider selection change is part of this stage.
- The external `/classify` contract remains unchanged.
- No runtime code change is included in this documentation commit.

## Scope And Boundaries

This stage covers only curated findings review and preparation of narrow compatibility fixes.

Included:

- review findings from Roadmap 2.10 curated evaluation artifacts
- identify recurring LLM mismatch patterns
- prepare narrow migration-safe compatibility fixes
- document evidence, risk, tests, and rollback expectations for each candidate fix
- preserve review-friendly evaluation outputs for later decision making

Excluded:

- runtime code changes in this documentation commit
- provider cutover
- rollout or canary mechanics
- runtime shadow execution
- default provider changes
- external API changes
- `/classify` response-shape changes
- broad taxonomy redesign
- subjective tuning without evidence

Boundaries:

- the default provider remains `legacy_musicnn`
- the legacy path remains available
- the external `/classify` contract remains unchanged
- no cutover is included
- no rollout is included
- no runtime shadow or canary behavior is included
- no runtime code change is included in this documentation commit

## Review Inputs

Roadmap 2.11 review should start from existing Roadmap 2.10 offline artifacts, especially:

- curated artifacts
- golden artifacts
- repeat-run artifacts
- category summaries
- warning rollups
- review queue
- readiness buckets
- Roadmap 2.10 decision artifact

The review should prefer artifact-backed findings over isolated impressions. Missing or incomplete artifacts should be called out directly rather than inferred around.

## Findings Taxonomy

Findings should be grouped into a small set of review categories:

- recurring mismatch patterns: repeated differences with a shared cause or shape
- category-level problem zones: concentrated issues within a subset category or genre area
- accepted drift: explainable differences that do not break compatibility semantics
- risky incompatibility: differences that may break contract expectations, compatibility mappings, or important downstream interpretation
- deferred findings: plausible issues that need more evidence before a fix is safe
- no-fix findings: subjective disagreements or harmless differences that should not drive code changes

The taxonomy is intended to keep review decisions explicit. It should not be used to force the LLM path to imitate legacy output byte-for-byte.

## Allowed Future Fix Classes

Only narrow, migration-safe fix classes are in scope:

- alias and normalization fixes
- controlled vocabulary adjustments
- threshold and ranking tweaks
- weak-output handling refinements
- compatibility mapping corrections
- prompt discipline corrections

Each fix should be tied to a documented finding. Broad retuning, provider replacement, production routing changes, or compatibility-breaking output changes are out of scope.

## Fix Candidate Gating Rules

A fix candidate is eligible only when it satisfies the review gate:

- use evidence-backed findings only
- fix only recurring or clearly risky findings
- do not fix subjective taste or musical disagreement
- do not force the LLM path to imitate legacy output byte-for-byte
- require evidence for the finding
- assign a risk level before implementation
- define a focused test plan before or alongside implementation
- include a rollback note for each fix

Golden-subset incompatibilities should be treated as higher-risk than broad curated-subset drift, but even golden findings still need a precise fix rationale.

## Decision Trail Template

Each proposed fix should keep a short decision trail:

```text
Fix ID:
Finding:
Evidence:
Risk:
Change:
Why now:
Why safe:
Tests:
Rollback:
```

The decision trail should be small enough to review in a pull request and specific enough to explain why the change is migration-safe.

## Fix Candidates Manifest

Roadmap 2.11 fix candidates should be tracked in `evaluation/manifests/roadmap_2_11/fix_candidates_v1.json`.

The manifest should stay evidence-backed and may keep `candidates` empty when the reviewed Roadmap 2.10 artifacts do not contain concrete findings suitable for a migration-safe fix candidate.

Roadmap 2.11 curated review artifacts can be written with the existing offline evaluation entrypoint:

```text
python -m app.evaluation.run_roadmap_2_9 --roadmap-stage 2.10 --subset curated_v1 --input-bundle <comparison-input.json> --output-kind roadmap_2_11_curated_review --output evaluation/artifacts/roadmap_2_11/curated_review_v1.json
```

The artifact records review evidence only. It does not generate fix candidates automatically; reviewers should use it as evidence when later updating `fix_candidates_v1.json`.

## Invariants

Roadmap 2.11 must preserve these invariants:

- provider default remains `legacy_musicnn`
- legacy path is preserved
- response shape remains unchanged
- compatibility semantics are preserved and backward-compatible
- controlled vocabulary discipline is preserved
- evaluation honesty is preserved through review-friendly artifacts and explicit unresolved findings

Any proposed change that weakens these invariants belongs in a later, separately reviewed roadmap stage.

## Suggested Next Steps

After this document is in place:

- create a fix candidates manifest if it would make review easier
- implement alias and normalization fixes first
- implement weak-output handling only after documented evidence
- rerun focused tests and offline curated evaluation after code changes
- write the Roadmap 2.11 decision artifact at the end of the stage

Roadmap 2.11 should end with a clear decision artifact summarizing which findings were fixed, deferred, accepted as drift, or closed as no-fix.
