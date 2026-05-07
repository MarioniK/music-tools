# Roadmap 4.72 - ONNX/MusiCNN dependency packaging gate for disabled-by-default runtime smoke

## 1. Purpose

Цель этого шага - зафиксировать минимальный путь упаковки зависимостей для будущего disabled-by-default runtime smoke на базе `onnx_musicnn`, не меняя production runtime и не включая provider.

Это decision gate, а не implementation step.

## 2. Scope

В рамках Roadmap 4.72 рассматриваются только:

- выбор минимального dependency packaging path для будущего smoke-only запуска;
- кандидаты зависимостей `onnxruntime` и `essentia-tensorflow`;
- проверка/фиксация Python ABI и platform compatibility как отдельного gate;
- оценка image-size / dependency weight risk;
- стратегия будущей поставки зависимостей;
- требования к lazy imports и безопасной деградации.

В рамках этого шага не меняются:

- production dependencies;
- Dockerfile / Compose;
- default provider;
- provider factory default;
- `/classify` contract;
- response shape;
- tidal-parser;
- runtime smoke;
- production readiness;
- production approval.

## 3. Inputs from Roadmap 4.64-4.71

Roadmap 4.64 подтвердил preprocessing-only path:

- raw observed shape: `[2948, 96]`;
- final shaped patch: `[187, 96]`;
- repeated-run stability: stable;
- max_abs_diff: `0.0`;
- mean_abs_diff: `0.0`.

Roadmap 4.65 подтвердил ONNX runtime I/O contract:

- `[187, 96]` patch принят official/local ONNX/MusiCNN;
- activations: `[50]`;
- embeddings: `[200]`;
- repeated-run stability: stable.

Roadmap 4.66 подтвердил semantic mapping:

- classes count: `50`;
- activations count: `50`;
- count match: true;
- index order usable: true;
- candidate `genres` / `genres_pretty` shape совместим с текущим response shape.

Roadmap 4.67 зафиксировал provider-safe design contract и mapping decision record.

Roadmap 4.68 создал disabled-by-default `onnx_musicnn` scaffold.

Roadmap 4.69 зафиксировал explicit opt-in artifact paths:

- default model path: `None`;
- default metadata/classes path: `None`;
- no `/tmp` defaults;
- no implicit artifact discovery;
- missing artifacts fail gracefully;
- app startup does not require `onnxruntime` or `essentia`.

Roadmap 4.70 разделил runtime dependency migration и artifact packaging:

- runtime downloads by default prohibited;
- preferred first artifact delivery: explicit mounted artifacts;
- image bundling not approved yet;
- checksums, provenance, and license notes are required before later smoke approval.

Roadmap 4.71 закрыл checksum / provenance / license gate:

- ONNX model checksum зафиксирован;
- metadata/classes checksum зафиксирован;
- provenance and license notes documented;
- artifacts not committed to repo;
- runtime downloads remain prohibited;
- image bundling remains not approved;
- production approval not granted.

## 4. Why dependency packaging gate follows artifact gate

Сначала были подтверждены artifact identity, provenance и license context. Только после этого имеет смысл обсуждать упаковку runtime-зависимостей.

Причины:

- без закреплённых artifacts любая packaging decision была бы преждевременной;
- dependency packaging без artifact gate увеличивает риск скрытого drift;
- `onnxruntime` и `essentia-tensorflow` имеют разный вес, ABI surface и operational footprint;
- runtime smoke должен опираться на уже подтверждённые artifacts, а не на новые источники истины.

Итог: Roadmap 4.72 фиксирует packaging boundary, но не включает runtime.

## 5. Why this is not Docker implementation

Это не Docker-этап, потому что:

- Dockerfile не изменяется;
- docker-compose файлы не изменяются;
- image build logic не меняется;
- service runtime contract не меняется;
- production deployment path не меняется.

Любая упаковка в Docker образ будет отдельным future gate после явной approval decision.

## 6. Why runtime smoke is not approved yet

Runtime smoke пока не approved, потому что отсутствует финальное решение по способу поставки runtime-зависимостей в production-like окружение.

Конкретно:

- exact dependency installation path ещё не выбран;
- Python ABI compatibility ещё должна быть подтверждена на целевой версии интерпретатора;
- platform compatibility ещё должна быть подтверждена на target Linux image;
- Essentia/TensorFlow preprocessing остаётся weight/ABI/license risk;
- production packaging approval не выдан.

Следовательно:

- `onnx_musicnn` остаётся disabled-by-default;
- `legacy_musicnn` остаётся default provider;
- `/classify` contract остаётся неизменным;
- response shape остаётся неизменным.

## 7. ONNX Runtime CPU-only dependency decision

Для будущего disabled-by-default smoke предпочтительный кандидат:

- package_name: `onnxruntime`;
- version_candidate: `1.25.1`;
- cpu_only: true;
- gpu_package_allowed: false;
- source: PyPI / official ONNX Runtime docs;
- install_target_future: optional requirements / future Docker gate;
- lazy_import_required: true;
- startup_import_allowed: false.

Decision:

- CPU-only `onnxruntime` is the preferred ONNX Runtime candidate;
- GPU package is not part of this gate;
- package must be imported lazily and only on `onnx_musicnn` path;
- app startup must not require `onnxruntime`.

Unsupported diagnostics expectations:

- missing package under `onnx_musicnn` must fail gracefully;
- legacy provider path must not import `onnxruntime`;
- startup must remain healthy when `onnxruntime` is absent.

## 8. Essentia preprocessing runtime decision

Для preprocessing кандидат остаётся:

- package_name: `essentia-tensorflow`;
- version_candidate: `2.1b6.dev1389`;
- tensorflow_input_musicnn_required: true;
- required_algorithm: `TensorflowInputMusiCNN`;
- source: PyPI / Essentia docs;
- install_target_future: optional requirements / dev-probe-only env / future Docker gate;
- lazy_import_required: true;
- startup_import_allowed: false;
- weight_risk: high;
- production_ready: false.

Decision:

- `essentia-tensorflow` is the current preprocessing candidate because `TensorflowInputMusiCNN` was the proven preprocessing path in Roadmap 4.64;
- this dependency must stay outside production dependencies at this stage;
- it must not be silently promoted into default runtime packaging.

License note:

- PyPI metadata states `AGPL-3.0-only`;
- this creates an explicit review requirement before any production packaging decision;
- no production approval is granted in Roadmap 4.72.

## 9. Python ABI / platform compatibility requirements

Перед любой implementation gate нужно отдельно подтвердить:

- Python ABI compatibility with the runtime version used by `genre-classifier`;
- wheel/platform compatibility with the target Linux image;
- availability of CPU-only `onnxruntime` for the chosen ABI/platform pair;
- availability of `essentia-tensorflow` for the same environment, if it is to be used in probe-only packaging.

This gate does not claim those compatibilities are already proven. It only records them as required verification items.

## 10. Image-size / dependency weight risk

Risk assessment:

- `onnxruntime` CPU-only size risk: medium;
- `essentia-tensorflow` weight risk: high;
- ABI mismatch risk: medium;
- CPU-only performance risk: medium;
- license review risk for production packaging: high.

Main concern:

- Essentia/TensorFlow preprocessing is the heaviest part of the future smoke path;
- it is the dominant weight and packaging risk;
- it should stay probe-only until a separate approval gate exists.

## 11. Optional requirements strategy

Preferred future packaging strategy:

- separate optional requirements file: future option only;
- dev/probe-only environment: allowed future direction;
- future Docker image packaging: possible later gate;
- staged production dependency gate later: required before production promotion;
- runtime downloads by default: false;
- implicit install: false;
- bundled artifacts: false.

Important:

- this step does not create requirements files;
- this step does not add dependencies to production packaging;
- this step only records the future packaging lane.

## 12. Lazy import and unsupported diagnostics requirements

Required runtime behavior for future smoke-only implementation:

- import `onnxruntime` lazily only when `onnx_musicnn` is selected;
- import `essentia-tensorflow` lazily only when preprocessing is needed;
- app startup must not require either package;
- legacy provider path must remain isolated from ONNX/Essentia imports;
- unsupported and missing-dependency states must be distinguishable in diagnostics.

Safe failure categories should include:

- missing `onnxruntime`;
- missing `essentia-tensorflow`;
- missing model artifact;
- missing metadata/classes artifact;
- invalid metadata/classes JSON;
- empty classes list;
- classes/activations mismatch;
- unsupported runtime/platform combination.

Diagnostics should remain structured and non-sensitive.

## 13. Runtime smoke prerequisites for future gate

Перед будущим disabled-by-default runtime smoke нужно отдельно подтвердить:

- exact dependencies selected;
- artifacts from Roadmap 4.71 are available via explicit mounts;
- artifact checksums are verified before smoke;
- provider is selected explicitly;
- default provider remains `legacy_musicnn`;
- `/classify` contract remains unchanged;
- response shape remains unchanged;
- runtime smoke approval is separate and explicit.

## 14. Explicit non-goals

- no production dependency changes;
- no Dockerfile changes;
- no Compose changes;
- no runtime smoke execution;
- no `/classify` call;
- no production inference;
- no real ONNX inference;
- no TensorFlow baseline;
- no TensorFlow vs ONNX comparison;
- no provider default change;
- no `/classify` contract change;
- no response shape change;
- no production migration;
- no `tidal-parser` changes;
- no ONNX/model files committed;
- no wheel/venv files committed;
- no audio files committed;
- no tag or release;
- no production readiness claim.

## 15. Risks and blockers

Blockers:

- `PRODUCTION_DEPENDENCY_CHANGE_NOT_APPROVED`;
- `DOCKER_CHANGE_NOT_APPROVED`;
- `RUNTIME_SMOKE_NOT_APPROVED`;
- `DEFAULT_PROVIDER_SWITCH_NOT_APPROVED`;
- `PRODUCTION_APPROVAL_NOT_GRANTED`.

Risks:

- `onnxruntime` CPU-only footprint may still be non-trivial;
- `essentia-tensorflow` carries high weight and ABI risk;
- Essentia license context requires explicit production review;
- platform mismatch could break future smoke on the target image;
- startup import leakage could accidentally make optional dependencies mandatory if lazy import is not enforced.

## 16. Rollback strategy

Rollback for this gate is simple because no runtime or packaging change is made.

If this decision later needs to be reverted:

- remove only the documentation/report artifacts from this gate;
- keep `legacy_musicnn` as default;
- keep `onnx_musicnn` disabled-by-default;
- keep production dependencies unchanged;
- keep Dockerfile and Compose unchanged;
- keep artifact gates from 4.71 as the last confirmed evidence.

## 17. Next step recommendation

Prepare a separate dependency packaging implementation gate for optional/dev-only ONNX runtime dependencies before any disabled-by-default runtime smoke.

That next gate should separately confirm:

- exact dependency installation shape;
- Python ABI and platform compatibility;
- image-size impact;
- lazy import boundaries;
- smoke-only execution boundary;
- rollback path;
- no production dependency promotion.

