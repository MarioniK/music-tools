# Roadmap 3.4 — essentia-tensorflow runtime compatibility spike

## Status

Completed as a primary safe-slice compatibility spike for `genre-classifier`.

Decision: **Python 3.12 + `essentia-tensorflow` passed the required Roadmap 3.4 primary smoke chain, but this does not approve production runtime migration**.

The candidate built successfully, resolved `essentia-tensorflow`, exposed `TensorflowPredictMusiCNN`, loaded the discovered MusiCNN `.pb` model, started the API, passed `/health`, and returned the expected `/classify` response shape for the available local audio fixture.

This is compatibility evidence for deeper Roadmap 3.5 validation only. Roadmap 3.4 does not approve canary rollout, provider switch, LLM cutover, LLM production adoption, or production Python/runtime migration.

## Service

`genre-classifier` only.

Repository areas outside this service, including `tidal-parser`, are out of scope and were not touched.

## Goal

Verify whether `essentia-tensorflow` can reproduce the production-required legacy MusiCNN capability in an isolated experimental runtime, without changing the production path.

## Scope

- Targeted compatibility spike.
- Primary candidate: Python 3.12 + `essentia-tensorflow`.
- Isolated Docker artifact only.
- Evidence capture for build, dependency resolution, imports, model loading, ffmpeg, API smoke, response parity, provider parity, and shadow parity.

## Non-goals

- No production Dockerfile replacement.
- No production compose replacement.
- No production requirements replacement.
- No production runtime migration.
- No provider switch.
- No canary rollout.
- No LLM cutover.
- No LLM production adoption.
- No `/classify` contract change.
- No response shape change.
- No `tidal-parser` changes.
- No full runtime redesign.
- No automatic approval of production migration.

## Roadmap 3.3 Findings Summary

Roadmap 3.3 showed that experimental runtimes using plain `essentia` could build and import TensorFlow/Essentia, but did not expose `TensorflowPredictMusiCNN`. Therefore, legacy MusiCNN app import, model loading, API startup, `/health`, `/classify`, and response parity were blocked.

Successful Docker build was not sufficient runtime compatibility evidence. Successful TensorFlow import was not sufficient MusiCNN compatibility evidence.

## Post-3.3 Clarification

`essentia-tensorflow` is distinct from plain `essentia` and may include TensorFlow-enabled Essentia algorithms. This requires a separate targeted spike. This clarification does not invalidate Roadmap 3.3.

## Production Rollback Baseline

- Python: 3.6.9
- container OS: Ubuntu 18.04.3 LTS
- base image: `mtgupf/essentia-tensorflow:latest`
- TensorFlow: 1.15.0
- Essentia: 2.1-beta6-dev
- numpy: 1.19.5
- protobuf: 3.11.3
- h5py: 2.10.0
- FastAPI: 0.83.0
- Pydantic: 1.9.2
- Uvicorn: 0.16.0

Production behavior remains unchanged:

- default provider remains `legacy_musicnn`
- production response remains legacy-only
- `/classify` contract unchanged
- response shape unchanged
- shadow disabled by default
- no canary rollout
- no LLM cutover

## Git and Production Safety Evidence

- branch: `roadmap-3.4-essentia-tensorflow-spike`
- starting HEAD: `d350330`
- production `Dockerfile` unchanged
- production `docker-compose.yml` unchanged
- production `requirements.txt` unchanged
- app code unchanged
- `tidal-parser` untouched
- no commit, tag, or push performed

## Experimental Build Artifacts

- `docker/experimental/python312-essentia-tensorflow/Dockerfile`

No optional Python 3.11 or Python 3.10 artifacts were added in this primary safe-slice.

## Tested Candidate Runtimes

| Candidate | Image tag | Result |
|---|---|---|
| Python 3.12 + `essentia-tensorflow` | `music-tools-genre-classifier-roadmap-3.4:py312-etf` | Passed primary build/import/model/API smoke |

## Docker Build Evidence

Command:

```sh
docker build \
  -f docker/experimental/python312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.4:py312-etf \
  .
```

Result: **SUCCESS**.

Image metadata:

- image id: `sha256:fc79a890fb897579669abf7d5679310de3ba62c9753e2dbd33bc9cf70716729f`
- created: `2026-05-02T01:53:18.767818554+03:00`
- size: `3434637857`

