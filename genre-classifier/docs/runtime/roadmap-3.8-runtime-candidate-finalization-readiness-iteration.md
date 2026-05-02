# Roadmap 3.8 - Runtime candidate finalization readiness iteration

## Goal

Run a focused finalization-readiness iteration for the non-production Python 3.12 + `essentia-tensorflow` runtime candidate, capture fresh evidence, and make a readiness decision without performing a production migration.

## Scope

- `genre-classifier` only.
- Non-production candidate artifact under `docker/runtime-candidates/py312-essentia-tensorflow/`.
- Evidence under `docs/runtime/evidence/roadmap-3.8/`.
- Clean candidate rebuild, resolver evidence, image identity evidence, import/model smoke, API smoke, baseline comparison, memory snapshot, log review, and rollback documentation.

## Non-goals

- No `tidal-parser` changes.
- No production `Dockerfile` change.
- No production `docker-compose.yml` change.
- No production `requirements.txt` change.
- No app code change.
- No production runtime migration.
- No provider switch or provider default change.
- No `/classify` contract change.
- No response shape change.
- No canary rollout.
- No LLM cutover.
- No commit, tag, or push.

## Roadmap 3.7 Findings Summary

Roadmap 3.7 hardened the candidate artifact by digest-pinning the Python 3.12 base image, pinning the full observed Python package set, avoiding floating packaging-tool upgrades, and revalidating the candidate against the production baseline.

Passing 3.7 findings:

- clean candidate build passed
- `pip check` passed
- natural app import path passed
- Essentia/MusiCNN model load smoke passed
- API startup passed
- `/health` passed
- `/classify app/tmp/upload.mp3` passed
- repeated classify smoke passed 10/10
- malformed and unsupported upload behavior remained HTTP `400`
- top-level success response keys matched baseline: `ok`, `message`, `genres`, `genres_pretty`
- provider default remained `legacy_musicnn`
- runtime shadow remained disabled by default

## Roadmap 3.7 Gaps/Blockers

Roadmap 3.7 decision was `needs_another_candidate_iteration`.

Remaining gaps entering Roadmap 3.8:

- TensorFlow-first import order still crashed with duplicate `Bitcast` op registration.
- The candidate registry repo digest was not available because the non-production image was not pushed.
- Evidence was still short-smoke only, not long-running stability or concurrency evidence.
- Finalization readiness still needed a fresh clean rebuild and fresh API parity check.

## Candidate Artifact Changes

Roadmap 3.8 made metadata-only candidate changes:

- Updated candidate Dockerfile comments and OCI title label from Roadmap 3.7 to Roadmap 3.8.
- Updated candidate README title, image tags, container name examples, and Roadmap 3.8 wording.

No dependency pins were changed. No production files and no app code were changed.

## Dependency Pinning Strategy

`requirements.runtime.txt` remains a full candidate-only pin set from the Roadmap 3.6 observed resolver output. Important pins:

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

Roadmap 3.8 resolver evidence:

- `candidate-pip-freeze.txt`
- `candidate-pip-show-core.txt`
- `candidate-pip-check.txt`
- `candidate-pip-freeze-vs-requirements.diff`
- `candidate-pip-freeze-vs-requirements-sorted.diff`

Observed result:

- `pip check`: `No broken requirements found.`
- Installed versions matched expected pins.
- The sorted freeze comparison only differs by canonical distribution capitalization: `jinja2==3.0.3` input vs `Jinja2==3.0.3` in `pip freeze`.

## Base Image Strategy

The candidate continues to use the digest-pinned default base:

```text
python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77
```

This avoids mutable tag drift. The Dockerfile still allows an explicit `PYTHON_BASE_IMAGE` override only for future separately validated candidate experiments.

## Apt/System Deps Strategy

The candidate installs only the existing runtime OS package set:

- `ca-certificates`
- `ffmpeg`
- `libgomp1`
- `libsndfile1`

