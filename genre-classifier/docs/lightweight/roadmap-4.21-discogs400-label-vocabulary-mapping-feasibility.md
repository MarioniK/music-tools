# Roadmap 4.21 - Discogs400 label vocabulary mapping feasibility

Status:

- documentation/research safe-slice;
- candidate-specific static label vocabulary review;
- mapping feasibility review only;
- non-production-facing;
- `not_production_decision: true`;
- no implementation approved;
- no production candidate selected;
- `approved_for_implementation: false`;
- `approved_for_offline_evaluation: false`;
- `approved_for_repo_label_artifact: false`;
- `approved_for_model_download: false`;
- `approved_for_dependency_changes: false`;
- `approved_for_provider_implementation: false`;
- `approved_for_provider_factory_wiring: false`;
- `approved_for_default_provider_switch: false`;
- `approved_for_shadow_execution: false`;
- `approved_for_canary_rollout: false`;
- `approved_for_production_migration: false`;

Roadmap 4.21 is research only. It records static label vocabulary and mapping
feasibility evidence for the Essentia Discogs/EffNet / Discogs400 candidate
lane after Roadmap 4.20. It does not approve a model download, dependency
change, full label artifact, label mapping, provider implementation, provider
factory wiring, default provider switch, shadow execution, canary rollout, or
production migration.

## Scope

Roadmap 4.21 is limited to this documentation file under
`genre-classifier/docs/lightweight/`.

The scope is a static review of the Discogs400 candidate label vocabulary and
the feasibility of a future mapping into the current project controlled
vocabulary. This review may cite official sources and the Roadmap 4.20
provenance deep dive, but it does not add a local label list, JSON/CSV/YAML
artifact, model file, audio file, script, test, validator, dependency, or
runtime code.

The current production baseline remains unchanged:

- `legacy_musicnn` remains the default provider;
- the production classifier path remains legacy MusiCNN;
- the `/classify` contract is unchanged;
- the response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

Runtime shadow execution remains disabled. No canary rollout or production
migration is approved. `tidal-parser` is out of scope and remains unchanged.

## Current candidate status

Candidate family:

- Essentia / MTG Discogs-EffNet embedding model plus Genre Discogs400
  classifier head.

Candidate identity carried forward from Roadmap 4.20:

- `discogs-effnet-bs64-1`
  - role: Discogs-EffNet feature extractor / embedding model;
  - official metadata:
    https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.json
- `genre_discogs400-discogs-effnet-1`
  - role: Genre Discogs400 classifier head operating on Discogs-EffNet
    embeddings;
  - official metadata:
    https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json

Roadmap 4.20 kept Essentia Discogs/EffNet / Discogs400 as a promising but
blocked research candidate. This Roadmap 4.21 review narrows the review to
static label vocabulary and mapping feasibility only.

Current status: `blocked_for_offline_evaluation`.

The ONNX lane remains infrastructure-ready but evidence-blocked. The small
audio tagging lane remains research-only. `legacy_musicnn` remains the only
production path.

## Source / label vocabulary evidence

Found reference:

- The Essentia models page lists pre-trained models, model weights, metadata
  files, example snippets, license notes, and the Genre Discogs400 classifier:
  https://essentia.upf.edu/models.html
- The Essentia models page describes Discogs-EffNet as trained with a
  multi-label classification objective targeting 400 Discogs styles:
  https://essentia.upf.edu/models.html
- The Genre Discogs400 section describes music style classification by 400
  styles from the Discogs taxonomy:
  https://essentia.upf.edu/models.html
- The official Genre Discogs400 metadata JSON contains a `classes` array,
  classifier head link, version, release date, framework metadata, output shape
  `[batch_size, 400]`, and Discogs-4M dataset notes:
  https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json
- Roadmap 4.20 records the candidate provenance, license, artifact, label, and
  runtime evidence already reviewed in this repository:
  `docs/lightweight/roadmap-4.20-essentia-discogs-effnet-provenance-deep-dive.md`

Verified evidence:

- Exact label count is known from the official metadata and output shape: 400.
- The official metadata exposes the label vocabulary in a `classes` array.
- The label format is `<Discogs genre>---<Discogs style>`.
- The label vocabulary is tied to a classifier head whose output shape is
  `[batch_size, 400]`, so label ordering must be treated as classifier-head
  specific.