Build conclusion:

- Docker build success is only build evidence.
- It is not by itself runtime compatibility evidence.
- Compatibility required the later import, model loading, ffmpeg, API, and response shape checks.

## Dependency Resolver Evidence

Resolver input was isolated to `docker/experimental/python312-essentia-tensorflow/Dockerfile`.

The production `requirements.txt` was copied into the image as `/app/production-requirements.txt` for evidence comparison, but was not changed.

Relevant resolver result from `python -m pip install`:

- `tensorflow-2.21.0`
- `essentia-tensorflow-2.1b6.dev1389`
- `numpy-2.4.4`
- `protobuf-7.34.1`
- `h5py-3.14.0`
- `fastapi-0.83.0`
- `pydantic-1.10.26`
- `uvicorn-0.16.0`
- `python-multipart-0.0.5`
- `jinja2-3.0.3`

Resolver behavior:

- pip resolver completed successfully on Python 3.12.
- `python-multipart==0.0.5` built a wheel successfully.
- `tensorflow` was intentionally unpinned as experimental resolver input and resolved to `2.21.0`.
- This TensorFlow version does not match the production TensorFlow `1.15.0` runtime.
- The resolved package stack is compatibility-spike evidence only, not a production dependency proposal.

## Package Version Evidence

Commands:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf python --version
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf pip --version
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf pip freeze
```

Results:

- Python: `3.12.13`
- pip: `26.1`
- `essentia-tensorflow==2.1b6.dev1389`
- `tensorflow==2.21.0`
- `numpy==2.4.4`
- `protobuf==7.34.1`
- `h5py==3.14.0`
- `fastapi==0.83.0`
- `pydantic==1.10.26`
- `uvicorn==0.16.0`
- `starlette==0.19.1`
- `python-multipart==0.0.5`
- `Jinja2==3.0.3`

Full relevant `pip freeze`:

```text
absl-py==2.4.0
anyio==4.13.0
asgiref==3.11.1
astunparse==1.6.3
certifi==2026.4.22
charset-normalizer==3.4.7
click==8.3.3
essentia-tensorflow==2.1b6.dev1389
fastapi==0.83.0
flatbuffers==25.12.19
gast==0.7.0
google-pasta==0.2.0
grpcio==1.80.0
h11==0.16.0
h5py==3.14.0
idna==3.13
Jinja2==3.0.3
keras==3.14.0
libclang==18.1.1
markdown-it-py==4.0.0
MarkupSafe==3.0.3
mdurl==0.1.2
ml_dtypes==0.5.4
namex==0.1.0
numpy==2.4.4
opt_einsum==3.4.0
optree==0.19.0
packaging==26.2
protobuf==7.34.1
pydantic==1.10.26
Pygments==2.20.0
python-multipart==0.0.5
PyYAML==6.0.3
requests==2.33.1
rich==15.0.0
setuptools==82.0.1
six==1.17.0
starlette==0.19.1
tensorflow==2.21.0
termcolor==3.3.0
typing_extensions==4.15.0
urllib3==2.6.3
uvicorn==0.16.0
wheel==0.47.0
wrapt==2.1.2
```

## TensorFlow / Essentia Evidence

TensorFlow import command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "import tensorflow as tf; print(tf.__version__)"
```

Result:

- TensorFlow import: **PASS**
- TensorFlow version: `2.21.0`

Essentia import command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "import essentia; print(getattr(essentia, '__version__', 'unknown'))"
```

Result:

- Essentia import: **PASS**
- Essentia runtime identity: `2.1-beta6-dev`
- Installed package identity from `pip freeze`: `essentia-tensorflow==2.1b6.dev1389`

`essentia.standard` import command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "import essentia.standard as es; print('standard ok')"
```

Result: **PASS**.

Observed non-fatal logs:

- TensorFlow reported missing CUDA libraries and fell back to CPU.
- Essentia logged `MusicExtractorSVM: no classifier models were configured by default`.
- These logs did not block imports or later smoke checks.

## MonoLoader Evidence

Command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "from essentia.standard import MonoLoader; print('MonoLoader ok')"
```

Result: **PASS**.

## TensorflowPredictMusiCNN Evidence

Command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "from essentia.standard import TensorflowPredictMusiCNN; print('TensorflowPredictMusiCNN ok')"
```

