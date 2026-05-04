# Roadmap 4.20 - Essentia Discogs/EffNet / Discogs400 provenance deep dive

Status:

- documentation/research safe-slice;
- candidate-specific provenance deep dive;
- non-production-facing;
- `not_production_decision: true`;
- `approved_for_offline_evaluation: false`;
- `approved_for_repo_inclusion: false`;
- no implementation approved;
- no production candidate selected.

Roadmap 4.20 is research only. It records found references, verified
evidence, missing evidence, blockers, and no-go risks for the Essentia
Discogs/EffNet / Discogs400 candidate family. It does not approve model
download, model inclusion, inference, dependencies, provider implementation,
provider factory wiring, a default provider switch, runtime shadow execution,
canary rollout, or production migration.

## Scope

Roadmap 4.20 is limited to documentation under
`genre-classifier/docs/lightweight/`.

The scope is a candidate-specific provenance deep dive for Essentia
Discogs/EffNet / Discogs400 only. The document records references and review
gaps that would need to be closed before any later offline evaluation decision
could be considered.

This slice does not change production behavior, runtime behavior,
dependencies, Docker files, Docker Compose, provider code, provider factory
wiring, cache semantics, validators, tests, `/classify`, or the production
response shape.

`tidal-parser` is out of scope and remains unchanged.

## Current Roadmap 4 lane status

Roadmap 2 is complete and closed by release `v0.3.0`. Roadmap 3 is complete
and closed by release `v0.4.0`. Roadmap 4.1 through Roadmap 4.19 are complete
and published.

The current production baseline remains unchanged:

- `legacy_musicnn` remains the default provider;
- the production classifier path remains legacy MusiCNN;
- the `/classify` contract is unchanged;
- the response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

Runtime shadow execution remains off by default.

The ONNX lane remains infrastructure-ready but evidence-blocked. Existing ONNX
scaffolding and evidence shapes do not approve a real ONNX model, real model
provenance, label mapping, candidate output, runtime metrics, or production
migration.

The small audio tagging lane remains a research/documentation lane only.
Roadmap 4.19 shortlisted Essentia Discogs/EffNet / Discogs400 as the strongest
target for this documentation-only provenance deep dive, kept `musicnn` as a
reference candidate, and kept YAMNet and PANNs as weak or no-go comparison
candidates.

## Candidate identity

Candidate family:

- Essentia / MTG Discogs-EffNet embedding model plus Genre Discogs400
  classifier head.

Possible exact model identities found:

- `discogs-effnet-bs64-1`
  - role: Discogs-EffNet feature extractor / embedding model;
  - official metadata:
    https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.json
  - official weights reference:
    https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.pb
- `discogs-effnet-bsdynamic-1`
  - role: dynamic batch ONNX variant for the Discogs-EffNet embedding model;
  - official index reference only:
    https://essentia.upf.edu/models/feature-extractors/discogs-effnet/
- `genre_discogs400-discogs-effnet-1`
  - role: Genre Discogs400 classifier head operating on Discogs-EffNet
    embeddings;
  - official metadata:
    https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json
  - official weights reference:
    https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.pb

Model registry / model page:

- Essentia models page:
  https://essentia.upf.edu/models.html
- Feature extractor index:
  https://essentia.upf.edu/models/feature-extractors/discogs-effnet/
- Genre Discogs400 classifier index:
  https://essentia.upf.edu/models/classification-heads/genre_discogs400/
- Replicate demo page, useful only as a secondary demo reference:
  https://replicate.com/mtg/effnet-discogs

Official source / docs:

- Essentia model documentation:
  https://essentia.upf.edu/models.html
- Essentia machine learning documentation:
  https://essentia.upf.edu/machine_learning.html
- Essentia source repository:
  https://github.com/MTG/essentia
- Essentia models repository:
  https://github.com/MTG/essentia-models
- Essentia Replicate demos repository:
  https://github.com/MTG/essentia-replicate-demos

Weights artifact identity, reference only:

- `discogs-effnet-bs64-1.pb`
- `discogs-effnet-bs64-1-savedmodel.zip`
- `discogs-effnet-bsdynamic-1.onnx`
- `genre_discogs400-discogs-effnet-1.pb`

No artifact is approved for local download, repository inclusion, packaging, or
offline evaluation by this document.

## Source references

Found reference:

- The Essentia models page states that the page lists pre-trained models and
  links to weights (`.pb`) and metadata (`.json`) files, with some models also
  available in TensorFlow.js and ONNX formats:
  https://essentia.upf.edu/models.html
- The Discogs-EffNet section describes audio embedding models trained with
  classification and contrastive learning objectives using an in-house dataset
  annotated with Discogs metadata:
  https://essentia.upf.edu/models.html
- The Genre Discogs400 section identifies music style classification by 400
  styles from the Discogs taxonomy:
  https://essentia.upf.edu/models.html
- The `genre_discogs400-discogs-effnet-1.json` metadata file identifies the
  classifier as "Genre Discogs400", type "Music genre classification", version
  `1`, framework `tensorflow`, framework version `2.8.0`, and release date
  `2023-05-04`:
  https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json
- The `discogs-effnet-bs64-1.json` metadata file identifies the embedding model
  as "EffnetDiscogs", type "Music style classification and embeddings",
  version `1`, framework `tensorflow`, framework version `2.8.0`, and release
  date `2022-02-17`:
  https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.json
- The official feature extractor directory exposes metadata and model artifact
  names and sizes:
  https://essentia.upf.edu/models/feature-extractors/discogs-effnet/
- The official Genre Discogs400 classifier directory exposes metadata and model
  artifact names and sizes:
  https://essentia.upf.edu/models/classification-heads/genre_discogs400/
- The Essentia machine learning documentation states that current Essentia
  models are based on TensorFlow and that TensorFlow support is available via
  `essentia-tensorflow`:
  https://essentia.upf.edu/machine_learning.html

Verified evidence:

- The candidate has official Essentia documentation and official metadata JSON
  references.
- The candidate has an official classifier head and an official embedding
  model reference.
- The candidate label vocabulary is present in the official metadata JSON.
- The official docs provide example Essentia prediction code using
  `MonoLoader`, `TensorflowPredictEffnetDiscogs`, and `TensorflowPredict2D`.

Missing evidence:

- No immutable release tag, commit SHA, or registry revision was found for the
  exact official web-hosted artifacts.
- No checksum or cryptographic hash was found in the official index or metadata
  references reviewed here.
- No project-local approved local artifact path exists.
- No service-local runtime benchmark exists.
- No service-local dependency review exists.

## License evidence

Found reference:

- The Essentia models page states that all models created by MTG are licensed
  under CC BY-NC-SA 4.0 and are also available under proprietary license upon
  request:
  https://essentia.upf.edu/models.html
- The `MTG/essentia-models` license file states that the licensing file applies
  to model files with `.pb` extension hosted in that directory and names
  Creative Commons Attribution-NonCommercial-ShareAlike 4.0:
  https://raw.githubusercontent.com/MTG/essentia-models/master/LICENSE
- The Essentia source repository is licensed as AGPL-3.0:
  https://github.com/MTG/essentia
- The Essentia repository `COPYING.txt` contains the GNU Affero General Public
  License Version 3 text:
  https://raw.githubusercontent.com/MTG/essentia/master/COPYING.txt
- The Essentia Replicate demos repository states that its LICENSE covers demo
  source code and that the demos rely on Essentia models distributed under
  their own license:
  https://github.com/MTG/essentia-replicate-demos

Verified evidence:

- The official Essentia model page provides direct license evidence for
  MTG-created models as CC BY-NC-SA 4.0 with proprietary license available on
  request.
- The model license is non-commercial and share-alike. That is a compatibility
  concern for production or redistribution.
- The Essentia runtime/source license is separate from the model weights
  license and is AGPL-3.0 according to the source repository.

License scope notes:

- The Essentia models page appears to discuss MTG-created model artifacts.
- The `MTG/essentia-models` license file explicitly says it applies to `.pb`
  files hosted in that repository/directory. The reviewed candidate files are
  hosted under `essentia.upf.edu/models/`, so this is supporting evidence, not
  a complete per-artifact legal review.
- The AGPL-3.0 evidence applies to Essentia code/runtime, not automatically to
  the model weights.
- The Replicate demo source license is not sufficient evidence for the
  candidate weights.

Redistribution / usage constraints:

- CC BY-NC-SA 4.0 includes attribution, non-commercial, and share-alike terms.
- Proprietary licensing may be available from MTG/UPF, but no project-specific
  proprietary grant is present in this repository.
