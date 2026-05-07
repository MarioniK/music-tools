# Roadmap 4.87 - optional ONNX slim Compose profile static validation

Статус: local-only static validation, не production decision.

## Контекст

- `genre-classifier` уже имеет slim target `onnx-runtime-slim`.
- Default runtime остаётся `legacy-runtime`.
- Default provider остаётся `legacy_musicnn`.
- Эта итерация не запускает `docker compose up`.
- Эта итерация не вызывает `/classify`.
- Network HTTP smoke не выполняется.
- Production readiness не заявляется.

## Что проверено

- optional `genre-classifier-onnx` service/profile использует `target: onnx-runtime-slim`;
- default `genre-classifier` service остаётся на `target: legacy-runtime`;
- optional service явно задаёт `GENRE_PROVIDER=onnx_musicnn`;
- explicit mounted artifact paths сохранены только в optional service;
- runtime downloads по умолчанию отсутствуют;
- full `onnx-runtime` target в `Dockerfile` сохранён как fallback;
- `Dockerfile` в этом slice не изменялся.

## Валидация

- статическая проверка compose profile обновлена;
- lightweight report для Roadmap 4.87 добавлен;
- предыдущий report Roadmap 4.86 оставлен как baseline evidence;
- `tidal-parser` не затронут.

## Non-goals

- не менять default provider;
- не менять `/classify` contract;
- не менять response shape;
- не делать production readiness claim;
- не запускать Docker Compose;
- не запускать production inference;
- не добавлять runtime downloads;
- не менять production dependency files.

