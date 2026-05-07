# Roadmap 4.88: optional ONNX slim Compose config validation

Цель шага:

- проверить корректный рендер `docker compose config` для `genre-classifier`;
- подтвердить, что optional ONNX profile использует `onnx-runtime-slim`;
- зафиксировать постоянный host path для ONNX artifacts вне репозитория;
- не выполнять перенос artifacts и не запускать контейнеры.

Принятое размещение artifacts:

- host: `/opt/music-tools/artifacts/genre-classifier/onnx`
- container: `/opt/genre-classifier/onnx`
- files:
  - `msd-musicnn-1.onnx`
  - `msd-musicnn-1.json`

Статус:

- default service остаётся на `legacy-runtime`;
- optional ONNX service остаётся на `onnx-runtime-slim`;
- runtime downloads по умолчанию не добавлены;
- artifacts не baked into image;
- artifacts в этом шаге не копировались.

Перед runtime smoke вручную требуется:

1. создать persistent host directory;
2. положить туда `msd-musicnn-1.onnx` и `msd-musicnn-1.json`;
3. сверить checksum/provenance с Roadmap 4.71.
