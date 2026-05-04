# Roadmap 4.22 - Official MusiCNN ONNX model identity and parity feasibility review

Status:

- documentation/research safe-slice;
- model identity and parity feasibility review only;
- non-production-facing;
- `not_production_decision: true`;
- no implementation;
- no model integration;
- no model download;
- no dependency changes;
- no provider changes;
- no runtime changes;
- `approved_for_implementation: false`;
- `approved_for_model_download: false`;
- `approved_for_dependency_changes: false`;
- `approved_for_provider_implementation: false`;
- `approved_for_provider_factory_wiring: false`;
- `approved_for_default_provider_switch: false`;
- `approved_for_shadow_execution: false`;
- `approved_for_canary_rollout: false`;
- `approved_for_production_migration: false`;

Roadmap 4.22 is research only. It records found official Essentia MusiCNN ONNX
references and defines the evidence needed to decide whether an official
MusiCNN ONNX artifact could preserve the current `legacy_musicnn` semantics
while replacing TensorFlow inference runtime in a future local-only parity
spike. It does not approve production use, model download, inference,
dependency changes, provider implementation, default-provider switching,
runtime shadowing, canary rollout, or production migration.

## Scope

Roadmap 4.22 is limited to this documentation file under
`genre-classifier/docs/lightweight/`.

The scope is a model identity and parity feasibility review for official
Essentia MusiCNN ONNX references. The review is intentionally narrow:

- documentation/research safe-slice;
- non-production-facing;
- model identity review only;
- parity feasibility review only;
- no implementation;
- no model integration;
- no model download;
- no dependency changes;
- no provider changes;
- no runtime changes.

No model files, audio files, scripts, tests, validators, provider code,
provider factory wiring, runtime configuration, Docker files, Docker Compose
files, dependency files, lock files, or full label vocabulary artifacts are
added or changed by this slice.

## Why Roadmap 4 changes focus

Roadmap 4 started as a lightweight classifier migration track after runtime
modernization. Roadmap 4.20 and Roadmap 4.21 kept the Essentia
Discogs/EffNet / Discogs400 lane as promising but blocked. The blocker was not
only runtime weight; it also included provenance, labels, mapping, and
baseline-vs-candidate evidence.

New model families introduce new label semantics and mapping risk. Discogs400
may be useful in a future research lane, but it is not a direct continuation of
the current production MusiCNN behavior. Adopting it would require a new label
policy, a controlled-vocabulary mapping, evidence for label order, and
comparison against the existing production output.

Official Essentia MusiCNN ONNX references are potentially closer to the
current `legacy_musicnn` semantics because their artifact names indicate the
MusiCNN family and MSD identity. The safer next question is therefore not
"should Roadmap 4 adopt a new model family?" The safer question is:

- can the service preserve the current MusiCNN semantics while replacing only
  the TensorFlow inference runtime with ONNX Runtime in a future spike?

Roadmap 4.22 pauses the Discogs400 mapping lane and redefines the ONNX topic as
potential MusiCNN runtime replacement feasibility, not as a new model adoption
lane.

## Current production baseline

The current production baseline remains unchanged:

- `legacy_musicnn` remains the default provider;
- the production classifier path remains legacy MusiCNN;
- the `/classify` contract is unchanged;
- the response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `tidal-parser` is unchanged and out of scope;
- `legacy_musicnn` is the comparison baseline for any future candidate.

Runtime shadow execution remains disabled by default. No provider switch,
shadow execution, canary rollout, or production migration is approved.

## Current ONNX / Discogs400 / small audio tagging lane status

The previous ONNX new-candidate lane is blocked because there is no approved
real model evidence, model provenance, label mapping, output evidence, runtime
evidence, or baseline-vs-candidate comparison evidence.

The Discogs400 / EffNet lane remains promising but blocked. It has useful
official references, but it still carries unresolved provenance, label,
mapping, runtime weight, and baseline-vs-candidate evidence requirements.

The small audio tagging lane remains research-only.

Roadmap 4.22 redefines ONNX as potential MusiCNN runtime replacement
feasibility, not as a new model adoption lane. A future ONNX path would need to
prove that it preserves the existing MusiCNN production semantics before any
runtime replacement could be discussed.

## Official MusiCNN ONNX references

