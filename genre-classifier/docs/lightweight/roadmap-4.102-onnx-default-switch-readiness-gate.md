# Roadmap 4.102. ONNX default switch readiness gate

## Summary

Roadmap 4.102 фиксирует decision gate после успешных integration smoke 4.99 и 4.101.
Это documentation-only шаг: он оценивает готовность к будущему controlled switch,
но не меняет production default, не запускает runtime smoke и не выполняет миграцию.

## Why this gate exists after the 4.97 incident

Инцидент 4.97 показал, что standalone `/classify` smoke для `genre-classifier`
был недостаточен для безопасного default switch. Реальный `tidal-parser ->
genre-classifier` путь не был подтверждён до переключения, поэтому ONNX default
switch пришлось откатить.

4.98 зафиксировал дизайн integration smoke, 4.99 доказал legacy baseline на
реальном parser-flow, а 4.101 доказал ONNX candidate на том же интеграционном
путе без mutation production containers. Поэтому 4.102 нужен как финальная
readiness decision: gap из 4.97 закрыт для tested request, но switch ещё не делается.

## Current default state

- `genre-classifier` default provider: `legacy_musicnn`
- `genre-classifier` default Docker target: `legacy-runtime`
- `genre-classifier/requirements.txt` содержит `essentia-tensorflow==2.1b6.dev1389`
- ONNX остаётся candidate, not default
- production default после rollback не менялся

## Evidence table

| Roadmap | Scope | Provider | Target | Result | Key evidence |
| --- | --- | --- | --- | --- | --- |
| 4.99 | Legacy integration smoke | `legacy_musicnn` | `legacy-runtime` | Passed | `POST /` on `tidal-parser`, HTTP 200, Reference ID absent, `file_processing_succeeded`, response includes audio genres/final genres |
| 4.101 | ONNX candidate integration smoke | `onnx_musicnn` | `onnx-runtime-slim` | Passed | One-off `tidal-parser` with `AUDIO_CLASSIFIER_URL` override, HTTP 200, Reference ID absent, provider log confirmed `onnx_musicnn`, `file_processing_succeeded`, production containers not mutated |

## Gap closure from 4.97

- 4.97 blocker: standalone `/classify` was insufficient for default switch safety.
- 4.99 подтвердил full integration smoke для legacy baseline.
- 4.101 подтвердил full integration smoke для ONNX candidate без default switch.
- Следовательно, integration smoke gap из 4.97 закрыт для tested fixture/request.

## Readiness decision

ONNX eligible for a future controlled default switch slice.

Это означает, что evidence уже достаточно, чтобы готовить отдельный future
switch step, если он будет explicit, reversible и сопровождаться immediate
post-switch integration smoke.

## Non-decision

Этот шаг не выполняет default switch.

- production default не меняется;
- `legacy_musicnn` остаётся rollback path;
- release/tag не разрешаются этим gate;
- runtime migration не выполняется;
- production containers не мутируются.

## Remaining risks

- Протестирован только один parser request и одна audio fixture.
- ONNX output drift остаётся ожидаемым и должен быть документирован.
- Default switch меняет production runtime dependency on external ONNX artifacts.
- Legacy должен оставаться доступным как rollback path.
- Post-switch integration smoke обязателен сразу после любого будущего switch.
- Production config `tidal-parser` не должна мутироваться casually.

## Mandatory guardrails for future switch

- Separate switch step, не смешанный с decision gate.
- Explicit rollback path.
- Immediate post-switch integration smoke.
- External artifact checks before and after switch.
- No removal of legacy dependency while legacy remains fallback.
- No default provider change without explicit approval.
- No production container mutation as side effect of readiness gate.

## Recommended next roadmap

Roadmap 4.103 — controlled ONNX default switch execution.

Этот следующий шаг должен быть отдельным, reversible и сопровождаться rollback
plan plus immediate post-switch smoke.

## Confirmations

- `AGENTS.md` read and followed
- documentation/decision gate only
- no Docker build
- no Docker Compose run/up
- no `/classify` call
- no parse request
- no network HTTP call
- no inference
- no preprocessing
- no app code changes
- no Dockerfile changes
- no Compose changes
- no requirements changes
- no default provider changes
- no artifacts committed
- `tidal-parser` code untouched
