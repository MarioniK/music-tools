# Roadmap 4.84 - TensorFlow Python package removal feasibility probe

Статус: local-only feasibility probe, не production decision.

## Контекст

- Использован уже собранный image `music-tools-genre-classifier-onnx:roadmap-4.82`.
- Docker build не запускался.
- Docker Compose не запускался.
- `/classify` не вызывался.
- Network HTTP smoke не запускался.
- TensorFlow baseline не сравнивался.
- Цель шага - проверить, может ли optional ONNX/MusiCNN direct path работать без Python package `tensorflow`, сохраняя `essentia-tensorflow` и native `essentia_tensorflow.libs`.

## Команда probe

```bash
docker run --rm \
  -v /opt/music-tools/genre-classifier:/app:ro \
  -v /tmp/music-tools-onnx-parity:/tmp/music-tools-onnx-parity:ro \
  -v /tmp/music-tools-onnx-parity-output:/tmp/music-tools-onnx-parity-output:rw \
  music-tools-genre-classifier-onnx:roadmap-4.82 \
  sh -lc '
    set -e
    python -m pip show tensorflow >/dev/null
    python -m pip uninstall -y tensorflow
    python /app/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_tensorflow_removal_feasibility_probe.py \
      --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3 \
      --onnx-model-path /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx \
      --classes-path /tmp/music-tools-onnx-parity/msd-musicnn-1.json \
      --tensorflow-present-before-uninstall true \
      --output /tmp/music-tools-onnx-parity-output/onnx-musicnn-tensorflow-removal-feasibility-report.json
  '
```

## Итог

- Feasibility probe успешен.
- `tensorflow_python_package_removal_feasibility: true`.
- `original_image_unchanged: true`.
- `tensorflow_removed_only_in_disposable_container: true`.
- `tensorflow` присутствовал до uninstall и отсутствовал после uninstall внутри disposable container.
- `essentia-tensorflow` остался установлен.
- `import tensorflow` после uninstall не прошёл, как и ожидалось.
- `import essentia` и `import essentia.standard` прошли.
- `TensorflowInputMusiCNN` доступен.
- `onnxruntime` импортировался успешно.
- Полный direct path после uninstall завершился успешно.

## Тайминги

- `total_seconds`: `3.926693`
- `preprocessing_seconds`: `0.104353`
- `onnx_inference_seconds`: `0.054496`

## Full pipeline after uninstall

- `patch_shape`: `[187, 96]`
- `patch_shape_match`: `true`
- `activations_shape`: `[50]`
- `embeddings_shape`: `[200]`
- `classes_activations_count_match`: `true`
- `genres_non_empty`: `true`
- `genres_pretty_non_empty`: `true`

## Genres

- `genres`: `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`, `progressive rock`, `electronica`
- `genres_pretty`: `indie rock`, `alternative rock`, `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`

## Decision signal

- `tensorflow_python_package_removable_candidate: true`
- `potential_image_size_reduction`: approximately `1.9G`
- Recommendation: proceed to Roadmap 4.85 optional ONNX slim Docker target prototype if full pipeline succeeds.

## Report

JSON report сохранён здесь:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-tensorflow-removal-feasibility-report.json`

## Production boundaries

- `production_requirements_changed`: false
- `dockerfile_changed`: false
- `compose_changed`: false
- `default_provider_changed`: false
- `classify_contract_changed`: false
- `response_shape_changed`: false
- `tidal_parser_touched`: false

## Blockers and warnings

- `blockers`: `[]`
- `warnings`: `[]`
