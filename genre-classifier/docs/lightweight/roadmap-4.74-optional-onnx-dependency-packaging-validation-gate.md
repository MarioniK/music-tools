# Roadmap 4.74 - optional ONNX/MusiCNN dependency packaging validation gate

## 1. Purpose

Этот шаг добавляет lightweight/static validation gate для optional ONNX/MusiCNN dependency packaging path.
Он подтверждает, что optional requirements файл существует, содержит ожидаемые pinned зависимости, и не протекает
в production install path, Docker или default provider path.

Это validation gate, а не runtime smoke и не production migration.

## 2. Scope

В рамках Roadmap 4.74 проверяются только статические признаки:

- `genre-classifier/requirements-optional-onnx.txt` существует;
- optional requirements содержит ожидаемые pinned dependencies;
- optional requirements не содержит запрещённых форм зависимостей;
- production requirements не ссылаются на optional requirements file;
- production requirements не добавляют `onnxruntime`;
- Dockerfile не устанавливает optional requirements file;
- Compose не включает `onnx_musicnn` как default provider;
- default provider остаётся `legacy_musicnn`;
- `onnx_musicnn` остаётся disabled-by-default / explicit opt-in only;
- `/classify` contract и response shape остаются неизменными;
- forbidden model/audio/wheel/venv artifacts не добавляются в этот change set;
- `tidal-parser` остаётся untouched.

В рамках этого шага не выполняются:

- `pip install -r requirements-optional-onnx.txt`;
- Docker Compose;
- Docker build;
- `/classify`;
- inference/runtime smoke;
- TensorFlow baseline;
- TensorFlow vs ONNX comparison;
- provider activation;
- default switch;
- commit / push / tag.

## 3. What is validated

Validation is limited to:

- static text checks for requirements files;
- static text checks for Dockerfile and Compose;
- static settings/provider factory checks;
- static route contract checks;
- JSON report shape checks for the Roadmap 4.74 artifact.

## 4. Current state note

`essentia-tensorflow==2.1b6.dev1389` has been removed from production `requirements.txt` and remains only in
`requirements-optional-onnx.txt`.

`onnxruntime` remains absent from production requirements, and the optional requirements file stays separate.

## 5. Outcome

This step adds a reproducible static validation layer for the optional ONNX packaging path without changing:

- production dependencies;
- Dockerfile / Compose;
- default provider;
- `/classify` contract;
- response shape;
- `tidal-parser`.

## 6. Next step

Roadmap 4.75 may perform an isolated optional install probe only after explicit approval, without Docker/runtime migration.