- Repository inclusion and redistribution remain prohibited unless separate
  explicit approval is obtained.

Compatibility concerns:

- Non-commercial terms are likely incompatible with unrestricted production
  commercial use.
- Share-alike terms may be incompatible with packaging or redistribution goals.
- AGPL-3.0 runtime implications require separate review before adding Essentia
  runtime dependencies to a network service.

Missing license evidence:

- No project-specific legal approval exists.
- No exact license review exists for the candidate pair
  `discogs-effnet-bs64-1.pb` plus
  `genre_discogs400-discogs-effnet-1.pb`.
- No redistribution approval exists.
- No commercial-use approval exists.
- No approved repository inclusion policy exists for these files.

## Weights / artifact evidence

Found artifact references:

| Artifact | Role | Format | Official size reference | Source |
| --- | --- | --- | --- | --- |
| `discogs-effnet-bs64-1.pb` | embedding model | TensorFlow frozen model `.pb` | 18,366,619 bytes | https://essentia.upf.edu/models/feature-extractors/discogs-effnet/ |
| `discogs-effnet-bs64-1-savedmodel.zip` | embedding model | TensorFlow SavedModel zip | 16,775,141 bytes | https://essentia.upf.edu/models/feature-extractors/discogs-effnet/ |
| `discogs-effnet-bsdynamic-1.onnx` | embedding model | ONNX | 18,027,718 bytes | https://essentia.upf.edu/models/feature-extractors/discogs-effnet/ |
| `genre_discogs400-discogs-effnet-1.pb` | classifier head | TensorFlow frozen model `.pb` | 2,057,977 bytes | https://essentia.upf.edu/models/classification-heads/genre_discogs400/ |
| `genre_discogs400-discogs-effnet-1.json` | classifier metadata | JSON | 14,951 bytes | https://essentia.upf.edu/models/classification-heads/genre_discogs400/ |
| `discogs-effnet-bs64-1.json` | embedding metadata | JSON | 14,983 bytes | https://essentia.upf.edu/models/feature-extractors/discogs-effnet/ |

Verified evidence:

- Official directory indexes expose artifact names, timestamps, and byte sizes.
- Official metadata JSON files link to corresponding `.pb` weights.
- The classifier metadata declares model types `frozen_model`, `SavedModel`,
  and `onnx`.
- The embedding metadata declares model types `frozen_model`, `SavedModel`,
  and `onnx`.

Missing evidence:

- No SHA-256, checksum, detached signature, or signed manifest was found.
- No immutable release identifier was found for the exact web-hosted files.
- No local file exists in this repository.
- No local file hash exists.
- No approved local retrieval procedure exists.
- No approved model storage policy exists.

Decision status:

- `approved_for_repo_inclusion: false`
- `approved_for_offline_evaluation: false`
- `approved_for_runtime_use: false`

The ONNX files are references only. Their presence in the official index does
not unblock the ONNX lane and does not approve ONNX runtime use.

## Label vocabulary evidence

Found reference:

- The Genre Discogs400 docs list 400 music style labels grouped under Discogs
  genre families:
  https://essentia.upf.edu/models.html
- The `genre_discogs400-discogs-effnet-1.json` metadata includes a `classes`
  array with 400 labels.
- The `discogs-effnet-bs64-1.json` metadata includes a matching top-400
  Discogs style `classes` array for the embedding model's classification
  objective.

Verified evidence:

- Label count: 400.
- Label format in metadata: `<Discogs genre>---<Discogs style>`.
- Genre families found include `Blues`, `Brass & Military`, `Children's`,
  `Classical`, `Electronic`, `Folk, World, & Country`, `Funk / Soul`,
  `Hip Hop`, `Jazz`, `Latin`, `Non-Music`, `Pop`, `Reggae`, `Rock`, and
  `Stage & Screen`.
- Labels are music-specific in many cases and are more relevant to controlled
  genre mapping than generic AudioSet event labels.
- The vocabulary also includes non-genre or non-music labels, including the
  `Non-Music` family and labels such as audiobook, dialogue, interview,
  promotional, radioplay, religious, spoken word, score, soundtrack, theme,
  novelty, parody, and instrumental.

Mapping feasibility:

- Top-level genres and common styles appear potentially mappable to the
  existing controlled vocabulary.
