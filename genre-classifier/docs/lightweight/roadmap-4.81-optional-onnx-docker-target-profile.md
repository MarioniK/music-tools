# Roadmap 4.81 - optional ONNX Docker target/profile

## Summary

Roadmap 4.81 adds an explicit optional Docker/runtime packaging path for
`onnx_musicnn` without changing the default production path.

Что изменено:

- default build/install path remains legacy-only;
- `requirements-optional-onnx.txt` is installed only in the optional ONNX
  Docker target;
- default `genre-classifier` service keeps the legacy runtime path;
- optional `genre-classifier-onnx` service is gated behind a Compose profile
  and requires explicit ONNX model and metadata mounts;
- artifacts are delivered through mounted paths only;
- runtime downloads by default remain forbidden.

## Implementation shape

### Dockerfile

- `runtime-base` installs `requirements.txt` only;
- `legacy-runtime` remains the default final stage;
- `onnx-runtime` extends `runtime-base` and installs
  `requirements-optional-onnx.txt` only there.

### Compose

- default `genre-classifier` service targets `legacy-runtime`;
- optional `genre-classifier-onnx` service uses the `onnx` profile;
- optional service targets `onnx-runtime`;
- optional service sets explicit ONNX env vars:
  - `GENRE_PROVIDER=onnx_musicnn`
  - `ONNX_MUSICNN_MODEL_PATH`
  - `ONNX_MUSICNN_METADATA_PATH`
- optional service mounts ONNX artifacts explicitly from host paths.

## Validation notes

- production/default provider stays `legacy_musicnn`;
- `/classify` contract and response shape are unchanged;
- `requirements.txt` stays free of optional ONNX runtime dependencies;
- no Docker build was run for this slice;
- no Compose runtime smoke was run;
- no `/classify` call was made.

## Non-goals

- no default provider switch;
- no production readiness claim;
- no runtime downloads by default;
- no artifact baking into the image;
- no `tidal-parser` changes.

## Next step recommendation

Roadmap 4.82 can do optional Docker build/static runtime validation for the
new ONNX target without changing the default legacy runtime.
