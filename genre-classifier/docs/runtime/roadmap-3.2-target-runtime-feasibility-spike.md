# Roadmap 3.2 — Target runtime feasibility spike

## Статус

- completed
- service: `genre-classifier`
- scope: investigation / design / feasibility
- production migration: no
- provider promotion: no
- LLM cutover: no

## Цель этапа

Roadmap 3.2 фиксирует feasibility decision для будущей модернизации runtime `genre-classifier`.

Цель этапа — оценить, какие target runtime направления допустимо исследовать дальше, не меняя production behavior. Этот этап не является migration stage: он не меняет Python/runtime в production, не меняет Dockerfile, `docker-compose.yml`, dependency files, provider default, `/classify` contract или response shape.

Roadmap 3.2 опирается на Roadmap 3.1:

- commit: `c4b5072`
- artifact: `docs/runtime/roadmap-3.1-runtime-inventory-and-compatibility-audit.md`
- решение Roadmap 3.1: `Ready for Roadmap 3.2 feasibility spike`

## Что не входит в scope

В Roadmap 3.2 не входит:

- production Python upgrade
- production Docker/base image replacement
- dependency upgrade в production
- изменение `Dockerfile`
- изменение `docker-compose.yml`
- изменение `requirements.txt`
- изменение provider default
- изменение `/classify` contract
- изменение response shape
- canary rollout
- LLM cutover
- LLM production adoption decision
- provider promotion
- любые изменения в `tidal-parser`

## Исходное состояние после Roadmap 3.1

Текущий authoritative runtime baseline из Roadmap 3.1:

- Python `3.6.9`
- Ubuntu `18.04.3 LTS`
- TensorFlow `1.15.0`
- Essentia `2.1-beta6-dev`
- numpy `1.19.5`
- protobuf `3.11.3`
- h5py `2.10.0`
- FastAPI `0.83.0`
- Pydantic `1.9.2`
- Uvicorn `0.16.0`

Roadmap 3.1 также зафиксировал, что `python` executable отсутствует в текущем container PATH, `python3` присутствует, `/health` и `/classify` smoke baseline прошли, а `pytest` не установлен внутри текущего runtime container.

Текущий runtime остаётся rollback authority до отдельного доказанного и одобренного production migration stage.

## Repository facts

Runtime files:

- `Dockerfile`
  - использует base image `mtgupf/essentia-tensorflow:latest`;
  - устанавливает `ffmpeg` через apt;
  - unpinned обновляет `pip setuptools wheel`;
  - устанавливает `requirements.txt`;
  - стартует `uvicorn app.main:app --host 0.0.0.0 --port 8021`.
- `docker-compose.yml`
  - определяет только service `genre-classifier`;
  - port mapping: `8021:8021`;
  - external network: `musicnet`;
  - provider/runtime env vars в compose не заданы.

Dependency files:

- `requirements.txt` содержит:
  - `fastapi==0.83.0`
  - `uvicorn==0.16.0`
  - `python-multipart==0.0.5`
  - `jinja2==3.0.3`
  - `numpy==1.19.5`
- TensorFlow и Essentia не закреплены в `requirements.txt`.
- TensorFlow и Essentia наследуются из base image.
- Base image использует floating tag `latest`.
- Lockfile, constraints file, `pyproject.toml` и `setup.py` не найдены.

API baseline:

- `/health` возвращает `{"ok": true}`.
- `/classify` success response keys:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- Response shape должен оставаться неизменным.

## Runtime/dependency findings

Текущий runtime сильно зависит от base image. В `requirements.txt` закреплены только app-level зависимости, но не зафиксированы TensorFlow, Essentia и системные библиотеки, которые критичны для legacy MusiCNN path.

Основные dependency risks:

- `mtgupf/essentia-tensorflow:latest` является floating input, поэтому rebuild может получить другой upstream content.
- `ffmpeg` устанавливается через apt без pinning.
- `pip setuptools wheel` обновляются без pinning.
- TensorFlow `1.15.0` и Essentia `2.1-beta6-dev` являются runtime-critical, но приходят из base image.
- numpy `1.19.5`, protobuf `3.11.3` и h5py `2.10.0` совместимы с текущим legacy stack, но являются compatibility-sensitive для Python/runtime modernization.
- Отсутствие lockfile/constraints file усложняет reproducible rebuild и dependency resolver evidence.

