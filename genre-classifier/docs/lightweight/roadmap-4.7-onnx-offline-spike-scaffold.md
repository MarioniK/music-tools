# Roadmap 4.7 — ONNX offline candidate spike scaffold

## Status

- offline-only spike scaffold safe-slice
- non-production-facing
- no production behavior change
- no provider implementation
- no runtime dependency change

## Purpose

Roadmap 4.7 prepares an isolated ONNX offline candidate spike scaffold after Roadmap 4.6 selected ONNX Runtime audio classifier exploration as the first future candidate lane.

This document and the optional scaffold script define how a future experiment should shape its dry-run output, provenance placeholders, and review criteria before any real runtime, model, audio fixture, or provider code is added.

## Not a provider implementation

This safe-slice is not a production provider implementation. It does not add an ONNX provider class, does not add provider factory wiring, does not call the FastAPI app, does not call `/classify`, and does not execute runtime shadow behavior.

The scaffold exists only under the lightweight offline area:

- `scripts/lightweight/onnx_candidate_spike.py`

That script is intentionally isolated from production app, provider, cache, and inference modules.

## Baseline remains legacy MusiCNN

`legacy_musicnn` remains the production baseline and default provider.

Roadmap 4.7 makes no production decision. The production classifier path remains the legacy MusiCNN path, and future ONNX evidence must be compared against `legacy_musicnn` before any later integration proposal can be considered.

The `/classify` contract remains unchanged:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## No ONNX Runtime dependency yet

No `onnxruntime` dependency is added in this safe-slice because the current work is a dry-run scaffold only. Adding a runtime dependency should happen only after a separate actual ONNX experiment is approved with model provenance, fixture assumptions, runtime impact expectations, and validation criteria.

The dry-run script must not import or require:

- `onnxruntime`
- TensorFlow
- Essentia
- FastAPI app modules
- provider factory or production provider code

## No model or audio artifacts

No model files and no audio fixtures are added in Roadmap 4.7.

This avoids committing unreviewed binary artifacts, unclear licenses, unknown redistribution rights, or fixture data before provenance and evaluation scope are approved. The scaffold writes only an explicit JSON dry-run output when requested by `--write-output`.

## Future input assumptions

A future actual ONNX spike may define these inputs after approval:

- model path
- model source URL or registry reference
- model version
- model license
- model checksum
- label vocabulary or mapping table
- preprocessing assumptions
- audio fixture manifest
- fixture license/provenance notes
- CPU-only runtime method

None of those inputs are required or consumed by the Roadmap 4.7 dry-run scaffold.

## Output artifact shape

Any future candidate output artifact must remain compatible with the current `/classify` response shape:

```json
{
  "ok": true,
  "message": "dry-run only; no ONNX Runtime loaded; no model loaded; no audio processed; no inference executed",
  "genres": [
    {"tag": "electronic", "prob": 0.0}
  ],
  "genres_pretty": ["Electronic"]
}
```

The scaffold dry-run output uses this shape so downstream review can focus on contract compatibility without pretending real inference happened.

## Model provenance placeholders

A future actual spike should record model provenance before any model artifact is added:

- `model_name`
- `model_version`
- `model_source`
- `model_license`
- `model_checksum`
- `label_vocabulary_source`
- `preprocessing_reference`
- `redistribution_status`
- `training_data_notes`
- `review_notes`

Roadmap 4.7 records these as placeholders only. It does not add a model, model metadata file, or dependency.

## Dry-run behavior

The scaffold script supports:

- `--dry-run`
- `--write-output PATH`

In dry-run mode it must:

- require no ONNX Runtime installation
- require no model file
- require no audio file
- process no audio
- run no inference
- emit a clear stdout summary
- write JSON only when `--write-output` is provided
- create the parent directory for the explicit output path when needed
- exit 0 on successful dry-run

The script must not write to `docs/lightweight/evaluation/outputs` by default.

## Success criteria

Roadmap 4.7 succeeds when:

- the scaffold documentation exists
- the optional dry-run script remains stdlib-only
- the dry-run command exits successfully
- the optional JSON output is `/classify`-compatible
- tests, if present, pass without ONNX Runtime, models, or audio files
- production code path remains unchanged
- default provider remains `legacy_musicnn`
- no dependency files are changed
- no Dockerfile or Docker Compose files are changed
- no model/audio artifacts are added

## Explicit non-goals / no-go list

Roadmap 4.7 does not allow:

- production migration
- canary
- shadow execution
- provider factory wiring
- production provider implementation
- `/classify` contract changes
- response shape changes
- cache behavior changes
- Dockerfile or Docker Compose changes
- dependency changes
- model artifacts
- audio fixtures
- real inference
- ONNX Runtime import or dependency
- TensorFlow, Essentia, app, provider factory, or legacy provider imports
- `tidal-parser` changes
- release, tag, commit, or push work

## Next step

The next step for an actual ONNX Runtime experiment is a separately approved offline spike that selects a candidate model, records license/provenance, defines fixture assumptions, proposes dependency impact, and runs real inference only in an isolated offline lane.

No production decision is made by Roadmap 4.7.
