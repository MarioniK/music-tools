# Roadmap 4.85 — Optional ONNX Slim Docker Target Prototype

## Цель

Добавить optional slim Docker target `onnx-runtime-slim` для `genre-classifier`, который не наследует `tensorflow`-содержащий слой и собирается из filtered production requirements, не меняя default runtime и default provider.

## Что сделано

- Добавлен optional target `onnx-runtime-slim` в `genre-classifier/Dockerfile`.
- `legacy-runtime` оставлен как default/final stage.
- `onnx-runtime` по-прежнему доступен как full optional target.
- `onnx-runtime-slim` строится из `runtime-base`, а не из слоя, где уже установлен TensorFlow.
- В slim target используется filtered copy of `requirements.txt`, где top-level `tensorflow==...` исключён только для этого optional path.
- `requirements-optional-onnx.txt` устанавливается в full и slim optional targets.
- После установки optional deps в slim target выполняется safety cleanup `python -m pip uninstall -y tensorflow`.
- `docker-compose.yml` не менялся.

## Почему первый прототип дал 0%

Первый 4.85 prototype удалял `tensorflow` уже после того, как он был установлен в parent layer. Это скрывало пакет внутри контейнера, но не уменьшало итоговый image size из-за Docker layer inheritance.

Текущий fix устраняет именно это: slim target больше не наследует TensorFlow-layer.

## Команда build

```bash
cd /opt/music-tools/genre-classifier
docker build --target onnx-runtime -t music-tools-genre-classifier-onnx:roadmap-4.85-full .
docker build --target onnx-runtime-slim -t music-tools-genre-classifier-onnx:roadmap-4.85-slim .
```

## Итог build

- full baseline build result: success
- slim build result: success
- full baseline tag: `music-tools-genre-classifier-onnx:roadmap-4.85-full`
- slim image tag: `music-tools-genre-classifier-onnx:roadmap-4.85-slim`

## Размер

- full baseline size: `3479268977` bytes
- slim image size: `1572225060` bytes
- size reduction: `1907043917` bytes
- size reduction percent: `54.81%`

## Package checks

- `tensorflow`: absent
- `essentia-tensorflow`: present
- `onnxruntime`: present

## Direct path probe

Проверка full ONNX/MusiCNN direct path внутри slim image успешна.

- `tensorflow_import_ok`: false
- `essentia_import_ok`: true
- `essentia_standard_import_ok`: true
- `TensorflowInputMusiCNN`: available
- `patch_shape`: `[187, 96]`
- `activations_shape`: `[50]`
- `embeddings_shape`: `[200]`
- `genres_non_empty`: true
- `genres_pretty_non_empty`: true

## Genres

- `genres`: `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`, `progressive rock`, `electronica`
- `genres_pretty`: `indie rock`, `alternative rock`, `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`

## Вывод

Optional ONNX slim target теперь действительно slim: TensorFlow отсутствует в image, optional ONNX/MusiCNN path работает, default runtime остаётся неизменным.