- Many substyles would require consolidation into broader controlled genres.
- Some labels are ambiguous because the same style term appears under multiple
  families or can be interpreted as genre, style, instrumentation, era, mood,
  or format depending on context.
- Non-music and media-purpose labels require an explicit OOV or reject policy.
- A static label vocabulary review should be the next documentation-only step
  if this candidate continues.

Expected OOV risk:

- Moderate to high without a reviewed mapping artifact.
- OOV risk is concentrated in very specific electronic substyles, regional
  styles, non-music labels, stage/screen labels, and labels that are not clean
  production genres.

Missing evidence:

- No project-local controlled-vocabulary mapping exists.
- No OOV rate estimate exists.
- No duplicate or many-to-one mapping policy exists.
- No major genre shift review exists.
- No reviewed top-N or threshold policy exists.
- No label order hash exists.

## Preprocessing / runtime notes

Found reference:

- Official example prediction code uses:
  - `MonoLoader(filename="audio.wav", sampleRate=16000, resampleQuality=4)`;
  - `TensorflowPredictEffnetDiscogs(graphFilename="discogs-effnet-bs64-1.pb",
    output="PartitionedCall:1")`;
  - `TensorflowPredict2D(graphFilename="genre_discogs400-discogs-effnet-1.pb",
    input="serving_default_model_Placeholder", output="PartitionedCall:0")`.
- The classifier metadata declares input
  `serving_default_model_Placeholder`, type `float`, shape
  `[batch_size, 1280]`.
- The classifier metadata declares output `PartitionedCall:0`, type `float`,
  shape `[batch_size, 400]`, op `Sigmoid`, output purpose `predictions`.
- The embedding metadata declares input `serving_default_melspectrogram`, type
  `float`, shape `[64, 128, 96]`.
- The embedding metadata declares outputs:
  - `PartitionedCall:0`, type `float`, shape `[64, 400]`, op `Sigmoid`;
  - `PartitionedCall:1`, type `float`, shape `[64, 1280]`, op `Flatten`,
    output purpose `embeddings`.
- The metadata declares inference sample rate `16000`.
- The Essentia machine learning docs state that current Essentia models are
  based on TensorFlow and describe `essentia-tensorflow`.

Verified evidence:

- The likely direct runtime path is Essentia with TensorFlow support.
- The classifier head expects embeddings, not raw audio.
- The embedding model expects an Essentia-prepared mel-spectrogram input.
- The candidate is not a simple drop-in replacement for the current production
  path.

CPU-only feasibility evidence:

- Replicate's public demo page states that the demo runs on CPU hardware and
  predictions typically complete within a few seconds:
  https://replicate.com/mtg/effnet-discogs

CPU-only feasibility caveat:

- Replicate demo behavior is secondary evidence. It is not a service-local
  benchmark, not a dependency review, and not approval for this repository.

Missing preprocessing/input/output metadata:

- Full mel-spectrogram preprocessing details are not fully captured in this
  document.
- Windowing, hop size, normalization, segment aggregation, batch handling, and
  score postprocessing need separate review.
- No service-local latency, memory, or cold-start metrics exist.
- No dependency weight review exists for `essentia-tensorflow`,
  TensorFlow, TensorFlow shared libraries, or transitive native packages.

## Dependency / runtime risk

Found reference:

- Essentia source/runtime is AGPL-3.0.
- Essentia with TensorFlow support is documented as a separate
  `essentia-tensorflow` package.
- Building Essentia with TensorFlow support may require TensorFlow and native
  system dependencies according to the official machine learning docs.

Verified evidence:

- Adding Essentia/TensorFlow would be a material dependency and runtime change.
- This documentation slice does not add those dependencies.
- The current production runtime remains legacy MusiCNN.

Risks:

- AGPL-3.0 runtime licensing implications require legal review for a network
  service.
- TensorFlow and Essentia native dependencies may be too heavy for the
  lightweight lane.
- Packaging, build, Docker, and cold-start costs are unknown.
- ONNX artifacts exist as references, but no ONNX runtime path is approved and
  the ONNX lane remains evidence-blocked.
- Runtime downloads would be prohibited; any future evaluation would need an
  approved local-only artifact policy.

Blocker:

- Dependency/runtime weight review is missing.
- CPU-only service-local feasibility evidence is missing.
- Legal approval for runtime and model licenses is missing.

