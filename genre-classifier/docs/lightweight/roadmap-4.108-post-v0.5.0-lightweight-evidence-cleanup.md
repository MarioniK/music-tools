# Roadmap 4.108. Пост-v0.5.0 cleanup obsolete lightweight evidence

## Summary

Этот шаг удаляет устаревшие lightweight roadmap/evidence/report-structure файлы, которые использовались во время миграции ONNX MusiCNN и были нужны до выпуска `v0.5.0`.

Постоянная документация уже закрепила итоговое состояние, поэтому исторические строительные леса больше не нужны как source of truth.

## Why cleanup happens after `v0.5.0`

Cleanup выполняется только после выпуска `v0.5.0`, потому что именно релиз и связанные с ним постоянные docs стали стабильной опорной точкой для текущего runtime:

- `README.md`
- `CHANGELOG.md`
- `genre-classifier/docs/onnx-runtime.md`
- `genre-classifier/docs/releases/v0.5.0.md`

До релиза lightweight evidence помогал вести процесс миграции и проверять промежуточные решения. После релиза он стал дублировать уже закреплённые сведения и больше не нужен как постоянный набор артефактов.

## What was removed

Удалены только устаревшие строительные леса:

- все `genre-classifier/docs/lightweight/roadmap-4.*.md`
- все `genre-classifier/docs/lightweight/evaluation/parity-scaffold/*.json`
- все `genre-classifier/tests/lightweight/test_*_report.py`

Удаление затронуло:

- 96 roadmap markdown files;
- 57 parity-scaffold JSON files;
- 23 report-structure test files.

## What was kept

Сохранены файлы, которые продолжают защищать runtime и текущие контрактные ожидания:

- `genre-classifier/tests/test_settings.py`
- `genre-classifier/tests/test_provider_factory.py`
- `genre-classifier/tests/test_classify_orchestration.py`
- `genre-classifier/tests/lightweight/test_optional_onnx_dependency_packaging.py`
- `genre-classifier/app/models/msd-musicnn-1.pb`
- `genre-classifier/evaluation/artifacts/roadmap_2_11`
- `README.md`
- `CHANGELOG.md`
- `genre-classifier/docs/onnx-runtime.md`
- `genre-classifier/docs/releases/v0.5.0.md`

Также сохранены runtime/packaging assumptions, которые не являются мусором и не относятся к cleanup-срезу.

## Safety confirmations

- cleanup ограничен lightweight evidence и report scaffolding;
- app code не изменялся;
- Dockerfile не изменялся;
- docker-compose.yml не изменялся;
- requirements.txt не изменялся;
- default provider не изменялся;
- git history не переписывался;
- tag `v0.5.0` не трогался.

## Notes

`v0.5.0` остаётся стабильным release anchor.

Исторический `roadmap_2_11` в `genre-classifier/evaluation/artifacts/roadmap_2_11` сохранён, потому что он используется в tests/docs/evaluation pipeline и не является мусором.

Следующий follow-up `Roadmap 4.108-fix` обновил `tests/lightweight/test_optional_onnx_dependency_packaging.py`, чтобы он больше не зависел от удалённых parity-scaffold JSON reports и проверял текущий packaging/runtime contract напрямую.
