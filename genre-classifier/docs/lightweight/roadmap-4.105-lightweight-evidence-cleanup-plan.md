# Roadmap 4.105. План очистки lightweight roadmap/evidence

## Summary

Этот шаг только инвентаризирует старые lightweight roadmap/evidence файлы после консолидации `v0.5.0`.
Удалений, переносов и runtime-изменений здесь нет.

Постоянные документы уже существуют и теперь являются основной точкой истины для ONNX default runtime:

- `README.md`
- `CHANGELOG.md`
- `genre-classifier/docs/onnx-runtime.md`
- `genre-classifier/docs/releases/v0.5.0.md`

## Why cleanup is needed

Исторический lightweight trail помог довести ONNX default switch до стабильного состояния, но после консолидации
`v0.5.0` он стал избыточным:

- многие roadmap-заметки дублируют уже закреплённые release/operator docs;
- часть parity/evidence JSON отражает промежуточные решения, которые больше не нужны как постоянный источник истины;
- report-structure tests обслуживают исторические JSON-отчёты и должны уйти только отдельным cleanup-срезом;
- при этом несколько файлов всё ещё защищают текущий runtime/contract и их нельзя трогать до следующего шага.

## Permanent docs now replacing roadmap evidence

Эти файлы уже покрывают то, что раньше приходилось собирать по lightweight evidence:

- `README.md`
- `CHANGELOG.md`
- `genre-classifier/docs/onnx-runtime.md`
- `genre-classifier/docs/releases/v0.5.0.md`

Дополнительно текущий runtime/contract защищают живые тесты и артефакт:

- `genre-classifier/tests/test_settings.py`
- `genre-classifier/tests/test_provider_factory.py`
- `genre-classifier/tests/test_classify_orchestration.py`
- `genre-classifier/tests/lightweight/test_optional_onnx_dependency_packaging.py`
- `genre-classifier/app/models/msd-musicnn-1.pb`

## Inventory counts

- `lightweight` roadmap markdown files: `95`
- `parity-scaffold` JSON files: `56`
- `lightweight` report tests: `22`
- `genre-classifier/docs/lightweight` size: `1.6M`
- `genre-classifier/tests/lightweight` size: `1.7M`

## Keep list

### Permanent docs

- `README.md`
- `CHANGELOG.md`
- `genre-classifier/docs/onnx-runtime.md`
- `genre-classifier/docs/releases/v0.5.0.md`

### Runtime tests to keep

- `genre-classifier/tests/test_settings.py`
- `genre-classifier/tests/test_provider_factory.py`
- `genre-classifier/tests/test_classify_orchestration.py`
- `genre-classifier/tests/lightweight/test_optional_onnx_dependency_packaging.py`

### Artifact to keep

- `genre-classifier/app/models/msd-musicnn-1.pb`

## Candidate delete/archive list

Это кандидаты на последующий cleanup-срез, но не на этот шаг.

### Roadmap docs

- старые `genre-classifier/docs/lightweight/roadmap-4.xx*.md`, кроме файлов, которые специально отложены до tag

### Parity/evidence JSON

- старые `genre-classifier/docs/lightweight/evaluation/parity-scaffold/*.json`, кроме файлов, которые специально отложены до tag

### Report-structure tests

- временные `genre-classifier/tests/lightweight/test_*_report.py`, кроме тестов, которые защищают ещё не удаляемые deferred reports

## Defer-until-after-tag list

Эти файлы пока не трогаем. Они могут быть полезны до `v0.5.0` tag или как историческая опора для release review:

- `genre-classifier/docs/lightweight/roadmap-4.97-onnx-default-switch-rollback-incident.md`
- `genre-classifier/docs/lightweight/roadmap-4.103-controlled-onnx-default-switch.md`
- `genre-classifier/docs/lightweight/roadmap-4.104-v0.5.0-onnx-release-documentation-consolidation.md`
- `genre-classifier/docs/lightweight/evaluation/parity-scaffold/onnx-default-switch-rollback-incident-report.json`
- `genre-classifier/docs/lightweight/evaluation/parity-scaffold/controlled-onnx-default-switch-report.json`
- `genre-classifier/docs/lightweight/evaluation/parity-scaffold/v0.5.0-onnx-release-documentation-consolidation-report.json`
- `genre-classifier/tests/lightweight/test_onnx_default_switch_rollback_incident_report.py`
- `genre-classifier/tests/lightweight/test_controlled_onnx_default_switch_report.py`
- `genre-classifier/tests/lightweight/test_v050_onnx_release_documentation_consolidation_report.py`

## Recommended next step

Roadmap 4.106 — remove obsolete lightweight evidence files.

## Non-goals

- no runtime changes;
- no file deletion in 4.105;
- no file moves;
- no tag creation;
- no Docker build;
- no Docker Compose run or `up`;
- no `/classify` call;
- no `parse_request` call;
- no network HTTP call;
- no inference;
- no preprocessing.
