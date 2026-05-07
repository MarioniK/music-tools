# Roadmap 4.101: ONNX candidate integration smoke without default switch

## Цель

Проверить реальный full parser-flow:

`tidal-parser -> genre-classifier-onnx`

без переключения default provider и без изменения production baseline.

## Что было проверено

- `genre-classifier` default provider остался `legacy_musicnn`.
- `genre-classifier` default Docker target остался `legacy-runtime`.
- `essentia-tensorflow==2.1b6.dev1389` остался в `requirements.txt`.
- Production `tidal-parser` и production `genre-classifier` не были мутированы.
- ONNX candidate `genre-classifier-onnx` был поднят только через профиль `onnx`.
- One-off `tidal-parser` контейнер использовал `AUDIO_CLASSIFIER_URL=http://genre-classifier-onnx:8021/classify`.

## Итог smoke

- HTTP запрос `POST /` вернул `200`.
- Ответ сохранил ожидаемую HTML-форму.
- В ответе присутствуют audio genres.
- Логи `genre-classifier-onnx` подтвердили выбор `onnx_musicnn`.
- После smoke candidate был остановлен, production baseline остался доступен.

## Команды

- `docker compose --profile onnx build genre-classifier-onnx`
- `docker compose --profile onnx up -d genre-classifier-onnx`
- `docker compose --profile onnx stop genre-classifier-onnx`
- One-off `tidal-parser` smoke в отдельном контейнере на сети `musicnet`