## Mapping feasibility

Preliminary feasibility:

- Candidate labels are stronger than generic audio-event labels because the
  vocabulary is Discogs genre/style oriented.
- A future static mapping could likely map many broad labels to existing
  controlled genres.
- The model emits 400 multilabel style scores, so the future mapping must
  define top-N, thresholding, aggregation, de-duplication, and fallback
  behavior before any candidate output can be compared with `legacy_musicnn`.

Ambiguity examples:

- Some labels are very narrow substyles and would collapse into broad
  production genres.
- Some labels are contextual or media-purpose labels rather than genres.
- Some labels appear under multiple Discogs families or have names that overlap
  with other genre families.

Required future review:

- Static label vocabulary review for all 400 labels.
- Controlled vocabulary mapping artifact.
- OOV policy.
- Non-music label policy.
- Duplicate/many-to-one mapping policy.
- Major genre shift review.
- Baseline-vs-candidate comparison plan against `legacy_musicnn`.

## Evidence classification

### Found

- Official Essentia model documentation.
- Official Discogs-EffNet metadata JSON.
- Official Genre Discogs400 metadata JSON.
- Official directory indexes with artifact names and sizes.
- Official license statement on the Essentia models page.
- Supporting `MTG/essentia-models` license file for model `.pb` files in that
  repository.
- Official Essentia source repository and AGPL-3.0 code license reference.
- Official example code for embedding extraction and classifier prediction.
- Label vocabulary in metadata.
- TensorFlow framework metadata.
- Input/output tensor metadata at a high level.

### Verified

- Candidate identity can be named as
  `discogs-effnet-bs64-1` plus
  `genre_discogs400-discogs-effnet-1`.
- Label count is 400.
- Labels are Discogs genre/style labels.
- The classifier head expects 1280-dimensional embeddings and outputs 400
  sigmoid scores.
- The likely official runtime path is Essentia with TensorFlow support.
- Model license evidence points to CC BY-NC-SA 4.0 for MTG-created models,
  with proprietary licensing available on request.
- Production code, runtime, dependencies, and provider defaults are not changed
  by this document.

### Missing

- Exact approved artifact hash/checksum.
- Immutable release/tag/commit anchor for the exact hosted artifacts.
- Project-approved local artifact.
- Project-approved local retrieval procedure.
- Project-approved license/legal review.
- Redistribution approval.
- Commercial-use approval.
- Static label mapping artifact.
- OOV and non-music label policy.
- Full preprocessing specification.
- Complete input/output metadata review.
- Service-local CPU-only feasibility evidence.
- Dependency/runtime weight review.
- Baseline-vs-candidate comparison evidence.
- Real candidate output.
- Runtime metrics.

### Blocker

- License compatibility is unresolved because CC BY-NC-SA 4.0 is
  non-commercial and share-alike, and no proprietary license grant is present.
- Exact artifact integrity is unresolved because no checksum/hash is present.
- Repository inclusion is blocked because redistribution and approval are
  missing.
- Offline evaluation approval is blocked because artifact identity, license
  review, label mapping, preprocessing, runtime metrics, and dependency review
  are incomplete.
- Production migration is blocked because no implementation, offline evidence,
  comparison evidence, or production approval exists.

### No-go

- Use as production classifier now: no-go.
- Switch default provider from `legacy_musicnn`: no-go.
- Add Essentia/TensorFlow dependencies in this slice: no-go.
- Download or commit model files in this slice: no-go.
- Treat ONNX artifact references as ONNX lane approval: no-go.
- Run real inference or call `/classify`: no-go.
- Approve commercial or redistributed use from current evidence: no-go.

## No-go checklist

Active no-go items:

- `model_download_requested`
- `model_file_in_repo_requested`
- `repo_inclusion_not_approved`
- `approved_for_offline_evaluation_missing`
- `model_hash_missing`
- `immutable_artifact_reference_missing`
- `license_compatibility_unresolved`
- `redistribution_approval_missing`
- `commercial_use_approval_missing`
- `label_mapping_missing`
- `oov_policy_missing`
- `non_music_label_policy_missing`
- `preprocessing_spec_incomplete`
- `input_output_review_incomplete`
- `runtime_metrics_missing`
- `cpu_only_service_evidence_missing`
- `dependency_review_missing`
- `baseline_candidate_comparison_missing`
- `provider_switch_requested_prematurely`
- `shadow_canary_requested_prematurely`
- `production_migration_requested_prematurely`

