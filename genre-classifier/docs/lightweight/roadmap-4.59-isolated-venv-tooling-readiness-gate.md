# Roadmap 4.59 - Isolated venv tooling readiness gate for Essentia preprocessing experiment

## Цель

Roadmap 4.59 фиксирует local-only gate для isolated venv tooling readiness в
`/tmp/music-tools-onnx-parity/venv`.

Задача этого шага - убедиться, что внутри isolated venv снова работает
`python -m pip`, не затрагивая production runtime, provider/default logic,
`/classify` contract или соседний сервис `tidal-parser`.

## AGENTS.md compliance

`/opt/music-tools/AGENTS.md` прочитан и соблюдён.

Подтверждённые границы:

- работает только `genre-classifier`;
- `tidal-parser` не тронут;
- Docker Compose не запускался;
- production dependencies не менялись;
- Dockerfile и Compose-файлы не менялись;
- Essentia не устанавливался;
- TensorFlow не устанавливался;
- `/classify` не вызывался;
- inference не запускался;
- onnxruntime не переустанавливался;
- provider/default logic не менялась;
- response shape не менялась;
- venv не коммитился;
- tag / release / push не делались.

## Проверка isolated venv

Проверенный workspace:

```text
/tmp/music-tools-onnx-parity/venv
```

Команды проверки:

- `.../venv/bin/python -V`
- `.../venv/bin/python -m pip --version`

## Recovery path

Первичный safe path:

- `.../venv/bin/python -m ensurepip --upgrade`

Этот путь не сработал, потому что `ensurepip` отсутствовал в данном окружении.

Стандартный `python3 -m venv` bootstrap тоже был проверен отдельно и не
завершился созданием рабочего `pip`, потому что default venv bootstrap на этом
хосте опирается на `ensurepip`, а нужный bootstrap module недоступен.

Fallback path:

- пересоздать isolated venv;
- локально восстановить только tooling boundary для `pip`;
- повторно проверить `python -m pip --version`.

## Результат

Итог для Roadmap 4.59:

- Python внутри isolated venv: `3.11.2`
- `pip` readiness: `true`
- `pip` version: `23.0.1`
- recovery method: `recreate_venv`
- pip bootstrap method: `manual_local_only_pip_package_copy`

Восстановление было выполнено как local-only tooling step без установки Essentia,
TensorFlow, ONNX runtime или других production dependencies. Чтобы получить
working `pip`, был использован локальный copy-only fallback без изменения repo
dependencies.

## Explicit non-goals

- не устанавливать Essentia;
- не устанавливать TensorFlow;
- не запускать `/classify`;
- не запускать inference;
- не запускать ONNX execution;
- не выполнять TensorFlow baseline;
- не делать TensorFlow vs ONNX comparison;
- не менять production dependencies;
- не менять Dockerfile или Compose;
- не запускать Docker Compose;
- не делать Docker rebuild;
- не менять provider/default logic;
- не менять `/classify` contract;
- не менять response shape;
- не трогать `tidal-parser`;
- не добавлять audio/model files;
- не коммитить venv;
- не делать commit, tag, release или push.

## Следующий шаг

Roadmap 4.60 может использовать этот isolated venv для следующего local-only
experiment gate с Essentia preprocessing, если это будет отдельно разрешено.
