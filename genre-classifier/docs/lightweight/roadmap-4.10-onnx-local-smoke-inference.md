# Roadmap 4.10 - ONNX local smoke inference

## Status

- implemented safe-slice
- isolated CLI experiment only
- offline-only local smoke mode
- no production provider implementation
- no dependency, Docker, runtime image, or Compose change
- no model or audio artifact added

## Scope

Roadmap 4.10 extends the existing lightweight ONNX candidate spike tooling with an explicit local smoke mode:

```bash
python3 scripts/lightweight/onnx_candidate_spike.py --mode smoke --model-path /path/to/model.onnx --provenance-path /path/to/provenance.json
```

The default remains dry-run:

```bash
python3 scripts/lightweight/onnx_candidate_spike.py
python3 scripts/lightweight/onnx_candidate_spike.py --mode dry-run
```

Smoke mode is limited to a local developer environment. It reads an explicit local model path and an explicit local provenance JSON path, applies the Roadmap 4.9 provenance gate, checks optional ONNX Runtime availability, and only then attempts isolated model metadata inspection or dummy inference when the input shape is safe to construct without audio preprocessing.

## Non-goals

Roadmap 4.10 does not:

- implement an ONNX provider
- update provider factory wiring
- change the default provider
- change the production classifier path
- change `/classify`
- change response shape
- change cache or runtime behavior
- add `onnxruntime` to requirements, Dockerfile, Docker Compose, or pyproject metadata
- add any dependency
- add model files
- add audio files
- download model files
- add network or download logic
- add production label mapping
- claim genre classification quality
- touch `tidal-parser`

`legacy_musicnn` remains the baseline and default production provider.

## Why this follows Roadmap 4.9

Roadmap 4.9 established that no ONNX inference should run before a candidate has documented provenance, source, license, exact file identity, input/output metadata, and label mapping status.

Roadmap 4.10 enforces that rule in the CLI. Smoke mode reads `--provenance-path` first and requires an approved local provenance artifact before it checks the model file, imports ONNX Runtime, or creates an inference session. Example-only, incomplete, or not-approved provenance returns a controlled no-go JSON result and does not load the model.

## Dry-run default

Dry-run remains the default and keeps the existing scaffold behavior:

- structured JSON is printed to stdout
- no ONNX Runtime import occurs
- no model is loaded for inference
- no audio is processed
- no inference is executed
- the top-level `/classify`-compatible fields remain present:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`

Existing `--output` and `--write-output` usage remains available for dry-run artifacts.

## Explicit smoke mode

Smoke mode must be requested with:

```bash
--mode smoke
```

It requires:

- `--model-path`
- `--provenance-path`

The CLI returns controlled structured JSON for no-go cases such as:

- missing provenance path
- unreadable provenance JSON
- provenance not approved
- missing model path
- model path not a file
- missing or mismatched model hash
- optional ONNX Runtime missing
- unsafe dummy input shape
- model load or inference failure

No traceback is expected for normal no-go outcomes.

## Local-only model and provenance rules

Smoke mode only works with explicit local paths. It does not download, copy, or commit model files.

The provenance JSON must satisfy the Roadmap 4.9 required metadata shape and must be approved for local smoke use. The model file hash is checked with the Python standard library when the provenance gate has passed. A missing, placeholder, or mismatched SHA-256 blocks model loading.

The committed example provenance artifact under `docs/lightweight/evaluation/model-provenance/` is example-only and is intentionally not approved for inference.

## Optional ONNX Runtime handling

`onnxruntime` remains optional and local-only.

The CLI checks availability with:

```python
importlib.util.find_spec("onnxruntime")
```

It does not import ONNX Runtime at module import time, and dry-run mode never imports it. Smoke mode imports ONNX Runtime only after the provenance, model path, and hash gates pass. If ONNX Runtime is absent, the CLI returns structured JSON with an `onnxruntime_missing` warning.

## Output artifact policy

Without `--output-path`, smoke mode prints JSON to stdout and writes no committed artifact.

With `--output-path`, smoke mode can write a local JSON artifact. It refuses to overwrite an existing file unless `--allow-overwrite` is provided. This keeps committed example artifacts from being replaced accidentally.

Dry-run keeps backward-compatible `--output` and `--write-output` behavior.

## Genre output policy

Roadmap 4.10 does not fake genre classification.

If there is no approved label mapping, smoke output keeps:

```json
{
  "genres": [],
  "genres_pretty": []
}
```

The message and warnings state that the output is not a production classification and that raw output metadata only was captured. Raw ONNX output shape, input/output metadata, latency, and warning categories may appear under `metadata`.

## Approval gate before provider work

Smoke evidence is not approval to integrate ONNX into runtime provider selection.

Before any provider implementation, factory wiring, default-provider change, dependency addition, Docker change, or production path change, a later approval must review:

- candidate provenance
- license and redistribution rights
- exact model file identity
- input preprocessing requirements
- output label mapping
- evaluation results against `legacy_musicnn`
- latency and resource evidence
- production rollout and rollback plan

## Rollback notes

Rollback is limited to removing the Roadmap 4.10 documentation artifact, reverting the CLI smoke-mode changes, and reverting targeted tests.

No production runtime, provider, Docker, dependency, model, audio, tag, release, or `tidal-parser` state is involved.
