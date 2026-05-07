# Roadmap 4.96: switch default genre-classifier runtime to ONNX slim

## Цель

Перевести `genre-classifier` на `onnx_musicnn` как новый default provider и сделать `onnx-runtime-slim` default Docker target.

Это production readiness decision для default runtime сервиса `genre-classifier`.

## Что меняется

- default provider меняется с `legacy_musicnn` на `onnx_musicnn`;
- default Docker Compose service target меняется с `legacy-runtime` на `onnx-runtime-slim`;
- default service получает external ONNX artifact mount;
- default service получает `GENRE_PROVIDER=onnx_musicnn`;
- default service получает:
  - `ONNX_MUSICNN_MODEL_PATH=/opt/genre-classifier/onnx/msd-musicnn-1.onnx`
  - `ONNX_MUSICNN_METADATA_PATH=/opt/genre-classifier/onnx/msd-musicnn-1.json`

## Что не меняется

- `/classify` contract остаётся прежним;
- response shape остаётся прежним:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `legacy_musicnn` остаётся доступным для explicit rollback;
- external artifacts остаются вне репозитория;
- runtime downloads by default не включаются;
- `tidal-parser` не трогаем.

## External artifacts

Постоянный host path:

`/opt/music-tools-artifacts/genre-classifier/onnx`

Container mount:

`/opt/genre-classifier/onnx`

Файлы:

- `msd-musicnn-1.onnx`
- `msd-musicnn-1.json`

Контрольные суммы:

- `msd-musicnn-1.onnx`
  - `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`
- `msd-musicnn-1.json`
  - `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe`

## Rollback path

Если нужно вернуть legacy runtime:

1. вернуть default provider на `legacy_musicnn`;
2. вернуть default service target на `legacy-runtime`;
3. убрать ONNX artifact mount и ONNX env из default service;
4. пересобрать и перезапустить `genre-classifier`.

Legacy runtime target и provider сохраняются для безопасного отката.

## Validation

Для проверки использовались:

- `docker compose config`
- `docker compose build genre-classifier`
- `docker compose up -d genre-classifier`
- `curl /health`
- `curl /classify`
- логирование `provider_name=onnx_musicnn`, `provider_class=OnnxMusiCNNProvider`, `file_processing_succeeded`

## Safety boundaries

- не менять response shape;
- не удалять `legacy_musicnn`;
- не удалять `legacy-runtime`;
- не коммитить artifacts;
- не менять `tidal-parser`;
- не делать broad refactor.
