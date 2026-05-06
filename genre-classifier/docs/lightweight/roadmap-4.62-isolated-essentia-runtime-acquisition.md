# Roadmap 4.62 - Isolated Essentia runtime acquisition execution and TensorflowInputMusiCNN import probe

## Цель

Этот шаг должен был выполнить local-only acquisition для `essentia` и затем
проверить, доступен ли `TensorflowInputMusiCNN` в isolated runtime.

Цель остаётся строго ограниченной `genre-classifier` и не затрагивает
production path, default provider, Dockerfile, Compose, `/classify`,
TensorFlow baseline, ONNX comparison или full output capture.

## Boundary

Выполнены только безопасные проверки boundary:

- прочитан `/opt/music-tools/AGENTS.md` и инструкции соблюдены;
- проверен `git status --short` до изменений;
- проверен Roadmap 4.61 и его JSON report;
- проверены версии Python и `pip` в `/tmp/music-tools-onnx-parity/venv`;
- выполнен поиск local/offline `essentia` wheel вне репозитория;
- проверена доступность Option B через существующий container boundary
  без `docker compose up` и без rebuild;
- изменения ограничены только документацией и evidence report в `genre-classifier`.

## Option A result

Option A предусматривал offline/local wheel acquisition для isolated venv.
По факту wheel вне репозитория не найден.

Зафиксированный blocker:

- `OFFLINE_LOCAL_ESSENTIA_WHEEL_NOT_AVAILABLE`

Следствие:

- `pip install` из PyPI не выполнялся;
- wheel не устанавливался;
- import-level probe в venv не запускался, потому что runtime для него не был
  подготовлен безопасным способом;
- production dependencies не менялись;
- wheel не коммитился.

## Option B result

Option B допускался только как fallback, если Option A blocked, и только для
import-level probe без изменения контейнера.

В текущем окружении Option B недоступен как safe path:

- доступ к Docker API отсутствует;
- проверка `docker ps` завершилась ошибкой `permission denied`;
- запуск `docker compose up` или rebuild не выполнялся;
- контейнер для безопасного probe подтвердить нельзя.

Зафиксированный blocker:

- `DOCKER_CONTAINER_PROBE_UNAVAILABLE`

## Install target

Единственный допустимый target для установки runtime был бы:

- `/tmp/music-tools-onnx-parity/venv`

Фактическая установка не выполнялась.

## Import result

Import-level probe не выполнялся, потому что безопасный runtime acquisition
не был доступен ни по Option A, ни по Option B.

Фиксируем состояние честно:

- `import essentia` - not executed due blocker;
- `import essentia.standard as es` - not executed due blocker;
- `getattr(essentia, "__version__", None)` - not executed due blocker;
- `hasattr(es, "TensorflowInputMusiCNN")` - not executed due blocker.

## TensorflowInputMusiCNN availability

На этом шаге доступность `TensorflowInputMusiCNN` не подтверждена.
Причина не в доказанном отсутствии символа, а в том, что безопасный runtime
для import probe сейчас недоступен.

## Blockers

- `OFFLINE_LOCAL_ESSENTIA_WHEEL_NOT_AVAILABLE`
- `DOCKER_CONTAINER_PROBE_UNAVAILABLE`
- `ESSENTIA_IMPORT_PROBE_NOT_EXECUTED`

## Explicit non-goals

- не менять production dependencies;
- не менять Dockerfile или Compose;
- не менять provider/default logic;
- не трогать `tidal-parser`;
- не вызывать `/classify`;
- не запускать production inference;
- не запускать TensorFlow baseline;
- не запускать TensorFlow vs ONNX comparison;
- не запускать full ONNX output capture;
- не добавлять audio/model files;
- не коммитить wheel;
- не коммитить venv;
- не делать tag/release.

## Production untouched confirmations

- production dependencies unchanged;
- Dockerfile/Compose unchanged;
- provider/default logic unchanged;
- `tidal-parser` untouched;
- `/classify` not called;
- production inference not run;
- TensorFlow baseline not run;
- TensorFlow vs ONNX comparison not run;
- full ONNX output capture not run;
- no audio/model files added;
- no wheel committed;
- no venv committed;
- no tag/release created.

## Next step

Если безопасный runtime acquisition станет доступен и `TensorflowInputMusiCNN`
будет подтверждён, следующий шаг - Roadmap 4.63 preprocessing-only probe.

Если runtime acquisition останется blocked, нужно продолжать blocker
continuation без расширения scope.
