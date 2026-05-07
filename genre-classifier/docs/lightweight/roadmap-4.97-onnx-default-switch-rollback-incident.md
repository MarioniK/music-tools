# Roadmap 4.97: ONNX default switch rollback incident record

## Summary

Этот документ фиксирует rollback-инцидент вокруг попытки сделать `onnx_musicnn` новым default provider для `genre-classifier`.

Итог инцидента:

- default switch 4.96 оказался преждевременным;
- реальный `tidal-parser -> genre-classifier` flow сломался;
- switch был откатан;
- после rollback проявилась дополнительная проблема с legacy runtime: на старте не хватало `essentia`;
- legacy dependency была восстановлена hotfix-коммитом;
- production baseline снова стабилен на `legacy_musicnn`.

Документ намеренно ограничен incident/rollback record и не является approval для нового default switch.

## Timeline

1. `7b94fec279154daaee354ed950c93fd899c28a4b`
   - `genre-classifier: switch default provider to ONNX MusiCNN`
   - default provider и default runtime target были переключены на ONNX путь.

2. После switch
   - реальный parser-flow начал падать;
   - standalone проверки `genre-classifier` сами по себе выглядели достаточными, но full pipeline не был подтверждён.

3. `70e24e0`
   - `Revert "genre-classifier: switch default provider to ONNX MusiCNN"`
   - rollback восстановил baseline-ориентированную конфигурацию.

4. После rollback
   - legacy container при rebuild/startup упал с:
     `ModuleNotFoundError: No module named 'essentia'`
   - причина была в startup path legacy runtime:
     `from essentia.standard import MonoLoader, TensorflowPredictMusiCNN`

5. `4188c28`
   - `genre-classifier: restore legacy Essentia dependency`
   - в `requirements.txt` возвращён `essentia-tensorflow==2.1b6.dev1389`

6. После hotfix
   - health восстановился;
   - `/classify` снова возвращает `ok=true` с non-empty `genres` и `genres_pretty`;
   - реальный `tidal-parser -> genre-classifier` flow снова работает;
   - ONNX leftover image/container удалены;
   - build cache очищен.

## What Worked

- Standalone ONNX candidate path был валиден в изолированных проверках.
- Документы и evidence по ONNX-ветке показали, что candidate/runtime experiments были полезны и не потеряли ценность.
- Optional ONNX runtime как candidate остался рабочим направлением для будущих итераций.

## What Failed

- Full real parser-flow не был проверен до default switch.
- Standalone `/classify` smoke для `genre-classifier` оказался недостаточным критерием для production default switch.
- Legacy rebuild после rollback оказался не воспроизводим без восстановленного `essentia` dependency.

## Current Stable State

- Default provider восстановлен на `legacy_musicnn`.
- Default service target восстановлен на `legacy-runtime`.
- Production baseline снова stable.
- ONNX остаётся candidate, а не default.

## Root Causes / Findings

- Primary finding: ONNX default switch был преждевременным, потому что отсутствовал full integration smoke на реальном parser-flow.
- Secondary finding: legacy rebuild сломался из-за dependency gap после изоляции runtime dependencies.
- Legacy startup failure:
  - `ModuleNotFoundError: No module named 'essentia'`
  - startup import path: `from essentia.standard import MonoLoader, TensorflowPredictMusiCNN`
- ONNX candidate evidence remains valid, но этого недостаточно для default approval.

## Guardrails Before Next Default Switch Attempt

- Сначала запускать full `tidal-parser -> genre-classifier` integration smoke.
- Проверять реальный parser-flow, а не только standalone `/classify`.
- Держать rollback path готовым и задокументированным.
- Не убирать legacy runtime dependency, пока legacy path остаётся fallback/default.
- Считать ONNX candidate только candidate, пока integration smoke не пройден.

## Non-Goals

- Нет нового ONNX default switch.
- Нет runtime smoke в этом шаге.
- Нет изменений в `tidal-parser`.
- Нет изменений app code, Dockerfile, compose, requirements или response shape.

## Decision

- ONNX остаётся candidate, not default.
- `legacy_musicnn` остаётся stable default.
- Следующая попытка switch возможна только после отдельного integration-focused slice.

## Cleanup

- Старый WIP stash `wip-roadmap-4.97-before-onnx-default-rollback` считается obsolete.
- Stash не удалён в рамках этого шага, потому что это отдельное решение и явное подтверждение не требовалось.
