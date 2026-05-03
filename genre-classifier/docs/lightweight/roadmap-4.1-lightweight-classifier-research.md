# Roadmap 4.1 — Lightweight classifier research and candidate matrix

## Status

- research/design baseline
- documentation-only

## Purpose

Roadmap 3 completed the production runtime modernization through release `v0.4.0`. The `genre-classifier` production runtime now runs on Python 3.12 with TensorFlow 2.21 and `essentia-tensorflow`, so the main remaining classifier concern is no longer the legacy Python/TensorFlow 1.x runtime.

The remaining problem is the weight of the classifier path and its runtime footprint. The current production provider remains `legacy_musicnn`, and the production classifier path remains the legacy MusiCNN path. Roadmap 4.1 establishes a research/design baseline for investigating lighter alternatives without changing service behavior.

Roadmap 4.1 does not change the provider default, runtime, `/classify` contract, response shape, or production traffic path.

## Scope

- research candidate lightweight classifier paths
- define evaluation criteria for candidate comparison
- outline an offline comparison approach against `legacy_musicnn`
- define explicit approval gates before any production-facing change
- recommend the next Roadmap 4.2 step

## Non-goals

- no production code
- no runtime changes
- no provider default change
- no `/classify` contract change
- no response shape change
- no `tidal-parser` changes
- no canary rollout
- no shadow execution
- no LLM cutover
- no production migration
- no new dependencies
- no GitHub release work

## Current production baseline

Production provider:

- `legacy_musicnn`

Production runtime:

- Python `3.12.13`
- TensorFlow `2.21.0`
- `essentia-tensorflow` `2.1b6.dev1389`
- Essentia `2.1-beta6-dev`
- numpy `2.4.4`
- protobuf `7.34.1`
- h5py `3.14.0`
- FastAPI `0.83.0`
- Pydantic `1.10.26`
- Uvicorn `0.16.0`

Production API baseline:

- `/classify` contract unchanged
- response shape unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- runtime shadow disabled by default
- `tidal-parser` unchanged

## Why lightweight research is next

Runtime modernization and classifier lightweighting are separate concerns.

Roadmap 3 addressed runtime modernization by moving the production service away from the legacy Python 3.6 / TensorFlow 1.x stack and onto the current Python 3.12 / TensorFlow 2.21 / `essentia-tensorflow` runtime. That reduced runtime compatibility risk and made the production environment maintainable on a modern base.

It did not remove the operational cost of the current classifier path. The legacy MusiCNN path still carries TensorFlow/Essentia import cost, model load cost, dependency weight, image size, memory usage, and inference latency. Roadmap 4 should therefore investigate whether a lighter classifier path can preserve the production contract while reducing operational weight.

Potential improvement areas:

- import/startup weight
- memory footprint
- image size
- dependency weight
- inference latency
- operational rollback risk

## Candidate matrix

Roadmap 4.1 does not select any candidate as a production target. Each candidate below is research-only until evaluated offline and explicitly approved for later roadmap phases.

