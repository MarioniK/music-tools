# Roadmap 4.80 - ONNX/MusiCNN Docker/runtime packaging decision gate

## Summary

Roadmap 4.80 фиксирует только decision gate для Docker/runtime packaging
`onnx_musicnn` lane. Это не implementation step, не Docker build, не Docker
Compose run, не production migration и не readiness approval.

Главное решение:

- production/default image остаётся `legacy_musicnn` only;
- `onnx_musicnn` runtime packaging идёт через explicit optional runtime path;
- preferred next implementation - optional Docker target/profile или explicit
  build arg, а не production default install;
- optional dependencies устанавливаются только для optional ONNX runtime
  image/path;
- `requirements-optional-onnx.txt` не подключается к default production install
  path;
- artifacts не попадают в repo;
- artifacts доставляются только через explicit mounted paths;
- runtime downloads by default запрещены;
- default provider остаётся `legacy_musicnn`;
- `onnx_musicnn` включается только explicit opt-in:
  - `GENRE_PROVIDER=onnx_musicnn`
  - explicit ONNX model path
  - explicit classes metadata path
- missing deps/artifacts должны fail gracefully;
- production readiness не granted.

## Why 4.80 is decision-only

4.75-4.79 уже подтвердили, что ONNX/MusiCNN lane существует и работает в
локальных safe slices, но эти шаги intentionally stopped before Docker/runtime
packaging.

В 4.80 мы не внедряем контейнеризацию. Мы только выбираем упаковочную
стратегию, чтобы следующий шаг мог быть минимальным и migration-safe:

- не менять default production image;
- не подключать optional ONNX dependencies в production install path;
- не разрешать runtime downloads by default;
- не менять `/classify` contract;
- не менять response shape;
- не трогать `tidal-parser`.

## Current proven ONNX/MusiCNN path

### Roadmap 4.75

- isolated optional dependency install probe completed;
- `onnxruntime==1.25.1` and `essentia-tensorflow==2.1b6.dev1389` installed in
  an isolated environment;
- imports worked;
- `TensorflowInputMusiCNN` was available;
- production defaults and Docker were not changed.

### Roadmap 4.76

- isolated runtime readiness probe completed;
- explicit artifact path handling was validated;
- `onnxruntime` and `essentia.standard` readiness was confirmed;
- no Docker/runtime migration happened.

### Roadmap 4.77

- isolated vertical probe completed for patch -> ONNX -> mapping;
- explicit external artifacts were used;
- `genres` and `genres_pretty` became non-empty in the mapping flow;
- production boundaries remained unchanged.

### Roadmap 4.78

- disabled-by-default `onnx_musicnn` provider was exercised directly;
- direct provider smoke completed;
- explicit artifacts and preprocessing path were validated;
- `genres` and `genres_pretty` were non-empty;
- still no Docker/runtime migration.

### Roadmap 4.79

- local route-level `/classify` opt-in smoke completed;
- local boundary used `direct_async_route_coroutine`;
- request format was `POST /classify` with multipart field `file` and content
  type `audio/mpeg`;
- status code was `200`;
- required response fields were present:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- `genres` and `genres_pretty` were non-empty;
- this was not a Docker or network smoke.

## Chosen packaging direction

The chosen direction is:

- keep default runtime legacy-only;
- add optional ONNX runtime packaging path in the next implementation step;
- prefer explicit optional Docker target/profile/build arg;
- no runtime downloads by default;
- mounted artifacts only;
- explicit env opt-in only.

This keeps the default production path stable while making the optional ONNX
lane deployable in a controlled, explicit way later.

## Required explicit env/config

The explicit configuration surface remains:

- `GENRE_PROVIDER=onnx_musicnn`
- `ONNX_MUSICNN_MODEL_PATH`
- `ONNX_MUSICNN_METADATA_PATH`

Current code uses these exact names, and the default provider remains
`legacy_musicnn`.

## Non-goals

This gate does not do any of the following:

- no Docker implementation in 4.80;
- no build;
- no default provider switch;
- no production readiness claim;
- no change to `/classify` contract;
- no change to response shape;
- no `tidal-parser` changes.

## Risk notes

- `essentia-tensorflow` weight/size risk remains high;
- optional ONNX runtime image size must be measured in the implementation step;
- TensorFlow/CUDA warnings may remain noisy, but they are non-blocking for this
  decision gate;
- artifact provenance/checksum is already documented in 4.71;
- the 4.79 route-level smoke is not a network or Docker smoke.

## Next step recommendation

Roadmap 4.81 should implement the optional ONNX Docker target/profile without
changing the default provider or the default production install path.