Result: **PASS**.

This is the critical difference from Roadmap 3.3 plain `essentia` candidates: Python 3.12 + `essentia-tensorflow` exposes `TensorflowPredictMusiCNN`.

## TensorFlow Graph / Session Evidence

Command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "import tensorflow as tf; print('Graph', hasattr(tf, 'Graph')); print('compat.v1.Session', hasattr(tf.compat.v1, 'Session')); print('import_graph_def', hasattr(tf, 'import_graph_def')); print('compat.v1.import_graph_def', hasattr(tf.compat.v1, 'import_graph_def'))"
```

Result:

```text
Graph True
compat.v1.Session True
import_graph_def True
compat.v1.import_graph_def True
```

## App Import Evidence

Commands:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "import app.main; print('app.main import ok')"
```

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "import app.services.classify; print('app.services.classify import ok')"
```

Results:

- `app.main` import: **PASS**
- `app.services.classify` import: **PASS**

This removes the Roadmap 3.3 import-time blocker for this primary candidate.

## Model Discovery / Loading Evidence

Model discovery was performed before model loading. The model path was not treated as a hardcoded source of truth.

Command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  find /app -name *.pb
```

Result:

```text
/app/app/models/msd-musicnn-1.pb
```

Model loading command using the discovered path:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "from essentia.standard import TensorflowPredictMusiCNN; TensorflowPredictMusiCNN(graphFilename='/app/app/models/msd-musicnn-1.pb'); print('model load ok: /app/app/models/msd-musicnn-1.pb')"
```

Result:

```text
[   INFO   ] TensorflowPredict: Successfully loaded graph file: `/app/app/models/msd-musicnn-1.pb`
model load ok: /app/app/models/msd-musicnn-1.pb
```

Conclusion: **MusiCNN model discovery and TensorflowPredictMusiCNN model loading passed** for this candidate.

## ffmpeg Evidence

Availability command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf ffmpeg -version
```

Result:

- ffmpeg: `5.1.8-0+deb12u1`

Normalization smoke command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  ffmpeg -hide_banner -f lavfi -i sine=frequency=440:duration=1 -ar 16000 -ac 1 /tmp/roadmap-3.4.wav
```

Result: **PASS**.

The output WAV was written as 16 kHz mono PCM inside the container.

## API Smoke Evidence

API startup command:

```sh
docker run -d -p 8012:8021 --name genre-classifier-rm34-py312-etf \
  music-tools-genre-classifier-roadmap-3.4:py312-etf
```

Startup logs:

```text
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8021 (Press CTRL+C to quit)
```

Health command:

```sh
curl -sS http://127.0.0.1:8012/health
```

Result:

```json
{"ok":true}
```

Classify fixture:

- local file used: `app/tmp/upload.mp3`
- size: `7470185` bytes

Classify command:

```sh
curl -sS -X POST http://127.0.0.1:8012/classify \
  -F file=@app/tmp/upload.mp3
