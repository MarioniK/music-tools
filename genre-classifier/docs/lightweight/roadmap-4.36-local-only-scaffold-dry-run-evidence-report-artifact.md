# Roadmap 4.36 Local-Only Scaffold Dry-Run Evidence Report Artifact

## Goal

Roadmap 4.36 commits a lightweight JSON evidence artifact for the Roadmap 4.35 local-only MusiCNN ONNX parity scaffold dry-run output:

`docs/lightweight/evaluation/parity-scaffold/example-musicnn-onnx-parity-scaffold-dry-run-output.json`

The artifact preserves a structured dry-run result that can be reviewed and validated without running inference, importing production runtime code, or changing the `/classify` API contract.

## Relationship To Roadmap 4.35

Roadmap 4.35 added `scripts/lightweight/musicnn_onnx_parity_scaffold.py` as a stdlib-only CLI scaffold. The scaffold validates recorded metadata and documented approval boundaries for the local-only MusiCNN ONNX work.

Roadmap 4.36 does not extend that scaffold into inference. It records an example `--mode dry-run` output and adds documentation so future work has a stable reference for the scaffold's no-inference behavior.

## Why The Dry-Run Output Is Useful Evidence

The dry-run output is useful because it captures the checks the scaffold performs against committed metadata evidence. It records that the scaffold:

- completed successfully in `dry-run` mode;
- found the expected local artifact metadata records;
- preserved the no-inference and no-production boundary flags;
- left `onnxruntime`, TensorFlow, Essentia, providers, production runtime, and `/classify` untouched;
- emitted warnings and next-step guidance instead of approval.

This makes the scaffold output reviewable as a lightweight evidence artifact without requiring model files, audio fixtures, dependency installation, network access, or runtime execution.

## Not A Parity Run

This artifact is not a parity run. It does not compare TensorFlow and ONNX model outputs, does not execute ONNX Runtime, does not execute the legacy TensorFlow baseline, and does not evaluate audio fixtures.

The output may reference metadata observations, such as recorded hashes or documented JSON metadata differences, but those observations are not numeric parity evidence and do not approve parity.

## No-Inference Boundary

The scaffold and this artifact keep the following boundary:

- `inference_attempted` is `false`;
- `onnxruntime_imported` is `false`;
- `tensorflow_imported` is `false`;
- `essentia_imported` is `false`;
- `classify_called` is `false`;
- `provider_imported` is `false`;
- `production_runtime_touched` is `false`.

The artifact is intentionally metadata-only. It must not be used as an inference approval, production approval, provider implementation approval, default provider switch approval, or migration approval.

## What The Artifact Confirms

The artifact confirms that the Roadmap 4.35 scaffold can run locally in dry-run mode and produce structured JSON output. It also confirms that the output records the expected local-only safety semantics, including `not_production_decision: true`, `approved_for_inference: false`, and `approved_for_production: false`.

It confirms that the scaffold reviewed committed metadata evidence and reported successful dry-run checks at the time this example artifact was generated.

## What The Artifact Does Not Confirm

The artifact does not confirm:

- model output parity;
- TensorFlow baseline output values;
- ONNX Runtime output values;
- final genre ranking equivalence;
- `/classify` response equivalence;
- provider correctness;
- production readiness;
- dependency readiness;
- rollout readiness.

## Why Inference And Runtime Capture Are Not Approved

Inference, ONNX Runtime execution, TensorFlow baseline capture, Essentia execution, and audio fixture evaluation remain unapproved because this roadmap item is only a committed dry-run evidence artifact. Those steps would require separate approval gates, dependency review, fixture handling, runtime isolation, output comparison criteria, and explicit rollback planning.

No `onnxruntime` dependency is added here, and no model or audio files are committed.

## Production Baseline

`legacy_musicnn` remains the production baseline and default provider. Roadmap 4.36 does not change provider selection, provider factory behavior, production runtime code, cache behavior, controlled vocabulary behavior, or the `/classify` response shape.

## Validation Commands

Run from `/opt/music-tools/genre-classifier`:

```bash
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py
python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py --mode dry-run
python3 -m json.tool docs/lightweight/evaluation/parity-scaffold/example-musicnn-onnx-parity-scaffold-dry-run-output.json
python3 scripts/lightweight/validate_evaluation_artifacts.py
python3 -m pytest tests/lightweight -q
```

## Rollback Notes

Rollback is limited to removing the Roadmap 4.36 documentation artifact, removing the committed parity-scaffold dry-run JSON artifact, and reverting any validator/test additions that only validate this artifact type.

No runtime rollback is required because this work does not change production code, dependencies, Dockerfiles, providers, model files, audio fixtures, `/classify`, or inference paths.

## Explicit Non-Goals

- No inference.
- No TensorFlow inference.
- No ONNX Runtime execution.
- No model output comparison.
- No `/classify` calls.
- No production app imports.
- No provider imports.
- No provider implementation.
- No provider factory changes.
- No default provider switch.
- No dependency changes.
- No `onnxruntime` addition.
- No Dockerfile or Docker Compose changes.
- No model files in the repository.
- No audio fixtures.
- No network or download logic.
- No controlled vocabulary changes.
- No cache semantics changes.
- No `tidal-parser` changes.
- No shadow execution, canary rollout, LLM cutover, or production migration.
