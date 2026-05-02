# Roadmap 3.7 - Runtime candidate iteration and reproducibility hardening

## Goal

Harden the non-production Python 3.12 + `essentia-tensorflow` runtime candidate for `genre-classifier` after the Roadmap 3.6 decision `needs_additional_runtime_candidate_iteration`.

This stage does not approve production migration.

## Scope

- `genre-classifier` only
- non-production runtime candidate artifact only
- candidate dependency pinning hardening
- candidate base image reproducibility hardening
- build, resolver, image, import, API smoke, parity, memory, and log evidence
- decision artifact for Roadmap 3.7

Candidate artifact path:

```text
docker/runtime-candidates/py312-essentia-tensorflow/
```

Evidence path:

```text
docs/runtime/evidence/roadmap-3.7/
```

## Non-goals

- No `tidal-parser` changes.
- No production `Dockerfile` change.
- No production `docker-compose.yml` change.
- No production `requirements.txt` change.
- No app code change.
- No production runtime migration.
- No provider switch.
- No provider default change.
- No `/classify` contract change.
- No response shape change.
- No canary rollout.
- No LLM cutover.
- No candidate image wiring into production compose.
- No commit, tag, or push.

## Roadmap 3.6 findings summary

Roadmap 3.6 produced a reproducible candidate artifact and validated the Python 3.12 + `essentia-tensorflow` path against the current production baseline.

Passing Roadmap 3.6 findings:

- candidate build passed
- resolver evidence was captured
- model discovery passed
- API startup passed
- `/health` returned `{"ok":true}`
- primary `/classify` on `app/tmp/upload.mp3` returned `ok: true`
- success response shape matched production: `ok`, `message`, `genres`, `genres_pretty`
- top-1 genre matched: `electronic`
- genre sequence matched exactly
- `genres_pretty` matched exactly
- repeated request smoke passed 10/10 for baseline and candidate
- malformed upload parity passed for `empty.mp3`, `fake.mp3`, and `unsupported.txt`
- short smoke memory evidence was favorable for candidate
- natural app import path passed

Roadmap 3.6 did not approve production migration.

## Roadmap 3.6 gaps/blockers

Roadmap 3.6 decision remained:

```text
needs_additional_runtime_candidate_iteration
```

Blocking/caveat findings:

- Combined import smoke failed when `tensorflow` was imported before `essentia`.
- TensorFlow-before-app import failed with the same duplicate op registration crash.
- Failure summary: `RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)`.
- The issue was narrower than normal API startup because the natural app import path passed.
- The candidate default base image still used the tag form even though the observed digest was recorded.
- Direct runtime dependencies were pinned, but resolver-selected transitive dependencies were not listed in the candidate requirements input.
- Repeated build comparison and registry repo digest were not captured.
- Evidence remained short-smoke only, not long-running stability or concurrency evidence.

## Candidate artifact changes

Roadmap 3.7 changes:

- Changed the candidate default base from tag-only `python:3.12.13-slim-bookworm` to digest-pinned `python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`.
- Updated candidate labels/comments from Roadmap 3.6 to Roadmap 3.7.
- Kept the candidate isolated under `docker/runtime-candidates/py312-essentia-tensorflow/`.
- Expanded `requirements.runtime.txt` to pin the full Roadmap 3.6 observed `pip freeze` package set.
- Kept production `requirements.txt` unchanged.
- Kept the Dockerfile free of floating `pip install --upgrade pip setuptools wheel`.
- Rewrote the candidate README with purpose, non-production status, build command, smoke commands, known risks, and rollback baseline.

## Dependency pinning strategy

Roadmap 3.7 pins the candidate Python package input to the full package set observed in Roadmap 3.6 `pip freeze`, including direct dependencies and resolver-selected transitive dependencies.

Important pins include:

- `tensorflow==2.21.0`
- `essentia-tensorflow==2.1b6.dev1389`
- `numpy==2.4.4`
- `protobuf==7.34.1`
- `h5py==3.14.0`
- `fastapi==0.83.0`
- `pydantic==1.10.26`
- `uvicorn==0.16.0`
- `starlette==0.19.1`
- `python-multipart==0.0.5`
- `jinja2==3.0.3`
- pinned transitive dependencies listed in `requirements.runtime.txt`

Packaging tooling strategy:

- `pip` is inherited from the digest-pinned Python base image.
- The Dockerfile does not run a floating `pip`, `setuptools`, or `wheel` upgrade.
- `setuptools==82.0.1` and `wheel==0.47.0` are pinned in the candidate requirements because Roadmap 3.6 observed them in `pip freeze`.