- The official metadata identifies the classifier head as version `1`, release
  date `2023-05-04`, framework `tensorflow`, and framework version `2.8.0`.
- The official documentation and metadata are sufficient to justify a
  documentation-only feasibility review.

Missing evidence:

- No project-approved local label artifact exists.
- No approved project mapping exists.
- No hash of the exact `classes` array exists in this repository.
- No checksum, detached signature, signed manifest, or immutable registry
  revision was found for the exact hosted label metadata.
- No proof exists that the hosted metadata cannot change while retaining the
  same URL.
- No project-approved license/legal review exists for using the labels, model
  metadata, or model weights in production.
- No baseline-vs-candidate comparison exists against `legacy_musicnn`.
- No OOV rate, ambiguous-label rate, ignored-label rate, or major genre shift
  estimate exists.

Blocker:

- A future mapping artifact is blocked until the exact label source, label
  ordering, integrity evidence, license/provenance review, and artifact policy
  are approved.

No-go:

- Treating the official metadata URL alone as an approved project label
  artifact is no-go.
- Creating a complete local Discogs400 label artifact in Roadmap 4.21 is no-go.
- Creating an approved production mapping in Roadmap 4.21 is no-go.
- Downloading model files or running inference to validate labels in Roadmap
  4.21 is no-go.

Label evidence is enough for a future mapping artifact template only if
reviewers accept the official metadata as a sufficient source reference for
paper design. It is not enough to create an approved mapping artifact or
production-ready label package.

## Evidence classification

Found reference:

- Official Essentia models page.
- Official Genre Discogs400 metadata JSON.
- Official Discogs-EffNet metadata JSON.
- Roadmap 4.20 project-local provenance deep dive.

Verified evidence:

- Discogs400 is documented as a 400-label music style classifier.
- The metadata has a 400-item `classes` array.
- The classifier output is 400 sigmoid scores.
- Labels follow Discogs genre/style semantics rather than the current project
  controlled vocabulary.
- Many labels are music-specific and plausibly mappable at a broad level.
- Some labels are non-genre, contextual, regional, era, media-purpose, or
  ambiguous labels and require explicit policy.

Missing evidence:

- Approved label order hash.
- Immutable source anchor.
- Approved local label artifact policy.
- Approved project mapping.
- OOV policy.
- Ambiguous-label policy.
- Ignored-label policy.
- Controlled vocabulary extension policy.
- Baseline-vs-candidate comparison.
- License/provenance approval sufficient for production or redistribution.

Blocker:

- Mapping cannot be approved while label integrity, license/provenance,
  ordering stability, and mapping policy are incomplete.

No-go:

- Production use now: no-go.
- Offline evaluation now: no-go.
- Provider implementation now: no-go.
- Full repo label artifact now: no-go.
- Controlled vocabulary change now: no-go.

## Label category taxonomy

The Discogs400 vocabulary should be classified conceptually before any future
mapping artifact is considered. This taxonomy is for review structure only and
is not an approved mapping.

Conceptual label types:

- genre: broad music categories that may map directly to current controlled
  genres, such as broad rock, jazz, pop, hip hop, electronic, blues, country,
  folk, funk, soul, reggae, and metal concepts;
- style: subgenre or stylistic labels that may collapse into broader
  controlled genres, such as house, techno, punk, doom metal, synth-pop, trip
  hop, shoegaze, or bluegrass;
- mood/context: labels whose main meaning may be atmosphere, usage, or
  listening context rather than genre, such as ambient-like, lounge-like,
  novelty, parody, or soundtrack-adjacent terms;
- format/media: labels that describe media form or release purpose rather than
  genre, such as audiobook, interview, field recording, promotional, radioplay,
  score, soundtrack, or theme;
- era/decade: labels tied to period or scene history rather than clean project
  genres, such as old style forms, revival labels, or period-specific pop/rock
  scenes;
- region/culture: labels tied to geography, culture, language, or scene, such
  as regional folk, Latin, Nordic, Pacific, Bollywood, K-pop, J-pop, or
  country-specific styles;
