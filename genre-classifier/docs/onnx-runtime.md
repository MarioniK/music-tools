# ONNX runtime для `genre-classifier`

Этот документ фиксирует операторский контур для текущего default runtime `genre-classifier` после controlled ONNX default switch.

## Текущая конфигурация

- default provider: `onnx_musicnn`
- default Docker target: `onnx-runtime-slim`
- legacy fallback: `legacy_musicnn`
- legacy rollback service/profile: `genre-classifier-legacy` / `legacy` / `legacy-runtime`

## Артефакты

ONNX runtime зависит от внешних артефактов, которые не должны коммититься в репозиторий:

- host path: `/opt/music-tools-artifacts/genre-classifier/onnx`
- container path: `/opt/genre-classifier/onnx`

Требуемые файлы:

- `msd-musicnn-1.onnx`
- `msd-musicnn-1.json`

Проверенные checksums:

- `msd-musicnn-1.onnx`: `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`
- `msd-musicnn-1.json`: `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe`

## Compose expectations

Default service должен поднимать ONNX runtime через target `onnx-runtime-slim`, использовать соответствующий env/mount и оставаться без изменения `/classify` response shape.

Rollback путь должен оставаться доступным через:

- service `genre-classifier-legacy`
- profile `legacy`
- target `legacy-runtime`
- `GENRE_PROVIDER=legacy_musicnn`

## Проверка состояния

Базовые проверки для оператора:

```bash
curl http://localhost:8021/health
```

Если нужен end-to-end smoke через `tidal-parser`, проверяйте реальный поток через UI или `POST /` в `tidal-parser`.

## Что смотреть в логах

Ожидаемые сигналы успешного ONNX запуска:

- `provider_name=onnx_musicnn`
- `provider_class=OnnxMusiCNNProvider`
- `file_processing_succeeded`

## Ожидаемые предупреждения

Нативные предупреждения TensorFlow/CUDA от зависимостей Essentia могут появляться, но сами по себе не являются блокером, если:

- provider остаётся `onnx_musicnn`;
- обработка завершается успешно;
- health check проходит.

## Что не удалять

Сохраняйте следующие элементы как часть текущего rollback и preprocessing контекста:

- `/opt/music-tools-artifacts/genre-classifier/onnx`
- `essentia-tensorflow` dependency, пока ONNX preprocessing использует Essentia path
- `msd-musicnn-1.pb` fallback model, даже если он lightweight

`msd-musicnn-1.pb` остаётся в репозитории как небольшой fallback/rollback context и не удаляется в этом шаге.

## Что не входит в v0.5.0

- OpenVINO / iGPU runtime
- отдельный GPU-specific rollout
- response shape changes
- `tidal-parser` code migration

CPU ONNX runtime достаточно для v0.5.0, а OpenVINO/iGPU остаётся отдельной будущей опцией.