## Base image strategy

Default base:

```text
python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77
```

This digest was observed during Roadmap 3.6 validation for `python:3.12.13-slim-bookworm`. Roadmap 3.7 uses it as the candidate default so the base does not float with the mutable tag.

The Dockerfile keeps `PYTHON_BASE_IMAGE` as a build arg so future candidate experiments can explicitly override the base only with a separately validated digest.

## Reproducible build evidence

Status: pass for candidate build

Evidence:

- `docs/runtime/evidence/roadmap-3.7/candidate-build-output.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-image-inspect.json`

Observed:

- candidate image tag: `music-tools-genre-classifier-roadmap-3.7:py312-etf`
- candidate image id: `sha256:fe7875f63005715ade4ace05ff339c8f3a35c5aa04a54ee43fd16407fb1ad2de`
- digest-pinned base used by build: `python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`
- clean candidate build was executed with `--no-cache`

## Resolver evidence

Status: pass

Evidence:

- `docs/runtime/evidence/roadmap-3.7/candidate-python-version.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-pip-version.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-pip-freeze.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-pip-check.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-os-release.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-system-packages.txt`

Observed:

- OS: Debian GNU/Linux 12 (bookworm)
- Python: `3.12.13`
- pip: `25.0.1`
- `pip check`: `No broken requirements found.`
- TensorFlow: `2.21.0`
- `essentia-tensorflow`: `2.1b6.dev1389`
- numpy: `2.4.4`
- protobuf: `7.34.1`
- h5py: `3.14.0`

## Image digest evidence

Status: pass for local image and base digest evidence

Evidence:

- `docs/runtime/evidence/roadmap-3.7/candidate-image-inspect.json`
- `docs/runtime/evidence/roadmap-3.7/candidate-build-output.txt`

Captured:

- base digest: `sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77`
- candidate local image id: `sha256:fe7875f63005715ade4ace05ff339c8f3a35c5aa04a54ee43fd16407fb1ad2de`

Not captured:

- candidate registry repo digest, because this non-production candidate image was not pushed

## Smoke evidence

Status: pass for API/app path, fail for TensorFlow-first import order

Evidence:

- `docs/runtime/evidence/roadmap-3.7/candidate-import-smoke.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-essentia-algorithms-smoke.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-app-import-smoke.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-musicnn-smoke.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-import-essentia-then-tensorflow.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-import-tensorflow-before-app.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-ffmpeg-version.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-health.json`
- `docs/runtime/evidence/roadmap-3.7/candidate-classify-upload.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-repeated-classify.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-malformed-uploads.txt`

Observed passing smoke:

- Essentia import passed.
- `essentia.standard` import passed.
- `MonoLoader`: `True`
- `TensorflowPredictMusiCNN`: `True`
- `app.main` natural import passed.
- `app.services.classify` natural import passed.
- Essentia-then-TensorFlow import passed.
- ffmpeg exists and reports `5.1.8-0+deb12u1`.
- candidate API startup passed.
- candidate `/health`: HTTP `200`, `{"ok":true}`
- candidate `/classify app/tmp/upload.mp3`: HTTP `200`, `ok: true`
- candidate repeated `/classify`: 10/10 HTTP `200`
- malformed `empty.mp3`, malformed `fake.mp3`, and unsupported `unsupported.txt`: HTTP `400`

Observed failing smoke:

- TensorFlow-then-Essentia combined import smoke failed.
- TensorFlow-before-app import failed.
- Failure summary: `RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)`.

## Parity revalidation evidence

Status: pass for API parity, with import-order blocker noted separately

Evidence:

- `docs/runtime/evidence/roadmap-3.7/baseline-build-output.txt`
- `docs/runtime/evidence/roadmap-3.7/baseline-health.json`
- `docs/runtime/evidence/roadmap-3.7/baseline-classify-upload.txt`
- `docs/runtime/evidence/roadmap-3.7/baseline-repeated-classify.txt`
- `docs/runtime/evidence/roadmap-3.7/baseline-malformed-uploads.txt`
- `docs/runtime/evidence/roadmap-3.7/parity-summary.md`

Observed parity:

- baseline `/health`: HTTP `200`, `{"ok":true}`
- candidate `/health`: HTTP `200`, `{"ok":true}`
- baseline `/classify app/tmp/upload.mp3`: HTTP `200`, `ok: true`
- candidate `/classify app/tmp/upload.mp3`: HTTP `200`, `ok: true`
- success top-level keys match: `ok`, `message`, `genres`, `genres_pretty`
- top-1 genre matches: `electronic`
- genre sequence matches exactly
- `genres_pretty` matches exactly
- repeated request smoke: baseline 10/10 HTTP `200`, candidate 10/10 HTTP `200`
- malformed upload statuses match: HTTP `400` for `empty.mp3`, `fake.mp3`, and `unsupported.txt`

Observed score differences:

- baseline `rock`: `0.195`
- candidate `rock`: `0.1951`
- baseline `alternative`: `0.1556`
- candidate `alternative`: `0.1557`

The score differences did not change ordering, top-1, genre sequence, `genres_pretty`, or response shape.

## Performance/memory evidence

Status: short smoke captured

Evidence:

- `docs/runtime/evidence/roadmap-3.7/docker-stats.txt`
- timing captured in classify and repeated classify files

Observed memory after validation requests:

- baseline: `445.7MiB / 4GiB`, `10.88%`, PIDS `139`
- candidate: `340.4MiB / 4GiB`, `8.31%`, PIDS `9`

Repeated request timing:

- baseline min/max observed: `9.842547` / `12.817090`
- candidate min/max observed: `9.477613` / `12.026984`

This is short smoke evidence only, not long-running performance approval.

## Logs review

Status: reviewed

Evidence:

- `docs/runtime/evidence/roadmap-3.7/baseline-logs-tail-300.txt`
- `docs/runtime/evidence/roadmap-3.7/candidate-logs-tail-300.txt`

Baseline logs:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- `/classify` returned `200` for valid uploads
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- CUDA/GPU warnings were present
- runtime shadow remained skipped by config

Candidate logs:

- startup completed
- Uvicorn running on `0.0.0.0:8021`
- `/health` returned `200`
- `/classify` returned `200` for valid uploads
- malformed uploads returned `400`
- fake mp3 produced expected ffmpeg error log
- CUDA/GPU warnings were present
- CPU allocation warnings were present during model execution
- runtime shadow remained skipped by config

No API startup crash was observed in the validation container logs.

## Remaining risks

- TensorFlow-first import-order compatibility still fails after reproducibility hardening.
- This remains short-smoke evidence only unless longer-running tests are added later.
- The fixture set remains local and small.
- No registry repo digest is expected because this candidate is not pushed.
- The candidate still differs materially from production runtime versions and OS lineage.
- Full transitive pinning improves repeatability but does not remove upstream wheel availability risk unless wheels are mirrored or vendored in a future stage.

## Decision

Decision: `needs_another_candidate_iteration`

Rationale:

- Candidate reproducibility hardening passed: digest-pinned base, no floating tooling upgrade, full observed `pip freeze` package pins, clean build, and clean `pip check`.
- API parity remained good against the current production baseline image built from the current production Dockerfile.
- The natural app import path passed.
- The Roadmap 3.6 TensorFlow-first import-order crash persists and remains a blocker/caveat before controlled switch planning.

Production runtime migration is not approved by Roadmap 3.7.

Production safety statements:

- production Dockerfile remains unchanged
- production compose remains unchanged
- production requirements remains unchanged
- app code remains unchanged
- provider default remains `legacy_musicnn`
- `/classify` contract remains unchanged
- response shape remains unchanged
- `tidal-parser` remains untouched

## Recommendation for Roadmap 3.8

Roadmap 3.8 should perform another candidate iteration before controlled switch planning:

- investigate whether `tensorflow==2.21.0` and `essentia-tensorflow==2.1b6.dev1389` can safely support TensorFlow-first imports
- test an alternate compatible TensorFlow/Essentia package combination if available
- decide whether supported import order can be formally constrained to the natural app/Essentia-first path
- rerun import-order diagnostics after any dependency/runtime change
- keep the digest-pinned base and full candidate-only pins strategy
- repeat API parity checks against the current production baseline
- expand valid fixture coverage beyond `app/tmp/upload.mp3`
- add longer-running latency/memory and concurrency evidence
- keep production Dockerfile, compose, requirements, provider default, `/classify` contract, and response shape unchanged until a separate migration decision exists

## Rollback considerations

Rollback remains simple because Roadmap 3.7 does not change production runtime wiring.

Rollback action:

- continue using the existing production `Dockerfile`, `docker-compose.yml`, and `requirements.txt`
- do not build or run the Roadmap 3.7 candidate for production traffic
- remove or ignore the candidate image if validation fails

No production rollback command is required for this stage because no production migration is performed.