```

Result:

```json
{
  "ok": true,
  "message": "Аудио проанализировано",
  "genres": [
    {"tag": "electronic", "prob": 0.3894},
    {"tag": "indie", "prob": 0.3884},
    {"tag": "rock", "prob": 0.1951},
    {"tag": "indie rock", "prob": 0.1836},
    {"tag": "alternative", "prob": 0.1557},
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

Cleanup command:

```sh
docker rm -f genre-classifier-rm34-py312-etf
```

Result: container removed.

## Response Shape Parity Evidence

`/classify` response shape matched the existing public response contract:

- top-level `ok`
- top-level `message`
- top-level `genres`
- top-level `genres_pretty`
- each `genres` item has `tag` and `prob`
- `genres_pretty` is a list of strings

No `/classify` contract change was made.

No response shape change was made.

## Provider / Shadow Parity Evidence

Command:

```sh
docker run --rm music-tools-genre-classifier-roadmap-3.4:py312-etf \
  python -c "from app.core import settings; print('DEFAULT_GENRE_PROVIDER', settings.DEFAULT_GENRE_PROVIDER); print('configured_provider', settings.get_configured_genre_provider_name()); print('DEFAULT_SHADOW_ENABLED', settings.DEFAULT_SHADOW_ENABLED); print('configured_shadow_enabled', settings.get_configured_shadow_enabled())"
```

Result:

```text
DEFAULT_GENRE_PROVIDER legacy_musicnn
configured_provider legacy_musicnn
DEFAULT_SHADOW_ENABLED False
configured_shadow_enabled False
```

Provider default remains `legacy_musicnn`.

Runtime shadow remains disabled by default.

## Logs Review

Reviewed logs from import, model loading, ffmpeg, and API startup/classification smoke.

Observed logs:

- TensorFlow reports missing CUDA libraries and uses CPU.
- Essentia reports `MusicExtractorSVM: no classifier models were configured by default`.
- TensorFlow CPU feature messages are present.
- `TensorflowPredict` successfully loads `/app/app/models/msd-musicnn-1.pb`.
- Uvicorn startup completes.
- `/health` returns `{"ok":true}`.
- `/classify` returns `ok: true`.

No fatal startup/import/model/ffmpeg/API errors were observed in this safe-slice.

## Blockers

No primary safe-slice blockers were found.

Residual risks:

- TensorFlow resolved to `2.21.0`, while production uses TensorFlow `1.15.0`.
- numpy resolved to `2.4.4`, while production uses numpy `1.19.5`.
- protobuf resolved to `7.34.1`, while production uses protobuf `3.11.3`.
- h5py resolved to `3.14.0`, while production uses h5py `2.10.0`.
- Base OS is Debian bookworm via `python:3.12-slim-bookworm`, while production is Ubuntu 18.04.3 LTS through `mtgupf/essentia-tensorflow:latest`.
- The smoke used one available local audio fixture, not a representative validation corpus.
- This stage did not compare numerical output parity against production runtime on the same fixture set.
- This stage did not evaluate performance, memory behavior, cold start, concurrency, or long-running stability.

## Decision

Python 3.12 + `essentia-tensorflow` is a viable candidate for deeper Roadmap 3.5 validation.

This decision is limited to compatibility-spike evidence:

- build passed
- resolver completed
- `TensorflowPredictMusiCNN` is available
- app imports passed
- model discovery passed
- model loading passed
- ffmpeg smoke passed
- API startup passed
- `/health` passed
- `/classify` fixture smoke passed
- response shape parity passed
- provider default remained `legacy_musicnn`
- runtime shadow remained disabled by default

This decision does not approve:

- production runtime migration
- production Dockerfile replacement
- production compose replacement
- production requirements replacement
- provider switch
- canary rollout
- LLM cutover
- LLM production adoption

Allowed decisions:

- Candidate blocked.
- Candidate partially compatible but not production-ready.
- Candidate passes smoke and should proceed to deeper Roadmap 3.5 validation.

Not allowed:

- Production migration approval.
- Canary approval.
- Provider switch approval.
- LLM production adoption approval.

## Recommendation for Roadmap 3.5

Proceed with a deeper isolated validation stage before any production decision.

Recommended Roadmap 3.5 scope:

- Build a repeatable validation harness comparing current production runtime vs Python 3.12 + `essentia-tensorflow` on the same audio fixtures.
- Add a small curated audio fixture set, or explicitly document fixture provenance if existing files are reused.
- Compare response shape and top-N genre behavior across fixtures.
- Compare raw/normalized score behavior where feasible.
- Measure cold start time, model load time, request latency, memory footprint, and repeated request stability.
- Verify behavior under malformed/unsupported uploads.
- Verify container startup and shutdown behavior.
- Decide whether optional Python 3.11 / Python 3.10 `essentia-tensorflow` candidates are still necessary after Python 3.12 passed primary smoke.
- Keep all validation isolated from production compose until a later explicit migration decision.

## Rollback Considerations

Current production runtime remains the authoritative rollback baseline.

Production files remain unchanged:

- production `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- app code
- provider default
- `/classify` contract
- response shape
- `tidal-parser`

Rollback for Roadmap 3.4 is to stop using the experimental image tag:

- `music-tools-genre-classifier-roadmap-3.4:py312-etf`

The experimental image must not be referenced by production compose.

No Roadmap 3.4 artifact should be treated as a release artifact or deployment approval.
