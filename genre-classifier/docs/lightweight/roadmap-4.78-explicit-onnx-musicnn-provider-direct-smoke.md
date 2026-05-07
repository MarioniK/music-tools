# Roadmap 4.78 - explicit ONNX/MusiCNN provider direct smoke

## Цель

Roadmap 4.78 проверяет disabled-by-default `onnx_musicnn` provider напрямую,
без HTTP, без FastAPI app startup, без Docker и без production migration.

Проверяемая цепочка:

- explicit external fixture;
- explicit ONNX model artifact path;
- explicit classes/metadata artifact path;
- `OnnxMusiCNNProvider.classify_with_explicit_artifacts(...)`;
- preprocessing через `essentia.standard.TensorflowInputMusiCNN`;
- ONNX Runtime inference;
- provider result;
- validation / compatibility mapping;
- contract-compatible `genres` и `genres_pretty`.

## Scope

В рамках шага проверяются только:

- direct import provider-а без app startup;
- lazy optional imports на module import path;
- explicit artifact paths, переданные явно;
- direct call provider-а;
- validation / compatibility mapping;
- non-empty `genres` и `genres_pretty` на success path;
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
- runtime smoke through HTTP;
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
- HTTP runtime smoke не запускался;
- production inference не запускался;
- TensorFlow baseline не запускался;
- TensorFlow vs ONNX comparison не запускался;
- production dependencies не менялись;
- Dockerfile и Compose-файлы не менялись;
- provider/default logic не менялась;
- response shape не менялась;
- production readiness не claimed;
- venv / wheel / audio / model / patch files не коммитились.

## Direct smoke helper

Скрипт расположен здесь:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_provider_direct_smoke.py`

Поддерживаемые аргументы:

- `--audio-path <external audio fixture>`
- `--onnx-model-path <external onnx model>`
- `--classes-path <external classes metadata>`
- `--output <json report path>`
- `--top-n <int default 5>`

## Explicit artifacts

Для текущего шага используются только explicit external artifacts из `/tmp`:

- ONNX model artifact: `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`
- classes metadata: `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`
- audio fixture: `/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3`

Implicit discovery, download и repo-hosted audio/model artifacts не используются.

## Report

Результат сохраняется в:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-provider-direct-smoke-report.json`

Report фиксирует:

- `roadmap: "4.78"`
- `not_production_decision: true`
- `provider_direct_smoke_only: true`
- `explicit_opt_in_only: true`
- `classify_called: false`
- `http_called: false`
- `docker_run: false`
- `runtime_smoke_through_http: false`
- `production_approval: false`
- `python.version`
- `python.executable`
- `provider.key`
- `provider.direct_import_ok`
- `provider.direct_call_ok`
- `provider.lazy_optional_imports_preserved`
- `provider.default_provider_changed`
- `artifacts.*`
- `result.genres`
- `result.genres_pretty`
- `result.genres_non_empty`
- `result.genres_pretty_non_empty`
- `result.contract_compatible_fields`
- `production_boundaries.*`
- `blockers`
- `warnings`
- `next_step_recommendation`

## Expected outcome

При успешном direct smoke:

- `provider.direct_import_ok = true`;
- `provider.direct_call_ok = true`;
- `result.genres_non_empty = true`;
- `result.genres_pretty_non_empty = true`;
- `blockers = []`;
- `production_approval = false`;
- `onnx_musicnn_disabled_by_default = true`;
- `provider_default_unchanged = true`.

Если direct import или direct call не проходит, report должен зафиксировать честный blocker без перехода к production migration.

## Следующий шаг

Следующий safe step - Roadmap 4.79 explicit `/classify` opt-in smoke only после успешного Roadmap 4.78 direct smoke review.
