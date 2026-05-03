# Roadmap 4.11 - ONNX raw output and label mapping design

## Status

- documentation/design safe-slice
- optional sample label mapping artifact only
- shallow artifact validation only
- no ONNX inference
- no production provider implementation
- no dependency, Docker, runtime image, or Compose change
- no model or audio artifact added

## Purpose

Roadmap 4.11 defines the safety boundary between raw ONNX model output and future offline candidate genre output.

The central rule is that raw ONNX tensors, scores, probabilities, logits, embeddings, or class indices are not genre output until an approved label mapping artifact ties the output positions to a verified label source and to the Roadmap 4.9 model provenance record.

This roadmap prevents future offline evaluation from silently turning unknown model output into fake genre names. It is a design and documentation step for later evaluation work, not a runtime integration step.

## Why raw ONNX output is not genre output

ONNX output is a numeric contract, not a semantic contract. A tensor can expose scores or logits with shape such as `[1, N]`, but the tensor alone does not prove:

- which label each index represents
- whether the label order matches the model file being inspected
- whether values are logits, probabilities, multilabel scores, embeddings, or another intermediate representation
- whether labels are genres, moods, instruments, tags, scenes, datasets, or training artifacts
- whether labels can map to the existing controlled genre vocabulary
- whether ambiguous labels should be mapped, ignored, or rejected

Treating raw output as genre output would make the candidate look more meaningful than the evidence supports.

## Fake genres are prohibited

Future candidate outputs must not invent genre names to make ONNX smoke evidence look comparable with `legacy_musicnn`.

Fake genres are prohibited because they would:

- hide missing label metadata
- create misleading offline evaluation results
- make top-N comparisons appear valid when the label source is unknown
- allow ambiguous model labels to drift into the controlled vocabulary
- normalize a path that could later affect production behavior without review

If an approved mapping is missing, candidate `genres` and `genres_pretty` must stay empty in offline artifacts that follow the `/classify` response shape.

## Relationship with Roadmap 4.9 model provenance

Roadmap 4.9 established the provenance gate for ONNX candidates: source, license, exact model identity, hash/version strategy, input/output metadata, label source, label count, and approval status.

Roadmap 4.11 adds the mapping layer that must be bound to that provenance. A label mapping artifact is only meaningful when its `model_id`, `model_family`, label source, label count, and output-label assumptions match the approved provenance record for the model under review.

The mapping must be rejected when it does not match the provenance model identity, hash, version, output shape, or documented label source. A mapping approved for one model must not be reused for another model family or revision by name similarity alone.

## Relationship with Roadmap 4.10 smoke boundary

Roadmap 4.10 introduced offline-only local ONNX smoke mode. That mode may inspect metadata or run tightly controlled dummy inference after the provenance gate passes, but it does not approve genre semantics.

Roadmap 4.11 keeps that boundary explicit:

- smoke inference can observe raw output shape and numeric output
- smoke inference must not convert raw output into genre output without approved mapping
- raw scores may be kept under metadata for inspection
- `/classify`-compatible candidate fields remain empty when mapping is missing or not approved
- no smoke result is production approval

## Legacy baseline remains unchanged

`legacy_musicnn` remains the default provider, the production classifier path, and the baseline for evaluation.

Roadmap 4.11 does not change `/classify`, response shape, provider factory wiring, dependencies, runtime, Dockerfile, or Docker Compose. Any future ONNX candidate must be evaluated against the legacy MusiCNN baseline before later integration is proposed.

The response shape remains unchanged:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## Label mapping artifact contract

A label mapping artifact documents how a specific model output label list maps to the controlled genre vocabulary for offline evaluation.

It must be a reviewable JSON object that can be validated without model files, audio files, `onnxruntime`, production providers, or inference. The artifact is not runtime configuration and must not be loaded by production code in this roadmap.

Required top-level fields:

- `schema_version`
- `mapping_id`
- `model_id`
- `model_family`
- `label_source`
- `label_source_url`
- `label_count`
- `mapping_status`
- `labels`
- `controlled_vocabulary_version`
- `unmapped_labels`
- `warnings`
- `approval_status`

Required per-label fields:

- `raw_label`
- `raw_index`
- `mapped_genre`
- `mapped_confidence`
- `mapping_decision`
- `mapping_notes`

## Mapping decision values

Allowed `mapping_decision` values:

- `mapped`: the raw label directly maps to a controlled genre term.
- `alias_mapped`: the raw label is a reviewed alias for a controlled genre term.
- `ignored_non_genre`: the raw label is valid model output but is not a genre candidate.
- `unmapped`: no acceptable controlled-vocabulary mapping is known.
- `rejected_ambiguous`: the raw label has ambiguous semantics and must not become a genre.

Only `mapped` and `alias_mapped` entries may produce candidate genre tags, and only when the artifact is approved for offline evaluation.

## Mapping coverage rules

Coverage must be evaluated against the complete model label list, not only labels that are convenient or already known.

