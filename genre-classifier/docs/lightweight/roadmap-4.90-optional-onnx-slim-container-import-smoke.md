# Roadmap 4.90: optional ONNX slim container import smoke via Compose profile

## Краткое описание

Выполнен controlled container import/artifact smoke для optional ONNX slim профиля `genre-classifier-onnx` через `docker compose --profile onnx run --rm --no-deps`.

Это не `docker compose up`, не запуск сервера, не `/classify`, не network HTTP smoke и не production readiness.

## Использованный compose command

```bash
cd /opt/music-tools/genre-classifier
docker compose --profile onnx run --rm --no-deps genre-classifier-onnx python3 - <<'PY'
...
PY
```

## Итог по образу

- Optional image отсутствовал на старте.
- `docker compose run` автоматически выполнил targeted build только для `genre-classifier-onnx`.
- Default service не собирался.

## Mounted artifacts

- Model file: present.
- Metadata file: present.
- Persistent host mount использован:
  - `/opt/music-tools-artifacts/genre-classifier/onnx:/opt/genre-classifier/onnx:ro`

## Checksums inside container

- `msd-musicnn-1.onnx`: `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`
- `msd-musicnn-1.json`: `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe`

Обе проверки совпали с ожидаемыми хешами.

## Env checks

- `GENRE_PROVIDER=onnx_musicnn`
- `ONNX_MUSICNN_MODEL_PATH=/opt/genre-classifier/onnx/msd-musicnn-1.onnx`
- `ONNX_MUSICNN_METADATA_PATH=/opt/genre-classifier/onnx/msd-musicnn-1.json`

## Import checks

- `tensorflow` import: absent.
- `essentia` import: ok.
- `essentia.standard` import: ok.
- `TensorflowInputMusiCNN`: available.
- `onnxruntime` import: ok.
- `onnxruntime` CPU provider: available.
- `app.providers.onnx_musicnn` import: ok.

## Provider module status

Optional provider module импортируется безопасно и не запускает inference на import path.

## Blockers / warnings

- Blockers: none.
- Warning: compose run had to build the optional ONNX image because it was missing locally at the start of smoke.

## Confirmations

- `AGENTS.md` read and followed.
- Optional ONNX slim compose profile used.
- Persistent artifacts mounted.
- Checksums matched inside container.
- No `docker compose up`.
- No server start.
- No `/classify` call.
- No network HTTP call.
- No inference.
- No preprocessing.
- No production dependency changes.
- No Dockerfile changes.
- No Compose changes.
- No default provider changes.
- No response shape changes.
- No production readiness claim.
- No artifacts committed.
- `tidal-parser` untouched.
