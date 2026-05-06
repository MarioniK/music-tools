# Roadmap 4.69: ONNX/MusiCNN provider scaffold hardening and artifact path configuration gate

## Status

Hardening завершён как disabled-by-default / opt-in only шаг. `legacy_musicnn` остаётся default provider, а `onnx_musicnn` не становится production path.

## Scope

- Укреплён scaffold `OnnxMusiCNNProvider` без перехода на runtime migration.
- Добавлены explicit opt-in settings для ONNX model path и metadata/classes path.
- Defaults для ONNX artifact paths оставлены unset (`None`).
- Не добавлялись `/tmp` defaults, auto-discovery или local experiment fallback paths.
- Не менялись `/classify` contract и response shape.
- Не менялись production dependencies.
- Не менялись Dockerfile и docker-compose.
- `tidal-parser` не затронут.

## Изменённые файлы

- `app/core/settings.py`
- `app/providers/onnx_musicnn.py`
- `tests/test_settings.py`
- `tests/lightweight/test_onnx_musicnn_provider_scaffold.py`
- `docs/lightweight/roadmap-4.69-onnx-musicnn-provider-scaffold-hardening-artifact-path-configuration-gate.md`
- `docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-provider-scaffold-hardening-report.json`

## Что усилено

### Explicit artifact path boundary

Добавлены explicit opt-in settings для:

- ONNX model path;
- classes / metadata path.

Поведение по умолчанию теперь безопасное:

- path settings unset;
- никакие локальные `/tmp` пути не используются как defaults;
- provider не пытается авто-искать артефакты в произвольных директориях.

### Controlled unsupported / failure diagnostics

Scaffold возвращает controlled diagnostics для:

- отсутствующего model path;
- отсутствующего metadata path;
- отсутствующего model artifact;
- отсутствующего metadata artifact;
- отсутствующего runtime dependency;
- invalid metadata JSON;
- invalid metadata format;
- empty classes list;
- invalid class labels.

Диагностика не раскрывает private local paths в публичных сообщениях.

### Lazy import policy preserved

`onnxruntime` и `essentia` по-прежнему не импортируются на module import path.
Startup приложения и импорт provider module остаются безопасными при отсутствии этих зависимостей.

## Provider Guarantees

- `legacy_musicnn` remains default provider.
- `onnx_musicnn` remains explicit opt-in only.
- provider factory default logic unchanged.
- `/classify` response shape unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- existing error behavior preserved:
  - `ok`
  - `error`

## Tests Run

- `python3 -m pytest tests/test_settings.py tests/test_provider_factory.py tests/lightweight/test_onnx_musicnn_provider_scaffold.py`

## What Was Not Done

- No `/classify` call.
- No real ONNX inference.
- No TensorFlow baseline execution.
- No TensorFlow vs ONNX comparison.
- No production readiness claim.
- No Docker / Compose changes.
- No dependency migration.
- No audio/model/ONNX files added.
- No venv or wheel files committed.

## Notes

This step is a configuration hardening gate only. It prepares the provider scaffold for a later approval step before any runtime dependency or Docker migration work.
