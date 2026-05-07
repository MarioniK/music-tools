# Roadmap 4.98 - tidal-parser to genre-classifier integration smoke design

## Summary

Roadmap 4.98 фиксирует дизайн будущего integration smoke для реальной цепочки
`tidal-parser -> genre-classifier`. Это documentation-only шаг после rollback
инцидента 4.97. Он не меняет runtime, не запускает smoke и не переключает ONNX.

## Why 4.98 exists after the 4.97 incident

Инцидент 4.97 показал, что standalone smoke для `genre-classifier` через
`/classify` недостаточен. ONNX default switch был откатан, потому что реальный
parser-flow не был подтверждён до переключения. Поэтому 4.98 нужен как design
gate: сначала описываем, как проверять полный путь `tidal-parser ->
genre-classifier`, и только потом допускаем отдельный legacy smoke в 4.99.

## Current stable baseline

Текущий stable baseline зафиксирован так:

- `genre-classifier` default provider: `legacy_musicnn`
- `genre-classifier` default Docker target: `legacy-runtime`
- `requirements.txt` снова содержит `essentia-tensorflow==2.1b6.dev1389`
- real parser-flow восстановлен
- ONNX default switch откатан
- ONNX остаётся candidate, not default

Это означает, что 4.98 должен описывать путь проверки baseline, а не менять
его.

## Why standalone `/classify` was insufficient

Standalone `/classify` smoke проверяет только локальный classifier boundary.
После 4.97 стало ясно, что этого недостаточно для решения о default switch,
потому что:

- `tidal-parser` может передавать другой request shape, чем ожидает локальный smoke;
- логика request_id / Reference ID и пользовательского error path живёт на стороне
  `tidal-parser`;
- реальный интеграционный путь включает HTTP boundary внутри docker network;
- full parser-flow может ломаться при успешном standalone `/classify`.

Вывод: standalone smoke полезен, но не может быть единственным критерием для
default switch.

## Future 4.99 legacy integration smoke design

Roadmap 4.99 должен проверить текущий production baseline на реальном
parser-flow.

### Target

- путь: `tidal-parser -> genre-classifier`
- provider: `legacy_musicnn`
- default switch: `false`

### Smoke input

Нужен один воспроизводимый реальный TIDAL URL или заранее выбранный parser
request. По текущему коду `tidal-parser` имеет GET маршрут `/api/parse` с query
параметром `url`, то есть базовый формат smoke запроса должен быть совместим с
`GET /api/parse?url=<TIDAL_URL>&force_refresh=0`.

### Success criteria

- `tidal-parser` возвращает successful response;
- `genre-classifier` получает `audio/classify` request;
- в логах `genre-classifier` есть `file_processing_succeeded`;
- response сохраняет ожидаемый parser output shape;
- audio genres присутствуют или graceful degraded behavior документирован;
- нет `5xx`;
- request_id / correlation id фиксируется, если есть;
- нет user-facing `Reference ID` error page.

### Purpose

4.99 должен зафиксировать known-good baseline для текущего legacy режима, чтобы
потом безопасно сравнивать ONNX candidate against the same real integration path.

## Future 4.100 ONNX candidate integration smoke design

Roadmap 4.100 должен проверить ONNX candidate в полном parser-flow без default
switch.

### Target

- путь: `tidal-parser -> genre-classifier`
- provider: `onnx_musicnn`
- default switch: `false`

### Design requirement

Нужен explicit classifier URL / override / compose profile только для smoke.
Если такого override в проекте сейчас нет, это должно быть зафиксировано как
design requirement, а не реализовано в 4.98.

### Success criteria

- `tidal-parser` возвращает successful response using ONNX candidate classifier
  endpoint;
- `genre-classifier` logs show `provider_name=onnx_musicnn`;
- нет `5xx`;
- response shape preserved;
- output drift допустим только если он контролируемый и документированный.

### Boundary

ONNX candidate smoke не должен менять default provider, default compose service
или production runtime behavior.

## Evidence collection checklist

Для будущего smoke нужно собирать:

- command/request used;
- HTTP status;
- response excerpt / shape;
- `tidal-parser` logs tail;
- `genre-classifier` logs tail;
- `request_id` / `Reference ID`, если присутствует;
- provider selected in `genre-classifier` logs;
- duration, если легко получить;
- final classification fields.

## Failure handling

- Если parser возвращает user-facing error, собрать `Reference ID` и логи.
- Если `genre-classifier` падает, собрать provider logs и traceback.
- Если случился timeout, зафиксировать timeout boundary.
- Если response shape изменился, считать это blocker.
- Если ONNX candidate ломается только в интеграции, оставить legacy default.

## Guardrails

- no default switch before full integration smoke passes;
- no removal of legacy dependency while legacy remains default/fallback;
- no ONNX artifact commit;
- no runtime downloads by default;
- no `tidal-parser` config migration в том же slice, что и smoke, без явного
  approval;
- rollback path must remain simple.

## Non-goals

- нет runtime smoke;
- нет Docker build;
- нет Docker Compose run;
- нет `/classify` call;
- нет parse request execution;
- нет ONNX switch;
- нет production config change;
- нет response shape change;
- нет app code change.

## Decision

No default switch until full integration smoke passes.
