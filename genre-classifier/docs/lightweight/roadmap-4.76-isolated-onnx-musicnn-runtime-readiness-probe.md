# Roadmap 4.76 - isolated ONNX/MusiCNN runtime readiness and functional probe baseline

## Цель

Roadmap 4.76 фиксирует reusable isolated runtime-readiness probe для ONNX/MusiCNN lane.
Это stage для проверки окружения и явных артефактов, а не production migration,
не runtime smoke и не `/classify` execution.

## Scope

В рамках шага проверяются только:

- версия и executable path Python;
- import `onnxruntime`;
- `onnxruntime.__version__`;
- `onnxruntime.get_available_providers()`;
- наличие `CPUExecutionProvider`;
- import `essentia`;
- import `essentia.standard`;
- наличие `essentia.standard.TensorflowInputMusiCNN`;
- явная проверка `--onnx-model-path` без implicit artifact discovery;
- явная проверка `--classes-path` без implicit artifact discovery;
- запись JSON report;
- фиксация blockers и warnings;
- фиксация того, что production boundaries не меняются.

В рамках шага не выполняются:

- изменение `genre-classifier/requirements.txt`;
- изменение `requirements-optional-onnx.txt`;
- добавление `onnxruntime`, `essentia` или `essentia-tensorflow` в production deps;
- Dockerfile / Compose change;
- Docker Compose;
- Docker build;
- `/classify`;
- runtime smoke;
- production inference;
- real ONNX inference;
- preprocessing probe;
- TensorFlow baseline;
- TensorFlow vs ONNX comparison;
- provider/default logic change;
- default provider switch;
- `/classify` contract change;
- response shape change;
- production migration;
- Docker/runtime migration;
- `tidal-parser` changes;
- commit / push / tag / release.

## AGENTS.md compliance

`/opt/music-tools/AGENTS.md` прочитан и соблюдён.

Подтверждённые границы:

- работает только `genre-classifier`;
- `tidal-parser` не тронут;
- Docker Compose не запускался;
- Docker build не запускался;
- `/classify` не вызывался;
- runtime smoke не запускался;
- production inference не запускался;
- real ONNX inference не запускался;
- preprocessing probe не запускался;
- TensorFlow baseline не запускался;
- TensorFlow vs ONNX comparison не запускался;
- production dependencies не менялись;
- Dockerfile и Compose-файлы не менялись;
- provider/default logic не менялась;
- response shape не менялась;
- production readiness не claimed;
- venv / wheel / audio / model files не коммитились.

## Probe interface

Скрипт расположен здесь:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_runtime_readiness_probe.py`

Поддерживаемые аргументы:

- `--output <path>`
- `--onnx-model-path <path>` optional
- `--classes-path <path>` optional

## Report

Результат сохраняется в:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-runtime-readiness-probe-report.json`

Report фиксирует:

- `roadmap: "4.76"`
- `not_production_decision: true`
- `runtime_readiness_probe_only: true`
- `isolated_environment_required: true`
- `classify_called: false`
- `runtime_smoke_run: false`
- `onnx_inference_run: false`
- `preprocessing_probe_run: false`
- `production_approval: false`
- `python.version`
- `python.executable`
- `onnxruntime.expected_version`
- `onnxruntime.installed_version`
- `onnxruntime.import_ok`
- `onnxruntime.available_providers`
- `onnxruntime.cpu_execution_provider_available`
- `essentia_tensorflow.expected_version`
- `essentia_tensorflow.import_essentia_ok`
- `essentia_tensorflow.import_essentia_standard_ok`
- `essentia_tensorflow.tensorflow_input_musiccnn_available`
- `artifact_paths.implicit_discovery_used`
- `artifact_paths.onnx_model_path_provided`
- `artifact_paths.classes_path_provided`
- `artifact_paths.onnx_model_file_exists`
- `artifact_paths.onnx_model_read_ok`
- `artifact_paths.classes_file_exists`
- `artifact_paths.classes_read_ok`
- `artifact_paths.classes_count`
- `artifact_paths.classes_count_expected`
- `artifact_paths.classes_count_match`
- `production_boundaries.*`
- `blockers`
- `warnings`
- `next_step_recommendation`

## Результат

Roadmap 4.76 подтверждает, что isolated readiness probe можно запускать вне repo,
не трогая production defaults, Docker, `/classify` contract или соседний сервис.

Если explicit artifact paths не переданы, artifact checks пропускаются, а implicit
discovery не выполняется.

В текущем repo tree обнаружены pre-existing forbidden artifacts, включая `pb` и
audio files в `app/` и `docs/runtime/evidence/roadmap-3.8/`. Они зафиксированы
только как warning и не были изменены.

## Следующий шаг

Следующий safe step должен оставаться gated и запускаться только после того, как
будут доступны explicit artifact paths для ONNX model и classes.
