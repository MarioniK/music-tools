# Roadmap 4.60 - Isolated venv Essentia install and TensorflowInputMusiCNN availability check

## Цель

Этот шаг проверяет только local-only runtime boundary в isolated venv
`/tmp/music-tools-onnx-parity/venv`:

- можно ли установить `essentia` через venv-`pip`;
- можно ли импортировать `essentia` и `essentia.standard`;
- доступен ли `TensorflowInputMusiCNN` в этом isolated runtime.

Это не production decision и не шаг к смене default provider.

## Что было сделано

- прочитан `AGENTS.md`;
- проверен report/status Roadmap 4.59;
- проверены версии Python и `pip` внутри isolated venv;
- выполнен `python -m pip install essentia` только через `/tmp/music-tools-onnx-parity/venv/bin/python`;
- выполнен import check для `essentia` и `essentia.standard`;
- собран evidence report:
  `docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-essentia-isolated-venv-report.json`.

## Фактические результаты

- Python inside venv: `Python 3.11.2`;
- pip inside venv: `pip 23.0.1 from /tmp/music-tools-onnx-parity/venv/lib/python3.11/site-packages/pip (python 3.11)`;
- `pip list` не показал `essentia`;
- `pip install essentia` завершился ошибкой из-за недоступности индекса пакетов;
- `import essentia` завершился `ModuleNotFoundError`;
- `TensorflowInputMusiCNN` недоступен, потому что `essentia.standard` не импортируется.

## Блокер

Основной blocker на этом шаге - отсутствие сетевого доступа к Python package index из isolated venv:

- `Failed to establish a new connection: [Errno -2] Name or service not known`
- `ERROR: Could not find a version that satisfies the requirement essentia (from versions: none)`

Следствие:

- local-only install/check не смог подтвердить runtime availability;
- import path для `TensorflowInputMusiCNN` недоступен;
- это не доказывает, что `TensorflowInputMusiCNN` отсутствует в Essentia;
- это доказывает только то, что в текущем isolated venv нет usable Essentia runtime;
- production dependencies, Dockerfile, Compose и provider/default logic не тронуты.

## Подтверждения

- `AGENTS.md` прочитан;
- работал только в `genre-classifier`;
- `tidal-parser` не затронут;
- production dependencies не менялись;
- Dockerfile и Compose не менялись;
- provider/default logic не менялись;
- `/classify` не вызывался;
- production inference не запускался;
- TensorFlow baseline не запускался;
- TensorFlow vs ONNX comparison не выполнялся;
- ONNX output capture не выполнялся;
- audio/model files не добавлялись;
- venv files не коммитились;
- tag/release не создавались.

## Вывод

Roadmap 4.60 остаётся blocked по dependency/runtime boundary. Для этого isolated venv Essentia install/check нужен доступный local-only источник пакета `essentia`; в текущем запуске проверка зафиксировала blocker без изменения репозитория.
