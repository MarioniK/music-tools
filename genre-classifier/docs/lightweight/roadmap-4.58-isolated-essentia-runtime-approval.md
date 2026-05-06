# Roadmap 4.58 - Isolated local Essentia preprocessing runtime approval gate

## Цель

Roadmap 4.58 фиксирует approval gate для локального isolated runtime
эксперимента с Essentia preprocessing path. Это не production decision и не
шаг к смене default provider.

Задача этого шага - формально разрешить только следующий local-only проверочный
этап: Roadmap 4.59 может выполнить isolated venv Essentia install/check в
`/tmp/music-tools-onnx-parity/venv`.

## Почему выбран Option A

Выбран Option A: isolated local venv install approval.

Причины:

- это самый безопасный способ проверить availability boundary без изменения
  production runtime;
- он сохраняет lightweight direction Roadmap 4.x;
- он не требует менять `requirements*.txt`, `Dockerfile` или Compose;
- он позволяет проверить Essentia в отдельном local-only runtime boundary;
- он не трогает `legacy_musicnn` как production baseline.

## Почему isolated venv соответствует lightweight direction

Изолированный venv подходит для этого этапа, потому что:

- runtime эксперимент отделяется от production dependency set;
- проверка может быть воспроизводимой и локальной;
- результат можно задокументировать без изменения service contract;
- шаг остаётся reversible и не затрагивает соседний сервис.

## Почему `/tmp/music-tools-onnx-parity/venv` является local-only runtime boundary

Это внешний по отношению к репозиторию путь, который не является project
artifact и не должен попадать в commit.

Такой boundary подходит для approval gate, потому что:

- он находится вне `/opt/music-tools`;
- он не добавляет зависимости в репозиторий;
- он не меняет production defaults;
- он не меняет `/classify` contract;
- он не создаёт долгоживущий runtime внутри дерева проекта.

## Почему это не production dependency change

Roadmap 4.58 не устанавливает Essentia и не меняет production dependency
files.

Не происходит:

- обновление `requirements*.txt`;
- изменение `Dockerfile`;
- изменение `docker-compose*.yml`;
- добавление audio/model files;
- переключение provider/default logic;
- запуск inference.

## Почему install/check перенесён в Roadmap 4.59

Roadmap 4.58 только утверждает, что isolated venv эксперимент разрешён как
следующий шаг.

Сам install/check переносится в Roadmap 4.59, чтобы:

- не смешивать approval и execution в одном safe-slice;
- сохранить обозримую rollback-friendly границу;
- отдельно отследить, появится ли `essentia` и `TensorflowInputMusiCNN` в
  isolated env;
- не расширять текущий шаг до runtime validation.

## Почему `legacy_musicnn` остаётся default provider

Текущий production baseline не меняется:

- `legacy_musicnn` остаётся default provider;
- production classifier path остаётся legacy MusiCNN;
- shadow runtime disabled by default;
- production dependencies unchanged.

## Почему `/classify` нельзя вызывать на этом этапе

`/classify` не нужен для approval gate и может создать ложное впечатление о
runtime readiness.

На Roadmap 4.58 нельзя:

- запускать inference;
- проверять ONNX execution;
- выполнять TensorFlow baseline run;
- сравнивать TensorFlow и ONNX outputs;
- менять response shape или contract.

## Isolated venv diagnostic status

Диагностика local-only boundary проведена без установки зависимостей:

- `venv` существует;
- Python version: `3.11.2`;
- `python -m pip` внутри venv недоступен;
- `pip show onnxruntime` не выполнялся, потому что модуль `pip` внутри venv
  отсутствует;
- это зафиксировано только как diagnostic status, без install step.

## Explicit non-goals

- не устанавливать Essentia;
- не устанавливать зависимости вообще;
- не менять production requirements;
- не менять Dockerfile;
- не менять Docker Compose;
- не менять provider/default logic;
- не менять `/classify` contract;
- не менять response shape;
- не запускать `/classify`;
- не запускать inference;
- не запускать ONNX execution;
- не запускать TensorFlow baseline;
- не выполнять TensorFlow vs ONNX comparison;
- не добавлять audio/model files;
- не коммитить venv;
- не трогать `tidal-parser`;
- не делать tag/release;
- не делать commit на этом этапе.

## Next step

Roadmap 4.59 may perform isolated venv Essentia install/check.

Если isolated venv install/check подтвердит нужные imports, следующий шаг
должен отдельно документировать результат и только потом решать, есть ли смысл
переходить к дальнейшей pragmatic ONNX/MusiCNN validation.
