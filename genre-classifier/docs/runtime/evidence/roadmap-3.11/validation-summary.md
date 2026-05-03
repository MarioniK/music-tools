# Roadmap 3.11 validation summary

Validation directory:

```text
docs/runtime/evidence/roadmap-3.11/
```

## Result

Decision: `controlled_runtime_switch_validated`

No rollback trigger fired.

## Runtime identity

- Python: `3.12.13`
- TensorFlow: `2.21.0`
- `essentia-tensorflow`: `2.1b6.dev1389`
- Essentia: `2.1-beta6-dev`
- numpy: `2.4.4`
- protobuf: `7.34.1`
- h5py: `3.14.0`
- FastAPI: `0.83.0`
- Pydantic: `1.10.26`
- Uvicorn: `0.16.0`
- Starlette: `0.19.1`
- ffmpeg: `5.1.8-0+deb12u1`

Container image id:

```text
sha256:2ccb366bd05e691821d82e1348efdbc65bbcae35a1f2c171134449e5802fb55d
```

## Checks

- `docker compose build`: passed
- `docker compose up -d genre-classifier`: passed
- `/health`: passed, `{"ok":true}`
- `/classify` fixture: passed, HTTP `200`
- response shape: `ok`, `message`, `genres`, `genres_pretty`
- provider default: `legacy_musicnn`
- runtime shadow: disabled
- `pip check`: passed
- supported import-order smoke: passed
- Essentia-first model load: passed
- repeated classify: 10/10 HTTP `200`
- malformed empty upload: HTTP `400`
- malformed fake mp3 upload: HTTP `400`
- unsupported text upload: HTTP `400`
- logs review: no `Bitcast`, no `RegisterAlreadyLocked`, no tracebacks, no critical errors
- memory sanity: `306MiB / 4GiB`
- latency sanity over 10 repeated classify requests: min `9.626306s`, max `12.872652s`, avg `10.353960s`

## Evidence index

- `candidate-build-output.txt`
- `candidate-image-inspect.json`
- `candidate-container-image-id.txt`
- `candidate-compose-ps.txt`
- `candidate-compose-ps-after-validation.txt`
- `candidate-runtime-identity.txt`
- `candidate-pip-check.txt`
- `candidate-provider-shadow-config.txt`
- `candidate-health.json`
- `candidate-classify-upload.txt`
- `candidate-response-shape.txt`
- `candidate-repeated-classify.txt`
- `candidate-repeated-classify-latency-summary.txt`
- `candidate-malformed-uploads.txt`
- `candidate-startup-logs-initial.txt`
- `candidate-logs-tail-500.txt`
- `candidate-docker-stats.txt`
- `import-order-essentia_first.txt`
- `import-order-essentia_standard_first.txt`
- `import-order-classify_import.txt`
- `import-order-app_main_import.txt`
- `import-order-classify_then_tensorflow.txt`
- `import-order-app_then_tensorflow.txt`
- `import-order-model_load_essentia_first.txt`
- `import-order-same_process_repeated_imports.txt`
- `final-runtime-diff.patch`
- `git-head.txt`

