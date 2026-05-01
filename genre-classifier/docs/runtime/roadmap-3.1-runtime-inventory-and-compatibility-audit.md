# Roadmap 3.1 — Runtime inventory and compatibility audit

## Status

Completed as a factual runtime inventory and dependency compatibility audit for `genre-classifier`.

Decision: **Ready for Roadmap 3.2 feasibility spike**.

## Scope

- Service boundary: `genre-classifier` only.
- Working directory used for all commands: `/opt/music-tools/genre-classifier`.
- Repository area intentionally excluded: `tidal-parser`.
- This stage did not change application code, Dockerfile, Docker Compose files, dependencies, provider defaults, `/classify` contract, or response shape.
- This stage did not perform a Python upgrade, dependency upgrade, Docker/base image upgrade, canary rollout, LLM cutover, default-provider switch, commit, tag, or push.
- Roadmap 3.1 is inventory/design evidence only; runtime modernization decisions are deferred.

## Executive summary

The running `genre-classifier` container is based on `mtgupf/essentia-tensorflow:latest`, resolves to Ubuntu 18.04.3, and runs Python 3.6.9 through `python3`. The `python` executable is not present in the container PATH.

The production classification path is the legacy Essentia/MusiCNN runtime: `legacy_musicnn` is the default provider, `TensorflowPredictMusiCNN` loads `app/models/msd-musicnn-1.pb`, and metadata in `app/models/msd-musicnn-1.json` declares TensorFlow framework version `1.15.0`.

The live container currently has TensorFlow 1.15.0, Essentia 2.1-beta6-dev, numpy 1.19.5, protobuf 3.11.3, h5py 2.10.0, FastAPI 0.83.0, Pydantic 1.9.2, and Uvicorn 0.16.0. Several commonly relevant audio/scientific modules are not installed: scipy, librosa, soundfile, audioread, keras, tensorflow_cpu, and tflite_runtime.

The `/health` and documented `/classify` smoke baselines passed against the already-running service on port `8021`. No build or `up -d` was run because the container was already running.

## Runtime inventory

### Python

- `docker compose exec genre-classifier python --version`: failed; `python` executable not found in PATH.
- `docker compose exec genre-classifier python3 --version`: `Python 3.6.9`.
- `python3 -m pip --version`: `pip 21.3.1 from /usr/local/lib/python3.6/dist-packages/pip (python 3.6)`.
- `sys.version`: `3.6.9 (default, Nov 7 2019, 10:44:02) [GCC 8.3.0]`.
- `platform.platform()`: `Linux-7.0.0-3-pve-x86_64-with-Ubuntu-18.04-bionic`.
- `platform.machine()`: `x86_64`.
- `platform.processor()`: `x86_64`.
- Container image platform from `docker image inspect`: `linux/amd64`.

### Docker/base image

- Dockerfile path: `Dockerfile`.
- Compose file path: `docker-compose.yml`.
- Compose service name: `genre-classifier`.
- Container name: `genre-classifier`.
- Base image in Dockerfile: `mtgupf/essentia-tensorflow:latest`.
- OS inside running container: `Ubuntu 18.04.3 LTS (Bionic Beaver)`.
- Image built by compose: `genre-classifier-genre-classifier`.
- Container image SHA observed: `sha256:d655b70f571bbe6966ac4ed59c57b2499fa8699f20fb70f7c8b452a5a2bce7e1`.
- Exposed/listening port: Dockerfile `EXPOSE 8021`; compose maps `8021:8021`; Uvicorn listens on `0.0.0.0:8021`.
- Healthcheck: none configured (`docker inspect genre-classifier --format '{{json .Config.Healthcheck}}'` returned `null`).
- Compose network: external `musicnet`.
- Volumes: `./app/models`, `./app/tmp`, `./app/templates`, `./app/static`, and `./app/main.py` are bind-mounted into `/app/app/...`.
- Dockerfile apt packages: `ffmpeg`.
- Dockerfile Python install steps: upgrades `pip setuptools wheel`, then installs `-r /app/requirements.txt`.

Environment variables observed inside the running container:

| Variable | Value |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE` | `1` |
| `PYTHONUNBUFFERED` | `1` |
| `PYTHONPATH` | `/usr/local/lib/python3/dist-packages` |
| `PATH` | `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin` |
| `LANG` | `C.UTF-8` |

Provider/runtime env vars are not set in compose or the running container. Runtime code reads these env vars when present: `GENRE_PROVIDER`, `LLM_CLIENT`, `LLM_LOCAL_HTTP_ENDPOINT`, `LLM_LOCAL_HTTP_TIMEOUT_SECONDS`, `GENRE_CLASSIFIER_SHADOW_ENABLED`, `GENRE_CLASSIFIER_SHADOW_PROVIDER`, `GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE`, `GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS`, `GENRE_CLASSIFIER_SHADOW_ARTIFACTS_ENABLED`, `GENRE_CLASSIFIER_SHADOW_ARTIFACTS_DIR`, and `GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT`.

### Dependency files

Discovered dependency/build files:

| Path | Purpose | Pinned/unpinned dependencies | Runtime-critical dependencies | Test/dev dependencies |
| --- | --- | --- | --- | --- |
| `requirements.txt` | App Python dependencies installed by Dockerfile | All listed packages are pinned with `==`: `fastapi==0.83.0`, `uvicorn==0.16.0`, `python-multipart==0.0.5`, `jinja2==3.0.3`, `numpy==1.19.5` | FastAPI, Uvicorn, python-multipart, Jinja2, numpy | None in file |
| `Dockerfile` | Runtime image definition | Base image uses floating tag `mtgupf/essentia-tensorflow:latest`; apt package `ffmpeg` is unpinned; pip/setuptools/wheel upgrade is unpinned | Essentia/TensorFlow inherited from base image; ffmpeg; requirements.txt packages | None |
| `docker-compose.yml` | Local service definition | Image is locally built from `.`; no dependency pins | Port, bind mounts, external network | None |

Not found during audit: `pyproject.toml`, `poetry.lock`, `Pipfile*`, `constraints*.txt`, `setup.py`, `setup.cfg`, shell scripts with install commands.

Installed package snapshot from `python3 -m pip freeze` includes:

- `tensorflow==1.15.0`
- `tensorboard==1.15.0`
- `tensorflow-estimator==1.15.1`
- `numpy==1.19.5`
- `protobuf==3.11.3`
- `h5py==2.10.0`
- `fastapi==0.83.0`
- `pydantic==1.9.2`
- `uvicorn==0.16.0`
- `starlette==0.19.1`
- `python-multipart==0.0.5`
- `Jinja2==3.0.3`

## Dependency compatibility matrix

| Component | Current version | Source | Runtime role | Python compatibility concern | Modernization risk | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Python | 3.6.9 | `python3 --version` in container | App runtime | Python 3.6 is EOL; many modern packages no longer support it | High | `python` command absent; use `python3` in current container |
| Base image | `mtgupf/essentia-tensorflow:latest`; Ubuntu 18.04.3 | Dockerfile and `/etc/os-release` | Supplies Essentia/TensorFlow stack | Floating tag and old OS complicate reproducibility and target selection | High | Exact upstream digest not confirmed during audit |
| TensorFlow | 1.15.0 | `pip freeze`, import smoke, model metadata | MusiCNN inference framework via Essentia | TensorFlow 1.x has narrow Python support and is not expected to support modern Python targets without replacement | High | Import passed; startup logs show CUDA library warnings but CPU serving works |
| `tensorflow-cpu` / `tensorflow_cpu` | Not installed | Import smoke | Not used by current runtime | Future CPU-only replacement would need explicit feasibility check | Medium | `tensorflow_cpu` import failed |
| `tflite_runtime` | Not installed | Import smoke | Not used by current runtime | Any TFLite migration would be a separate runtime design | Medium | Import failed |
| Essentia | 2.1-beta6-dev | Import smoke | Provides `MonoLoader` and `TensorflowPredictMusiCNN` | Wheel availability for newer Python versions must be verified | High | Import passed |
| MusiCNN model/runtime | `msd-musicnn-1.pb`, metadata version `1`, framework `tensorflow`, framework version `1.15.0` | `app/models/msd-musicnn-1.json`; `app/models/msd-musicnn-1.pb` | Production model | Frozen TF 1.15 graph loading may break under newer TF/Python stacks | High | `.pb` size about 3.1 MB; metadata declares `TensorflowPredictMusiCNN` |
| numpy | 1.19.5 | `pip freeze`, import smoke | Score aggregation and TensorFlow dependency | Newer Python requires newer numpy; TensorFlow 1.15 constrains numpy choices | High | Import passed |
| scipy | Not installed | Import smoke | Not used by current app | If introduced by future audio stack, compatibility must be pinned | Low | Import failed |
| protobuf | 3.11.3 | `pip freeze`, import smoke | TensorFlow graph/runtime dependency | TensorFlow 1.x commonly has protobuf upper-bound sensitivity | High | Import passed |
| h5py | 2.10.0 | `pip freeze`, import smoke | TensorFlow/Keras-era model ecosystem dependency | h5py major-version changes can break old TF/Keras stacks | Medium | Import passed |
| keras | Not installed as `keras`; `Keras-Applications==1.0.8`, `Keras-Preprocessing==1.1.0` installed | Import smoke, `pip freeze` | Indirect TensorFlow-era dependency | Standalone Keras compatibility with TF 1.15/new Python is risky | Medium | `import keras` failed |
| librosa | Not installed | Import smoke | Not used by current runtime | Future decoder/feature stack would require separate compatibility research | Low | Import failed |
| soundfile | Not installed | Import smoke | Not used directly | Would depend on libsndfile compatibility if introduced | Low | Import failed; `libsndfile.so.1` exists |
| audioread | Not installed | Import smoke | Not used directly | Low unless introduced by librosa path | Low | Import failed |
| FastAPI | 0.83.0 | `requirements.txt`, `pip freeze`, import smoke | HTTP API | Current version still supports older Pydantic 1; future FastAPI upgrades may require newer Python/Pydantic | Medium | Import passed |
| Pydantic | 1.9.2 | `pip freeze`, import smoke | FastAPI validation stack | Pydantic 2 migration would affect API validation behavior if upgraded | Medium | Import passed |
| Uvicorn | 0.16.0 | `requirements.txt`, `pip freeze`, import smoke | ASGI server | Modern Uvicorn versions may drop old Python support | Medium | Import passed |
| ffmpeg/system audio libs | ffmpeg 3.4.11; libavcodec 57; libavformat 57; libavutil 55; libsndfile.so.1; libsamplerate.so.0; libtag.so.1 | `ffmpeg -version`, `ldconfig -p` | Decode/normalize uploaded audio before model inference | OS/base image upgrade can change codec behavior and binary availability | Medium | Current `/classify` smoke decoded existing MP3 successfully |

## TensorFlow / Essentia / MusiCNN audit

### TensorFlow

- Installed: `tensorflow==1.15.0`, `tensorflow-estimator==1.15.1`, `tensorboard==1.15.0`.
- Import smoke: `tensorflow: OK version=1.15.0`.
- Import smoke: `tensorflow_cpu: FAIL ModuleNotFoundError`.
- Import smoke: `tflite_runtime: FAIL ModuleNotFoundError`.
- Model metadata declares `"framework": "tensorflow"` and `"framework_version": "1.15.0"`.
- Startup/log smoke shows TensorFlow CPU execution starts but emits CUDA-related warnings because `libcuda.so.1` is unavailable. Current classification still returned `200 OK`.

### Essentia

- Import smoke: `essentia: OK version=2.1-beta6-dev`.
- Code imports `MonoLoader` and `TensorflowPredictMusiCNN` from `essentia.standard` in `app/services/classify.py`.
- `tests/test_classify_orchestration.py` and `tests/test_upload_validation.py` include Essentia stubs when Essentia is not installed in the test environment.
- Wheel/source availability for modern Python targets was not confirmed during audit.

### MusiCNN legacy runtime

- Model files:
  - `app/models/msd-musicnn-1.pb` around 3.1 MB.
  - `app/models/msd-musicnn-1.json` around 3.3 KB.
- Settings:
  - `MODEL_PB = MODELS_DIR / "msd-musicnn-1.pb"`.
  - `MODEL_JSON = MODELS_DIR / "msd-musicnn-1.json"`.
- Metadata:
  - name: `MSD MusiCNN`.
  - type: `auto-tagging`.
  - release date: `2020-03-31`.
  - model type: `frozen_model`.
  - inference sample rate: `16000`.
  - inference algorithm: `TensorflowPredictMusiCNN`.
  - classes: 50 tags.
- Runtime flow:
  - Uploaded audio is normalized with `ffmpeg` to mono 16 kHz WAV.
  - `MonoLoader(filename=..., sampleRate=16000)` loads the WAV.
  - `TensorflowPredictMusiCNN(graphFilename=str(settings.MODEL_PB))` produces activations.
  - numpy mean aggregation ranks top 8 genre scores.

Import smoke results:

| Module | Result |
| --- | --- |
| `numpy` | OK `1.19.5` |
| `scipy` | FAIL `ModuleNotFoundError` |
| `tensorflow` | OK `1.15.0` |
| `tensorflow_cpu` | FAIL `ModuleNotFoundError` |
| `tflite_runtime` | FAIL `ModuleNotFoundError` |
| `essentia` | OK `2.1-beta6-dev` |
| `librosa` | FAIL `ModuleNotFoundError` |
| `soundfile` | FAIL `ModuleNotFoundError` |
| `audioread` | FAIL `ModuleNotFoundError` |
| `google.protobuf` | OK `3.11.3` |
| `h5py` | OK `2.10.0` |
| `keras` | FAIL `ModuleNotFoundError` |
| `fastapi` | OK `0.83.0` |
| `pydantic` | OK `1.9.2` |
| `uvicorn` | OK `0.16.0` |

## Audio/system libraries

- Dockerfile installs `ffmpeg` through apt.
- `ffmpeg -version`: `ffmpeg version 3.4.11-0ubuntu0.1`, built with GCC 7 on Ubuntu 18.04.
- FFmpeg library versions:
  - `libavutil 55.78.100`
  - `libavcodec 57.107.100`
  - `libavformat 57.83.100`
  - `libavdevice 57.10.100`
  - `libavfilter 6.107.100`
  - `libavresample 3.7.0`
  - `libswscale 4.8.100`
  - `libswresample 2.9.100`
  - `libpostproc 54.7.100`
- `ldconfig -p` confirmed:
  - `libtag.so.1`
  - `libsndfile.so.1`
  - `libsamplerate.so.0`
  - `libavutil.so.55`
  - `libavformat.so.57`
  - `libavcodec.so.57`
- Audio normalization command in code: `ffmpeg -y -i <input> -ac 1 -ar 16000 <output.wav>`.

## Provider configuration

- Available providers from settings/factory:
  - `legacy_musicnn`
  - `llm`
  - `stub`
- Default provider:
  - `DEFAULT_GENRE_PROVIDER = "legacy_musicnn"`.
  - `get_configured_genre_provider_name()` reads `GENRE_PROVIDER` and falls back to `legacy_musicnn`.
- Running container env did not set `GENRE_PROVIDER`; current production default is therefore `legacy_musicnn`.
- `legacy_musicnn` provider calls `run_genre_classification()` and returns model name `settings.MODEL_PB.stem`.
- `llm` provider exists but is not default. It uses `LLM_CLIENT`, defaulting to `stub`, and can use local HTTP settings when configured.
- Runtime shadow observer is wired after production response construction, but defaults are disabled:
  - `DEFAULT_SHADOW_ENABLED = False`.
  - `DEFAULT_SHADOW_PROVIDER = "llm"`.
  - `DEFAULT_SHADOW_SAMPLE_RATE = 0.0`.
  - `DEFAULT_SHADOW_TIMEOUT_SECONDS = 2.0`.
  - `DEFAULT_SHADOW_MAX_CONCURRENT = 1`.
- Logs from the `/classify` smoke showed `genre_classifier.shadow.skipped status=skipped_by_config`, confirming shadow stayed disabled by config during this audit.

## Current API behavior

### /health

Command:

```sh
curl -sS -i http://localhost:8021/health
```

Observed response:

```http
HTTP/1.1 200 OK
content-type: application/json