| Candidate | Basic idea | Potential advantages | Main risks | Contract impact | Roadmap 4.1 stance |
| --- | --- | --- | --- | --- | --- |
| ONNX Runtime | Convert or replace the classifier path with an ONNX-compatible model and run inference through ONNX Runtime. | Smaller runtime than full TensorFlow in some builds; portable model format; measurable startup and inference profile. | Model conversion quality loss; unsupported ops; runtime packaging complexity; may still be heavy depending on provider build. | Must preserve current `/classify` response fields and controlled genre output. | Research-only candidate; not selected for production. |
| TFLite | Use a TensorFlow Lite model for local inference. | Potentially smaller model/runtime footprint; mobile/edge-oriented inference; possible latency gains. | Genre model availability; conversion drift; limited op support; Python server packaging may reduce expected gains. | Must map outputs into existing `genres` and `genres_pretty` shape. | Research-only candidate; not selected for production. |
| sklearn/lightweight ML over audio features | Extract compact audio features and classify with a small classical ML model. | Very small inference dependency footprint if features are cheap; easier model inspection; fast startup. | Feature extraction may still require heavy audio libraries; quality may trail MusiCNN; needs controlled training/evaluation data. | Contract can be preserved if outputs are normalized to current genre vocabulary. | Research-only candidate; useful for baseline comparison. |
| CLAP/audio embeddings + classifier | Use audio embeddings from a pretrained model and a small classifier head or similarity layer. | Strong semantic embeddings; flexible downstream classifier; possible better coverage for broad genre labels. | Embedding model may be large; licensing/provenance must be checked; dependency and latency risk; may not be lighter in practice. | Contract must remain unchanged; embedding labels need compatibility mapping. | Research-only candidate; no production assumption. |
| small audio tagging models | Evaluate smaller pretrained audio tagging models and map tags to supported genres. | May reduce model size while retaining audio-specific signal; model zoo offers several architectures. | Tag-to-genre mismatch; OOV tags; inconsistent model provenance; quality variance across genres. | Requires strict mapping into controlled output vocabulary and existing response shape. | Research-only candidate; compare offline before any spike. |
| rule-assisted audio feature classifier | Combine deterministic audio features with simple rules or a small scorer. | Transparent failure modes; low dependency weight if features are already available; easy rollback. | Likely lower genre quality; brittle across recordings; may overfit local fixtures. | Contract can be preserved, but confidence and genre mapping need careful normalization. | Research-only candidate; possible fallback/baseline lane. |
| teacher/student lightweight model trained against legacy outputs | Train a smaller student model using captured `legacy_musicnn` outputs as teacher labels. | Explicit compatibility with current baseline; can optimize for size and speed; measurable top-N overlap target. | May inherit teacher errors; requires reproducible training data; quality may degrade on unseen inputs; provenance needs documentation. | Designed to preserve current output vocabulary and shape. | Research-only candidate; promising only after offline harness design. |
| optional remote/local lightweight provider, research-only | Define an optional provider shape for a local or remote lightweight classifier without enabling it by default. | Allows comparison of external or separately packaged models; isolates provider risk; can remain non-production. | Network reliability if remote; privacy/security review; operational complexity; provider drift risk. | Must not alter default provider or `/classify` contract. | Research-only lane; no default switch and no production traffic. |

## LLM provider foundation status

The LLM provider foundation exists from Roadmap 2. It remains non-default and is not an automatic production target for Roadmap 4.

LLM-based genre classification may be considered only as a separate research lane. Any LLM adoption requires explicit approval for that specific direction, including quality, cost, latency, privacy, and rollback review. Roadmap 4.1 does not recommend an LLM cutover.

## Evaluation criteria

- genre quality
- controlled vocabulary compatibility
- compatibility mapping preservation
- latency
- memory
- image size
- startup/import time
- dependency weight
- rollback risk
- maintainability
- failure-mode clarity
- licensing/model provenance
- reproducibility

## Offline comparative evaluation approach against legacy_musicnn

Candidate evaluation should happen offline only. It must not use production traffic, shadow execution, or a provider default switch.

Proposed approach:

- define a fixed evaluation manifest
- use representative local audio fixtures
- capture baseline outputs from `legacy_musicnn`
- capture outputs from each candidate under the same manifest
- normalize all candidate genres through the same compatibility mapping rules
- compare normalized genres against the `legacy_musicnn` baseline
- measure controlled vocabulary hit rate
- measure OOV rate
- measure top-N overlap
- measure latency, memory, and startup/import time
- record dependency and image-size implications separately
- preserve `legacy_musicnn` as the default provider throughout evaluation

## Explicit approval gates

Provider default switch:

- requires explicit approval before changing the default provider away from `legacy_musicnn`
- requires offline evidence, contract preservation evidence, rollback notes, and a migration plan

Canary:

- requires explicit approval before sending any production traffic to a candidate provider
- requires an approved observation plan, rollback criteria, and success/failure thresholds

Production migration:

- requires explicit approval before replacing the production classifier path
- requires candidate evaluation evidence, operational readiness evidence, compatibility review, and rollback plan

LLM adoption:

- requires explicit approval before any LLM provider becomes a production path or production default
- requires separate review of cost, latency, privacy, reliability, output determinism, and rollback behavior

## Recommended Roadmap 4.2

Recommended next artifact:

```text
Roadmap 4.2 — Offline lightweight candidate evaluation harness design
```

Recommended Roadmap 4.2 scope:

- design the evaluation manifest
- define the report format
- select the first 1-2 candidates for an offline spike
- preserve `legacy_musicnn` as default
- avoid production behavior changes

## Rollback and safety notes

This artifact is documentation-only. It adds no production code, runtime changes, provider changes, dependencies, Docker changes, traffic routing changes, or release work.

Rollback for Roadmap 4.1 is deleting this single file:

```text
docs/lightweight/roadmap-4.1-lightweight-classifier-research.md
```

No runtime rollback is required.