Evidence:

- `candidate-ffmpeg-version.txt`: `ffmpeg 5.1.8-0+deb12u1`
- `candidate-dpkg-av-packages.txt`: captured `ffmpeg`, `libav*`, `libsw*`, `libsndfile1`, and `libgomp1` package versions.

## Reproducible Build Evidence

Status: pass for clean local candidate build.

Command:

```sh
docker build --no-cache \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools/genre-classifier:py312-essentia-tensorflow-roadmap-3.8 \
  .
```

Evidence:

- `candidate-build-output.txt`
- `candidate-image-inspect.json`
- `candidate-image-ls.txt`

## Resolver Evidence

Status: pass.

Observed:

- Python: `3.12.13`
- pip: `25.0.1`
- `pip check`: `No broken requirements found.`
- `essentia-tensorflow`: `2.1b6.dev1389`
- TensorFlow: `2.21.0`
- numpy: `2.4.4`
- protobuf: `7.34.1`
- h5py: `3.14.0`
- FastAPI/Pydantic/Uvicorn/Starlette pins matched expected candidate pins.

Evidence:

- `candidate-python-version.txt`
- `candidate-pip-version.txt`
- `candidate-pip-check.txt`
- `candidate-pip-freeze.txt`
- `candidate-pip-show-core.txt`

## Image Id/Digest Evidence

Candidate tag:

```text
music-tools/genre-classifier:py312-essentia-tensorflow-roadmap-3.8
```

Observed local image id:

```text
sha256:a8eaa7fa4b48e56f65f901288f21c20bae00958192cccc848d4b932a49f707a8
```

Observed `docker image ls` digest:

```text
<none>
```

`RepoDigests` is empty because this non-production candidate image was not pushed to a registry.

## Smoke Evidence

Passing:

- Essentia-first import smoke passed.
- `MonoLoader` exists.
- `TensorflowPredictMusiCNN` exists.
- TensorFlow import after Essentia passed.
- `app.main` import passed.
- `app.services.classify` import passed.
- MusiCNN `.pb` discovery passed for `/app/app/models/msd-musicnn-1.pb`.
- MusiCNN model load passed.
- ffmpeg smoke passed.
- API startup passed.
- `/health` passed with HTTP `200`.
- `/classify app/tmp/upload.mp3` passed with HTTP `200`, `ok: true`.
- 10 repeated `/classify` requests passed with HTTP `200`.
- malformed empty upload returned HTTP `400`.
- malformed fake mp3 returned HTTP `400`.
- unsupported text upload returned HTTP `400`.

Failing:

- TensorFlow-first import order still failed with duplicate `Bitcast` op registration:

```text
RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

Evidence:

- `candidate-import-smoke.txt`
- `candidate-import-tensorflow-first-smoke.txt`
- `candidate-musicnn-model-smoke.txt`
- `candidate-ffmpeg-version.txt`
- `candidate-startup-logs-initial.txt`
- `candidate-health.json`
- `candidate-classify-upload.txt`
- `candidate-repeated-classify.txt`
- `candidate-malformed-uploads.txt`

## Parity Revalidation Evidence

Production baseline was available through the `genre-classifier` service compose from `/opt/music-tools/genre-classifier`. No monorepo-root compose command was used.

Evidence:

- `baseline-compose-ps.txt`
- `baseline-docker-ps.txt`
- `baseline-health.json`
- `baseline-classify-upload.txt`
- `baseline-logs-tail-300.txt`

Observed:

- baseline `/health`: HTTP `200`, `{"ok":true}`
- candidate `/health`: HTTP `200`, `{"ok":true}`
- baseline `/classify app/tmp/upload.mp3`: HTTP `200`, `ok: true`
- candidate `/classify app/tmp/upload.mp3`: HTTP `200`, `ok: true`
- top-level success response keys remained `ok`, `message`, `genres`, `genres_pretty`
- top-1 genre remained `electronic`
- genre order remained:

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

- `genres_pretty` remained:

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

Observed score drift remained tiny and did not change shape or ordering:

- baseline `rock`: `0.195`
- candidate `rock`: `0.1951`
- baseline `alternative`: `0.1556`
- candidate `alternative`: `0.1557`

## Performance/Memory Evidence

Evidence:

- `candidate-classify-upload.txt`
- `candidate-repeated-classify.txt`
- `candidate-docker-stats.txt`
- `docker-stats.txt`

Observed candidate repeated classify timing:

- min: `9.410514`
- max: `11.666863`
- result: 10/10 HTTP `200`

Baseline single classify timing:

- `11.178532`

Candidate single classify timing:

- `10.355976`

Docker stats after smoke:

- baseline: `250MiB / 4GiB`, `6.10%`, PIDS `26`
- candidate: `424.5MiB / 4GiB`, `10.36%`, PIDS `9`

This remains short-smoke evidence only.

## Logs Review

Evidence:

- `candidate-logs-tail-300.txt`
- `baseline-logs-tail-300.txt`

Observed candidate logs:

- Uvicorn startup completed.
- Valid `/classify` requests logged `file_processing_succeeded`.
- Runtime shadow stayed disabled by config: `genre_classifier.shadow.skipped status=skipped_by_config`.
- Empty and unsupported uploads logged validation warnings.
- Fake mp3 logged expected ffmpeg error.
- CUDA/GPU absence warnings were present and non-fatal.
- No API startup crash was observed.

## Remaining Risks

- TensorFlow-first import-order crash remains unresolved.
- The candidate is validated only on short smoke workloads.
- Fixture coverage remains limited to `app/tmp/upload.mp3` plus small malformed/unsupported fixtures.
- No registry repo digest exists because the candidate image was not pushed.
- The candidate runtime differs materially from production runtime versions and OS lineage.
- Full pinning does not protect against future upstream wheel unavailability unless wheels are mirrored or vendored.

## Decision

Decision: `needs_another_candidate_iteration`

Rationale:

- Most finalization-readiness criteria passed: clean build, pinned dependency evidence, digest-pinned base, apt package evidence, `pip check`, model load, API startup, `/health`, valid `/classify`, repeated classify, malformed/unsupported behavior, response shape, provider default, runtime shadow default, no production file changes, and rollback documentation.
- The Roadmap 3.7 blocker persists: TensorFlow-first import order still crashes with duplicate `Bitcast` op registration.
- Until that import-order caveat is resolved or explicitly accepted as a supported runtime constraint, this candidate should not advance to controlled switch planning.

Production runtime migration is not approved by Roadmap 3.8.

## Recommendation For Roadmap 3.9

Roadmap 3.9 should focus on one of these outcomes:

- Resolve TensorFlow-first import-order incompatibility by testing an alternate compatible TensorFlow/Essentia package combination.
- Or explicitly document and approve the supported import order as Essentia/app-first only, with startup/import guards or operational checks if needed.
- Repeat the same clean build, resolver, model load, API parity, malformed upload, memory, and log evidence after the chosen resolution.
- Add longer-running stability and basic concurrency evidence before any controlled switch planning.

## Rollback Considerations

Rollback remains simple because Roadmap 3.8 does not change production runtime wiring.

Rollback baseline:

- production Dockerfile: `Dockerfile`
- production compose: `docker-compose.yml`
- production requirements: `requirements.txt`
- default provider: `legacy_musicnn`
- production `/classify` contract and response shape unchanged
- `tidal-parser` unchanged
- `tidal-parser` unchanged

Rollback action:

- continue using the existing production service/runtime
- do not route traffic to the Roadmap 3.8 candidate
- remove or ignore the non-production candidate image/container if validation is no longer needed

No production rollback command is required for this stage because no production migration was performed.