{"ok":true}
```

### /classify

Existing fixture/command evidence:

- Existing audio file found: `app/tmp/upload.mp3`.
- Existing docs mention `POST /classify` multipart form with `file=@app/tmp/upload.mp3`.

Command:

```sh
curl -sS -i -F file=@app/tmp/upload.mp3 http://localhost:8021/classify
```

Observed response:

```http
HTTP/1.1 200 OK
content-type: application/json
```

Observed JSON shape:

```json
{
  "ok": true,
  "message": "Аудио проанализировано",
  "genres": [
    {"tag": "electronic", "prob": 0.3894},
    {"tag": "indie", "prob": 0.3884},
    {"tag": "rock", "prob": 0.195},
    {"tag": "indie rock", "prob": 0.1836},
    {"tag": "alternative", "prob": 0.1556},
    {"tag": "electro", "prob": 0.1237},
    {"tag": "pop", "prob": 0.1012},
    {"tag": "electronica", "prob": 0.0754}
  ],
  "genres_pretty": [
    "indie rock",
    "alternative rock",
    "electronic",
    "indie",
    "rock",
    "alternative",
    "electro",
    "pop"
  ]
}
```

Route source:

- `/health`: `app/api/routes.py`.
- `/classify`: `app/api/routes.py`.
- Success response keys: `ok`, `message`, `genres`, `genres_pretty`.
- Error response keys: `ok`, `error` with HTTP 400.

## Build/test/smoke baseline

Boundary checks:

- `pwd`: `/opt/music-tools/genre-classifier`.
- Initial `git status`: clean working tree.
- `docker compose config --services`: `genre-classifier`.
- `docker compose config`: succeeded.

Runtime checks:

- `docker compose ps`: container `genre-classifier` was already `Up`, so no `docker compose build` or `docker compose up -d` was run.
- `docker compose exec genre-classifier python --version`: failed because `python` is not in PATH.
- `docker compose exec genre-classifier python3 --version`: `Python 3.6.9`.
- `docker compose exec genre-classifier python3 -m pip --version`: `pip 21.3.1`.
- `docker compose exec genre-classifier python3 -m pip freeze`: completed.
- Python platform snippet: completed.
- Python import smoke: completed.
- `docker compose exec genre-classifier ffmpeg -version`: completed.
- `docker compose exec genre-classifier sh -lc "ldconfig -p | grep -E ..."`: completed.
- `curl -sS -i http://localhost:8021/health`: passed.
- `curl -sS -i -F file=@app/tmp/upload.mp3 http://localhost:8021/classify`: passed.
- `docker compose logs --tail=30 genre-classifier`: completed.

