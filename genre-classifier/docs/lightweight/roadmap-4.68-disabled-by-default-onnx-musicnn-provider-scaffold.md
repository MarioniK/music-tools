# Roadmap 4.68: disabled-by-default ONNX/MusiCNN provider scaffold

## Status

Scaffold добавлен. `onnx_musicnn` доступен только как explicit provider, `legacy_musicnn` остаётся default.

## Scope

- Добавлен безопасный scaffold нового provider-а `OnnxMusiCNNProvider`.
- Не менялся контракт `/classify`.
- Success response shape не менялся: `ok`, `message`, `genres`, `genres_pretty`.
- Existing error payload shape preserved: `ok`, `error`.
- Не менялся default provider.
- Не менялись Dockerfile, docker-compose и production dependencies.
- `tidal-parser` не затронут.

## Изменённые файлы

- `app/core/settings.py`
- `app/providers/factory.py`
- `app/providers/__init__.py`
- `app/providers/onnx_musicnn.py`
- `tests/test_settings.py`
- `tests/test_provider_factory.py`
- `tests/test_classify_orchestration.py`
- `tests/lightweight/test_onnx_musicnn_provider_scaffold.py`
- `docs/lightweight/roadmap-4.68-disabled-by-default-onnx-musicnn-provider-scaffold.md`
- `docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-provider-scaffold-report.json`

## Architecture Summary

Существующая provider-архитектура осталась прежней:

- `factory` выбирает provider по имени.
- `legacy_musicnn` остаётся production default.
- `validation` и `compat` продолжают формировать legacy-совместимый выход.

Новый scaffold добавляет только безопасную точку расширения:

- dependency availability check;
- model artifact availability check;
- metadata/classes availability check;
- preprocessing boundary placeholder;
- inference boundary placeholder;
- activations/classes mapping helper.

## Provider Scaffold Boundary

`OnnxMusiCNNProvider`:

- не импортирует `onnxruntime` или `essentia` на module import path;
- использует lazy loading внутри runtime-boundary методов;
- возвращает controlled `RuntimeError` для unsupported / disabled state;
- поддерживает helper `build_candidate_scores(...)` для будущего mapping-а activations/classes;
- сохраняет index alignment при формировании кандидатов;
- использует existing alias / controlled vocabulary normalization path, где это возможно.

## Disabled-by-default Confirmation

- Новый provider не стал default.
- `legacy_musicnn` остался default provider.
- `GENRE_PROVIDER=onnx_musicnn` требуется явно, если scaffold надо выбрать вручную.

## `/classify` Contract Unchanged

Контракт остаётся прежним:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## Success Response Shape Unchanged

`tests/test_classify_orchestration.py` продолжает подтверждать, что success response shape не изменился.

## Existing Error Behavior Preserved

Route-level error boundary остаётся существующим поведением:

- `ok: false`
- `error: <message>`

Это не contract migration и не расширение response shape в рамках Roadmap 4.68.

## Lazy Import Policy

Runtime imports остаются внутри explicit runtime methods:

- `onnxruntime`
- `essentia`
- `essentia.standard`

Это защищает startup приложения от `ModuleNotFoundError` на module import path.

## Graceful Unsupported Behavior

Scaffold не ломает startup и не пытается выполнять реальный inference.

Если artifacts / dependencies отсутствуют, provider возвращает controlled unsupported state через `RuntimeError` с явной причиной.

## Unit Tests Summary

Добавлены / обновлены tests, которые проверяют:

- lazy import boundary;
- graceful missing dependency behavior;
- graceful missing model artifact behavior;
- graceful missing metadata behavior;
- controlled failure для activations/classes mismatch;
- route-level mapping `RuntimeError` -> existing controlled 400 JSON error response;
- valid mapping helper result compatible with existing `genres` / `genres_pretty` conversion;
- default provider remains `legacy_musicnn`;
- factory does not switch default to `onnx_musicnn`.

## Non-goals

- Не выполнялся production inference.
- Не выполнялся TensorFlow baseline.
- Не выполнялось TensorFlow vs ONNX сравнение.
- Не менялись production dependency files.
- Не менялись Docker / runtime configs.
- Не трогался `tidal-parser`.

## Rollback Considerations

Изменение rollback-friendly:

- scaffold изолирован в отдельном provider module;
- default path не менялся;
- existing validation / compat pipeline не переписывался;
- revert возможен точечным удалением нового provider-а, settings constant и factory branch.