## Decision options

Available future decision options:

- continue to candidate-specific provenance artifact;
- continue to static label vocabulary review;
- revise/search more evidence;
- pause candidate and review `musicnn` reference lane;
- reject candidate for now;
- keep `legacy_musicnn` as only production path.

Decision option notes:

- `continue to candidate-specific provenance artifact` would require a
  separate documentation-only artifact that records exact source, local
  retrieval policy, license evidence, expected local filename, and hash
  requirements. It would still not download or include model files.
- `continue to static label vocabulary review` is reasonable because the
  official metadata exposes the 400-label vocabulary.
- `revise/search more evidence` is required if reviewers need stronger license,
  checksum, source repository, or preprocessing evidence before even preparing
  a provenance artifact.
- `pause candidate and review musicnn reference lane` remains available if
  Essentia/TensorFlow or CC BY-NC-SA 4.0 risk appears too high.
- `reject candidate for now` is appropriate if non-commercial/share-alike terms,
  AGPL runtime risk, or missing checksums cannot be resolved.
- `keep legacy_musicnn as only production path` remains the current production
  decision regardless of the research option selected.

## Recommended decision

Recommended status: `blocked_for_offline_evaluation`.

Recommended next action:

- continue only with documentation if reviewers accept the current official
  provenance, license, and label references as sufficient for more paper
  review;
- otherwise choose `revise/search more evidence` or `reject candidate for now`.

Recommended documentation-only continuation:

- perform a static label vocabulary review for the 400 Discogs labels;
- prepare a candidate-specific provenance artifact template that remains
  `approved_for_offline_evaluation: false` until exact artifact hash, license
  review, local-only retrieval policy, preprocessing review, and dependency
  review are complete.

Do not start implementation. Do not add dependencies. Do not add models. Do not
run inference. Keep `legacy_musicnn` as the production baseline and the only
production path. Keep the ONNX lane infrastructure-ready but evidence-blocked.

## Explicit non-goals

- no production classifier code;
- no provider implementation;
- no provider factory wiring;
- no default provider switch;
- no shadow execution;
- no canary rollout;
- no production migration;
- no model download;
- no model files in repo;
- no audio artifacts;
- no dependency additions;
- no runtime changes;
- no Dockerfile or Docker Compose changes;
- no validator/test changes;
- no `/classify` contract changes;
- no response shape changes;
- no cache semantics changes;
- no `tidal-parser` changes;
- no tag/release.

## Allowed next steps

Allowed next steps are documentation-only:

- review official Essentia and MTG references more deeply;
- review the full 400-label vocabulary statically;
- draft a candidate-specific provenance artifact template;
- document exact future hash/checksum requirements;
- document license questions for legal review;
- document dependency and runtime review questions;
- compare this candidate's evidence gaps with the `musicnn` reference lane;
- keep all future artifacts under `genre-classifier/docs/lightweight/` unless
  a later roadmap explicitly approves otherwise.

## Prohibited next steps

The following remain prohibited:

- production classifier code;
- provider implementation;
- provider factory wiring;
- default provider change;
- runtime shadow execution;
- canary rollout;
- production migration;
- model download;
- model file inclusion;
- audio fixture inclusion;
- dependency additions, including ONNX, TFLite, sklearn, CLAP, audio tagging,
  Essentia, TensorFlow, or related runtime packages;
- network/download logic in the project;
- real inference;
- `/classify` calls;
- heavy runtime/provider imports;
- Dockerfile changes;
- Docker Compose changes;
- validator changes;
- test changes;
- cache semantics changes;
- `tidal-parser` changes;
- commit, tag, push, or release.

## Rollback considerations

This slice is documentation-only. Rollback is limited to deleting this
Roadmap 4.20 markdown file.

No production code, runtime configuration, provider defaults, dependencies,
Docker files, Docker Compose files, validators, tests, model files, audio
artifacts, cache behavior, `/classify` contract, response shape, or
`tidal-parser` files should need rollback because none are changed by this
slice.

The temporary review report created at the monorepo root for this task is not a
project artifact. It must remain unstaged, must not be committed, and should be
deleted before any future commit.