Вывод: прямое изменение production runtime без предварительного isolated build evidence является высоким риском.

## Legacy MusiCNN compatibility findings

Legacy provider path:

- `/classify` в `app/api/routes.py` вызывает `classify_upload`.
- `classify_upload` вызывает `process_uploaded_audio`.
- `process_uploaded_audio` вызывает `get_genre_provider(settings)`.
- Default provider остаётся `legacy_musicnn`.
- `LegacyMusiCNNProvider` вызывает `run_genre_classification` из `app.services.classify`.
- `run_genre_classification` использует:
  - `MonoLoader`
  - `TensorflowPredictMusiCNN`
  - `app/models/msd-musicnn-1.pb`
  - `app/models/msd-musicnn-1.json`
  - `np.mean` по activations.
- `app.services.classify` импортирует Essentia на module import time.

Model/runtime assumptions:

- `MODEL_PB`: `app/models/msd-musicnn-1.pb`
- `MODEL_JSON`: `app/models/msd-musicnn-1.json`
- Metadata:
  - framework: `tensorflow`
  - framework version: `1.15.0`
  - model type: `frozen_model`
  - inference sample rate: `16000`
  - algorithm: `TensorflowPredictMusiCNN`
  - classes: `50`
- Upload limit: `20 MB`
- Allowed extensions: `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`
- `ffmpeg` normalizes input to mono 16 kHz WAV.
- Essentia `MonoLoader` loads WAV with `sampleRate=16000`.

Compatibility implication:

- Any target Python/runtime must prove that Essentia can import and provide `TensorflowPredictMusiCNN`.
- It must prove that the frozen TensorFlow 1.15-era `.pb` model can be loaded and executed.
- It must preserve audio normalization behavior and `/classify` response shape.
- Because Essentia is imported at module import time, missing or incompatible Essentia can break app import before request handling begins.

## Target Python compatibility assessment

### Python 3.7

- Assessment: possible bridge experiment, not strategic target.
- Rationale:
  - It is closer to current Python `3.6.9` and may reduce migration distance for a compatibility experiment.
  - It is still an old/EOL line and should not be treated as a durable modernization target.
  - It may be useful only to understand whether the legacy TensorFlow/Essentia stack can move at all without a full runtime replacement.
- Decision: may be evaluated only as an isolated bridge experiment.

### Python 3.10

- Assessment: candidate for isolated experimental runtime spike.
- Rationale:
  - It is a more realistic modernization target than Python 3.7.
  - It still requires evidence for Essentia availability, TensorFlow/frozen graph compatibility or replacement path, numpy/protobuf/h5py resolution, ffmpeg behavior, and API smoke.
  - It must not be applied in-place to production runtime.
- Decision: candidate for Roadmap 3.3 isolated experimental runtime image.

### Python 3.11

- Assessment: candidate for isolated experimental runtime spike, slightly higher risk.
- Rationale:
  - It is a modern target, but compatibility risk is higher for old TensorFlow/Essentia assumptions.
  - Dependency resolver and binary wheel availability must be proven rather than assumed.
  - Model loading and Essentia algorithm smoke are mandatory before any production discussion.
- Decision: candidate for Roadmap 3.3 isolated experimental runtime image, with higher expected compatibility risk than Python 3.10.

### Python 3.12

- Assessment: defer.
- Rationale:
  - It is the highest-risk candidate against a TensorFlow 1.15-era frozen graph and current Essentia dependency assumptions.
  - It should not be prioritized before Python 3.10/3.11 feasibility evidence exists.
- Decision: deferred.

## Modernization strategies evaluated

### 1. In-place runtime upgrade

- description: Update the current production Dockerfile/base image/dependencies directly toward a newer Python runtime.
- pros:
  - Shortest path if it worked.
  - Minimal parallel runtime maintenance.
- cons:
  - High blast radius.
  - Risks breaking `legacy_musicnn`, `/classify`, Essentia import, model loading, or ffmpeg behavior.
  - No current evidence that TensorFlow/Essentia/MusiCNN works on target Python versions.
  - Harder rollback if dependency changes are mixed into production files.
- decision: rejected for Roadmap 3.2 and not approved for production.

### 2. Pin/reproduce current legacy runtime first

- description: First make current runtime more reproducible by pinning base image digest and documenting exact runtime dependency inputs before modernization.
- pros:
  - Improves rollback confidence.
  - Reduces rebuild drift from floating `latest`, apt, and pip tooling.
  - Creates a stable baseline for comparison.
