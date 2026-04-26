# Roadmap 2.10 Curated Evaluation Quality Gates

## Stage Goal

This stage defines the documentation-level framework for curated evaluation runs and quality gates after the Roadmap 2.9 offline evaluation baseline.

The goal is to make evaluation results reviewable and comparable before any later shadow, canary, or cutover work is considered.

Current baseline assumptions:

- The default provider remains `legacy_musicnn`.
- The `llm` path is evaluated only through offline artifacts.
- No rollout, canary, shadow execution, or provider selection change is part of this stage.
- The external `/classify` contract remains unchanged.

## Scope

This stage covers only curated evaluation corpus expectations, artifact review shape, and quality gate framing.

Included:

- subset definitions for curated, golden, and repeat-run evaluation
- recommended sample categories
- sample selection principles
- review-friendly artifact expectations
- quality gate groups and readiness buckets
- migration-safe boundaries for follow-up work

## Non-Goals

This stage does not include:

- provider cutover
- default provider changes
- runtime shadow execution
- rollout or canary mechanics
- provider selection changes
- response schema changes
- `/classify` API changes
- compatibility semantics changes
- taxonomy redesign
- new dependencies
- test-suite changes

## Evaluation Subsets

### Curated Subset

The curated subset is the broad evaluation corpus used to compare behavior across representative inputs.

It should:

- cover the main expected classification shapes
- include easy, medium, ambiguous, and weak-signal examples
- include known compatibility and aliasing stress cases
- include enough diversity to make aggregate findings meaningful
- remain small enough for review-friendly artifacts

The curated subset is the primary breadth corpus. It is not required to be strict enough for every case to have a single undisputed expected answer.

### Golden Subset

The golden subset is a smaller, high-confidence slice inside the curated subset.

It should:

- contain stable examples with well-understood expected semantics
- support stricter regression review
- avoid cases where human interpretation is intentionally broad
- make contract, compatibility, and dominant-tag regressions easy to identify

The golden subset is the stricter regression reference. It is not the full diversity corpus.

### Repeat-Run Subset

The repeat-run subset is a smaller slice used to evaluate stability across repeated offline executions of the same inputs.

It should:

- be drawn from the curated subset
- include straightforward and ambiguous examples
- include cases where weak output, close ranking, or partial output is plausible
- be stable enough to distinguish acceptable variation from noisy behavior

The repeat-run subset exists to make later comparison work interpretable. It does not require exact byte-for-byte equality across every weak-output case.

## Recommended Sample Categories

The curated corpus should include a deliberate mix of categories:

- clear single-genre examples
- clear multi-genre examples
- genre-boundary examples
- alias-heavy examples
- sparse or low-confidence examples
- noisy or partial-signal examples
- examples with historically unstable rankings
- examples where important tags should not disappear
- examples likely to produce empty or weak outputs
- examples that exercise `genres` and `genres_pretty` compatibility semantics

Each category should have an explicit reason for inclusion. A sample may satisfy more than one category.

## Selection Principles

Evaluation samples should be selected deliberately, not randomly.

Selection should:

- represent known product and provider risk areas
- include both common and edge-case classification shapes
- avoid over-weighting one genre family, source type, or confidence profile
- preserve enough ambiguous cases to expose behavior differences
- preserve enough stable cases to identify clear regressions
- document why each sample belongs in the subset
- keep subset membership stable unless a change is reviewed explicitly

Selection should not:

- use only convenient or recently observed inputs
- optimize for provider agreement
- optimize for a favorable readiness decision
- rely on a random sample without later curation
- mix unrelated rollout or cutover criteria into corpus membership

## Review-Friendly Artifact Model

Each curated evaluation run should produce artifacts that can be reviewed without rerunning the evaluation immediately.

Expected artifacts include:

- provider identifiers and code revision
- evaluated subset name
- source manifest path or identifier
- evaluated sample count and sample ids
- missing sample ids, if any
- per-sample comparison results
- contract-validity summary
- empty and weak-output summary
- overlap summary
- ranking-drift summary
- warning summary
- readiness bucket with rationale
- unresolved findings, if any