Tests:

- `docker compose exec genre-classifier python3 -m pytest`: failed with `/usr/bin/python3: No module named pytest`.
- No attempt was made to install pytest or dependencies.

Not run:

- `docker compose build`.
- `docker compose up -d`.
- Any dependency upgrade.
- Any provider switch.
- Any LLM cutover/canary.

## Risks

### High risk

- TensorFlow 1.15.0 is tightly coupled to old Python/runtime assumptions; moving to newer Python may require replacing or isolating the TensorFlow/MusiCNN execution path.
- Essentia 2.1-beta6-dev wheel availability for Python 3.10/3.11/3.12 is not confirmed.
- MusiCNN frozen graph loading depends on `TensorflowPredictMusiCNN`, TensorFlow 1.15 behavior, and the current Essentia build.
- numpy/protobuf/h5py are old and compatibility-sensitive around TensorFlow 1.15.
- Base image uses a floating `latest` tag, which weakens build reproducibility.

### Medium risk

- Ubuntu 18.04 and ffmpeg 3.4.11 are old; a base image upgrade can change audio decoding behavior.
- FastAPI/Pydantic/Uvicorn upgrades could alter validation/server behavior even if `/classify` shape is intentionally preserved.
- Current Dockerfile upgrades `pip setuptools wheel` without pinning them, so rebuilds may vary.
- Runtime tests are not directly runnable inside the current container because pytest is absent.
- `python` command absence can break scripts or smoke commands that assume `python` instead of `python3`.

