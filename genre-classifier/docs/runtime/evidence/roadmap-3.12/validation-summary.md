# Roadmap 3.12 validation summary

Validation directory:

```text
docs/runtime/evidence/roadmap-3.12/
```

## Result

Decision: `production_runtime_stabilized`

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

Container image id:

```text
sha256:2ccb366bd05e691821d82e1348efdbc65bbcae35a1f2c171134449e5802fb55d
```

## Checks

- `docker compose ps`: passed, service `Up`
- `/health`: passed, HTTP `200`, `{"ok":true}`
- `/classify` fixture: passed, HTTP `200`
- response shape: `ok`, `message`, `genres`, `genres_pretty`
- provider default: `legacy_musicnn`
- runtime shadow: disabled
- supported import-order smoke: passed
- Essentia-first model load: passed
- TensorFlow-first model load: failed as expected and remains unsupported/documented only
- repeated classify: `10/10` HTTP `200`
- malformed empty upload: HTTP `400`
- malformed fake mp3 upload: HTTP `400`
- unsupported text upload: HTTP `400`
- logs review: no service-path `Bitcast`, no `RegisterAlreadyLocked`, no import-order crash, no unexpected model load crash
- memory sanity: `376.6MiB / 4GiB`
- latency sanity over 10 repeated classify requests: min `9.509416s`, max `10.992559s`, avg `9.948980s`

## Evidence index

- `git-head.txt`
- `candidate-compose-ps.txt`
- `candidate-compose-ps-after-validation.txt`
- `candidate-container-image-id.txt`
- `candidate-image-inspect.json`
- `candidate-runtime-identity.txt`
- `candidate-provider-shadow-config.txt`
- `candidate-health.json`
- `candidate-health.meta.txt`
- `candidate-response-shape.txt`
- `candidate-repeated-classify-latency-summary.txt`
- `candidate-malformed-uploads.txt`
- `candidate-startup-logs-initial.txt`
- `candidate-logs-full.txt`
- `candidate-logs-tail-500.txt`
- `candidate-logs-review.txt`
- `candidate-docker-stats.txt`
- `candidate/upload.classify.body.json`
- `candidate/upload.classify.meta.txt`
- `candidate/upload.repeat-*.body.json`
- `candidate/upload.repeat-*.meta.txt`
- `empty.classify.body.json`
- `empty.classify.meta.txt`
- `fake.classify.body.json`
- `fake.classify.meta.txt`
- `unsupported.classify.body.json`
- `unsupported.classify.meta.txt`
- `import-order-essentia_first.txt`
- `import-order-essentia_standard_first.txt`
- `import-order-classify_import.txt`
- `import-order-app_main_import.txt`
- `import-order-classify_then_tensorflow.txt`
- `import-order-app_then_tensorflow.txt`
- `import-order-model_load_essentia_first.txt`
- `import-order-model_load_tensorflow_first.txt`
- `import-order-same_process_repeated_imports.txt`
