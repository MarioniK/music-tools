# Roadmap 4.83 - ONNX/MusiCNN optional image performance and resource baseline

Статус: local-only performance/resource baseline, не production decision.

## Контекст

- Использован уже собранный image `music-tools-genre-classifier-onnx:roadmap-4.82`.
- Docker build не запускался.
- Docker Compose не запускался.
- `/classify` не вызывался.
- Network HTTP smoke не запускался.
- Legacy TensorFlow baseline не сравнивался в этом slice.

## Команда benchmark

```bash
docker run --rm \
  -v /opt/music-tools/genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_optional_image_performance_probe.py:/app/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_optional_image_performance_probe.py:ro \
  -v /tmp/music-tools-onnx-parity:/tmp/music-tools-onnx-parity:ro \
  -v /tmp/music-tools-onnx-parity-output:/tmp/music-tools-onnx-parity-output:rw \
  music-tools-genre-classifier-onnx:roadmap-4.82 \
  python /app/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_optional_image_performance_probe.py \
    --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3 \
    --onnx-model-path /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx \
    --classes-path /tmp/music-tools-onnx-parity/msd-musicnn-1.json \
    --runs 3 \
    --output /tmp/music-tools-onnx-parity-output/onnx-musicnn-optional-image-performance-baseline-report.json
```

## Итог

- Benchmark успешен.
- `onnx_runtime_functional: true`.
- `repeated_run_stable: true`.
- `performance_benefit_confirmed: false`.
- Сигнал на пользу относительно legacy пока не доказан.

## Тайминги

- `total_seconds`: 1.873967, 1.745251, 1.654825
- `import_seconds`: 0.142362, 0.136413, 0.125352
- `audio_loading_seconds`: 0.537870, 0.480890, 0.476575
- `preprocessing_seconds`: 0.108405, 0.100992, 0.096274
- `onnx_session_seconds`: 0.021601, 0.009482, 0.008931
- `onnx_inference_seconds`: 0.058606, 0.050385, 0.047237
- `mapping_seconds`: 0.001036, 0.000677, 0.000726

## Ресурсы

- `method`: `python_resource_getrusage`
- `max_rss_kb`: 280012

## Heavy dependency usage

- `tensorflow_installed`: true
- `tensorflow_imported_before_preprocessing`: false
- `tensorflow_imported_after_preprocessing`: false
- `essentia_tensorflow_installed`: true
- `essentia_standard_used`: true
- `tensorflow_input_musicnn_used`: true
- `onnxruntime_used`: true
- `new_heavy_modules_loaded_during_preprocessing`: `[]`

## Результат genres

- `genres`: `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`, `progressive rock`, `electronica`
- `genres_pretty`: `indie rock`, `alternative rock`, `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`

## Вывод

ONNX/MusiCNN optional image path функционален и стабилен по повторным прогонам, но по этому slice benefit относительно legacy ещё не доказан. Размер image остаётся высоким, поэтому рекомендация прежняя: отдельно измерить legacy baseline перед любым performance claim.

