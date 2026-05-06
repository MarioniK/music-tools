# Roadmap 4.61 - Essentia package acquisition strategy for isolated preprocessing probe

## Краткое резюме

Roadmap 4.61 фиксирует decision gate для стратегии получения `essentia`
runtime для isolated preprocessing probe в `genre-classifier`.

Этот шаг не устанавливает `essentia`, не меняет production dependencies,
не трогает `Dockerfile` / Compose и не запускает `/classify` или inference.
Цель шага - выбрать безопасный и воспроизводимый путь получения runtime для
последующего local-only probe.

## Контекст Roadmap 4.60

Roadmap 4.60 проверил только isolated venv boundary в
`/tmp/music-tools-onnx-parity/venv` и зафиксировал, что:

- `python` внутри venv доступен: `Python 3.11.2`;
- `pip` внутри venv доступен: `pip 23.0.1`;
- `pip install essentia` не смог получить пакет из package index / PyPI;
- `import essentia` завершился `ModuleNotFoundError`;
- `TensorflowInputMusiCNN` не удалось подтвердить, потому что
  `essentia` runtime не был доступен.

Вывод из 4.60 важен: blocker относится к acquisition boundary, а не к
доказанной непригодности `TensorflowInputMusiCNN`.

## Классификация blocker

Блокер 4.60 классифицируется как `package_acquisition_blocker`.

Это означает, что:

- текущая проблема находится на этапе получения runtime;
- отсутствие доступа к package index не закрывает ONNX/MusiCNN lane;
- путь `official_onnx_musicnn` остаётся целевым кандидатом;
- production baseline и default provider остаются неизменными.

## Почему blocker по package index не закрывает ONNX/MusiCNN lane

Roadmap 4 переводит `genre-classifier` на более лёгкий
`ONNX/MusiCNN` path, сохраняя `/classify` contract и response shape.

Проверка 4.60 не показала проблему в самой целевой архитектуре:

- не было выполнено ни одного ONNX execution run;
- не было выполнено TensorFlow baseline rerun;
- не было выполнено сравнение TensorFlow vs ONNX;
- не было изменений provider/default logic;
- не было изменений production dependencies.

Следовательно, package-index failure мешает только acquisition phase и не
является доказательством того, что `official_onnx_musicnn` непригоден.

## Почему сейчас не добавляем Essentia в production requirements

Мы не добавляем `essentia` в production requirements на этом этапе, потому что
это было бы лишним расширением scope.

Причины:

- blocker сейчас находится в acquisition strategy, а не в production runtime;
- production baseline должен остаться стабильным;
- changing requirements files сейчас создало бы ненужный migration surface;
- задача 4.61 - зафиксировать decision gate, а не менять deployment path;
- repo-level production defaults и contract должны остаться без изменений.

## Выбранная стратегия: Option A

Предпочтительная стратегия - `Option A`, offline/local wheel acquisition for
isolated venv.

Смысл стратегии:

- подготовить `essentia` wheel вне репозитория;
- сохранить wheel для будущего использования только в
  `/tmp/music-tools-onnx-parity/venv`;
- не устанавливать `essentia` на этапе 4.61, если шаг остаётся decision gate;
- фиксировать provenance, version и source notes до любого будущего install.

### Требования к provenance и версии wheel

Любой wheel для следующего шага должен иметь documented provenance:

- точное имя файла wheel;
- точную версию `essentia`;
- источник получения или сборки;
- `sha256` или другой однозначный checksum;
- сведения о совместимости с Python 3.11.2 и целевой платформой;
- дату и контекст получения;
- подтверждение, что wheel предназначен только для isolated probe и не
  коммитится в репозиторий.

## Fallback strategy: Option B

Если `Option A` окажется заблокированной, допускается только
`Option B` - use existing genre-classifier container only for
`TensorflowInputMusiCNN` import-level probe.

Policy for Option B:

- probe-only;
- не вызывать `/classify`;
- не делать provider integration;
- не менять production files;
- не запускать production inference;
- не сравнивать ONNX и TensorFlow outputs;
- не менять default provider;
- использовать только для import-level confirmation.

## Deferred strategy: Option C

`Option C` остаётся deferred:

- disposable probe environment outside repo;
- outside production deployment;
- использовать только если `Option A` и `Option B` непригодны.

## Explicit non-goals

- no provider implementation;
- no default provider switch;
- no production migration;
- no production dependency changes;
- no Dockerfile/Compose changes;
- no `/classify` calls;
- no inference;
- no ONNX execution;
- no TensorFlow baseline rerun;
- no TensorFlow vs ONNX comparison;
- no audio/model files;
- no venv files committed;
- no wheel committed;
- no `tidal-parser` changes;
- no tag/release.

## Validation performed

В рамках этого шага были выполнены только безопасные проверки:

- прочитан `/opt/music-tools/AGENTS.md`;
- проверен report/status Roadmap 4.60;
- проверены версии Python и `pip` внутри isolated venv;
- подтверждено, что новые пакеты не устанавливались;
- подтверждено, что `/classify` не вызывался;
- подтверждено, что inference и ONNX execution не запускались;
- подтверждено, что TensorFlow baseline не запускался;
- подтверждено, что `tidal-parser` не тронут.

## Next Roadmap 4.62

Roadmap 4.62 - isolated Essentia runtime acquisition execution and
`TensorflowInputMusiCNN` import probe.

Этот шаг должен использовать выбранную acquisition strategy, но не должен
расширять scope до production migration или provider changes.