Found source index:

- https://essentia.upf.edu/models/feature-extractors/musicnn/

Referenced artifacts:

- `msd-musicnn-1.onnx`
- `msd-musicnn-1.pb`
- `msd-musicnn-1.json`
- `msd-musicnn-1-tfjs.zip`

Based on artifact naming, the referenced model family appears to be MusiCNN
and MSD-based. This is found reference evidence only. It is not verified
production parity evidence, and it does not prove that `msd-musicnn-1.onnx`
matches the exact model artifact, label vocabulary, label order,
preprocessing, output tensor, or post-processing used by the current
production `legacy_musicnn` path.

No referenced artifact is downloaded, vendored, checksummed, imported, or
executed by Roadmap 4.22.

## Current legacy_musicnn identity questions

The current production path must be inspected before any ONNX parity spike can
be scoped. Open questions:

- what exact production model artifact is currently used;
- whether the production path uses MSD, MTT, or another model family;
- where labels and metadata come from;
- how `genres` and `genres_pretty` are formed;
- whether label filtering or compatibility mapping is applied;
- where preprocessing is implemented;
- whether the path uses an Essentia TensorFlow predictor or a custom wrapper;
- whether model input is raw audio, mel/spectrogram, or patches;
- what output tensor shape is produced;
- what post-processing rules convert raw model outputs into response genres.

These questions are blockers for any claim of identity or parity.

## Parity feasibility checklist

A future local-only MusiCNN ONNX parity spike would need evidence for:

- model family parity;
- dataset identity parity;
- label vocabulary parity;
- label order parity;
- preprocessing parity;
- output tensor shape parity;
- ability to compare `.pb` vs `.onnx` numeric outputs;
- current post-processing can be preserved;
- `/classify` response shape can be preserved;
- TensorFlow can eventually be removed without rewriting unrelated service
  code;
- rollback to `legacy_musicnn` remains trivial.

Until these checks have evidence, the ONNX artifact is only a reference, not a
replacement candidate.

## Preprocessing parity questions

Preprocessing is part of model identity. A future review must identify and
compare:

- sample rate;
- mono/stereo handling;
- normalization;
- window or patch size;
- hop size;
- spectrogram or feature transform;
- where preprocessing is implemented now;
- whether the ONNX artifact expects precomputed features or audio-derived
  tensors;
- whether Essentia preprocessing can be preserved without TensorFlow.

If preprocessing cannot be replicated or preserved, parity cannot be assumed
even if artifact names look related.

## Label vocabulary and label order questions

Label vocabulary and label order are blockers for production compatibility. A
future review must identify:

- label list source;
- label order source;
- the role of `msd-musicnn-1.json` metadata;
- current production labels source;
- compatibility between raw labels and the controlled `genres` output;
- whether raw label filtering or compatibility mapping exists today;
- whether `genres_pretty` depends on current ordering or display-name rules.

The full label vocabulary artifact is not added in Roadmap 4.22. Missing label
order evidence is a blocker. A future spike may reference metadata for review,
but any local label artifact would need separate approval.

## Response contract preservation

The production response contract must remain stable:

- `ok`, `message`, `genres`, and `genres_pretty` must remain unchanged;
- no new response fields are approved;
- response semantics for `tidal-parser` must not change;
- cache semantics must not change;
- any future candidate must be compared against `legacy_musicnn` output.

Any future MusiCNN ONNX path must be a runtime replacement candidate only if it
can preserve the current service contract.

## Lightweight target stack implications

If parity is proven in a future step, a potential target can initially preserve
Python 3.12 and the current FastAPI, Pydantic, and Uvicorn stack. The first
question should be ML runtime parity, not API stack modernization.

`onnxruntime` can be considered only in a future local-only spike after the
identity and parity plan is approved. TensorFlow and `essentia-tensorflow`
removal can be considered only after parity proof.

FastAPI/Pydantic v2 upgrade must not be mixed with ML runtime migration.
Docker slimming must not happen before parity proof. Roadmap 4.22 does not
propose an API stack upgrade.

## Evidence classification

Found reference:

- official Essentia MusiCNN feature extractor index:
  https://essentia.upf.edu/models/feature-extractors/musicnn/
