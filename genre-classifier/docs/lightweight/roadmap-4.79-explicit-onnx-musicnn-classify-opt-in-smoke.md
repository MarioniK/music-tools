# Roadmap 4.79 - Explicit `/classify` opt-in smoke for `onnx_musicnn`

Roadmap 4.79 проверяет только локальный service boundary `/classify` в explicit opt-in режиме для `onnx_musicnn`.

Что подтверждаем:

- default provider остаётся `legacy_musicnn`;
- `onnx_musicnn` активируется только явно через `GENRE_PROVIDER=onnx_musicnn`;
- используются только внешние артефакты ONNX и metadata;
- `/classify` сохраняет исходный контракт ответа;
- успешный ответ остаётся в формате:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `genres` и `genres_pretty` не пустые на success;
- Docker Compose и Docker build не используются;
- `tidal-parser` не затрагивается;
- production readiness не утверждается.

## Локальный smoke helper

Сценарий запускается через:

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx_musicnn_classify_opt_in_smoke.py`

Он:

- поднимает локальный FastAPI/TestClient boundary;
- временно выставляет:
  - `GENRE_PROVIDER=onnx_musicnn`
  - `ONNX_MUSICNN_MODEL_PATH`
  - `ONNX_MUSICNN_METADATA_PATH`
- отправляет внешний mp3 fixture на `/classify`;
- пишет JSON report в отдельный файл;
- восстанавливает env после выполнения.

## Границы

Не делаем в этой roadmap:

- смену default provider;
- изменение `/classify` contract;
- изменение response shape;
- Docker/runtime migration;
- production dependency changes;
- any `tidal-parser` work.

## Ожидаемый артефакт

`genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-classify-opt-in-smoke-report.json`

## Следующий шаг

Если explicit opt-in smoke succeeds, переходить к Roadmap 4.80 только для отдельного Docker/runtime packaging decision.
