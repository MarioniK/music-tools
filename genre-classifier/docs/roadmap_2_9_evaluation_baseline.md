# Roadmap 2.9 Evaluation Baseline

## Stage Goal

This stage defines the documentation baseline for comparative evaluation between the current default provider and the existing `llm` path before any cutover decision.

The goal is to produce a repeatable evaluation package that answers two questions:

1. Is the `llm` path contract-compatible with the current production-facing semantics?
2. Is the `llm` path stable enough to be considered shadow-ready for later safe slices?

Current baseline assumptions:

- The default provider remains `legacy_musicnn`.
- The `llm` path already exists but is not the default path.
- No rollout, canary, shadow execution, or provider selection change is part of this stage.
- The external `/classify` contract remains unchanged.

## Scope

This stage covers only evaluation design and evaluation output expectations.

Included:

- comparison dimensions and acceptance framing
- sample-set definitions
- repeat-run stability expectations
- shadow-readiness gates
- required artifacts from an evaluation run
- rollback-safe boundaries for follow-up work

## Non-Goals

This stage does not include:

- provider cutover
- runtime shadow execution
- rollout or canary mechanics
- provider selection changes
- response schema changes
- `/classify` API changes
- compatibility semantics changes
- taxonomy redesign
- new dependencies
- test-suite changes

## Evaluation Inputs

### Curated Sample Set

The curated sample set is the main comparison corpus for Roadmap 2.9.

It should:

- cover easy, medium, and ambiguous classification cases
- include genre-dense and genre-sparse examples
- include examples known to stress aliasing, overlap, and boundary genres
- include examples likely to trigger weak or partial outputs
- include examples with historically noisy rankings

The curated sample set is intended to show comparative behavior breadth, not only pass/fail correctness.

### Golden Subset

The golden subset is a smaller, high-confidence subset inside the curated sample set.

It should:

- contain examples with stable expected semantics
- be appropriate for strict contract and compatibility checks
- avoid items where human interpretation is intentionally broad or disputed

The golden subset is the reference slice for identifying clear regressions. It is not the full diversity corpus.

### Repeat-Run Subset

The repeat-run subset is a smaller subset used to measure output stability across repeated executions of the same input.

It should:

- be drawn from the curated sample set
- include straightforward cases and ambiguous cases
- include inputs where ranking ties or weak outputs are plausible

The repeat-run subset exists to detect non-deterministic or unstable behavior that would make later shadow analysis unreliable.

## Comparison Dimensions

### Contract Validity

The evaluated provider output must remain valid with respect to the existing `/classify` contract and downstream expectations.

Checks include:

- response shape is unchanged
- required fields are present when currently expected
- field types remain unchanged
- no provider-specific leakage appears in the public contract
- invalid values do not bypass existing validation boundaries

### Output Stability

Repeated executions on the repeat-run subset should not show material instability in output presence, ordering, or compatibility mapping results.

This dimension is about reproducibility, not exact equality under every weak-output case.

### Tag Overlap

Compare how much of the `llm` output overlaps with the baseline `legacy_musicnn` output on the curated sample set.

The purpose is to quantify agreement and divergence, not to force identical outputs.

### Ranking Drift

Compare ordering changes for shared tags and top positions.

Drift matters most when:

- top-ranked tags change meaningfully
- a previously dominant tag disappears
- low-confidence tags move into dominant positions

Minor lower-rank permutation without semantic impact is less important than top-rank displacement.

### Compatibility With `genres` / `genres_pretty` Semantics

The `llm` path must remain compatible with existing downstream semantics for `genres` and `genres_pretty`.

Checks include:

- existing compatibility mapping behavior is preserved
- canonical tag handling does not break current semantics
- pretty-format output remains derived in a compatible way
- semantically equivalent upstream output does not produce incompatible downstream presentation

### Weak Or Partial Output Behavior

Weak, partial, or empty outputs are acceptable only when they remain compatible with current invariants.

Evaluation must explicitly track:

- empty outputs
- single-tag outputs
- partial outputs where only strong tags survive
- invalid or weak items being dropped before downstream exposure

This dimension is especially important for distinguishing safe abstention from silent degradation.

### Latency And Failure Profile

The evaluation must record latency and failure shape for both providers across the curated sample set.

At minimum, capture:

- success rate
- failure rate
- timeout behavior if applicable
- latency distribution summary
- examples of malformed or unusable provider output

This stage does not define production SLO changes. It only establishes the comparison baseline needed before shadow-style work.

## Acceptable Vs Alarming Differences

### Acceptable Differences

The following are acceptable during evaluation if contract and compatibility semantics remain intact:

- lower-rank ordering differences with no material semantic impact
- narrower outputs where weak tags are dropped
- partial outputs that preserve strong tags and remain contract-valid
- benign tag substitutions that map to equivalent downstream semantics
- small latency differences without elevated failure behavior

### Alarming Differences

The following must be treated as blocking until understood:

- any public contract violation
- any change in response shape
- any break in `genres` or `genres_pretty` compatibility semantics
- frequent instability on repeat runs
- dominant-tag churn on otherwise stable inputs
- systematic loss of important tags on the golden subset
- increased malformed output rate
- materially worse failure or timeout profile
- divergence patterns that would make later shadow interpretation noisy or misleading

## Shadow-Readiness Gates

The `llm` path is shadow-ready only if all gates below are satisfied by the evaluation package:

1. Contract validity is clean across the curated sample set.
2. No response shape or compatibility semantic regression is observed.
3. Golden subset differences are understood and non-blocking.
4. Repeat-run stability is strong enough that major output churn is not observed.
5. Weak or partial outputs are explainable and remain within documented invariants.
6. Failure behavior is observable, bounded, and not materially worse in a way that would invalidate shadow comparison.
7. Evaluation artifacts are complete enough to support later review without rerunning the analysis immediately.

Shadow-ready in this stage means ready for later shadow-oriented safe slices, not approved for cutover.

## Required Artifacts After Evaluation Run

Each evaluation run should produce a reviewable artifact set containing:

- provider identifiers and code revision
- sample-set manifest
- golden subset manifest
- repeat-run subset manifest
- per-sample comparison results
- contract-validity summary
- overlap and ranking-drift summary
- weak/partial-output summary
- latency and failure summary
- explicit list of acceptable differences
- explicit list of alarming differences or unresolved findings
- final shadow-readiness decision with rationale

Artifacts should be stable enough for diff-based review across later safe commits.

## Rollback-Friendly Scope

Follow-up work derived from this document must stay rollback-friendly.

That means safe slices may add:

- offline evaluation tooling
- reporting artifacts
- internal comparison helpers that do not alter runtime behavior
- documentation updates

Safe slices must not require:

- changing the default provider
- changing runtime provider selection
- modifying external contract behavior
- introducing irreversible data or rollout state

## Invariants That Must Not Be Broken

The following invariants are mandatory for all Roadmap 2.9 follow-up work:

- `legacy_musicnn` remains the default provider.
- The `llm` path is not cut over by this stage.
- The external `/classify` contract does not change.
- Response shape does not change.
- Compatibility semantics do not change.
- No rollout, canary, or shadow execution logic is introduced in this documentation slice.
- No runtime behavior changes are introduced.
- No new dependencies are introduced.
- No tests are modified as part of this documentation slice.

## Relation To Existing Invariants

This document complements [docs/llm_invariants.md](./llm_invariants.md).

`docs/llm_invariants.md` defines the current LLM-path constraints.
This document defines how Roadmap 2.9 should evaluate those constraints against the current default provider before any later migration step is considered.
