# Roadmap 3.10 - Controlled production runtime switch planning

## 1. Goal

Prepare the planning and decision artifact for a later controlled production runtime switch implementation for `genre-classifier`.

Roadmap 3.10 decides whether the Python 3.12 + `essentia-tensorflow` candidate has enough evidence to enter an implementation planning stage with an explicit approval gate. It does not perform the production runtime switch.

## 2. Scope

- `genre-classifier` only.
- Planning documentation.
- Switch design recommendation.
- Approval gates.
- Rollback strategy.
- Import-order invariant guardrail.
- Risk register.
- Roadmap 3.11 implementation boundaries.

The current production runtime remains the authoritative rollback baseline.

## 3. Non-goals

- No `tidal-parser` changes.
- No production `Dockerfile` changes.
- No production `docker-compose.yml` changes.
- No production `requirements.txt` changes.
- No app code changes.
- No production runtime switch.
- No provider switch.
- No provider default change.
- No `/classify` contract change.
- No response shape change.
- No canary rollout.
- No LLM cutover.
- No commit, tag, or push.

Roadmap 3.10 keeps production behavior unchanged:

- default provider remains `legacy_musicnn`
- `/classify` contract remains unchanged
- success response shape remains `ok`, `message`, `genres`, `genres_pretty`
- app code remains unchanged
- production Dockerfile, compose, and requirements remain unchanged
- `tidal-parser` is untouched

## 4. Evidence summary from Roadmap 3.4-3.9

Roadmap 3.4 established primary candidate viability for Python 3.12 + `essentia-tensorflow`:

- Docker build passed in an isolated experimental artifact.
- `TensorflowPredictMusiCNN` was available.
- the MusiCNN `.pb` model loaded.
- API startup, `/health`, and `/classify` smoke passed.
- provider default remained `legacy_musicnn`.
- production files and app code remained unchanged.

Roadmap 3.5 validated isolated runtime parity against the production baseline:

- baseline and candidate containers started.
- `/health` returned HTTP `200`.
- `/classify` returned HTTP `200` for `app/tmp/upload.mp3`.
- success response shape matched: `ok`, `message`, `genres`, `genres_pretty`.
- top-N genre sequence and `genres_pretty` matched for the primary fixture.
- 10 repeated requests passed for both runtimes.
- malformed upload behavior remained HTTP `400` without crashing.

Roadmap 3.6 produced a reproducible non-production candidate artifact:

- candidate artifact created under `docker/runtime-candidates/py312-essentia-tensorflow/`.
- direct runtime dependency pins were introduced.
- build, resolver, model discovery, API smoke, parity, and memory evidence were captured.
- TensorFlow-first import order failed with duplicate `Bitcast` registration, while the natural app path still passed.

Roadmap 3.7 hardened reproducibility:

- Python base image was digest-pinned.
- the full observed Python package set was pinned in candidate-only `requirements.runtime.txt`.
- `pip check` passed.
- app-first and Essentia-first runtime behavior passed.
- API parity passed again.
- TensorFlow-first mixed import paths remained blocked.

Roadmap 3.8 completed finalization-readiness validation:

- clean candidate rebuild passed.
- dependency pins still matched expected installed versions.
- `pip check` passed.
- app import, model load, `/health`, `/classify`, repeated classify, malformed upload, memory snapshot, and log review passed.
- TensorFlow-first import order remained the only finalization blocker.

Roadmap 3.9 investigated the import-order blocker:

- TensorFlow-only import passed.
- Essentia-first imports passed.
- app-first imports passed.
- model load with Essentia-first order passed.
- app-then-TensorFlow and classify-then-TensorFlow passed.
- TensorFlow-then-Essentia, TensorFlow-then-`essentia.standard`, TensorFlow-then-MusiCNN symbol, and TensorFlow-first model load failed deterministically with duplicate `Bitcast` registration.
- decision was `ready_for_controlled_switch_planning_with_import_order_invariant`.

## 5. Why controlled switch planning is now allowed

Controlled switch planning is allowed because Roadmap 3.4-3.9 evidence shows that the candidate works on the production-relevant path when the process initializes through the current app-first / Essentia-first import order.

The remaining blocker is no longer unknown. Roadmap 3.9 isolated it to unsupported TensorFlow-first mixed import paths. The current service path does not require that unsupported order, and later implementation can add explicit validation gates to prove the invariant before any production switch.

