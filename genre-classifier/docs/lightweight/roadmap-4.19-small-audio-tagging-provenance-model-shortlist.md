# Roadmap 4.19 — Small audio tagging provenance and model shortlist research

## Status

- documentation/research safe-slice
- non-production-facing
- `not_production_decision: true`
- no implementation approved
- no production candidate selected
- no provider, factory wiring, shadow, canary, rollout, or migration approved

Roadmap 4.19 is research only. It does not approve real inference, model
downloads, dependency additions, provider implementation, provider factory
wiring, a default provider switch, runtime shadow execution, canary rollout, or
production migration.

## Context

Roadmap 4.18 opened the small audio tagging lane as a research-only direction
after the ONNX lane reached an evidence-blocked state. Roadmap 4.18 defined the
small audio tagging lane and its evidence requirements, but it did not choose a
model family or approve implementation.

The current production baseline remains unchanged:

- `legacy_musicnn` remains the default provider;
- the production classifier path remains legacy MusiCNN;
- the `/classify` contract is unchanged;
- the response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

The ONNX lane remains infrastructure-ready but evidence-blocked. Existing ONNX
scaffolding and evidence shapes do not approve a real ONNX model, real model
provenance, label mapping, candidate output, runtime metrics, or production
migration.

`tidal-parser` is out of scope and remains unchanged.

## Scope

Roadmap 4.19 is limited to documentation and research under
`genre-classifier/docs/lightweight/`. It creates a small shortlist of possible
small audio tagging candidate families for future evidence review.

This slice does not change production behavior, runtime behavior, dependencies,
Docker files, provider code, provider factory wiring, cache semantics,
validators, tests, `/classify`, or the production response shape.

## Why This Step Exists

Roadmap 4.18 established that small audio tagging may be a useful research lane,
but the lane still needs provenance discipline before any candidate can be
evaluated. The project needs a short, reviewable set of candidate families so
future work can focus on evidence instead of broad model search.

This step exists to answer four research questions:

- Which small audio tagging families are close enough to music genre
  classification to be worth future evidence work?
- Which candidates have public source, label vocabulary, license, and weights
  evidence that could plausibly support a later review?
- Which candidates are weak or no-go because their labels are generic audio
  events, their dependencies are too heavy, or their provenance is incomplete?
- What should be the next documentation-only step before any model download,
  dependency addition, or provider implementation is discussed?

No candidate below is production-ready. No candidate below is selected for
implementation.

## Candidate Search Criteria

A future candidate must be reviewed against these criteria before any
implementation can be considered:

- stable source reference for code, model card, paper, registry page, or
  project documentation;
- clear license evidence for code and, separately where applicable, weights;
- clear weights provenance, including source, version, release, registry
  revision, or future immutable reference;
- explicit raw label vocabulary and label source;
- music genre or music style relevance;
- feasible mapping to the existing controlled genre vocabulary;
- local-only feasibility with no runtime network access;
- CPU-only feasibility;
- manageable dependency surface for a lightweight lane;
- reproducible preprocessing requirements;
- offline evaluation compatibility against `legacy_musicnn`;
- no `/classify` contract or response shape change;
- no model or audio artifact required in this documentation slice;
- clear no-go risks.

Unclear license, unclear weights provenance, missing label vocabulary, weak
music genre relevance, runtime download requirements, or a poor controlled
vocabulary mapping should keep a candidate blocked.

## Shortlisted Candidates / Model Families

### Candidate: musicnn / Musically Motivated CNN Audio Tagging Family

- Source: `jordipons/musicnn` GitHub project and the ISMIR 2019 musicnn paper
  page from MTG-UPF:
  - https://github.com/jordipons/musicnn
  - https://www.mtg.upf.edu/node/3985
- Model type: pre-trained convolutional neural networks for music audio
  tagging, including musically motivated CNN and VGG-like baselines.
- License status: public repository indicates ISC license for the code. Weight
  redistribution and production compatibility must still be verified for the
  exact artifact selected in any future review.
