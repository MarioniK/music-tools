# Roadmap 4.9 - ONNX model provenance and selection criteria

## Status

- documentation/design safe-slice
- optional sample metadata validation only
- no ONNX inference
- no model or audio artifacts
- no production behavior change

## Purpose

Roadmap 4.9 defines the provenance, license, metadata, and approval gates that must be satisfied before any future actual ONNX inference experiment is allowed.

The goal is to prevent an ONNX candidate from entering even an offline proof without a clear answer to these questions:

- where the model came from
- who published it
- what license and redistribution rights apply
- which exact file/version/revision is being inspected
- what input and output contract the model exposes
- how output labels can be mapped to the existing controlled genre vocabulary
- whether the model can be handled entirely local-only

This roadmap is a readiness checkpoint for future experimentation, not an experiment.

## Scope

Roadmap 4.9 covers:

- model source eligibility rules
- prohibited source rules
- local-only model handling expectations
- required provenance metadata fields
- checksum and version strategy
- input/output metadata requirements
- label mapping requirements
- approval status model
- no-go criteria
- Roadmap 4.10 readiness gate
- production invariants that must remain unchanged

The optional JSON artifact under `docs/lightweight/evaluation/model-provenance/` is a documentation sample only. It is not an approved model record and must not be used as an instruction to download or run a model.

## Non-goals

Roadmap 4.9 does not:

- choose a real ONNX model
- download a model
- add model files
- add audio fixtures
- add download scripts
- add network access logic
- add `onnxruntime`
- run inference
- implement an ONNX provider
- update provider factory wiring
- change app/runtime behavior
- change `/classify`
- change response shape
- change cache semantics
- perform shadow, canary, or production migration work

## Why provenance is required before ONNX inference

ONNX inference is only meaningful if the model under test is identifiable, reproducible, and legally usable. Without provenance, an offline result cannot be reviewed or repeated because reviewers cannot know whether the same file, revision, preprocessing contract, or label set was used.

Provenance must be collected before inference so that the future experiment does not accidentally normalize an unsafe process:

- running a file from an unknown or unofficial source
- interpreting labels that do not match the documented model output
- comparing `legacy_musicnn` to an untraceable artifact
- building evaluation evidence that cannot be reproduced later
- discovering license or redistribution blockers after technical work has already biased the decision

## License and provenance gate

Every candidate model must pass a license/provenance gate before any model use, including offline proof-of-concept inference.

The gate exists because model files can carry usage, redistribution, attribution, commercial-use, research-only, or dataset-derived restrictions. A model with an unclear license is not safe to inspect as part of a project workflow, and a model with unclear provenance cannot become reliable engineering evidence.

The license/provenance gate must verify:

- explicit license name
- license URL or repository license file
- source repository or official model page
- publisher or project identity
- stable model version, revision, release, or commit
- documented label set
- documented input/output contract
- redistribution status for committing or packaging artifacts
- local-only execution compatibility

Unknown license, missing source repository, unclear redistribution rights, or missing label metadata are blockers.

## Model files must not be committed without explicit approval

Model binaries must not be committed by default, even for offline experiments.

Committing model files without explicit approval creates avoidable risk:

- repository bloat from large binary artifacts
- accidental redistribution of files with unclear rights
- unclear review boundary between documentation and runtime behavior
- hard-to-revert dependency on a specific binary
- accidental promotion of a local experiment into project state

Allowed future model handling starts with local-only paths outside the repository, plus recorded metadata and checksums. A model file may be committed only after explicit later approval that names the file, license, provenance, intended use, storage location, and review owner.

## Baseline remains legacy MusiCNN

`legacy_musicnn` remains the baseline because it is the current production classifier path and the stable reference for `/classify` behavior.

Any ONNX candidate must be evaluated against the existing legacy MusiCNN behavior before any later integration proposal. Roadmap 4.9 does not alter the provider default, production classifier path, response contract, cache semantics, runtime image, or dependencies.

## Allowed model sources

Allowed sources are candidates for review only. They are not automatically approved.

An ONNX candidate may be considered if it comes from:

- official model repositories from model authors
- official GitHub repositories with clear license
- Hugging Face repositories with explicit model card and license
- academic or project repositories with reproducible provenance
- sources with a documented label set
- sources with a documented input/output contract
- models that can run local-only
- models with stable version, revision, release, commit, or hash

The source must be stable enough that another reviewer can locate the same artifact and verify the same metadata later.

## Prohibited model sources

An ONNX candidate must not be used when it comes from or requires:

- random mirrors
- forum attachments
- unauthoritative cloud-drive links
- unknown license
- missing source repository
- missing label metadata
- network-required inference
- GPU-only requirement for basic offline proof
- unclear redistribution rights
- impossible controlled-vocabulary mapping
- required production dependency changes before offline proof
- required `/classify` response shape changes
- required `tidal-parser` changes
- committed binary model artifacts without approval

## Local-only model handling

Future approved ONNX experiments must treat model files as local-only unless a later approval explicitly says otherwise.

Local-only handling means:

- model paths are provided by the developer or CI environment explicitly
- model files are not copied into this repository
- model files are not committed
- no script downloads a model
- no runtime code performs network fetches
- metadata may record source URLs for provenance, but those URLs are not download instructions
- validation may inspect JSON metadata only unless a later experiment approves local file checks
- any checksum comparison against a real local file requires a separately approved offline inference or file-inspection step