### Low risk

- `scipy`, `librosa`, `soundfile`, and `audioread` are absent and not used by the current application path.
- Compose config has a single service and no provider env overrides, reducing accidental provider switch risk in current baseline.

### Unknowns

- Exact upstream digest/content of `mtgupf/essentia-tensorflow:latest` was not confirmed during audit.
- Modern Python target support for the combined Essentia + TensorFlow + MusiCNN stack was not confirmed during audit.
- Whether the current `.pb` model can load under any TensorFlow 2.x compatibility mode was not confirmed during audit.
- Whether an equivalent Essentia TensorFlow predictor exists for newer supported Python versions was not confirmed during audit.
- Rebuild reproducibility from scratch was not confirmed because no build was run.

## Blockers

- Missing fully pinned base image digest.
- Floating/unpinned Dockerfile install inputs: base image `latest`, apt `ffmpeg`, and `pip setuptools wheel` upgrade.
- Unknown Essentia wheel/source compatibility for target Python versions.
- Unknown TensorFlow 1.15 or replacement compatibility for target Python versions.
- Unknown MusiCNN frozen graph compatibility outside the current TensorFlow 1.15/Essentia runtime.
- Missing pytest in the runtime container.
- Missing explicit modernization target Python evidence.
- Build reproducibility not verified during this audit.
- Existing `/classify` smoke fixture exists, but it lives under `app/tmp`; a deliberate stable smoke fixture policy is not confirmed.