This is planning permission only. It is not production migration approval.

## 6. Why Roadmap 3.10 does not perform the switch

Roadmap 3.10 does not perform the switch because production runtime changes require a separate explicit implementation approval gate.

The switch may affect production runtime identity, dependency set, base image, container build behavior, startup path, operational rollback, and deployment evidence. Those changes must be reviewed and approved as Roadmap 3.11 or later implementation work.

In Roadmap 3.10:

- production `Dockerfile` remains unchanged
- production `docker-compose.yml` remains unchanged
- production `requirements.txt` remains unchanged
- app code remains unchanged
- provider default remains `legacy_musicnn`
- `/classify` contract remains unchanged
- response shape remains unchanged
- current production runtime remains the authoritative rollback baseline

## 7. Recommended switch design

Recommended implementation design for a later approved stage:

- Keep the production app path unchanged.
- Preserve default provider `legacy_musicnn`.
- Preserve `/classify` request contract and success response shape.
- Use the Roadmap 3.7/3.8 digest-pinned Python 3.12 + `essentia-tensorflow` candidate as the source runtime design.
- Use the validated candidate artifact paths as the Roadmap 3.11 source runtime reference:
  - `docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile`
  - `docker/runtime-candidates/py312-essentia-tensorflow/requirements.runtime.txt`
  - `docker/runtime-candidates/py312-essentia-tensorflow/README.md`
- Promote candidate dependency pins only through an explicitly reviewed production requirements change.
- Promote runtime Dockerfile changes only through an explicitly reviewed production Dockerfile change.
- Update compose only if needed for build/runtime identity, without changing the API surface.
- Add validation evidence before and after the switch.
- Treat current production runtime as the rollback target until the switched runtime has accumulated separately approved production evidence.

The switch should be controlled as a single-service runtime replacement for `genre-classifier`, not as an app behavior migration.

## 8. Production files likely to change in the implementation stage

Roadmap 3.11 may need changes to:

- `Dockerfile`
- `requirements.txt`
- `docker-compose.yml`, only if runtime/build wiring requires it
- docs under `docs/runtime/`
- evidence under `docs/runtime/evidence/`

Roadmap 3.11 should avoid app code changes unless an explicit later approval expands scope. Provider behavior, `/classify` contract, and response shape should remain unchanged.

## 9. Production switch candidate scope

Candidate scope for implementation:

- Python `3.12.13`.
- Debian bookworm slim base, digest-pinned.
- `essentia-tensorflow==2.1b6.dev1389`.
- `tensorflow==2.21.0`.
- full pinned runtime dependency set from the Roadmap 3.7/3.8 candidate.
- OS runtime packages already validated in the candidate: `ca-certificates`, `ffmpeg`, `libgomp1`, `libsndfile1`.
- existing `app/` package copied unchanged.
- existing startup command shape: `uvicorn app.main:app --host 0.0.0.0 --port 8021`.

Out of candidate scope:

- LLM provider activation.
- provider default change.
- response shape extension.
- `/classify` contract change.
- `tidal-parser`.
- monorepo-root compose orchestration.

## 10. Approval gates

Roadmap 3.11 must not switch production until all required gates are explicitly approved and recorded.

Required validation gates:

- pre-switch baseline capture from the current production runtime
- clean production-candidate build
- runtime identity capture: OS, Python, pip, TensorFlow, Essentia, numpy, protobuf, h5py, FastAPI, Uvicorn
- `pip check`
- import-order smoke matrix
- Essentia-first model load
- `/health`
- `/classify` valid fixture
- parity against current production baseline
- repeated request smoke
- malformed upload behavior
- startup and request log review
- memory sanity snapshot
- latency sanity snapshot
- rollback readiness check

The approval record should include the exact image id, base digest, dependency evidence, validation commands, and rollback command plan.

## 11. Rollback strategy

The current production runtime remains the authoritative rollback baseline.

Rollback strategy:

- Preserve the pre-switch production image/build path.
- Preserve the pre-switch production compose/runtime configuration until the switch is accepted.
- Keep evidence showing the baseline `/health`, `/classify`, response shape, provider default, and logs.
- If any rollback trigger fires, restore the previous production runtime files/configuration and restart `genre-classifier` from the known baseline.
- After rollback, rerun `/health`, `/classify` fixture, malformed upload, and log checks to prove service recovery.

