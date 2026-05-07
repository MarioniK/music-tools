# Roadmap 4.94: ONNX slim operational readiness gate

## Summary

Этот документ фиксирует операционный decision gate для `onnx-runtime-slim` в `genre-classifier`.
По итогам уже подтверждённых шагов 4.85–4.93 ONNX slim-путь признан документированным optional runtime candidate, но не production default и не production readiness.

## Evidence

| Roadmap | Что доказано | Итог |
| --- | --- | --- |
| 4.85 | Добавлен optional Docker target `onnx-runtime-slim`, размер slim image уменьшен, TensorFlow Python package отсутствует | Passed |
| 4.86 | Slim performance baseline показал отсутствие регрессии и сигнал `same/faster` | Passed |
| 4.87 | Compose profile статически переключает optional ONNX service на `onnx-runtime-slim`, default остаётся `legacy-runtime` | Passed |
| 4.88 | Подтверждён persistent host artifact path и отсутствие baked artifacts / runtime downloads by default | Passed |
| 4.89 | Артефакты вынесены вне репозитория, checksum match подтверждён | Passed |
| 4.90 | Container import smoke подтвердил отсутствие TensorFlow и успешные импорты provider stack | Passed |
| 4.91 | Provider direct smoke подтвердил audio -> preprocessing -> ONNX inference -> mapping | Passed |
| 4.92 | Benchmark legacy vs ONNX slim показал выигрыши по времени и памяти при контролируемом drift | Passed |
| 4.93 | Optional `/classify` smoke прошёл с неизменённым response shape и выбранным `onnx_musicnn` provider | Passed |

## Decision

ONNX slim зафиксирован как documented optional runtime candidate.
Это означает, что путь пригоден как опциональная runtime-ветка для операторского использования и дальнейшей оценки.

## Non-decisions

- Нет production readiness approval.
- Нет default switch на `onnx_musicnn`.
- Нет переключения default service target с `legacy-runtime`.
- Нет миграции `tidal-parser`.
- Нет изменения `/classify` contract.

## Operational notes

- Persistent artifacts размещаются вне репозитория: `/opt/music-tools-artifacts/genre-classifier/onnx`.
- Чек-суммы model и metadata уже сопоставлены с provenance record.
- Runtime downloads by default не включены.
- Артефакты не baked into image.

## Risks

- Output drift между legacy и ONNX slim контролируем, но он не идентичен.
- Текущая smoke/benchmark coverage опирается на ограниченный fixture set.
- Для production default switch требуется более широкая проверка и отдельное явное одобрение.
- External artifact provisioning остаётся операторской обязанностью.

## Next steps

1. Подготовить operator provisioning docs и troubleshooting notes для отсутствующих артефактов и checksum mismatch.
2. Расширить optional ONNX slim smoke или benchmark на несколько fixture.
3. При необходимости добавить README/operator documentation о том, что runtime является опциональным.
4. Default switch рассматривать только после отдельного явного решения.

## Boundary summary

Этот gate не меняет production defaults, response shape, `/classify` contract, Dockerfile или Compose.
Он только документирует текущую готовность `onnx-runtime-slim` как optional candidate и границы, которые сохраняются до следующего этапа.