Artifacts should be deterministic in shape, stable for diff-based review, and explicit about missing inputs or skipped samples.

## Quality Gate Groups

### Contract Validity

The evaluated output must remain valid with respect to the existing `/classify` contract and downstream expectations.

The gate should check:

- response shape remains unchanged
- required fields remain present when currently expected
- field types remain unchanged
- provider-specific details do not leak into the public response
- invalid values do not bypass existing validation boundaries
- `genres` and `genres_pretty` compatibility semantics remain intact

Any public contract violation is blocking.

### Empty And Weak Outputs

Empty, weak, or partial outputs must be visible in the artifact and interpreted against existing invariants.

The gate should check:

- empty outputs are counted
- single-tag and partial outputs are counted
- weak values dropped by post-processing are explainable
- safe abstention is distinguishable from silent degradation
- golden-subset empty output is reviewed as a potential blocker unless expected

Weak output is acceptable only when contract and compatibility semantics remain intact and the behavior is understood.

### Overlap Expectations

Overlap should be used to explain agreement and divergence between the evaluated path and the baseline path.

The gate should check:

- shared canonical tags are captured
- missing important tags are visible
- benign substitutions are documented
- no-shared-tag cases are reviewed
- golden-subset divergence has explicit rationale

Overlap is not an exact-match requirement for the full curated subset.

### Ranking Drift Tolerance

Ranking drift should focus on semantic impact, especially at the top of the result.

The gate should check:

- dominant-tag displacement is reviewed
- top-rank churn is visible
- lower-rank permutation is separated from material drift
- shared-tag ranking changes are summarized
- historically unstable examples are not used as sole blockers without context

Minor lower-rank drift may be acceptable when the public contract and important semantics remain intact.

### Warnings

Warnings should make review risk explicit without automatically implying failure.

The gate should track:

- empty evaluated output
- weak or partial evaluated output
- no shared tags with the baseline
- material ranking drift
- malformed or unusable provider-shaped output
- missing sample inputs
- unresolved interpretation differences

Warning counts should be paired with sample ids so reviewers can inspect concrete cases.

## Readiness Buckets

### Ready

Use `ready` when:

- contract validity is clean
- golden-subset differences are understood and non-blocking
- empty or weak outputs are acceptable under documented invariants
- overlap and ranking drift do not show material unexplained regressions
- warnings are bounded and reviewable
- artifacts are complete enough for follow-up review

`ready` means ready for a later safe migration step, not approved for cutover.

### Limited-Ready

Use `limited-ready` when:

- contract validity is clean
- remaining concerns are bounded to documented sample categories
- warnings require follow-up but do not block continued offline or shadow-preparation work
- artifacts are complete enough to explain the limitations

`limited-ready` means more evaluation or targeted fixes are needed before broader rollout planning.

### Not-Ready

Use `not-ready` when:

- any public contract violation is present
- response shape or compatibility semantics regress
- golden-subset failures are unexplained
- empty or weak outputs indicate silent degradation
- overlap or ranking drift would make later review misleading
- warnings are too frequent or too vague to interpret
- artifacts are incomplete or unstable

`not-ready` blocks later shadow, canary, or cutover-oriented work until the findings are resolved.

## Migration-Safe Boundary

The following boundaries are mandatory for Roadmap 2.10:

- no cutover
- no default provider change
- no runtime rollout
- no shadow or canary execution
- no runtime request handling changes
- no external API changes
- no response schema changes
- no compatibility semantics changes

Follow-up work may add or refine offline documentation and review artifacts only when those changes preserve the same boundary.

## Relation To Existing Evaluation Baseline

This document extends [docs/roadmap_2_9_evaluation_baseline.md](./roadmap_2_9_evaluation_baseline.md) and complements [docs/llm_invariants.md](./llm_invariants.md).

Roadmap 2.9 defines the offline evaluation baseline and initial artifact expectations.
Roadmap 2.10 defines how curated runs should be selected, reviewed, and bucketed before any later runtime migration step is considered.
