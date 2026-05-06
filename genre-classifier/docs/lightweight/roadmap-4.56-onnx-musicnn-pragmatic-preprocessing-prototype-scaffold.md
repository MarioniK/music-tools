# Roadmap 4.56 - ONNX/MusiCNN pragmatic preprocessing prototype scaffold

## Purpose

Roadmap 4.56 is a local-only scaffold for the selected Roadmap 4.55 strategy:

- target candidate remains `official_onnx_musicnn`;
- preprocessing direction is `Essentia standard audio loading + documented standalone mel-spectrogram generation path`;
- strict legacy parity is not required;
- controlled output drift is allowed;
- documented, reproducible preprocessing is required;
- TensorflowPredictMusiCNN is not used as the preprocessing oracle.

This slice exists to answer one narrow question:

- can we locally and reproducibly obtain the ONNX/MusiCNN input shape
  `melspectrogram [187, 96]` without changing production defaults or contracts?

## Why this is local-only

This roadmap slice does not make a production decision. It only prepares
sanitized evidence about the preprocessing path and the ONNX input metadata.

No production provider implementation, no default switch, no `/classify`
contract change, no response shape change, no cache change, no runtime
migration, and no dependency migration are part of this step.

## AGENTS.md compliance

This artifact was prepared after reading and following
`/opt/music-tools/AGENTS.md`.

Confirmed boundaries:

- only `genre-classifier` is in scope;
- `tidal-parser` is untouched;
- Docker Compose was not run;
- Docker rebuild was not run;
- production provider/default logic was not changed;
- production dependencies were not changed;
- `/classify` was not called;
- no TensorFlow baseline rerun was performed;
- no TensorFlow vs ONNX comparison was performed;
- no strict parity claim is made;
- no production readiness claim is made.

## Helper modes

The scaffold helper lives at
`scripts/lightweight/musicnn_pragmatic_preprocessing_prototype.py` and exposes
two local-only modes.

### `metadata-only`

This mode is for safe inspection only:

- inspect ONNX input/output metadata;
- inspect the committed fixture list;
- inspect the Roadmap 4.55 strategy source;
- write a sanitized report without pretending that preprocessing succeeded.

### `preprocessing-probe`

This mode is for a bounded attempt at the mel path:

- it may attempt the preprocessing probe only when the local approved isolated
  environment already has the needed dependencies;
- it must not use TensorflowPredictMusiCNN as the oracle;
- it must not fake a mel patch or ONNX output;
- if Essentia standard support is missing, it records explicit blockers.

## Report format

The committed evidence report is stored at
`docs/lightweight/evaluation/evidence/roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json`.

The report should stay sanitized and document:

- roadmap and strategy source;
- target candidate;
- ONNX input metadata with `melspectrogram [187, 96]`;
- expected outputs `[50]` and `[200]`;
- local environment status;
- sanitized fixture hashes and license status;
- preprocessing probe result;
- blockers and next-step recommendation.

The report must not publish:

- private full local paths;
- model binaries;
- audio binaries;
- venv paths as project artifacts;
- fake preprocessing output;
- fake ONNX outputs;
- strict parity claims;
- production approvals.

## Current blockers

The approved isolated environment currently lacks Essentia, so the preprocessing
probe is blocked.

Expected blocker codes for this slice:

- `PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE`
- `ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE`

If a future local environment can execute the probe but still cannot materialize
the patch, use `MEL_PATCH_SHAPE_NOT_PRODUCED`.

## Non-goals

Roadmap 4.56 does not:

- implement the production provider;
- switch the default provider;
- change `/classify` contract or response shape;
- change cache semantics;
- change Dockerfile or Compose;
- add production dependencies;
- add model or audio files to the repo;
- run Docker or rebuild images;
- claim strict legacy parity;
- claim production readiness;
- claim final migration approval.

## Rollback notes

This slice is designed to be easy to revert:

- remove the helper script if the scaffold is not needed;
- remove the generated evidence report and this documentation page if the
  roadmap direction changes;
- keep the production code path untouched.

## Next step

If Essentia standard mel-path support becomes available in a safe local
environment, rerun the `preprocessing-probe` mode and capture whether the
generated patch really reaches `[187, 96]` in a reproducible way.
