# Roadmap 4.73 - optional ONNX/MusiCNN dependency packaging implementation gate

## 1. Purpose

Цель этого шага - зафиксировать отдельный optional/dev-only dependency packaging artifact для будущего disabled-by-default ONNX/MusiCNN smoke path, не меняя production runtime, Docker, provider default или `/classify` contract.

Это implementation gate для упаковки зависимостей, а не production migration и не runtime smoke.

## 2. Scope

В рамках Roadmap 4.73 рассматриваются только:

- отдельный optional requirements artifact для будущего ONNX/MusiCNN smoke path;
- exact pinned версии зависимостей;
- явная фиксация того, что артефакт не подключён к production install path;
- подтверждение, что default provider остаётся `legacy_musicnn`;
- подтверждение, что `onnx_musicnn` остаётся disabled-by-default;
- lightweight static validation optional requirements file;
- документирование границ для следующего шага.

В рамках этого шага не меняются:

- production requirements;
- Dockerfile / Compose;
- provider factory default;
- default provider;
- `/classify` contract;
- response shape;
- tidal-parser;
- runtime smoke;
- production readiness;
- production approval;
- inference path;
- model artifact handling;
- audio artifact handling;
- wheel / venv artifacts;
- runtime downloads;
- implicit artifact discovery.

## 3. What was added

Добавлен отдельный optional/dev-only requirements file:

- `genre-classifier/requirements-optional-onnx.txt`

Содержимое файла зафиксировано как минимальный pinned set для будущего disabled-by-default smoke path:

- `onnxruntime==1.25.1`
- `essentia-tensorflow==2.1b6.dev1389`

Этот файл создан только как packaging gate и не означает разрешение на runtime smoke.

## 4. Why this is not a production dependency change

Этот шаг не является production dependency change, потому что:

- production requirements не изменялись;
- production install path не перенаправлен на optional файл;
- Dockerfile и Compose не используют этот файл по умолчанию;
- default provider остаётся `legacy_musicnn`;
- `onnx_musicnn` остаётся explicit opt-in only;
- runtime smoke не approved;
- production readiness не заявляется.

Итог: это отдельный optional packaging artifact, а не миграция production runtime.

## 5. Optional dependency details

### 5.1 ONNX Runtime

- package_name: `onnxruntime`
- version: `1.25.1`
- cpu_only: true
- gpu_package_allowed: false
- lazy_import_required: true
- startup_import_allowed: false

### 5.2 Essentia preprocessing runtime

- package_name: `essentia-tensorflow`
- version: `2.1b6.dev1389`
- required_algorithm: `TensorflowInputMusiCNN`
- tensorflow_input_musicnn_required: true
- lazy_import_required: true
- startup_import_allowed: false
- weight_risk: high
- production_ready: false

## 6. Validation notes

Для этого шага допустима только lightweight static validation optional requirements file.

Не разрешается:

- install dependency set;
- import `onnxruntime`;
- import `essentia`;
- import `tensorflow`;
- запуск inference;
- вызов `/classify`;
- Docker Compose;
- runtime smoke;
- TensorFlow baseline;
- TensorFlow vs ONNX comparison.

## 7. Outcome

Результат Roadmap 4.73:

- optional/dev-only dependency packaging artifact добавлен;
- production requirements unchanged;
- Dockerfile / Compose unchanged;
- provider default unchanged;
- `onnx_musicnn` remains disabled-by-default;
- `/classify` contract unchanged;
- response shape unchanged;
- runtime smoke not approved;
- production approval false.

## 8. Next step

Рекомендуемый следующий шаг - Roadmap 4.74, который должен проверять optional dependency packaging path без изменения production requirements, Docker, provider defaults, `/classify` contract и без запуска production inference.