Roadmap 4.9 itself does not read model files.

## Required provenance fields

Every future candidate provenance record must include these fields:

- `schema_version`
- `model_id`
- `model_name`
- `model_family`
- `model_format`
- `source_url`
- `source_repository`
- `license`
- `license_url`
- `model_version`
- `model_hash_sha256`
- `model_file_name`
- `model_file_size_bytes`
- `input_names`
- `input_shapes`
- `output_names`
- `output_shapes`
- `label_source`
- `label_count`
- `label_mapping_strategy`
- `intended_use`
- `known_limitations`
- `approval_status`
- `warnings`

Missing fields block readiness. Placeholder values are acceptable only in documentation examples or records explicitly marked incomplete, and warnings must state why the record is not approved.

## Hash, checksum, and version strategy

Future ONNX candidate records must identify the exact model artifact.

Required strategy:

- record a stable source version, release, revision, commit, or model registry revision
- record the exact model file name
- record file size in bytes when the real local file is approved for inspection
- record SHA-256 for the exact file before inference
- keep checksum metadata separate from source trust; a hash proves identity, not license safety
- treat any file mismatch as a new candidate requiring review
- treat placeholder hashes as invalid for inference

A future inference experiment must fail its readiness gate if the model file hash is missing, placeholder-only, or inconsistent with the approved provenance record.

## Input/output metadata requirements

Before inference, the candidate must document:

- input tensor names
- input tensor shapes
- input tensor dtypes when known
- audio preprocessing expectations
- sample rate assumptions
- mono/stereo handling
- clip duration or windowing assumptions
- output tensor names
- output tensor shapes
- output meaning, such as logits, probabilities, embeddings, or multilabel scores
- postprocessing needed before label mapping

The metadata must be specific enough to prove that a future offline experiment can run without changing production runtime code.

## Label mapping requirements

The candidate must include a documented label source and label count. The output labels must be mappable to the existing controlled genre vocabulary without changing `/classify` response shape.

The label mapping strategy must define:

- original model label source
- exact label order
- mapping from model labels to controlled vocabulary terms
- handling for labels outside the controlled vocabulary
- handling for multi-label outputs
- handling for ties or low-confidence outputs
- whether mapping is direct, normalized, grouped, or discarded
- known ambiguity and expected review warnings

If output labels cannot produce an artifact-contract-compatible candidate output with `genres` and `genres_pretty`, the model is no-go.

## Approval status model

Candidate provenance records must use explicit approval states.

Allowed statuses:

- `example_only`: documentation sample, not usable for inference
- `metadata_incomplete`: real candidate metadata is still incomplete
- `provenance_review_required`: source and license need review
- `license_review_required`: license or redistribution rights need review
- `offline_proof_candidate`: approved only for a future local offline proof
- `offline_proof_complete`: local offline proof completed, no production approval implied
- `rejected`: candidate failed a gate

Any status that implies production use, production approval, or default-provider replacement is prohibited in Roadmap 4.9 artifacts.

## No-go criteria

A candidate is no-go if any of the following are true:

- unknown license
- missing source/provenance
- unclear redistribution rights
- model file committed without approval
- no label metadata
- output labels cannot be mapped to controlled vocabulary
- model requires production dependency changes before offline proof
- model requires GPU-only runtime
- model source is untrusted
- model cannot run local-only
- model output cannot produce artifact-contract-compatible candidate output
- model requires `/classify` response shape changes
- model requires `tidal-parser` changes
- model requires cache semantics changes
- model requires shadow/canary before offline proof
- model requires copyrighted audio fixtures

No-go criteria must be applied before running inference.

## Roadmap 4.10 readiness gate

Roadmap 4.10 may begin only if a future proposal provides an explicit candidate record that satisfies this document.

Readiness requires:

- completed provenance record with all required fields
- approved source category
- no prohibited source condition
- explicit license and license URL
- documented redistribution status
- exact model version/revision/hash strategy
- documented input/output metadata
- documented label source and label count
- controlled-vocabulary mapping plan
- local-only handling plan
- no model or audio artifacts committed without approval
- no production dependency, Docker, provider, factory, runtime, cache, or `/classify` changes required before offline proof
- explicit statement that `legacy_musicnn` remains the baseline

If any item is missing, Roadmap 4.10 must remain blocked.

## Production invariants

Roadmap 4.9 preserves these invariants:

- default provider remains `legacy_musicnn` until explicit later approval
- production classifier path remains legacy MusiCNN
- `/classify` contract unchanged
- response shape unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- no response shape redesign
- no cache semantics changes
- no provider implementation
- no provider factory changes
- no runtime changes
- no dependency changes
- no Dockerfile / Docker Compose changes
- no model files
- no audio fixtures
- no downloads
- no network access logic
- no inference
- no shadow/canary
- no production migration
- `tidal-parser` untouched

## Validation boundary

The optional validator extension for Roadmap 4.9 may only perform shallow checks on sample provenance JSON:

- JSON readability
- required field presence
- basic type checks
- `model_format == "onnx"`
- `warnings` is a list
- sample artifact is not production-approved

The validator must not:

- import `onnxruntime`
- import production provider/runtime modules
- read model files
- calculate real model hashes from the filesystem
- access the network

This keeps Roadmap 4.9 as documentation/design evidence and avoids accidentally starting the ONNX experiment early.
