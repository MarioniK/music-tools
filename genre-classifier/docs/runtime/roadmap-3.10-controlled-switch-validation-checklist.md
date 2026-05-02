# Roadmap 3.10 - Controlled switch validation checklist

This checklist is the recommended Roadmap 3.11 gate set for a controlled `genre-classifier` production runtime switch implementation.

Roadmap 3.10 does not perform the switch. Production `Dockerfile`, `docker-compose.yml`, `requirements.txt`, app code, provider default, `/classify` contract, and response shape remain unchanged.

## Baseline

- [ ] Confirm work is inside `/opt/music-tools/genre-classifier`.
- [ ] Confirm `tidal-parser` is untouched.
- [ ] Capture current production runtime as the authoritative rollback baseline.
- [ ] Capture baseline image/container identity.
- [ ] Capture baseline `/health`.
- [ ] Capture baseline `/classify` valid fixture output.
- [ ] Capture baseline provider default and response shape.
- [ ] Capture baseline malformed upload behavior.
- [ ] Capture baseline logs.
- [ ] Capture baseline memory and latency sanity.

## Build and Runtime Identity

- [ ] Build the production switch candidate from the approved implementation files.
- [ ] Record image id and base image digest.
- [ ] Record OS release.
- [ ] Record Python version.
- [ ] Record pip version.
- [ ] Record TensorFlow version.
- [ ] Record `essentia-tensorflow` version.
- [ ] Record numpy, protobuf, h5py, FastAPI, Pydantic, Uvicorn, and Starlette versions.
- [ ] Run `pip check`.

## Import-Order Guardrail

- [ ] Confirm production startup preserves app-first / Essentia-first import order.
- [ ] Confirm no startup, config, health, metrics, monitoring, warmup, or provider path imports TensorFlow before Essentia/classify initialization.
- [ ] Pass `essentia_first`.
- [ ] Pass `essentia_standard_first`.
- [ ] Pass `classify_import`.
- [ ] Pass `app_main_import`.
- [ ] Pass `classify_then_tensorflow`.
- [ ] Pass `app_then_tensorflow`.
- [ ] Pass `model_load_essentia_first`.
- [ ] Pass `same_process_repeated_imports`.
- [ ] Treat TensorFlow-first mixed import paths as unsupported unless future evidence explicitly resolves duplicate `Bitcast` registration.

## API and Behavior

- [ ] Start candidate runtime successfully.
- [ ] Pass `/health`.
- [ ] Pass `/classify` on the valid fixture.
- [ ] Confirm provider default remains `legacy_musicnn`.
- [ ] Confirm `/classify` contract is unchanged.
- [ ] Confirm success response shape remains `ok`, `message`, `genres`, `genres_pretty`.
- [ ] Compare candidate output against baseline fixture output.
- [ ] Pass repeated request smoke.
- [ ] Pass malformed empty upload behavior.
- [ ] Pass malformed fake mp3 upload behavior.
- [ ] Pass unsupported text upload behavior.
- [ ] Review startup and request logs.
- [ ] Capture memory sanity.
- [ ] Capture latency sanity.

## Rollback Readiness

- [ ] Preserve current production runtime files/configuration until acceptance.
- [ ] Document rollback commands.
- [ ] Confirm previous runtime can be restored without monorepo-root compose usage.
- [ ] Confirm rollback validation commands for `/health`, `/classify`, malformed upload, and logs.

## Rollback Triggers

- [ ] Startup failure.
- [ ] `/health` failure.
- [ ] `/classify` failure.
- [ ] Response shape change.
- [ ] Provider default change.
- [ ] Unexpected runtime shadow activation.
- [ ] Supported import-order failure.
- [ ] Duplicate `Bitcast` in normal startup path.
- [ ] Model load failure.
- [ ] Malformed upload crash.
- [ ] Memory instability.
- [ ] Unacceptable latency.