- Weights/provenance status: public project describes pre-trained models, but
  this roadmap does not review an exact weight file, checksum, package version,
  or immutable artifact. Blocked until exact local candidate provenance exists.
- Label vocabulary status: music tagging labels are expected to be more
  music-relevant than generic AudioSet labels, but the exact label list must be
  extracted from a reviewed version before mapping work.
- Music genre relevance: strong relative fit because the family is designed for
  music audio tagging.
- Mapping feasibility: potentially feasible, but not approved. Mapping depends
  on the exact raw label vocabulary and how many tags map cleanly to the
  existing controlled genre vocabulary.
- Runtime/dependency notes: likely TensorFlow-era dependency assumptions and
  audio preprocessing requirements need review. This may overlap with the
  existing legacy MusiCNN baseline rather than provide a smaller production
  path.
- CPU-only feasibility: plausible for offline research, but not evidenced here
  with runtime metrics.
- Local-only feasibility: plausible if exact weights are acquired and stored
  under an approved local artifact policy, but no download or local model file
  is approved by this document.
- Evidence gaps: exact model identity, exact weights source, checksum, package
  version, label list, preprocessing contract, license review for weights,
  dependency review, CPU metrics, and baseline comparison.
- No-go risks: may not materially reduce dependency weight compared with the
  legacy path; provenance may be too similar to the current baseline to justify
  a new lane; exact labels may not map cleanly enough.
- Preliminary recommendation: keep as a reference candidate and provenance
  baseline, but do not select as the default next implementation target.

### Candidate: Essentia Discogs/EffNet / Discogs400 Style Tagging Family

- Source: Essentia model documentation for Discogs-EffNet and Genre
  Discogs400:
  - https://essentia.upf.edu/documentation/models.html
  - https://essentia.upf.edu/models.html
- Model type: EfficientNet-style music embedding and classifier models trained
  around Discogs metadata, including a genre/style classifier targeting
  Discogs400 style labels.
- License status: code/model license and weights redistribution terms need
  explicit review from the exact source and artifact selected. Do not assume
  compatibility from documentation alone.
- Weights/provenance status: public documentation references weights and
  metadata, but this roadmap does not review exact files, hashes, release
  identifiers, or redistribution terms. Blocked until a concrete artifact is
  reviewed.
- Label vocabulary status: promising because Discogs styles are music-specific
  and publicly documented as a genre/style taxonomy. Exact model metadata must
  be reviewed before mapping.
- Music genre relevance: strong relative fit because the family targets music
  genre/style labels rather than generic sound events.
- Mapping feasibility: potentially high for top-level genres and common styles,
  but still requires an explicit controlled-vocabulary mapping artifact, OOV
  policy, duplicate handling, and major genre shift review.
- Runtime/dependency notes: likely requires Essentia and TensorFlow graph
  execution paths. Dependency weight and packaging risk may be significant for a
  lightweight service.
- CPU-only feasibility: plausible for offline research according to public demo
  patterns, but service-local CPU metrics are missing and not approved here.
- Local-only feasibility: plausible if weights and metadata can be obtained
  under approved provenance and stored outside this documentation slice. Runtime
  downloads are not acceptable.
- Evidence gaps: exact license for selected weights, redistribution terms,
  exact artifact identity, checksum, full label vocabulary, preprocessing
  contract, dependency review, CPU latency/memory metrics, and comparison
  against `legacy_musicnn`.
- No-go risks: dependency surface may be too heavy; Discogs style labels may
  overfit to metadata taxonomy instead of the existing controlled vocabulary;
  license or redistribution terms may block use.
- Preliminary recommendation: strongest research candidate for the next
  documentation-only provenance pass, but blocked until exact artifact,
  license, and label evidence are reviewed.

### Candidate: YAMNet / AudioSet Event Tagging Family

- Source: TensorFlow Hub YAMNet tutorial and TensorFlow Model Garden YAMNet
  documentation:
  - https://www.tensorflow.org/hub/tutorials/yamnet
  - https://github.com/tensorflow/models/blob/master/research/audioset/yamnet/README.md