- non-genre: labels from `Non-Music` or labels that describe speech, comedy,
  education, politics, religion, or spoken content;
- ambiguous: labels that may be genre, style, instrumentation, mood, scene, or
  media purpose depending on context;
- unmappable: labels that cannot safely map into the current controlled
  vocabulary without losing meaning or creating misleading production output.

This taxonomy suggests that a future mapping would need both category
classification and output policy. A one-column label-to-genre table would be
too weak without reasons, status, and review ownership.

## Mapping feasibility model

A future mapping model should use explicit outcomes for every candidate label.
Roadmap 4.21 does not create that mapping.

Mapping outcomes:

- direct mapping: the Discogs400 label cleanly maps to one existing controlled
  genre with low semantic loss;
- alias mapping: the label can normalize through an existing or future alias to
  one existing controlled genre;
- ignored label: the label should not contribute to `genres` because it is
  non-genre, media-purpose, contextual, too narrow, or policy-excluded;
- ambiguous label: the label requires human review because several controlled
  genres or policies could apply;
- unmapped label: the label has no acceptable current controlled-vocabulary
  target;
- needs controlled vocabulary extension: the label may be valuable, but a new
  controlled genre would be required before it can be represented safely.

Required fields for a future mapping artifact template:

- raw label;
- raw Discogs family;
- raw Discogs style;
- conceptual label type;
- mapping outcome;
- controlled target, if any;
- confidence;
- reason;
- reviewer status;
- ignored/unmapped policy reason;
- source metadata URL;
- source label order hash requirement;
- explicit `approved_for_production: false` until separately reviewed.

## Limited illustrative examples

These examples are illustrative only. They are not an approved mapping, not a
complete review, not a label artifact, and not permission to implement mapping
logic.

Illustrative direct or alias candidates:

- `Rock---Hard Rock` could plausibly map to an existing broad `hard rock`
  controlled genre, pending review.
- `Electronic---House` could plausibly map to existing `house`, pending
  review.
- `Hip Hop---Trap` could plausibly map upward to existing `hip hop`, pending
  review.

Illustrative ignored or non-genre candidates:

- `Non-Music---Interview` should likely be ignored or rejected from genre
  output, pending policy.
- `Non-Music---Audiobook` should likely be ignored or rejected from genre
  output, pending policy.
- `Stage & Screen---Soundtrack` may describe media context rather than final
  genre output, pending policy.

Illustrative ambiguous or extension candidates:

- `Electronic---Industrial` may overlap with electronic, rock, and industrial
  semantics, pending review.
- `Rock---Parody` mixes genre family and content intent, pending review.
- `Folk, World, & Country---Nordic` may require region/culture policy rather
  than a direct controlled genre.

No example above is approved for a production response, offline evaluation
output, provider implementation, or controlled vocabulary change.

## OOV and ambiguous-label risk

OOV risk is expected to be moderate to high until every Discogs400 label is
reviewed against the current controlled vocabulary.

Risk areas:

- long-tail labels may have no current controlled target;
- country/region/culture labels may collapse into overly broad genres or lose
  important meaning;
- format/media labels may leak audiobook, interview, soundtrack, score, or
  similar descriptors into `genres`;
- era/decade labels may imply historical scenes rather than production genres;
- mood/context labels may describe atmosphere or usage rather than genre;
- duplicate and near-duplicate labels may map many-to-one and inflate broad
  genre scores;
- style-vs-genre ambiguity may make narrow labels look more precise than the
  current output contract supports;
- Discogs genre/style semantics may not align with the current project
  controlled vocabulary;
- non-music labels may produce valid model scores that are invalid final
  genres;
- baseline parity risk remains unknown because no comparison exists against
  `legacy_musicnn`.

Ambiguous-label risk requires future human review. Automatic normalization
alone is not enough because the same style string can carry different meaning
under different Discogs families.

## Controlled vocabulary compatibility

The current controlled vocabulary must not change in Roadmap 4.21.

Project-local context:

- current controlled vocabulary is implemented in
  `app/genres/vocabulary.py`;
- current final response compatibility also depends on normalization and
  filtering behavior in the existing production path;