- cons:
  - Does not itself modernize Python.
  - May require separate approval because it touches Docker/dependency inputs.
- decision: recommended as supporting work before production migration, but not implemented in Roadmap 3.2.

### 3. Experimental runtime image

- description: Create an isolated experimental runtime image/build target for Python 3.10 and/or 3.11, optionally Python 3.7 bridge, without changing production compose or provider behavior.
- pros:
  - Contains risk outside production runtime.
  - Allows collecting build, import, model-load, ffmpeg, and API evidence.
  - Preserves current runtime as rollback authority.
  - Supports comparison between target candidates.
- cons:
  - Requires additional build/test artifact management.
  - May reveal that legacy MusiCNN cannot move without deeper runtime replacement.
- decision: recommended next path for Roadmap 3.3.

### 4. Split legacy MusiCNN runtime and future LLM runtime

- description: Keep legacy MusiCNN runtime isolated while future LLM/runtime work evolves separately.
- pros:
  - Reduces pressure to force TensorFlow 1.15-era assumptions into a modern app runtime.
  - Lets future LLM work use a more modern Python/runtime independently.
  - May lower long-term coupling between legacy inference and newer provider code.
- cons:
  - Introduces service/runtime boundary complexity.
  - Requires careful API, latency, observability, and failure isolation design.
  - Does not approve LLM production adoption by itself.
- decision: viable design direction for later architecture work, not approved as implementation in Roadmap 3.2.

### 5. Keep current runtime and document debt

- description: Keep current Python 3.6.9 / TensorFlow 1.15 / Essentia runtime unchanged and document the modernization debt.
- pros:
  - Lowest immediate production risk.
  - Preserves known working `/classify` behavior.
  - Avoids unsupported migration without evidence.
- cons:
  - Leaves EOL runtime and reproducibility risks unresolved.
  - Does not answer target runtime feasibility.
  - Accumulates operational and security debt.
- decision: acceptable short-term production posture while Roadmap 3.3 gathers experimental evidence; not sufficient as long-term strategy.

## Recommended decision

Roadmap 3.2 decision:

- Production runtime remains unchanged.
- Direct in-place Python 3.10/3.11/3.12 upgrade is not approved.
- Python 3.12 is deferred.
- Python 3.10/3.11 may be evaluated only through isolated experimental runtime images.
- Python 3.7 may be evaluated only as a bridge experiment.
- No provider promotion.
- No canary.
- No LLM cutover.
- No LLM production adoption.
- Next stage should be Roadmap 3.3 experimental runtime build spike.

## Required evidence before any production runtime change

Before any production runtime change can be considered, a later stage must provide:

- docker build evidence
- dependency resolver output
- import smoke
- Essentia algorithm smoke
- MusiCNN model loading smoke
- ffmpeg normalization smoke
- `/health` smoke
- `/classify` fixture smoke
- proof that response shape is unchanged
- proof that provider default is unchanged
- proof that shadow remains disabled by default
- reviewed logs from startup, import/model load, ffmpeg normalization, `/health`, and `/classify`

The evidence must be collected against an isolated candidate runtime before modifying production runtime files.

## Recommended Roadmap 3.3

Recommended next stage:

Roadmap 3.3 — Experimental runtime build spike

Scope:

- separate branch recommended
- no production compose change
- no provider default change
- no `/classify` contract change
- test Python 3.10 and/or 3.11
- optionally test Python 3.7 bridge
- collect build/import/model/API evidence

Roadmap 3.3 should create or use isolated experimental runtime images and record whether each candidate can satisfy the required evidence list. It should not promote a provider, enable canary behavior, or approve LLM production adoption.

## Rollback considerations

- Current Roadmap 3.1 runtime remains the rollback authority.
- Because Roadmap 3.2 is documentation-only, rollback is simply removing or reverting this artifact.
- Future experimental runtime work should preserve current Dockerfile, compose, provider default, and `/classify` response shape unless a later approved production migration explicitly changes them.
- Any candidate runtime must be disposable until it proves build, import, model-load, audio, API, and log evidence.

## Final decision

Decision: Ready for Roadmap 3.3 experimental runtime build spike.

This decision does not approve:

- production Python upgrade
- production Docker/base image replacement
- dependency upgrade in production
- provider switch
- canary rollout
- LLM cutover
- LLM production adoption
