# Roadmap 4.82 - Optional ONNX Docker Build Validation

## Цель

Проверить, что optional Docker target `onnx-runtime` реально собирается и содержит optional ONNX / MusiCNN runtime dependencies, не затрагивая default legacy runtime и не выполняя runtime smoke.

## Что проверено

- `docker build --target onnx-runtime -t music-tools-genre-classifier-onnx:roadmap-4.82 .`
- `onnxruntime` установлен в optional image.
- `essentia-tensorflow` установлен в optional image.
- `onnxruntime` импортируется.
- `essentia` и `essentia.standard` импортируются.
- `essentia.standard.TensorflowInputMusiCNN` доступен.
- optional runtime использует mounted artifacts, а не baked-in model files.

## Что не проверялось

- `docker compose up`
- network HTTP smoke
- `/classify`
- production readiness

## Итог build validation

- build result: success
- build duration: 124 seconds
- image id: `sha256:c1c8101f93012ce23a545b7f5c95ef28732825343e253443e9c94995271ac1d7`
- image size: `3479268978` bytes

## Статические runtime checks

- `onnxruntime` installed/import ok: yes
- `essentia-tensorflow` installed/import ok: yes
- `TensorflowInputMusiCNN` available: yes

Во время import checks в контейнере были видны ожидаемые TensorFlow/CUDA warnings, но они не блокировали validation.

## Policy confirmation

- default provider unchanged: `legacy_musicnn`
- default runtime remains legacy-only
- `requirements-optional-onnx.txt` is not connected to default install path
- no artifacts baked into image
- mounted artifacts required
- no production dependency changes
- no response shape changes
- no `/classify` call
- no Docker Compose run

## Risks

- image size should be tracked explicitly
- TensorFlow/CUDA warnings may be noisy
- no network or runtime smoke was executed yet

## Next step

Roadmap 4.83 - optional ONNX Compose profile config/static validation or optional container smoke without `/classify`, depending on 4.82 outcome.