- Model type: MobileNetV1-based audio event tagging model trained on AudioSet
  classes.
- License status: TensorFlow documentation and code samples indicate Apache 2.0
  for code samples, but exact model weights/license and redistribution status
  must be reviewed from the selected model source before use.
- Weights/provenance status: public TensorFlow Hub source exists, but this
  roadmap does not review an exact model revision, downloaded artifact, hash, or
  local storage policy.
- Label vocabulary status: known generic AudioSet event labels, not a music
  genre vocabulary.
- Music genre relevance: weak. Labels can identify broad events such as music
  or instruments, but they are not designed to classify controlled music genres.
- Mapping feasibility: low. A small subset may map to broad musical concepts,
  but most labels are non-music events or too generic for the existing genre
  vocabulary.
- Runtime/dependency notes: likely TensorFlow/TensorFlow Hub dependency surface
  if used directly; TFLite variants may exist but would require separate
  provenance, preprocessing, and runtime review.
- CPU-only feasibility: plausible for small inputs in general, but no
  service-local metrics exist here.
- Local-only feasibility: possible only after an approved local artifact is
  reviewed. Runtime TensorFlow Hub downloads are not acceptable.
- Evidence gaps: exact model revision, license/weights review, local artifact
  hash, label mapping usefulness, dependency review, CPU metrics, and genre
  quality comparison.
- No-go risks: label mismatch is likely decisive; model may classify audio
  events rather than music genres; dependency weight may not support the
  lightweight goal.
- Preliminary recommendation: treat as a weak/no-go comparison candidate unless
  a future document needs a generic audio-event baseline.

### Candidate: PANNs / AudioSet Tagging CNN Family

- Source: `qiuqiangkong/audioset_tagging_cnn` GitHub project, PANNs paper
  references, and Zenodo pre-trained model record:
  - https://github.com/qiuqiangkong/audioset_tagging_cnn
  - https://huggingface.co/papers/1912.10211
  - https://zenodo.org/records/3576403
- Model type: PyTorch convolutional audio tagging family trained on AudioSet,
  including CNN variants such as Cnn10 and Cnn14.
- License status: public repository includes an MIT license file for code.
  Exact weights license, redistribution status, and production compatibility
  must be reviewed separately for the selected Zenodo artifact.
- Weights/provenance status: public pre-trained model records exist, but files
  may be large and this roadmap does not review any exact artifact, checksum, or
  local copy.
- Label vocabulary status: AudioSet event labels, not a music genre vocabulary.
- Music genre relevance: weak to moderate. The family can detect broad audio
  events and music-related tags, but it is not primarily a controlled music
  genre classifier.
- Mapping feasibility: low for production genre classification. Some
  music-related AudioSet labels may map to broad concepts, but coverage is
  likely sparse and OOV risk is high.
- Runtime/dependency notes: PyTorch dependency surface and model size may be
  large for this service. Public model archives include large checkpoint files,
  which conflicts with the small candidate goal unless a much smaller reviewed
  variant is identified later.
- CPU-only feasibility: possible for some CNN variants, but not evidenced here;
  latency and memory may be unacceptable.
- Local-only feasibility: possible only with an approved local artifact and no
  runtime downloads. No model download is approved.
- Evidence gaps: selected checkpoint identity, weights license, checksum, full
  label list, preprocessing contract, CPU metrics, dependency impact, OOV rate,
  and baseline comparison.
- No-go risks: generic AudioSet labels, large weights, PyTorch dependency
  surface, and poor controlled-vocabulary mapping may make this unsuitable.
- Preliminary recommendation: keep as weak/no-go comparison evidence only; do
  not prioritize for implementation.

## Comparison Table