Rollback triggers:

- startup failure
- `/health` failure
- `/classify` failure
- response shape change
- provider default change
- unexpected runtime shadow activation
- supported import-order failure
- duplicate `Bitcast` in normal startup path
- model load failure
- malformed upload crash
- memory instability
- unacceptable latency

## 12. Import-order invariant guardrail

Production runtime must preserve the app-first / Essentia-first import path.

TensorFlow-first mixed import paths are unsupported for this candidate.

No production startup, configuration, health, metrics, monitoring, warmup, or provider code should introduce a direct TensorFlow import before the Essentia/classify path initializes.

Required supported scenarios for later qualification:

- `essentia_first`
- `essentia_standard_first`
- `classify_import`
- `app_main_import`
- `classify_then_tensorflow`
- `app_then_tensorflow`
- `model_load_essentia_first`
- `same_process_repeated_imports`

Known unsupported scenarios unless future dependency evidence resolves them:

- `tensorflow_then_essentia`
- `tensorflow_then_essentia_standard`
- `tensorflow_then_musicnn_symbol`
- `model_load_tensorflow_first`

Any duplicate `Bitcast` failure in the normal startup/classify path is a switch blocker and rollback trigger.

## 13. Risk register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| TensorFlow-first import introduced by future startup, metrics, health, or provider code | Process abort before serving traffic | Enforce import-order smoke gate and code review boundary |
| Native duplicate `Bitcast` failure appears in normal app path | Startup or classify failure | Block switch or rollback immediately |
| Runtime dependency drift | Reproducibility loss | Use digest-pinned base and pinned production dependency input |
| Response shape drift | Client compatibility regression | Compare `/classify` fixture output against baseline |
| Provider default drift | Behavior regression | Assert default remains `legacy_musicnn` |
| Model load regression | Classify unavailable | Run Essentia-first model load gate before switch |
| Latency regression | User-visible slowdown | Capture baseline and candidate timing; require approval for acceptable bounds |
| Memory instability | Operational instability | Capture memory sanity and rollback on instability |
| Malformed upload crash | Availability regression | Validate malformed upload behavior remains HTTP `400` without process crash |
| Rollback not rehearsed | Longer incident recovery | Require rollback readiness evidence before switch |

## 14. Implementation boundaries for Roadmap 3.11

Roadmap 3.11 may implement a controlled runtime switch only after explicit approval.

Allowed after approval:

- production `Dockerfile` update
- production `requirements.txt` update
- production `docker-compose.yml` update if needed
- docs updates
- evidence capture under `docs/runtime/evidence/`

Still out of scope unless separately approved:

- app code changes
- provider default changes
- `/classify` contract changes
- response shape changes
- LLM cutover
- canary rollout
- `tidal-parser` changes
- monorepo-root compose changes
- git commit, tag, or push

If Roadmap 3.11 requires app code changes to make the runtime switch pass, the switch implementation should stop and become a blocker investigation stage rather than silently expanding scope.

## 15. Blockers for switch

The switch remains blocked until Roadmap 3.11 or later captures passing implementation evidence for:

- clean production-candidate build
- exact runtime identity
- `pip check`
- supported import-order matrix
- Essentia-first model load
- `/health`
- valid `/classify` fixture
- response shape parity
- provider default parity
- repeated request stability
- malformed upload behavior
- log review
- memory and latency sanity
- rollback readiness

Any unsupported TensorFlow-first mixed import path becoming part of normal startup, health, metrics, monitoring, or classify behavior blocks the switch.

## 16. Decision

Decision: `ready_for_controlled_runtime_switch_implementation_with_explicit_approval_gate`

Roadmap 3.10 approves moving to a controlled runtime switch implementation stage for `genre-classifier`, with explicit approval required before any production runtime file changes are made.

Roadmap 3.10 does not switch production runtime and does not modify production Dockerfile, production compose, production requirements, app code, provider default, `/classify` contract, or response shape.

## 17. Recommendation for Roadmap 3.11

Proceed to Roadmap 3.11 only as a controlled implementation stage with an explicit approval gate.

Roadmap 3.11 should prepare the production runtime switch candidate, run the full validation checklist, capture baseline and candidate evidence, and keep rollback to the current production runtime ready until the switched runtime is explicitly accepted.
