# Roadmap 2.12 Decision Artifact — Runtime Shadow / Canary Readiness

## Summary

Roadmap 2.12 prepared a migration-safe baseline for runtime shadow and limited canary readiness in `genre-classifier`.

The stage added documentation, disabled-by-default configuration, diagnostic comparison helpers, an isolated observer, evidence artifact helpers, and safe structured logging payload helpers.

Roadmap 2.12 did not perform cutover, actual canary serving, runtime shadow wiring into `/classify`, LLM provider execution, or production behavior changes.

Production behavior remains unchanged.

## Implemented Artifacts

Roadmap 2.12 added or updated:

- `docs/roadmap_2_12_runtime_shadow_design.md`
- `evaluation/manifests/roadmap_2_12/runtime_shadow_manifest_v1.json`
- `app/core/settings.py`
- `app/services/shadow_compare.py`
- `app/services/runtime_shadow.py`
- `app/services/shadow_artifacts.py`
- `app/services/shadow_logging.py`
- `tests/test_settings.py`
- `tests/test_shadow_compare.py`
- `tests/test_runtime_shadow.py`
- `tests/test_shadow_artifacts.py`
- `tests/test_shadow_logging.py`

## Commit Trail

Roadmap 2.12 was built through small rollback-friendly commits:

- `3a4affe` — docs/roadmap: add roadmap 2.12 runtime shadow design
- `54bcf9e` — feat/shadow: add runtime shadow settings baseline
- `6c1e3a2` — feat/shadow: add provider comparison helpers
- `a32722c` — feat/shadow: add isolated runtime shadow observer
- `31cbc2f` — feat/shadow: add runtime shadow evidence artifact helpers
- `509ee44` — feat/shadow: add runtime shadow logging helpers

## Preserved Invariants

Roadmap 2.12 preserved these invariants:

- default provider remains `legacy_musicnn`
- production response remains legacy-only
- external `/classify` contract unchanged
- response shape unchanged
- compatibility semantics unchanged
- no cutover
- no actual canary serving
- no runtime shadow wiring into `/classify`
- no real LLM provider call
- no HTTP call to LLM runtime
- no `legacy_musicnn` removal or bypass
- no `tidal-parser` changes
- no thresholds changed
- no controlled vocabulary changed
- no production decision logic changed

## What Was Added

### A. Runtime Shadow Design

Roadmap 2.12 added the runtime shadow design document and documentation-level manifest stub:

- `docs/roadmap_2_12_runtime_shadow_design.md`
- `evaluation/manifests/roadmap_2_12/runtime_shadow_manifest_v1.json`

The design records `Qwen2.5-7B-Instruct` as the primary LLM shadow candidate.

Qwen is treated as a candidate structured decision, normalization, and controlled vocabulary layer. It is not treated as a direct replacement for the audio backend.

The current `legacy_musicnn` / Essentia / MusiCNN path remains the production baseline and production audio evidence source.

### B. Settings Baseline

Roadmap 2.12 added disabled-by-default runtime shadow settings:

- `shadow_enabled`
- `shadow_provider`
- `shadow_sample_rate`
- `shadow_timeout_seconds`
- `shadow_artifacts_enabled`
- `shadow_artifacts_dir`
- `shadow_max_concurrent`

The defaults are safe:

- shadow execution disabled
- sample rate `0.0`
- artifact writing disabled
- default provider unchanged
- strict validation for sample rate, timeout, and concurrency values

These settings do not connect shadow execution to runtime behavior.

### C. Comparison Helpers

Roadmap 2.12 added pure provider comparison helpers for future shadow evidence:

- `shared_tags`
- `legacy_only_tags`
- `llm_only_tags`
- `top_tag_match`
- `top_tag_mismatch`
- `has_no_shared_tags`
- `has_partial_overlap`
- `weak_overlap`
- `comparison_signal`

Comparison helpers normalize tags for diagnostic comparison only. They do not change thresholds, compatibility mapping, controlled vocabulary, or production decisions.

### D. Runtime Shadow Observer

Roadmap 2.12 added an isolated runtime shadow observer module.

The observer is:

- isolated
- dependency-injected through `shadow_runner`
- timeout-isolated
- provider-error-isolated
- invalid-output-isolated
- comparison-error-isolated
- structured around diagnostic outcomes
- not connected to runtime

The observer does not mutate production response objects and does not own production response construction.

### E. Evidence Artifact Helpers

Roadmap 2.12 added evidence artifact helpers for future runtime shadow capture:

- `runtime_shadow_v1` payload schema
- JSON-serializable evidence payload shape
- best-effort JSONL append writer

The evidence payload excludes:

- raw audio
- raw prompt
- full raw LLM response

The writer is not connected to runtime behavior. It writes only when explicitly called by tests or future integration code.

### F. Logging Helpers

Roadmap 2.12 added safe structured logging payload helpers:

- event name constants
- log-safe payload builder
- outcome-to-event classifier

No logger is created and no runtime logs are written by this stage.

Default log payloads exclude:

- tag lists
- raw prompt
- raw audio
- raw LLM response
- source URL

Tags remain appropriate for evidence artifacts, not default runtime logs.

## Roadmap 2.11 Deferred Candidates Handling

Roadmap 2.12 did not fix Roadmap 2.11 deferred candidates.

It added diagnostic signals that can support future analysis.

For `weak-top-partial-output-threshold-review`, Roadmap 2.12 can now represent:

- `weak_overlap`
- `top_tag_match`
- `top_tag_mismatch`
- `partial_overlap`

For `no-shared-tags-genre-boundary-review`, Roadmap 2.12 can now represent:

- `has_no_shared_tags`
- `shared_tag_count`
- `legacy_only_tags`
- `llm_only_tags`

Roadmap 2.12 did not:

- change thresholds
- expand genre ontology
- change compatibility mapping
- change production decision logic

## Verification

Final full test suite:

```text
PYTHONPATH=. pytest tests
```

Result:

```text
213 passed
```

Targeted suites included:

- `tests/test_settings.py`
- `tests/test_shadow_compare.py`
- `tests/test_runtime_shadow.py`
- `tests/test_shadow_artifacts.py`
- `tests/test_shadow_logging.py`

## Readiness Status

Roadmap 2.12 status:

- shadow/canary readiness baseline complete
- runtime wiring not yet implemented
- production rollout not started
- cutover not allowed from this stage

The stage prepares the codebase for a later controlled integration step, but does not activate runtime shadow execution.

## Recommended Next Stage

Recommended next stage:

Roadmap 2.13 — controlled runtime shadow wiring / dry-run integration.

Suggested Roadmap 2.13 scope:

- connect the observer to `/classify` only behind disabled-by-default config gates
- production response must remain legacy-only
- optional artifact and logging behavior only when explicitly enabled
- no actual canary serving
- no LLM response returned to users
- strict timeout and failure isolation
- manual local smoke verification

Roadmap 2.13 still must not be cutover.

## Rollback Notes

Roadmap 2.12 rollback can be performed by reverting individual small commits.

Because Roadmap 2.12 is not connected to runtime behavior, no operational rollback is required.

If needed, individual helper modules can be reverted without affecting production behavior.