- referenced artifact name `msd-musicnn-1.onnx`;
- referenced artifact name `msd-musicnn-1.pb`;
- referenced artifact name `msd-musicnn-1.json`;
- referenced artifact name `msd-musicnn-1-tfjs.zip`;
- artifact naming that appears to indicate MusiCNN / MSD.

Verified evidence:

- the current service production baseline remains `legacy_musicnn`;
- Roadmap 4.22 does not change code, dependencies, model files, Docker files,
  provider wiring, runtime behavior, or the `/classify` response shape;
- the official references are sufficient to justify documentation-only
  identity/parity planning.

Missing evidence:

- exact current production model artifact identity;
- proof that the current model and `msd-musicnn-1.onnx` share the same model
  family and dataset identity;
- label vocabulary identity;
- label order identity;
- preprocessing identity;
- output tensor shape identity;
- `.pb` vs `.onnx` numeric parity evidence;
- post-processing compatibility evidence;
- runtime weight improvement evidence;
- license/provenance approval for production use.

Blocker:

- identity and parity cannot be claimed until the exact production artifact,
  labels, preprocessing, tensor shape, and post-processing are verified.

No-go:

- treating the found ONNX reference as production-ready;
- downloading or vendoring the model in this slice;
- adding `onnxruntime` in this slice;
- switching providers in this slice;
- changing `/classify` semantics in this slice.

## Blockers / no-go checklist

The MusiCNN ONNX path is no-go if any of the following remain true:

- model family mismatch;
- dataset mismatch;
- label vocabulary or label order cannot be verified;
- preprocessing cannot be replicated or preserved;
- output tensor shape is incompatible;
- post-processing cannot be preserved;
- `/classify` contract would need to change;
- `tidal-parser` would need to change;
- parity cannot be measured;
- runtime weight does not improve meaningfully.

## Decision options

Possible future decisions:

- continue to local-only MusiCNN ONNX parity spike planning;
- continue to `legacy_musicnn` model identity inspection;
- continue to preprocessing and label parity evidence review;
- pause MusiCNN ONNX path and return to Discogs400 label mapping;
- reject official MusiCNN ONNX as a non-matching candidate;
- keep `legacy_musicnn` as the only production path.

These are decision options only. Roadmap 4.22 does not select a production
candidate.

## Recommended decision

Recommended Roadmap 4.22 decision:

- do not start implementation;
- do not add `onnxruntime`;
- do not download model files;
- do not run inference;
- do not change the provider;
- pause the Discogs400 mapping lane;
- continue only documentation/planning for a local-only ONNX parity spike if
  model identity continues to look promising;
- keep `legacy_musicnn` as the production baseline and default provider.

The next useful work is evidence planning, not runtime change.

## Explicit non-goals

Roadmap 4.22 explicitly excludes:

- production classifier code;
- provider implementation;
- provider factory changes;
- default-provider switch;
- shadow execution;
- canary;
- production migration;
- dependency changes;
- model download;
- model files;
- audio artifacts;
- network/download logic;
- inference;
- `/classify` calls;
- Dockerfile changes;
- Docker Compose changes;
- controlled vocabulary changes;
- response shape changes;
- cache semantics changes;
- `tidal-parser` changes;
- commit, tag, push, or release.

## Allowed next steps

Allowed next steps are documentation, planning, and evidence review only:

- document the exact current `legacy_musicnn` model identity questions;
- plan how to inspect label sources without adding full label artifacts;
- plan how to compare preprocessing behavior;
- plan a future local-only `.pb` vs `.onnx` numeric parity spike;
- define acceptance criteria for preserving post-processing and response
  contract;
- document rollback and default-provider preservation requirements.

Any step that requires model files, dependency changes, inference, or provider
wiring needs a separate approval gate.

## Prohibited next steps

The following next steps are prohibited by Roadmap 4.22:

- implementation;
- provider wiring;
- model download;
- dependency changes;
- Docker changes;
- inference;
- default switch;
- shadow or canary execution;
- release work.

## Rollback considerations

Rollback is documentation-only:

- delete this markdown document;
- delete any temporary report created for this work.

No runtime rollback is needed because code, dependency, model, audio, runtime
configuration, Docker, Docker Compose, provider, default-provider, inference,
and `tidal-parser` changes are prohibited by this slice.
