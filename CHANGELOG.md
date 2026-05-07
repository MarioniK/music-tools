# Changelog

## [v0.5.0] - Unreleased

### Added

- Постоянная release documentation для ONNX default runtime в `genre-classifier`.
- Operator guide для текущего ONNX runtime и rollback path.
- Release summary, фиксирующая post-switch state после controlled ONNX default switch.

### Changed

- Default runtime `genre-classifier` переключён на `onnx_musicnn`.
- Default Docker target переключён на `onnx-runtime-slim`.
- `README.md` больше не описывает legacy MusicNN как текущий default runtime.

### Operational notes

- ONNX runtime использует внешние артефакты из `/opt/music-tools-artifacts/genre-classifier/onnx`.
- Health check остаётся `curl http://localhost:8021/health`.
- Legacy rollback path сохранён через `genre-classifier-legacy` и `legacy_musicnn`.

### Migration notes

- `tidal-parser` code не мигрировался в этом release slice.
- `/classify` response shape не менялся.
- Legacy `.pb` model и `essentia-tensorflow` dependency сохранены.

### Known risks

- Runtime depends on external artifact provisioning.
- Future cleanup of old lightweight roadmap/evidence files should be done in a separate step.
- OpenVINO/iGPU is not part of v0.5.0.