| Candidate family | Music relevance | Label mapping outlook | Provenance outlook | Runtime/dependency outlook | CPU/local outlook | Preliminary recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| musicnn / musically motivated CNN | Strong | Potentially feasible, unreviewed | Public code and paper, exact weights still blocked | TensorFlow-era stack may not reduce weight | Plausible but unevidenced | Reference candidate; do not select yet |
| Essentia Discogs/EffNet / Discogs400 | Strong | Potentially strongest, unreviewed | Public docs mention weights/metadata, exact license blocked | Essentia/TensorFlow graph stack may be heavy | Plausible but unevidenced | Best next provenance research target |
| YAMNet / AudioSet | Weak | Low because labels are generic events | Public TF source exists, exact artifact still blocked | TensorFlow/TFLite review required | Plausible but unevidenced | Weak/no-go comparison candidate |
| PANNs / AudioSet CNNs | Weak to moderate | Low because labels are generic events | Public code and Zenodo records, exact weights blocked | PyTorch and large checkpoints are high risk | Possible but unevidenced | Weak/no-go comparison candidate |

## Decision Options

Available decisions after this shortlist are:

- continue documentation-only provenance research for Essentia
  Discogs/EffNet / Discogs400;
- continue documentation-only provenance research for musicnn as a reference
  candidate;
- document YAMNet or PANNs as rejected or weak generic-event baselines;
- pause the small audio tagging lane until stronger public provenance appears;
- keep ONNX blocked and do not reopen it without real approved model evidence;
- keep `legacy_musicnn` as the only production classifier path.

No decision option in Roadmap 4.19 approves implementation.

## Recommended Default Decision

The recommended default decision is:

- keep `legacy_musicnn` as the production baseline and default provider;
- keep the ONNX lane infrastructure-ready but evidence-blocked;
- do not select a production candidate;
- do not approve implementation;
- use Essentia Discogs/EffNet / Discogs400 as the first candidate for a future
  documentation-only provenance deep dive because its label space appears most
  music genre/style relevant;
- keep musicnn as a reference candidate because it is close to the current
  domain and baseline;
- treat YAMNet and PANNs as likely weak/no-go comparison candidates because
  their AudioSet labels are generic audio events.

The next step should be a documentation-only provenance artifact for one
candidate, not model download or inference.

## Explicit Non-Goals

Roadmap 4.19 does not include:

- production classifier code;
- provider implementation;
- provider factory wiring;
- default provider switch;
- shadow execution;
- canary rollout;
- production migration;
- runtime changes;
- Dockerfile changes;
- Docker Compose changes;
- dependency changes;
- requirements, pyproject, or lockfile changes;
- validator changes;
- test changes;
- model files;
- downloaded files;
- audio artifacts;
- copyrighted fixtures;
- network or download logic;
- inference;
- `/classify` calls;
- `/classify` contract changes;
- response shape changes;
- cache semantics changes;
- `tidal-parser` changes;
- tag, release, commit, or push work.

## Allowed Next Steps

Allowed next steps are limited to documentation and research:

- create a candidate-specific provenance checklist for Essentia
  Discogs/EffNet / Discogs400;
- create a candidate-specific provenance checklist for musicnn as a reference
  candidate;
- record exact source URLs, model registry pages, metadata pages, license
  evidence, and label vocabulary references;
- draft a future label mapping plan using static label lists only after they
  are reviewed;
- define what a later offline evidence package would need before any inference;
- keep ONNX blocked until real approved evidence exists.

## Prohibited Next Steps

The following are prohibited by Roadmap 4.19:

- adding dependencies;
- adding model files;
- downloading models;
- adding audio fixtures;
- adding network/download logic;
- importing heavy runtime/provider modules for research;
- implementing providers;
- wiring provider factory;
- changing the default provider;
- enabling shadow execution;
- planning canary rollout as an approved path;
- running inference;
- calling `/classify`;
- changing runtime, Docker, Docker Compose, tests, validators, cache semantics,
  or dependencies;
- touching `tidal-parser`;
- creating a tag, release, commit, or push.

## Rollback Considerations

Rollback is documentation-only. Remove or edit this Roadmap 4.19 document if
the shortlist is superseded or if a candidate's source, license, weights, or
label evidence changes.

No runtime rollback is required. No dependency rollback is required. No Docker
rollback is required. No provider rollback is required. No cache or contract
rollback is required. No `tidal-parser` rollback is required.
