# Roadmap 4.95: optional ONNX slim operator provisioning docs

## Purpose / scope

Этот документ описывает только операторскую подготовку optional `onnx-runtime-slim` для `genre-classifier`.

- ONNX slim runtime остаётся optional only.
- Default provider остаётся `legacy_musicnn`.
- Default service target остаётся `legacy-runtime`.
- Production readiness не заявляется.
- Default switch не разрешён.
- Документ относится только к `genre-classifier`.

## Required external artifacts

Артефакты должны лежать вне репозитория, в постоянной host-директории:

- host directory: `/opt/music-tools-artifacts/genre-classifier/onnx`
- container mount: `/opt/genre-classifier/onnx`
- files:
  - `msd-musicnn-1.onnx`
  - `msd-musicnn-1.json`

Пути внутри контейнера должны использоваться через env:

- `ONNX_MUSICNN_MODEL_PATH=/opt/genre-classifier/onnx/msd-musicnn-1.onnx`
- `ONNX_MUSICNN_METADATA_PATH=/opt/genre-classifier/onnx/msd-musicnn-1.json`

## Checksums

Перед запуском optional profile необходимо сверить checksums:

- `msd-musicnn-1.onnx`
  - `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`
- `msd-musicnn-1.json`
  - `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe`

Если checksum не совпадает, использовать файл нельзя.

## Provisioning steps

1. Создать host directory:

```bash
mkdir -p /opt/music-tools-artifacts/genre-classifier/onnx
```

2. Скопировать внешние артефакты в эту директорию.

3. Проверить checksums:

```bash
cd /opt/music-tools-artifacts/genre-classifier/onnx
sha256sum msd-musicnn-1.onnx
sha256sum msd-musicnn-1.json
```

4. Убедиться, что вывод совпадает с ожидаемыми значениями из раздела `Checksums`.

Warnings:

- не размещать артефакты внутри дерева репозитория;
- не коммитить артефакты;
- не включать runtime downloads by default;
- не встраивать артефакты в image.

## Compose usage

Все команды выполнять из директории `genre-classifier`:

```bash
cd /opt/music-tools/genre-classifier
```

Проверить рендер optional profile:

```bash
docker compose --profile onnx config
```

Поднять только optional ONNX service:

```bash
docker compose --profile onnx up -d genre-classifier-onnx
```

Проверить health:

```bash
curl http://localhost:8021/health
```

Проверить `/classify`:

```bash
curl -X POST -F "file=@/path/to/audio.mp3;type=audio/mpeg" http://localhost:8021/classify
```

Посмотреть логи:

```bash
docker compose --profile onnx logs --tail=80 genre-classifier-onnx
```

Остановить optional service:

```bash
docker compose --profile onnx stop genre-classifier-onnx
```

## Expected success indicators

- health отвечает `200` и `{"ok": true}`;
- `/classify` отвечает `200`;
- response fields присутствуют:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- логи содержат:
  - `provider_name=onnx_musicnn`
  - `provider_class=OnnxMusiCNNProvider`
  - `file_processing_succeeded`

## Troubleshooting

- Missing artifact:
  - проверить путь на host;
  - проверить mount в container;
  - проверить значения `ONNX_MUSICNN_MODEL_PATH` и `ONNX_MUSICNN_METADATA_PATH`.
- Checksum mismatch:
  - заменить артефакт;
  - не продолжать запуск с неподтверждённым файлом.
- TensorFlow/CUDA warnings:
  - такие предупреждения могут появляться от native `essentia` libs;
  - Python `tensorflow` должен оставаться отсутствующим в slim image.
- Import failure:
  - проверить, что используется optional image target `onnx-runtime-slim`;
  - проверить наличие `requirements-optional-onnx`.
- `/classify` returns `500`:
  - проверить логи;
  - проверить путь к артефактам;
  - проверить checksums;
  - проверить, что выбран provider `onnx_musicnn`.
- Port conflict:
  - проверить, не занят ли порт `8021`;
  - проверить активный Compose profile.
- Stale image:
  - rebuild only optional service при необходимости:

```bash
docker compose --profile onnx build genre-classifier-onnx
```

## Rollback

Если нужно безопасно вернуться к legacy path:

```bash
cd /opt/music-tools/genre-classifier
docker compose --profile onnx stop genre-classifier-onnx
```

- default legacy service остаётся отдельным;
- default provider остаётся `legacy_musicnn`;
- default service target остаётся `legacy-runtime`;
- rollback артефактов не требуется, если файлы не заменялись;
- удалять external artifacts нужно только если оператор хочет полностью отключить optional runtime.

## Safety boundaries

- не менять production requirements;
- не менять default provider;
- не bake артефакты в image;
- не включать runtime downloads by default;
- не трогать `tidal-parser`;
- не менять `/classify` contract;
- не менять response shape;
- не заявлять production readiness;
- не считать optional profile default switch.
