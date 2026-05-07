# Roadmap 4.86 - ONNX/MusiCNN slim image performance baseline

Статус: local-only performance/resource baseline, не production decision.

## Контекст

- Использован уже собранный image `music-tools-genre-classifier-onnx:roadmap-4.85-slim`.
- Docker build не запускался.
- Docker Compose не запускался.
- `/classify` не вызывался.
- Network HTTP smoke не запускался.
- Legacy TensorFlow baseline не пересчитывался в этом slice.

## Команда benchmark

```bash
docker run --rm \
  -v /opt/music-tools/genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_slim_image_performance_probe.py:/app/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_slim_image_performance_probe.py:ro \
  -v /tmp/music-tools-onnx-parity:/tmp/music-tools-onnx-parity:ro \
  -v /tmp/music-tools-onnx-parity-output:/tmp/music-tools-onnx-parity-output:rw \
  music-tools-genre-classifier-onnx:roadmap-4.85-slim \
  python /app/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_slim_image_performance_probe.py \
    --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3 \
    --onnx-model-path /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx \
    --classes-path /tmp/music-tools-onnx-parity/msd-musicnn-1.json \
    --runs 3 \
    --output /tmp/music-tools-onnx-parity-output/onnx-musicnn-slim-image-performance-baseline-report.json
```

## Итог

- Benchmark успешен.
- `slim_runtime_functional: true`.
- `repeated_run_stable: true`.
- `performance_signal: same/faster`.
- `runtime_regression_detected: false`.

## Тайминги

- `total_seconds`: 1.664650, 1.658408, 1.673625
- `import_seconds`: 0.134478, 0.131604, 0.131978
- `audio_loading_seconds`: 0.479821, 0.482193, 0.480352
- `preprocessing_seconds`: 0.101193, 0.101372, 0.104150
- `onnx_session_seconds`: 0.010443, 0.008566, 0.008528
- `onnx_inference_seconds`: 0.046213, 0.045582, 0.046001
- `mapping_seconds`: 0.000661, 0.000655, 0.000642

## Результат genres

- `genres`: `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`, `progressive rock`, `electronica`
- `genres_pretty`: `indie rock`, `alternative rock`, `electronic`, `rock`, `indie`, `pop`, `dance`, `alternative`

## Pipeline sanity

- `tensorflow_import_ok`: false
- `essentia_import_ok`: true
- `essentia_standard_import_ok`: true
- `tensorflow_input_musiccnn_available`: true
- `patch_shape`: `[187, 96]`
- `activations_shape`: `[50]`
- `embeddings_shape`: `[200]`
- `genres_non_empty`: true
- `genres_pretty_non_empty`: true

## Ресурсы

- `method`: `python_resource_getrusage`
- `max_rss_kb`: 292768

## Comparison with Roadmap 4.83 full baseline

- `avg_total_seconds_full`: 1.7580143333333333
- `avg_total_seconds_slim`: 1.6655609513400123
- `avg_preprocessing_seconds_full`: 0.10189033333333335
- `avg_preprocessing_seconds_slim`: 0.10223855633133401
- `avg_onnx_inference_seconds_full`: 0.052076000000000004
- `avg_onnx_inference_seconds_slim`: 0.04593166435370222
- `max_rss_kb_full`: 280012
- `max_rss_kb_slim`: 292768

## Package status

- `tensorflow_installed`: false
- `tensorflow_import_ok`: false
- `essentia_tensorflow_installed`: true
- `essentia_standard_used`: true
- `tensorflow_input_musiccnn_used`: true
- `onnxruntime_used`: true

## Size signal

- `size_bytes`: 1572225060
- `full_baseline_size_bytes`: 3479268977
- `size_reduction_bytes`: 1907043917
- `size_reduction_percent`: 54.81

## Вывод

Slim ONNX/MusiCNN image функционален, повторяем по нескольким прогонам и показывает размерное преимущество относительно full optional baseline. На этом slice это всё ещё не production approval, но сигнал достаточно сильный, чтобы продолжать optional container/profile smoke.

