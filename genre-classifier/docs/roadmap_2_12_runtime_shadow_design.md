# Roadmap 2.12 Runtime Shadow Design

## Stage Goal

Roadmap 2.12 prepares migration-safe runtime shadow and limited canary readiness for `genre-classifier`.

The goal is to compare the current production baseline, `legacy_musicnn`, against the LLM path without changing production behavior.

Roadmap 2.12 must not:

- perform cutover
- change the external `/classify` API
- change the `/classify` response shape
- change the default provider
- return LLM output as the production response

`Qwen2.5-7B-Instruct` is the primary LLM shadow candidate for this stage. It is not treated as a direct replacement for the audio model. It is treated as a candidate structured decision, normalization, and controlled vocabulary layer. The existing `legacy_musicnn` path remains the production audio evidence source.

## Required Invariants

Roadmap 2.12 must preserve these invariants:

- production response is always calculated from `legacy_musicnn`
- LLM shadow result never replaces or mutates the production response
- shadow failures do not fail `/classify`
- shadow timeouts do not fail `/classify`
- invalid LLM output does not fail `/classify`
- comparison failures do not fail `/classify`
- artifact write failures do not fail `/classify`
- compatibility semantics remain unchanged
- legacy path remains intact
- `tidal-parser` is not changed

The external behavior of `/classify` must remain production-compatible with the current `legacy_musicnn` baseline.

## Runtime Shadow Execution Design

Runtime shadow execution should be ordered so that production behavior is isolated from shadow behavior:

1. Execute the legacy path.
2. Build the production-compatible response from the legacy result.
3. Decide whether the optional shadow branch is enabled and selected.
4. If selected, execute the LLM shadow branch under a strict timeout.
5. Validate the LLM shadow result using existing compatibility expectations.
6. Compare LLM evidence against the legacy result.
7. Emit structured logs and optionally append JSONL evidence artifacts.
8. Return the already-built legacy production response.

The shadow branch is an observer. It must not be part of production response construction.

## Design Options

### In-Process Shadow After Legacy Response Calculation

Description: run shadow logic in the request process only after the legacy response has been calculated.

Pros:

- simple execution model
- direct access to legacy result and request context
- easiest first implementation for comparison helpers and structured evidence
- does not require a separate worker or queue

Risks:

- can add request latency if not bounded tightly
- requires careful timeout and exception isolation
- artifact writes must be best-effort only

Migration-safety:

- safe when disabled by default
- safe when the legacy response is calculated before shadow work
- safe when all shadow outcomes are non-fatal evidence

Fit for first safe slice:

- recommended as the first safe slice because it is narrow, observable, rollback-friendly, and does not change routing.

### Config-Gated Dual-Run Inside `genre-classifier`

Description: execute both legacy and LLM paths inside `genre-classifier` when explicit config enables the dual-run observer.

Pros:

- keeps comparison logic close to provider abstractions
- supports percentage-gated shadow selection
- enables consistent structured logs and counters

Risks:

- accidental config enablement could increase load
- dual-run naming can be confused with canary serving unless documented clearly
- provider errors must stay isolated from `/classify`

Migration-safety:

- safe only when the dual run is shadow-only
- safe only when production response source remains `legacy_musicnn`
- safe only when disabled by default

Fit for first safe slice:

- suitable when implemented as a disabled-by-default shadow observer, not as provider routing.

### Asynchronous Or Offline Follow-Up Capture

Description: capture enough metadata for later offline LLM evaluation rather than running the LLM path in the request path.

Pros:

- avoids LLM latency in `/classify`
- avoids runtime provider availability risk
- useful for larger evaluation batches

Risks:

- may miss request-time context or runtime provider behavior
- requires capture storage, retention, and privacy review
- does not directly test runtime timeout or failure isolation

Migration-safety:

- very safe for production response behavior
- less complete as a runtime shadow-readiness exercise

Fit for first safe slice:

- useful as a supporting path, but not enough by itself for Roadmap 2.12 runtime shadow readiness.

### Limited Canary By Explicit Config Or Percentage Gate

Description: use config or percentage sampling to select a subset of requests for shadow execution.

Pros:

- controls LLM load
- allows gradual evidence collection
- supports operational abort via config

Risks:

- the term canary can be misread as serving LLM responses
- sampling bugs could over-select traffic
- percentage gates need clear metrics for selected and skipped requests

Migration-safety:

- safe only if the gate selects shadow execution, not production response source
- unsafe if any selected request returns LLM output

Fit for first safe slice:

- suitable as percentage-gated shadow only. Actual canary serving is out of scope and prohibited in Roadmap 2.12.

## Recommended Design

Roadmap 2.12 should implement a disabled-by-default runtime shadow observer inside `genre-classifier`.

The recommended design has these properties:

- controlled by explicit config
- default disabled
- production response always generated from `legacy_musicnn`
- LLM branch runs only after production response calculation
- strict config-driven timeout for the shadow LLM path
- all shadow errors converted into evidence outcomes
- structured runtime logs for selection, outcome, duration, and comparison summary
- optional JSONL evidence artifact
- artifact writing is best-effort and non-fatal
- no production response impact

The main abort switch should be:

```text
GENRE_CLASSIFIER_SHADOW_ENABLED=false
```

## Canary-Readiness Clarification

Roadmap 2.12 allows only percentage-gated shadow execution.

Actual canary serving is prohibited:

- do not return LLM responses for any traffic percentage
- do not switch the production response source by sampling
- do not treat the LLM path as the default provider
- do not expose a different response shape

Any sample-rate or percentage gate must choose only whether to run shadow observation.

## Timeout Policy

The shadow LLM path must have a separate timeout from the production legacy path.

Timeout policy:

- timeout is strict
- timeout is config-driven
- timeout outcome is recorded as evidence
- timeout does not change the production response
- timeout does not fail `/classify`
- timeout increments shadow timeout counters

The production response must already be available before shadow timeout handling can affect control flow.

## Failure Isolation

Shadow outcomes should use explicit outcome classes:

- `success`: shadow path completed, output validated, comparison completed
- `timeout`: shadow path exceeded the configured timeout
- `provider_error`: LLM provider returned or raised an execution error
- `invalid_output`: LLM output could not be parsed or did not match expected structure
- `validation_failed`: parsed LLM output failed schema or compatibility validation
- `comparison_error`: comparison logic failed after legacy and LLM results were available
- `artifact_write_failed`: evidence artifact write failed after an otherwise classified shadow outcome
- `skipped_by_config`: shadow observer disabled by configuration
- `skipped_by_sampling`: shadow observer enabled but request not selected by sampling

All outcomes are evidence. None of them change the production response.

## Logging And Artifacts

Expected structured events:

- `genre_classifier.shadow.skipped`
- `genre_classifier.shadow.selected`
- `genre_classifier.shadow.completed`
- `genre_classifier.shadow.failed`
- `genre_classifier.shadow.artifact_write_failed`

Minimal structured log fields:

- `event`
- `roadmap_stage`
- `shadow_enabled`
- `shadow_selected`
- `shadow_outcome`
- `provider`
- `default_provider`
- `primary_llm_shadow_candidate`
- `duration_ms`
- `timeout_ms`
- `top_tag_match`
- `partial_overlap`
- `shared_tag_count`
- `has_no_shared_tags`
- `artifact_written`

Runtime logs should not include raw prompts or large raw LLM payloads. If deeper debugging is needed, use explicitly configured evidence artifacts with careful retention and review.

Suggested JSONL evidence shape:

```json
{
  "schema_version": "1",
  "roadmap_stage": "2.12",
  "event": "genre_classifier.shadow.completed",
  "shadow_outcome": "success",
  "default_provider": "legacy_musicnn",
  "primary_llm_shadow_candidate": "qwen2.5-7b-instruct",
  "duration_ms": 0,
  "timeout_ms": 0,
  "comparison": {
    "top_tag_match": false,
    "partial_overlap": false,
    "shared_tag_count": 0,
    "has_no_shared_tags": true,
    "legacy_only_tags": [],
    "llm_only_tags": []
  }
}
```

Artifact writing must be best-effort and non-fatal. A write failure should be recorded as `artifact_write_failed` and counted without changing the production response.

## Metrics, Counters, And Decision Signals

Roadmap 2.12 should prepare these counters:

- `shadow_selected_total`
- `shadow_skipped_config_total`
- `shadow_skipped_sampling_total`
- `shadow_success_total`
- `shadow_timeout_total`
- `shadow_failure_total`
- `shadow_invalid_output_total`
- `shadow_validation_failed_total`
- `shadow_no_shared_tags_total`
- `shadow_top_tag_match_total`
- `shadow_partial_overlap_total`
- `shadow_artifact_write_failed_total`

Useful future cutover decision signals:

- success rate
- timeout rate
- invalid output rate
- no-shared-tags rate
- top-tag match rate
- partial overlap rate
- duration and latency distribution

These signals are evidence for later stages. They do not authorize cutover in Roadmap 2.12.

## Abort And Rollback Conditions

Operational abort conditions:

- shadow timeout rate exceeds the accepted operating threshold
- LLM provider errors spike
- artifact writes create storage pressure
- request latency regresses even with shadow timeout isolation
- structured logs or artifacts are too noisy for safe operations

Config rollback conditions:

- disable shadow with `GENRE_CLASSIFIER_SHADOW_ENABLED=false`
- set sample percentage to zero
- disable evidence artifact writing
- reduce timeout to the minimum safe value if shadow work is still needed for diagnostics

Code rollback conditions:

- shadow observer changes unexpectedly affect production response
- response shape changes
- default provider changes
- legacy path is altered or bypassed
- comparison or validation code introduces runtime instability

The primary rollback path must be config disablement. Code rollback is reserved for invariant violations or unsafe implementation behavior.

## Roadmap 2.11 Deferred Candidates

Roadmap 2.12 should account for the Roadmap 2.11 deferred candidates, but must not fix them without a separate stage:

- `weak-top-partial-output-threshold-review`
- `no-shared-tags-genre-boundary-review`

Runtime shadow evidence should collect diagnostic signals for these candidates:

- `top_tag_match`
- `top_tag_mismatch`
- `partial_overlap`
- `weak_overlap`
- `shared_tag_count`
- `has_no_shared_tags`
- `legacy_only_tags`
- `llm_only_tags`

Roadmap 2.12 must not:

- change thresholds
- change compatibility mapping
- expand genre ontology
- change controlled vocabulary
- change production decision logic

## Safe Implementation Plan

Future Roadmap 2.12 commits should be small and rollback-friendly:

1. `docs/design`: add this runtime shadow design and documentation-level manifest.
2. `settings baseline`: add disabled-by-default config fields with explicit defaults.
3. `comparison helpers`: add pure comparison helpers and focused tests.
4. `isolated shadow observer`: add observer orchestration after legacy response calculation.
5. `artifact/logging baseline`: add structured logs, counters, and optional best-effort JSONL evidence.
6. `decision artifact`: summarize observed evidence and readiness decision without cutover.

Each implementation commit should preserve the public `/classify` contract and response shape.

## Explicit Out Of Scope

Roadmap 2.12 explicitly excludes:

- cutover
- actual rollout
- production response from LLM
- default provider change
- `legacy_musicnn` removal
- `tidal-parser` changes
- audio-backbone replacement
- AST implementation
- PANNs or CNN14 implementation
- Whisper encoder implementation
- newer Essentia model implementation

Audio-backbone refresh is a separate future topic and is not part of Roadmap 2.12.
