# Roadmap 4.8 — ONNX Runtime feasibility spike

## Status

- offline-only feasibility spike
- Variant B: isolated local-only experiment support
- no production provider implementation
- no dependency, Docker, runtime image, or Compose change
- no model or audio artifact added

## Why this exists after Roadmap 4.7

Roadmap 4.7 created the ONNX offline candidate spike scaffold and proved that a dry-run candidate artifact can stay isolated from production code.

Roadmap 4.8 extends that scaffold just enough to answer the next feasibility questions locally:

- Is ONNX Runtime present in a developer's local Python environment?
- Can a local candidate model path be inspected without copying the model into this repository?
- Can model provenance, runtime availability, and timing metadata be recorded in structured JSON?
- Can this remain safe when ONNX Runtime and model files are absent?

This is still evidence gathering only. It does not evaluate classifier quality, does not run inference, and does not make an integration decision.

## Not a provider implementation

Roadmap 4.8 does not add an ONNX provider, does not update provider factory wiring, and does not call production app code. The production classifier path remains the legacy MusiCNN path.

The scaffold remains isolated under:

- `scripts/lightweight/onnx_candidate_spike.py`

The script intentionally uses only the Python standard library. It must not import TensorFlow, Essentia, production app modules, provider modules, provider factory code, cache code, or inference runtime modules.

## ONNX Runtime remains optional and local-only

`onnxruntime` is not added to requirements, Dockerfile, Docker Compose, or the runtime image.

The script checks local availability with:

```python
importlib.util.find_spec("onnxruntime")
```

It does not import ONNX Runtime at module import time or during the dry-run path. If ONNX Runtime is not installed, the output records a controlled availability status instead of raising a traceback.

Real inference requires a separate approval step because it would introduce a different risk profile: runtime behavior, model compatibility, preprocessing assumptions, latency, and output interpretation.

## Dry-run default

Running the script with no arguments is the default dry-run:

```bash
python3 scripts/lightweight/onnx_candidate_spike.py
```

Dry-run mode:

- emits structured JSON to stdout
- requires no ONNX Runtime installation
- requires no model file
- processes no audio
- runs no inference
- preserves `/classify`-compatible top-level fields:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

Additional spike metadata is included under separate JSON keys so the candidate record can be reviewed without changing production response shape.

## Local model path policy

An optional `--model-path` may point to a local model file for shallow checks only. The model file is not copied into the repository and must not be committed.

The shallow checks are intentionally limited to standard-library filesystem metadata:

- path provided
- exists
- is file
- suffix, with `.onnx` expected
- file size in bytes when available

If no model path is provided, the script stays in metadata-only dry-run mode. If the path is missing or not a file, the script records a controlled status and warning.

## Model provenance policy

Roadmap 4.8 records the provenance fields a future approved ONNX experiment must provide:

- `model_name`
- `model_source_url`
- `license`
- `license_url`
- `checksum_sha256` optional
- `provenance_status`

When license or provenance data is incomplete, the JSON output includes warnings:

- `license_unknown`
- `model_provenance_unknown`

Unknown provenance is acceptable for this local feasibility spike, but it is a blocker for committing model artifacts or proposing production integration.

## Resource and latency metadata

Roadmap 4.8 records only metadata available from the standard library:

- `started_at_utc`
- `finished_at_utc`
- `duration_ms` from `time.perf_counter()`
- `python_version`
- `platform`
- ONNX Runtime availability
- `model_size_bytes` when a local model path exists and is a file

This spike does not claim real memory metrics. Memory, CPU profiling, and inference latency need a separately approved runtime experiment.

## Candidate output and artifact policy

The CLI writes structured JSON to stdout. An optional artifact can be written with:

```bash
python3 scripts/lightweight/onnx_candidate_spike.py --output /tmp/onnx-spike.json
```

The existing `--write-output` option remains as a backward-compatible alias.

Metadata-only outputs should not be placed into auto-validated lightweight evaluation outputs unless they remain compatible with the current validator contract. The Roadmap 4.8 feasibility output keeps `/classify`-compatible top-level fields, but it is not a real evaluation result and should be reviewed as a spike artifact, not as classifier evidence.

## Validation and report relationship

The lightweight evaluation artifact validator continues to validate committed example evaluation artifacts. Roadmap 4.8 does not require new committed evaluation outputs.

Targeted tests for the spike cover behavior that must pass without ONNX Runtime and without model files:

- dry-run without arguments
- runtime detection without importing ONNX Runtime
- metadata-only mode with no model path
- controlled status for missing model path
- local inspection of a temporary fake `.onnx` file
- stable JSON shape
- isolation from production and heavy runtime imports

## Roadmap 4.9 success / no-go criteria

Roadmap 4.9 may proceed only if a separate plan can answer:

- Which ONNX model will be used?
- What is its source URL, license, license URL, and provenance status?
- How will preprocessing and labels be mapped to the existing genre vocabulary?
- Which local-only audio fixtures are approved for the experiment?
- How will candidate outputs be compared to `legacy_musicnn`?
- What runtime, latency, and resource evidence will be collected?
- How will the experiment remain isolated from provider factory and production `/classify` behavior?

Roadmap 4.9 is no-go if:

- model license or provenance remains unknown
- preprocessing assumptions are missing
- label mapping is unclear
- runtime dependencies require production image changes
- model or audio artifacts would be committed without approval
- the proposal requires changing the default provider or `/classify` contract

## Invariants

- default provider remains `legacy_musicnn`
- production classifier path remains legacy MusiCNN
- `/classify` contract is unchanged
- response shape is unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- no Docker changes
- no Docker Compose changes
- no dependency changes
- no runtime image changes
- no model artifacts added
- no audio artifacts added
- no production provider, factory, app, cache, or runtime path changed
- `tidal-parser` untouched
- no commit, tag, push, or release work
