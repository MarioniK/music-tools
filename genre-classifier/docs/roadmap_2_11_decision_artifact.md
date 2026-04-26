# Roadmap 2.11 Decision Artifact

## Stage Summary

Roadmap 2.11 focused on curated findings review and targeted compatibility-fix preparation for `genre-classifier`.

The stage did not perform provider cutover, rollout, runtime shadow execution, canary execution, default provider changes, or external API changes.

Scope remained limited to `genre-classifier`.

## Inputs Reviewed

Roadmap 2.11 used the following inputs:

- `docs/roadmap_2_11_curated_findings_review.md`
- `evaluation/manifests/roadmap_2_11/fix_candidates_v1.json`
- `evaluation/artifacts/roadmap_2_11/curated_review_v1.json`
- Roadmap 2.10 manifests and docs where relevant
- Roadmap 2.10 curated, golden, and repeat-run sources

## Artifact Summary

Roadmap 2.11 produced an evidence-backed fix candidates manifest and a concrete curated review artifact.

The curated review artifact includes:

- per-item results
- category summaries
- warning rollups
- review queue
- readiness buckets
- candidate evidence summary

The artifact records review evidence only. It does not auto-generate fix candidates.

## Candidates Found

Roadmap 2.11 recorded three evidence-backed candidates.

### `weak-output-empty-results`

- type: `weak_output_handling`
- status: `proposed`
- risk: `high`
- decision: handled in this stage by preserving empty-output evidence explicitly in the Roadmap 2.11 curated review artifact

### `weak-top-partial-output-threshold-review`

- type: `threshold_ranking`
- status: `deferred`
- risk: `medium`
- decision: deferred because the evidence is real but single-sample and should not drive threshold or ranking changes yet

### `no-shared-tags-genre-boundary-review`

- type: `prompt_discipline`
- status: `deferred`
- risk: `medium`
- decision: deferred because the evidence is real but comes from a single hard, ambiguous genre-boundary case and should not drive prompt changes yet

## Implemented Change

Only evidence preservation for empty LLM output was implemented.

Existing evaluation logic already treated `llm_empty_output` as:

- a warning
- a review queue item
- a blocking `not-ready` readiness signal

The Roadmap 2.11 curated review artifact now preserves explicit `candidate_evidence_summary` fields:

- `warning_case_counts`
- `review_queue_sample_ids`
- `blocking_findings`
- `empty_llm_output_sample_ids`
- `empty_llm_output_blocks_readiness`

No production runtime behavior changed.

## Preserved Invariants

Roadmap 2.11 preserved these invariants:

- default provider remains `legacy_musicnn`
- legacy path remains available
- external `/classify` contract remains unchanged
- response shape remains unchanged
- no production runtime changes
- no cutover
- no rollout
- no runtime shadow or canary
- no threshold or ranking changes
- no prompt discipline changes
- no controlled vocabulary changes
- no alias or normalization changes
- no compatibility mapping changes

## Verification

Final targeted test run:

```text
PYTHONPATH=. pytest tests/test_roadmap_2_11_fix_candidates_manifest.py tests/test_roadmap_2_11_curated_review_artifact.py tests/test_evaluation_entrypoint.py tests/test_evaluation_report.py
```

Result:

```text
23 passed
```

Nearby evaluation and Roadmap 2.11 test run:

```text
PYTHONPATH=. pytest tests -k "evaluation or roadmap_2_11"
```

Result:

```text
34 passed, 124 deselected
```

## Outcome

Roadmap 2.11 is ready to close.

The `llm` path is better prepared for later shadow or runtime work because review evidence is now explicit, machine-readable, and reviewable.

No rollout decision is made in this stage.

Deferred candidates remain intentionally unresolved.

## Next Stage Input

Roadmap 2.12 should use Roadmap 2.11 artifacts and deferred candidates as input, but should not assume cutover readiness.

If Roadmap 2.12 is about runtime shadow or canary work, it should start from the current invariants:

- default provider remains `legacy_musicnn`
- external `/classify` contract remains unchanged
- candidate implementation is not automatic
