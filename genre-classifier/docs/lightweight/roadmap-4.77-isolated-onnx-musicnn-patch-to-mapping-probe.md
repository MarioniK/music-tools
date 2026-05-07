# Roadmap 4.77 - isolated ONNX/MusiCNN patch-to-mapping vertical probe

## Цель

Roadmap 4.77 фиксирует isolated probe для вертикальной цепочки
`explicit patch -> ONNX Runtime inference -> activations/classes mapping ->
controlled vocabulary -> genres_pretty`.

Это безопасный local-only step для проверки цепочки вне production path.

## Scope

В рамках шага проверяются только:

- версия и executable Python;
- `onnxruntime` и доступные providers;
- наличие `CPUExecutionProvider`;
- явный external ONNX model artifact;
- явный external classes metadata artifact;
- optional explicit patch artifact, если он уже существует вне репозитория;
- чтение metadata без implicit discovery;
- ONNX Runtime inference только если patch artifact явным образом передан;
- mapping activations/classes в `genres` и `genres_pretty` compatible shape;
- фиксация blockers и warnings;
- фиксация того, что production boundaries не меняются.

В рамках этого шага не выполняются:

- изменение `genre-classifier/requirements.txt`;
- изменение optional requirements;
- добавление `onnxruntime`, `essentia` или `essentia-tensorflow` в production deps;
- Dockerfile / Compose change;
- Docker Compose;
- Docker build;
- `/classify`;
- runtime smoke через provider;
- production inference;
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
- TensorFlow baseline не запускался;
- TensorFlow vs ONNX comparison не запускался;
- production dependencies не менялись;
- Dockerfile и Compose-файлы не менялись;
- provider/default logic не менялась;
- response shape не менялась;
- production readiness не claimed;
- venv / wheel / audio / model / patch files не коммитились.

## Probe interface

Скрипт расположен здесь:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_patch_to_mapping_probe.py`

Поддерживаемые аргументы:

- `--onnx-model-path <path>` required
- `--classes-path <path>` required
- `--patch-path <path>` optional
- `--output <path>` required
- `--top-n <int>` default `5`

## Explicit artifacts

Для текущего probe использованы только explicit external artifacts из `/tmp`:

- ONNX model artifact: `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`
- classes metadata: `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`
- patch artifact: `/tmp/music-tools-roadmap-4.77-patch-to-mapping/musicnn_patch.npy`

Patch artifact был пересоздан outside repo в isolated env из approved external
fixture:

- fixture: `/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3`
- preprocessing chain: `essentia.standard.MonoLoader + FrameGenerator + TensorflowInputMusiCNN`

Не выполнялись ни implicit discovery, ни download, ни repo audio/preprocessing
input reuse.

## Report

Результат сохраняется в:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-patch-to-mapping-probe-report.json`

Report фиксирует:

- `roadmap: "4.77"`
- `not_production_decision: true`
- `isolated_vertical_probe_only: true`
- `classify_called: false`
- `runtime_smoke_run: false`
- `production_approval: false`
- `python.version`
- `python.executable`
- `onnxruntime.expected_version`
- `onnxruntime.installed_version`
- `onnxruntime.import_ok`
- `onnxruntime.available_providers`
- `onnxruntime.cpu_execution_provider_available`
- `artifacts.*`
- `patch_input.*`
- `onnx_outputs.*`
- `mapping.*`
- `production_boundaries.*`
- `blockers`
- `warnings`
- `next_step_recommendation`

## Expected outcome

Если explicit patch artifact отсутствует, report должен завершиться честным blocker-ом
`EXPLICIT_PATCH_INPUT_NOT_AVAILABLE` без traceback и без inference run.

В текущем completed probe blocker был снят: patch `[187, 96]` был получен вне
repo, ONNX Runtime inference выполнился, activations/classes mapping отработал,
а `candidate_genres` и `candidate_genres_pretty` стали non-empty.

## Следующий шаг

Следующий safe step - Roadmap 4.78 explicit provider direct smoke only после
того, как результаты isolated patch-to-mapping probe будут отдельно reviewed.
