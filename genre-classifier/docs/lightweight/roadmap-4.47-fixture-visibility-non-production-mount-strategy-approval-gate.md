# Roadmap 4.47 - Fixture visibility / non-production mount strategy approval gate

Roadmap 4.47 is a fixture visibility and mount strategy gate for the local MusiCNN ONNX parity scaffold. Roadmap 4.46 confirmed that the existing `genre-classifier` container is available and that TensorFlow and Essentia imports work inside it, but the external legal fixture path is not visible from that running container.

This stage chooses a safe non-production strategy for making the legal CC0 fixtures visible during a future scoped baseline-only run. It does not repeat baseline capture, run ONNX, compare TensorFlow against ONNX, run full numeric parity, call `/classify`, or change production behavior.

The strategy decision is recorded in:

- `docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-fixture-visibility-strategy-report.json`

## Why baseline capture is not repeated

Roadmap 4.46 already reached the relevant blocker: `FIXTURE_PATH_NOT_AVAILABLE_IN_CONTAINER`, which also blocks baseline capture through `BASELINE_CAPTURE_BLOCKED_BY_CONTAINER_MOUNT`. Repeating capture before approving a mount strategy would only re-hit the same container visibility problem or require an unapproved Docker/Compose workaround.

Roadmap 4.47 therefore remains an approval gate. It selects the strategy for a later baseline-only execution stage and records the boundaries that keep the work non-production.

## Selected strategy

The preferred strategy is `one_off_compose_run_bind_mount`.

This is preferred because it requires no committed Compose changes, no Dockerfile changes, no image rebuild, and no mutation of the running service container. The legal fixtures remain outside the repository and can be mounted only for the future scoped baseline-only command. The rollback is simple: stop using the one-off command and the mount is gone.

## Fallback strategies

`temporary_local_override_not_committed` is a fallback only. It can be acceptable when the one-off run form is unavailable, but the override file must remain local and uncommitted. A committed override would turn a local evaluation convenience into persistent project configuration, which is outside the roadmap scope.

`docker_cp_to_container_temp_path` is less clean and fallback only. It avoids committed files, Dockerfile edits, and rebuilds, but it mutates container state and is less transparent than a one-off read-only bind mount.

`existing_mounted_path` can be used only if discovered in the scoped `genre-classifier` service context. Roadmap 4.46 showed that the known external fixture path was not available inside the running container, so this cannot be assumed.

If none of these strategies can be selected safely, the correct decision is to block rather than widen the execution scope.

## Why /classify is not allowed

`/classify` is a production API contract. Roadmap 4.47 is only about fixture visibility for a future scoped baseline-only capture path, so endpoint behavior and response shape must remain untouched and untested in this stage.

## Baseline

`legacy_musicnn` remains the baseline. This roadmap does not approve provider implementation, default provider switching, ONNX execution, production inference, or production migration.

## Non-goals

- Execute baseline capture.
- Run ONNX.
- Run TensorFlow vs ONNX comparison.
- Run full numeric parity.
- Call `/classify`.
- Rebuild Docker.
- Modify Dockerfile or committed Compose files.
- Change provider factory, default provider, `/classify` contract, or response shape.
- Change production dependencies.
- Add audio files, model files, or venv files.
- Touch `tidal-parser`.
- Create a commit, tag, release, or push.

## Next step

The next recommended roadmap step is Roadmap 4.48 - scoped baseline-only capture. That future step should run scoped `legacy_musicnn` baseline-only capture using the approved `one_off_compose_run_bind_mount` execution strategy from the `genre-classifier` service directory. It should still exclude ONNX execution, `/classify` calls, TensorFlow vs ONNX comparison, full numeric parity, provider changes, dependency changes, Docker rebuilds, and production Compose changes.