- this document does not modify either.

Compatibility status:

- no approved mapping is created;
- no controlled vocabulary extension is approved;
- ignored labels require future policy;
- ambiguous labels require future review;
- candidate output requires a future evidence package;
- baseline-vs-candidate comparison against `legacy_musicnn` is required before
  any production decision;
- the `/classify` response must remain `ok`, `message`, `genres`, and
  `genres_pretty`.

Feasibility assessment:

- broad genre families appear partially compatible with the existing
  vocabulary;
- many styles would require aliasing or many-to-one collapse;
- several labels would require ignore/reject policy;
- several useful labels may require controlled vocabulary extension, but no
  extension is approved here;
- compatibility cannot be determined from label names alone because output
  thresholds, score aggregation, and baseline comparison are missing.

## Major genre shift risk

Discogs400 is a genre/style classifier trained around Discogs metadata, while
the current production path is legacy MusiCNN. Even if many labels map to the
same broad controlled vocabulary, the candidate may shift output behavior.

Major genre shift risks:

- high-scoring specific styles may collapse into a small number of broad genres
  and change top-N ordering;
- Discogs taxonomy families may bias results toward metadata styles rather than
  the current production behavior;
- region/culture labels may introduce outputs that legacy MusiCNN did not
  produce;
- electronic and rock substyle density may overweight those families after
  many-to-one mapping;
- non-music or stage/screen labels may suppress or distort music genre output
  if not ignored correctly;
- score calibration is unknown because classifier scores are sigmoid style
  scores, not current production probabilities;
- baseline parity risk cannot be estimated without offline comparison evidence.

Major genre shift review remains required before any production decision.

## Non-genre leakage risk

Non-genre leakage is a blocker for direct production use. The official
Discogs400 vocabulary includes labels that are not clean final music genres.

Leakage categories:

- `Non-Music` labels;
- spoken, interview, audiobook, education, comedy, political, religious, and
  promotional content labels;
- stage/screen labels such as score, soundtrack, theme, and musical;
- format or media-purpose labels;
- mood/context labels;
- labels that describe novelty, parody, instrumentation, or scene context more
  than genre.

Required future policy:

- reject or ignore non-genre labels before `genres` output;
- keep ignored-label decisions auditable;
- prevent non-genre labels from appearing in `genres_pretty`;
- verify response shape remains unchanged;
- compare ignored-label behavior against `legacy_musicnn` outputs.

## Future evidence required

Future evidence required before even a documentation-only mapping artifact
could be considered complete:

- exact official metadata URL and retrieval date;
- approved immutable source anchor or accepted alternative;
- exact count check for 400 labels;
- exact label order hash requirement;
- approved source/license/provenance note for metadata and labels;
- clear statement that label ordering is tied to the exact classifier head;
- explicit artifact policy for whether a local label list may exist;
- conceptual type review for every label;
- mapping outcome review for every label;
- OOV, ambiguous, ignored, and extension counts;
- duplicate and near-duplicate policy;
- many-to-one aggregation policy;
- score threshold and top-N policy for offline evidence only;
- non-genre leakage policy;
- major genre shift review plan;
- baseline-vs-candidate comparison plan against `legacy_musicnn`;
- explicit no-go gates carried into any future artifact.

Future evidence required before offline evaluation:

- approved model provenance;
- approved label artifact or approved retrieval policy;
- approved mapping artifact;
- approved license/legal review;
- approved local-only model artifact path and hash;
- dependency/runtime review;
- preprocessing review;
- service-local CPU metrics plan;
- separate approval for offline inference.

## No-go checklist

Active no-go items:

- `approved_mapping_missing`
- `approved_label_artifact_missing`
- `approved_for_repo_label_artifact_false`
- `approved_for_offline_evaluation_false`
- `label_order_hash_missing`
- `immutable_label_reference_missing`
- `license_provenance_unresolved`
- `oov_policy_missing`
- `ambiguous_label_policy_missing`
- `ignored_label_policy_missing`
- `controlled_vocabulary_extension_not_approved`
- `non_genre_leakage_policy_missing`
- `major_genre_shift_unresolved`
- `baseline_candidate_comparison_missing`
- `model_download_not_approved`
- `dependency_changes_not_approved`
- `provider_implementation_not_approved`
- `provider_factory_wiring_not_approved`
- `default_provider_switch_not_approved`
- `shadow_execution_not_approved`
- `canary_rollout_not_approved`
- `production_migration_not_approved`

