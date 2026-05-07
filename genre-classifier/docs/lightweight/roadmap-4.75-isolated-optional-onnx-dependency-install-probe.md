# Roadmap 4.75 - isolated optional ONNX/MusiCNN dependency install probe gate

## 1. Purpose

Этот шаг проверяет, что `genre-classifier/requirements-optional-onnx.txt` реально устанавливается в изолированном probe environment вне репозитория, и фиксирует фактические версии пакетов и import status.

Это install probe gate, а не production migration, не runtime smoke и не `/classify` execution.

## 2. Scope

В рамках Roadmap 4.75 проверяются только:

- isolated environment вне repo;
- установка `genre-classifier/requirements-optional-onnx.txt` в этот environment;
- `pip` / Python version capture;
- `pip show` для `onnxruntime` и `essentia-tensorflow`;
- import probe для `onnxruntime`, `essentia`, `essentia.standard`;
- проверка наличия `TensorflowInputMusiCNN` в `essentia.standard`;
- фиксация warnings и blockers;
- фиксация того, что production / Docker / default provider / `/classify` contract не меняются.

В рамках этого шага не выполняются:

- изменение `genre-classifier/requirements.txt`;
- добавление optional deps в production requirements;
- Dockerfile / Compose change;
- Docker build / Docker Compose;
- `/classify`;
- runtime smoke;
- production inference;
- real ONNX inference;
- preprocessing probe;
- TensorFlow baseline;
- TensorFlow vs ONNX comparison;
- default provider switch;
- provider factory default change;
- production migration;
- commit / push / tag.

## 3. Probe Environment

Изолированное окружение использовалось вне репозитория:

- path: `/tmp/music-tools-roadmap-4.75-onnx-install-probe/venv`
- Python: `3.11.2`
- pip: `26.1.1`

## 4. Installation Result

`genre-classifier/requirements-optional-onnx.txt` содержит:

- `onnxruntime==1.25.1`
- `essentia-tensorflow==2.1b6.dev1389`

Установка в isolated probe environment завершилась успешно.

Фактические установленные версии:

- `onnxruntime`: `1.25.1`
- `essentia-tensorflow`: `2.1b6.dev1389`

## 5. Import Result

Import probe завершился успешно:

- `import onnxruntime` - ok;
- `import essentia` - ok;
- `import essentia.standard` - ok;
- `hasattr(essentia.standard, "TensorflowInputMusiCNN")` - `True`.

Во время импорта `essentia.standard` были видны ожидаемые runtime warnings, связанные с отсутствием CUDA libraries в окружении probe, но это не помешало import status и доступности `TensorflowInputMusiCNN`.

## 6. Boundary Confirmation

Это подтверждение не означает production readiness и не меняет:

- production requirements;
- Dockerfile / Compose;
- default provider;
- `onnx_musicnn` disabled-by-default status;
- `/classify` contract;
- response shape;
- `tidal-parser`.

## 7. Outcome

Roadmap 4.75 confirms that optional ONNX/MusiCNN dependencies can be installed and imported in an isolated environment outside the repo without changing production defaults or runtime contracts.

## 8. Next Step

Если потребуется следующий шаг, он должен оставаться в safe slice и не должен включать production dependency change, Docker/runtime migration, provider default switch или `/classify` execution.