Required coverage rules:

- `label_count` must match the number of entries in `labels`.
- Each `raw_index` must be unique.
- `raw_index` values must be associated with the model output shape and label order.
- Every model output label must have a mapping decision.
- `mapped` and `alias_mapped` entries must have a non-empty `mapped_genre`.
- `ignored_non_genre`, `unmapped`, and `rejected_ambiguous` entries must not create candidate genres.
- `unmapped_labels` must list labels that remain unmapped or rejected because of ambiguity.
- Warnings must describe incomplete, ambiguous, or example-only mapping conditions.

Exact numeric thresholds for "too many unmapped labels" or "too many ambiguous labels" are intentionally left to a future evaluation gate. Roadmap 4.11 requires the condition to be visible and review-blocking when it affects candidate interpretation.

## Unmapped and ambiguous handling

Unmapped and ambiguous labels must remain visible to reviewers.

Handling rules:

- `unmapped` means the label has no approved controlled-vocabulary target.
- `rejected_ambiguous` means the label could mean multiple things or depends on model-specific semantics that are not documented.
- top scoring labels that are unmapped or ambiguous must block interpretation of the candidate result.
- ambiguous labels must not be forced into the nearest genre to improve apparent overlap.
- ignored non-genre labels may be retained in metadata, but must not appear in `genres` or `genres_pretty`.

## Candidate behavior with approved mapping

When a mapping artifact has `approval_status: "approved_for_offline_evaluation"` and matches the Roadmap 4.9 provenance record, offline evaluation may convert raw output into candidate genre output.

Expected behavior:

- use only `mapped` and `alias_mapped` labels as candidate genres
- map labels to the controlled vocabulary version recorded by the artifact
- drop `ignored_non_genre` labels from genre output
- surface `unmapped` and `rejected_ambiguous` high-scoring labels as warnings
- keep output compatible with the unchanged `/classify` response shape
- record mapping metadata in offline evaluation artifacts, not production responses

`approved_for_offline_evaluation` is not production approval.

## Candidate behavior without approved mapping

When the mapping artifact is absent, mismatched, incomplete, rejected, deprecated, or not approved, offline candidate output must not claim genre semantics.

Expected behavior:

- `genres` remains `[]`
- `genres_pretty` remains `[]`
- raw output may be recorded under metadata for local inspection
- message and warnings must state that no approved label mapping exists
- evaluation reports must treat the candidate as not comparable for genre quality

## Approval status model

Allowed mapping approval statuses:

- `not_approved`: documentation sample, draft, or incomplete mapping; not usable for inference interpretation by default.
- `approved_for_offline_evaluation`: usable only for offline evaluation against the matching provenance record.
- `rejected`: reviewed and found unsafe or invalid.
- `deprecated`: previously useful but no longer valid for the current model, label source, vocabulary, or evaluation policy.

`approved_for_offline_evaluation` is not production approval. Production approval is out of scope for Roadmap 4.11 and would require a separate review of runtime behavior, dependencies, rollout, rollback, API compatibility, and operational evidence.

## No-go criteria

Mapping is no-go when any of the following are true:

- no label source
- unverifiable label source
- label count mismatch with model output
- labels cannot be associated with model output shape
- mapping artifact does not match provenance `model_id`, hash, or version
- labels cannot be mapped to controlled vocabulary
- too many unmapped labels
- too many ambiguous labels
- top scoring labels are unmapped or ambiguous
- ambiguous model label semantics
- `approval_status` is not `approved_for_offline_evaluation`
- raw output shape cannot be associated with label list
- mapping requires production vocabulary redesign
- mapping would create fake genre output
- mapping requires production runtime, dependency, or Docker changes in this roadmap

No-go criteria must block genre interpretation before any candidate output is compared against `legacy_musicnn`.

## Explicit non-goals

Roadmap 4.11 does not:

- write production classifier code
- create a production provider implementation
- connect anything to provider factory
- change the default provider
- change `/classify`
- change response shape
- add `onnxruntime`
- add TFLite, sklearn, or model dependencies
- add model files
- download model files
- add network or download logic
- add copyrighted audio fixtures
- run inference
- change runtime
- change Dockerfile
- change Docker Compose
- touch `tidal-parser`
- create a tag
- create a release

## Future handoff to Roadmap 4.12

Roadmap 4.12 may use this design to define a real offline evaluation gate for mapped ONNX candidate outputs.

The handoff should include:

- selecting a real candidate only after Roadmap 4.9 provenance approval
- verifying the exact label source and label order
- approving or rejecting a complete mapping artifact
- defining quantitative coverage thresholds
- defining how high-scoring unmapped and ambiguous labels affect evaluation
- comparing mapped candidate output against `legacy_musicnn`
- keeping production approval separate from offline evaluation approval

Roadmap 4.12 must continue to preserve the production contract unless a later explicit roadmap authorizes runtime integration work.