These no-go items prevent implementation, runtime changes, model download,
full label artifact creation, offline evaluation, shadow execution, canary
rollout, and production migration.

## Decision options

Available future decision options:

1. Continue to documentation-only candidate-specific label mapping artifact
   template.
2. Continue to deeper label vocabulary evidence search.
3. Block candidate until exact label file/reference is approved.
4. Pause Essentia Discogs/EffNet and review `musicnn` reference candidate.
5. Reject candidate for now.
6. Keep `legacy_musicnn` as only production path.

Decision option notes:

- Option 1 is only reasonable if reviewers accept the static label source
  evidence as sufficiently clear for a template that remains unapproved for
  production and offline evaluation.
- Option 2 is reasonable if label ordering, hash, source stability, or license
  evidence remains too weak even for a template.
- Option 3 is required if the project needs an exact approved label file or
  immutable source before any mapping design.
- Option 4 remains available if Essentia/TensorFlow, Discogs taxonomy, or
  license risk makes the candidate too heavy.
- Option 5 is appropriate if the candidate cannot satisfy label integrity,
  license, mapping, or dependency requirements.
- Option 6 remains true regardless of any research continuation.

## Recommended decision

Recommended status: `blocked_for_implementation`.

Recommended decision:

- Continue only if static label vocabulary evidence is sufficiently clear.
- Otherwise block or revise.
- Do not create approved mapping.
- Do not start implementation.
- Do not add dependencies.
- Do not add models.
- Do not run inference.
- Keep `legacy_musicnn` as production baseline.
- Keep Essentia Discogs/EffNet / Discogs400 as promising but blocked research
  candidate.

The most conservative next action is deeper label vocabulary evidence search
or a documentation-only mapping artifact template that remains explicitly
unapproved.

## Explicit non-goals

Roadmap 4.21 does not:

- choose a production candidate;
- create approved label mapping;
- approve label vocabulary as production-ready;
- add full label vocabulary artifact;
- add model files;
- download models;
- add dependencies;
- add provider implementation;
- wire provider factory;
- change default provider;
- enable shadow execution;
- start canary rollout;
- start production migration;
- run inference;
- call `/classify`;
- change `/classify` contract;
- change response shape;
- change cache semantics;
- change controlled vocabulary;
- change runtime;
- change Dockerfile;
- change Docker Compose;
- touch `tidal-parser`;
- create tag/release.

## Allowed next steps

Allowed future next steps:

- documentation-only candidate-specific label mapping artifact template, if
  evidence is sufficient;
- deeper label vocabulary evidence search;
- future label artifact requirements definition;
- future offline evidence package requirements definition;
- keep `legacy_musicnn` as baseline.

Allowed next steps must remain documentation-only unless separately approved in
a later roadmap slice.

## Prohibited next steps

Roadmap 4.21 prohibits:

- adding dependencies;
- adding model files;
- downloading model files;
- adding full label vocabulary artifact;
- adding network/download logic;
- adding audio artifacts;
- importing heavy runtime/provider modules;
- implementing providers;
- wiring provider factory;
- changing default provider;
- enabling shadow execution;
- canary rollout;
- production migration;
- running inference;
- calling `/classify`;
- changing runtime;
- changing Dockerfile / Docker Compose;
- changing validators/tests;
- changing controlled vocabulary;
- touching `tidal-parser`;
- creating tag/release.

## Rollback considerations

Rollback for Roadmap 4.21 is documentation-only. Remove this file:

- `genre-classifier/docs/lightweight/roadmap-4.21-discogs400-label-vocabulary-mapping-feasibility.md`

No production code, dependency file, Docker file, Docker Compose file,
validator, test, script, model file, audio artifact, provider, provider
factory, `/classify` contract, response shape, controlled vocabulary, shadow
configuration, canary setting, or `tidal-parser` file is changed by this
roadmap slice.
