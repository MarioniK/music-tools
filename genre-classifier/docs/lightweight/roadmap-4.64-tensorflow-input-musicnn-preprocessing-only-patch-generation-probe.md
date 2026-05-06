# Roadmap 4.64 - Isolated TensorflowInputMusiCNN preprocessing-only patch generation probe

## Цель

Roadmap 4.64 проверяет только preprocessing-only путь для `TensorflowInputMusiCNN` в
approved isolated runtime и не затрагивает production provider/default logic.

Проверка была выполнена на approved legal fixture вне репозитория:

- `/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3`
- sha256: `d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628`

## Почему это preprocessing-only

В этом шаге мы подтверждали только способность получить MusiCNN input patch
`[187, 96]` через `TensorflowInputMusiCNN` в local-only probe.

Это не:

- production inference;
- `/classify`;
- ONNX output capture;
- provider implementation;
- default provider switch;
- TensorFlow vs ONNX parity claim.

## Почему использован `TensorflowInputMusiCNN`

`TensorflowInputMusiCNN` выбран как preprocessing-only candidate для pragmatic
ONNX/MusiCNN lane. Он нужен именно как локальный источник mel-style patch, а
не как oracle для legacy parity.

## Почему не использован `TensorflowPredictMusiCNN`

`TensorflowPredictMusiCNN` не использовался, потому что в 4.64 мы не строим
strict parity oracle. Задача шага - только подтвердить preprocessing path и
repeated-run stability для input patch.

## Результат

`TensorflowInputMusiCNN` был доступен в isolated env.

Итог прогона:

- `raw_observed_shape`: `[2948, 96]`
- `final_patch_shape`: `[187, 96]`
- `patch_shape_expected`: `[187, 96]`
- `patch_produced`: `true`
- `repeated_run_stability.checked`: `true`
- `repeated_run_stability.stable`: `true`
- `repeated_run_stability.max_abs_diff`: `0.0`
- `repeated_run_stability.mean_abs_diff`: `0.0`

## Почему это не strict parity lane

Полное совпадение с legacy `musicnn` на этом шаге не доказывалось и не
требовалось. Допускается controlled output drift, если preprocessing
reproducible и документирован.

## Почему ONNX output capture ещё не запускается

Roadmap 4.64 завершает только preprocessing gate. ONNX output capture должен
идти отдельно, только после успешного подтверждения patch `[187, 96]` и
stability.

## Warnings

Зафиксированы ожидаемые CPU import warnings про отсутствующие CUDA библиотеки:

- `libcudart.so.11.0`
- `libcuda.so.1`

Это не blocker для import-level evidence в CPU-only isolated env.

## Что осталось blocked

Для этой точки Roadmap 4.64 blockers отсутствуют. Остальные ограничения
остаются как roadmap boundary:

- production readiness не доказана;
- ONNX output capture не запускался;
- `/classify` не вызывался;
- production dependencies, Dockerfile и Compose не менялись;
- `tidal-parser` не затрагивался.

## Production untouched

Проверка выполнялась local-only и не меняла production runtime, provider/default
logic или deployment artifacts.

## Следующий шаг

Если patch `[187, 96]` produced и repeated-run stability подтверждена, следующий
этап Roadmap 4.65 может переходить к ONNX output capture.

Если бы patch не был produced, Roadmap 4.65 оставался бы blocked до
разблокировки preprocessing path.
