# Roadmap 4.12 - ONNX Mapping-Aware Candidate Output

Status: offline-only spike extension.

## Purpose

Roadmap 4.12 allows the local ONNX candidate spike to apply an approved label
mapping to raw candidate scores. This is limited to the explicit smoke path in
`scripts/lightweight/onnx_candidate_spike.py`; it does not make ONNX output a
production genre classifier.

Raw ONNX labels and scores are not genre output by themselves. Candidate genres
may be emitted only when the local smoke run has raw scores and the provenance
and label mapping gates both pass.

## Relationship To Roadmap 4.10

Roadmap 4.10 introduced an offline-only ONNX smoke boundary. That boundary
remains intact:

- smoke mode is still explicit via `--mode smoke`;
- dry-run remains the default;
- smoke output is still marked as not production classification;
- ONNX Runtime is optional and is not a runtime dependency;
- no model or audio artifact is downloaded or bundled.

Roadmap 4.12 adds interpretation gates after the smoke path has real raw scores.
It does not broaden the smoke boundary.

## Relationship To Roadmap 4.11

Roadmap 4.11 added the label mapping design and the sample mapping artifact at
`docs/lightweight/evaluation/label-mapping/example-onnx-label-mapping.json`.
Roadmap 4.12 uses that existing schema:

- `model_id`;
- `approval_status`;
- `label_count`;
- `labels`;
- per-label `raw_index`, `raw_label`, `mapped_genre`, and `mapping_decision`.

The sample artifact is intentionally not approved, so it must not produce
genres.

## Mapping And Provenance Gates

Mapped candidate genres are allowed only when all of these checks pass:

- `--label-mapping-path` is provided and readable;
- the mapping JSON is valid for the current schema;
- `approval_status` is exactly `approved_for_offline_evaluation`;
- the mapping `model_id` matches the provenance `model_id`;
- smoke inference produced raw numeric scores;
- raw score count matches mapping `label_count`.

If any gate fails, the spike emits a controlled warning and keeps top-level
`genres` and `genres_pretty` empty.

## Mapping Decisions

These decisions may populate candidate genres:

- `mapped`;
- `alias_mapped`.

These decisions must not populate candidate genres:

- `ignored_non_genre`;
- `unmapped`;
- `rejected_ambiguous`.

The spike never converts `raw_label` directly into a genre without an approved
mapping target.

## Fake Probability Prohibition

The spike must not create fake probabilities. If inference does not run, raw
scores are missing, or the raw output object only exposes shape metadata, mapped
genres stay empty.

Scores used by unit tests are static test-only values supplied through mocked
runtime output. They are not model files, audio files, or production inference.

## Output Shape

The top-level artifact remains compatible with the candidate response shape:

- `ok`;
- `message`;
- `genres`;
- `genres_pretty`.

Roadmap 4.12 metadata, including mapping path, mapping approval state, raw score
count, and mapped genre count, stays under smoke metadata. Production endpoint
code is not involved.

## Non-Goals

Roadmap 4.12 does not:

- change the production provider path;
- change the default provider from `legacy_musicnn`;
- connect ONNX candidate code to the provider factory;
- add a production provider implementation;
- change `/classify`;
- change response shape for the production endpoint;
- add ONNX Runtime, TensorFlow, Essentia, TFLite, sklearn, or model dependencies;
- change Dockerfile, Docker Compose, or runtime dependencies;
- add, download, or reference bundled model/audio artifacts;
- run shadow, canary, or production inference.

`tidal-parser` is unchanged.

## Validation Plan

Run from `/opt/music-tools/genre-classifier`:

```bash
python3 -m pytest tests/lightweight -q
python3 scripts/lightweight/onnx_candidate_spike.py
python3 scripts/lightweight/onnx_candidate_spike.py --mode dry-run
python3 scripts/lightweight/onnx_candidate_spike.py \
  --mode smoke \
  --model-path /tmp/nonexistent-model.onnx \
  --provenance-path docs/lightweight/evaluation/model-provenance/example-onnx-model-provenance.json \
  --label-mapping-path docs/lightweight/evaluation/label-mapping/example-onnx-label-mapping.json
python3 scripts/lightweight/validate_evaluation_artifacts.py
```

Targeted tests cover optional mapping path behavior, not-approved mappings,
approved test-only mappings, allowed and blocked mapping decisions, model ID
mismatch, score count mismatch, missing raw scores, and environments without
ONNX Runtime or model/audio files.

## Rollback

Rollback is limited to removing this documentation, the optional
`--label-mapping-path` spike logic, and the targeted lightweight tests. Since
production provider selection, runtime dependencies, Docker configuration,
model/audio artifacts, and `/classify` are unchanged, rollback does not require
service runtime migration.