## Recommended target Python investigation path

Do not choose a final target Python in Roadmap 3.1.

Recommended Roadmap 3.2 investigation sequence:

1. Preserve the current Python 3.6.9 / TensorFlow 1.15.0 / Essentia 2.1-beta6-dev baseline as authoritative.
2. Identify candidate Python targets only after checking supported combinations for TensorFlow or replacement runtime, Essentia, numpy, protobuf, h5py, and MusiCNN model loading.
3. Treat Python 3.10, 3.11, and 3.12 as feasibility candidates, not decisions.
4. For each candidate, test imports, model load, ffmpeg normalization, and `/classify` response shape against the existing fixture.
5. Keep `legacy_musicnn` as production default during investigation.
6. Keep `/classify` contract and response shape unchanged during investigation.
7. Prefer an isolated experimental Dockerfile/build target only after explicit approval.

## Rollback considerations

- Current runtime remains authoritative until a later approved stage proves compatibility.
- No production switch was made in Roadmap 3.1.
- No provider switch was made in Roadmap 3.1.
- No `/classify` contract or response-shape change was made in Roadmap 3.1.
- Rollback for future experiments should be simple: keep the current compose/Dockerfile/runtime path unchanged while testing any experimental runtime separately.

## Roadmap 3.1 decision

**Ready for Roadmap 3.2 feasibility spike**

Rationale:

- Required baseline facts were collected from the running `genre-classifier` service.
- Compose config succeeds.
- Current runtime versions are known.
- TensorFlow/Essentia/MusiCNN usage and model paths are identified.
- `/health` and documented `/classify` smoke passed.
- Major modernization risks are known enough to scope a feasibility spike.

This decision does not approve a Python upgrade, dependency upgrade, base image upgrade, provider switch, canary rollout, LLM cutover, or production behavior change.

## Recommendation for Roadmap 3.2

Roadmap 3.2 should be a target-runtime feasibility spike.

Constraints for Roadmap 3.2:

- No production switch.
- No provider switch.
- No `/classify` contract changes.
- No response shape changes.
- No canary rollout.
- No default-provider change.
- Use the current runtime as the rollback authority.
- Consider a separate experimental Dockerfile or build target only after explicit approval.
- Prove candidate compatibility with import smoke, model load, audio decode, `/health`, and `/classify` smoke before any modernization decision.
