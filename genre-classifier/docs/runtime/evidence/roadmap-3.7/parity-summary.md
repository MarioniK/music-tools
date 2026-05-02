# Roadmap 3.7 parity summary

Validation date: 2026-05-03

Working directory: `/opt/music-tools/genre-classifier`

Branch: `roadmap-3.7-runtime-candidate-hardening`

## Images

Baseline image:

- tag: `music-tools-genre-classifier-roadmap-3.7:baseline`
- image id: `sha256:6ef15c1bdbeb6b82efef02045b9a68de309c41442860da00c635ffa061d3ab75`
- base observed during build: `mtgupf/essentia-tensorflow:latest@sha256:43dbaf1507416167f2adeebc2cb9c6c657b65d38a967b6408487f48271b7b44b`

Candidate image:

- tag: `music-tools-genre-classifier-roadmap-3.7:py312-etf`
- image id: `sha256:fe7875f63005715ade4ace05ff339c8f3a35c5aa04a54ee43fd16407fb1ad2de`
- base: `python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`

## Resolver and runtime identity

Candidate:

- OS: Debian GNU/Linux 12 (bookworm)
- Python: `3.12.13`
- pip: `25.0.1`
- `pip check`: `No broken requirements found.`
- ffmpeg: `5.1.8-0+deb12u1`
- TensorFlow: `2.21.0`
- `essentia-tensorflow`: `2.1b6.dev1389`
- numpy: `2.4.4`
- protobuf: `7.34.1`
- h5py: `3.14.0`

## Import smoke

Passing:

- Essentia import passed.
- `essentia.standard` import passed.
- `MonoLoader` exists.
- `TensorflowPredictMusiCNN` exists.
- `app.main` natural import passed.
- `app.services.classify` natural import passed.
- Essentia-then-TensorFlow import passed.

Failing:

- TensorFlow-then-Essentia import failed.
- TensorFlow-before-app import failed.

Failure summary:

```text
RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

## API health

- baseline `/health`: HTTP `200`, `{"ok":true}`
- candidate `/health`: HTTP `200`, `{"ok":true}`

## Primary classify parity

Fixture: `app/tmp/upload.mp3`

- baseline `/classify`: HTTP `200`, `ok: true`, `TIME_TOTAL:10.564639`
- candidate `/classify`: HTTP `200`, `ok: true`, `TIME_TOTAL:10.738028`
- top-level success keys match: `ok`, `message`, `genres`, `genres_pretty`
- top-1 genre matches: `electronic`
- genre sequence matches exactly:

```text
electronic
indie
rock
indie rock
alternative
electro
pop
electronica
```

- `genres_pretty` matches exactly:

```text
indie rock
alternative rock
electronic
indie
rock
alternative
electro
pop
```

Observed score differences remained small and did not change response shape, top-1, genre ordering, or `genres_pretty`:

- baseline `rock`: `0.195`
- candidate `rock`: `0.1951`
- baseline `alternative`: `0.1556`
- candidate `alternative`: `0.1557`

## Repeated classify

- baseline: 10/10 repeated `/classify` requests returned HTTP `200`
- candidate: 10/10 repeated `/classify` requests returned HTTP `200`

Baseline repeated timing:

- min: `9.842547`
- max: `12.817090`

Candidate repeated timing:

- min: `9.477613`
- max: `12.026984`

## Malformed and unsupported uploads

Fixtures:

- `empty.mp3`
- `fake.mp3`
- `unsupported.txt`

Baseline:

- `empty.mp3`: HTTP `400`, `{"ok":false,"error":"Файл пустой"}`
- `fake.mp3`: HTTP `400`, ffmpeg error body
- `unsupported.txt`: HTTP `400`, `{"ok":false,"error":"Неподдерживаемый формат файла"}`

Candidate:

- `empty.mp3`: HTTP `400`, `{"ok":false,"error":"Файл пустой"}`
- `fake.mp3`: HTTP `400`, ffmpeg error body
- `unsupported.txt`: HTTP `400`, `{"ok":false,"error":"Неподдерживаемый формат файла"}`

Result: status and error shape parity passed. ffmpeg version text differs as expected because the runtimes use different OS images.

## Docker stats

Captured after validation requests:

- baseline: `445.7MiB / 4GiB`, `10.88%`, PIDS `139`
- candidate: `340.4MiB / 4GiB`, `8.31%`, PIDS `9`

Result: candidate used less memory in this short validation smoke.

## Logs review

Baseline and candidate logs showed:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- valid `/classify` requests returned `200`
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- runtime shadow remained skipped by config
- no API startup crash was observed

Candidate logs also showed CPU allocation warnings during model execution. These were non-fatal in this smoke and did not prevent successful `/classify` responses.

## Decision impact

API parity remained good after reproducibility hardening, but the TensorFlow-first import-order crash persists. Roadmap 3.7 therefore should not proceed directly to controlled switch planning.
