# Roadmap 3.9 - TensorFlow Import-Order Blocker Investigation

## Goal

Investigate the remaining non-production Python 3.12 + `essentia-tensorflow` runtime candidate blocker where TensorFlow-first import order fails with duplicate `Bitcast` op registration.

## Scope

- `genre-classifier` only.
- Non-production runtime candidate only.
- Import-order validation script under `scripts/runtime_validation/`.
- Evidence under `docs/runtime/evidence/roadmap-3.9/`.
- Documentation update for the candidate README.

## Non-goals

- No `tidal-parser` changes.
- No production `Dockerfile` changes.
- No production `docker-compose.yml` changes.
- No production `requirements.txt` changes.
- No app code changes.
- No provider default changes.
- No `/classify` contract changes.
- No response shape changes.
- No canary rollout.
- No LLM cutover.
- No production Python/runtime upgrade.
- No commit, tag, or push.

## Roadmap 3.8 findings summary

Roadmap 3.8 found that the Python 3.12 + `essentia-tensorflow` candidate remained viable on the production app-first path: app import, model load, `/health`, `/classify`, repeated classify smoke, and malformed upload behavior all passed against the local non-production candidate.

Roadmap 3.8 also confirmed that TensorFlow-first import order still failed with duplicate `Bitcast` op registration.

## Import-order blocker statement

The remaining blocker is a process-local import-order incompatibility:

```text
RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

The app-first / Essentia-first path is the current service path. TensorFlow-first import order is not currently treated as production-safe for this candidate.

## Import-order test matrix

The Roadmap 3.9 smoke script runs exactly one scenario per process:

```sh
python scripts/runtime_validation/import_order_smoke.py <scenario>
```

Scenarios:

- `essentia_first`
- `essentia_standard_first`
- `tensorflow_first`
- `tensorflow_then_essentia`
- `tensorflow_then_essentia_standard`
- `tensorflow_then_musicnn_symbol`
- `essentia_then_tensorflow`
- `essentia_standard_then_tensorflow`
- `classify_import`
- `app_main_import`
- `classify_then_tensorflow`
- `app_then_tensorflow`
- `model_load_essentia_first`
- `model_load_tensorflow_first`
- `same_process_repeated_imports`

Detailed matrix tracking lives in `docs/runtime/evidence/roadmap-3.9/import-order-matrix.md`.

## Evidence collected

Candidate image built from `/opt/music-tools/genre-classifier` without changing candidate dependencies or production runtime files:

```sh
docker build \
  -f docker/runtime-candidates/py312-essentia-tensorflow/Dockerfile \
  -t music-tools-genre-classifier-roadmap-3.9:py312-etf \
  .
```

Observed local image id:

```text
sha256:a8eaa7fa4b48e56f65f901288f21c20bae00958192cccc848d4b932a49f707a8
```

### Validation method

The candidate image was built as `music-tools-genre-classifier-roadmap-3.9:py312-etf`; the observed image id was `sha256:a8eaa7fa4b48e56f65f901288f21c20bae00958192cccc848d4b932a49f707a8`.

Scenario execution used fresh `docker run` processes. The service checkout was bind-mounted to `/app` so the newly added validation script and evidence path were available without changing the candidate Dockerfile. Runtime behavior under test still came from the candidate image and its pinned runtime dependencies.

This validation method does not change the production runtime, the candidate Dockerfile, or candidate dependency pins.

Validation artifacts:

- `scripts/runtime_validation/import_order_smoke.py`
- `docs/runtime/evidence/roadmap-3.9/import-order-matrix.md`
- `docs/runtime/evidence/roadmap-3.9/decision-inputs.md`

Scenario execution evidence:

| Scenario group | Result |
| --- | --- |
| Essentia-first imports | Pass: `essentia_first`, `essentia_standard_first`, `essentia_then_tensorflow`, `essentia_standard_then_tensorflow` all returned `exit_code=0`. |
| App-first imports | Pass: `classify_import`, `app_main_import`, `classify_then_tensorflow`, and `app_then_tensorflow` all returned `exit_code=0`. |
| Model load, Essentia-first | Pass: `model_load_essentia_first` returned `exit_code=0`. |
| TensorFlow-only import | Pass: `tensorflow_first` returned `exit_code=0`. |
| TensorFlow-first before Essentia integration | Fail: `tensorflow_then_essentia`, `tensorflow_then_essentia_standard`, `tensorflow_then_musicnn_symbol`, and `model_load_tensorflow_first` returned `exit_code=1` with duplicate `Bitcast` op registration. |
| Repeated supported imports in one process | Pass: `same_process_repeated_imports` returned `exit_code=0`. |

Evidence files:

- `docs/runtime/evidence/roadmap-3.9/import-order-essentia_first.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-essentia_standard_first.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-tensorflow_first.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-tensorflow_then_essentia.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-tensorflow_then_essentia_standard.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-tensorflow_then_musicnn_symbol.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-essentia_then_tensorflow.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-essentia_standard_then_tensorflow.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-classify_import.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-app_main_import.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-classify_then_tensorflow.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-app_then_tensorflow.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-model_load_essentia_first.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-model_load_tensorflow_first.txt`
- `docs/runtime/evidence/roadmap-3.9/import-order-same_process_repeated_imports.txt`

## Failure analysis

Roadmap 3.9 evidence confirms that importing TensorFlow by itself succeeds, and the supported Essentia-first / app-first path succeeds. The failure appears only when TensorFlow is imported before Essentia's TensorFlow-backed integration initializes.

The failure is deterministic across the TensorFlow-first mixed scenarios:

```text
RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

The `tensorflow_then_musicnn_symbol` evidence shows the crash happens while importing `essentia.standard`, before the script can resolve the `TensorflowPredictMusiCNN` symbol. The `model_load_tensorflow_first` evidence confirms that TensorFlow-first model loading is blocked for the same reason.

The app import scenarios pass because the current app path imports `app.services.classify`, which imports `essentia.standard` before any explicit TensorFlow import. `classify_then_tensorflow` and `app_then_tensorflow` also pass, confirming that TensorFlow can be imported after the app-first / Essentia-first path has initialized.

## Mitigation options evaluated

- Accept app-first / Essentia-first as an explicit runtime invariant for this candidate: supported by evidence because the app import path, app-then-TensorFlow path, Essentia-first path, and Essentia-first model load all pass.
- Add validation guardrails: supported. The Roadmap 3.9 smoke script can be reused in later candidate qualification to prove both the supported invariant and the known failing TensorFlow-first behavior.
- Investigate alternate dependency pins: not selected for this stage. Evidence isolates the failure to TensorFlow-first mixed import order, while supported app-first behavior remains stable.
- Require app code import-boundary changes: not selected for this stage because current app imports already follow the supported ordering and no production app code change is allowed in Roadmap 3.9.
- Reject the candidate: not selected because the production-relevant app-first path and Essentia-first model load pass.

## Selected mitigation / decision

Decision: `ready_for_controlled_switch_planning_with_import_order_invariant`

The candidate may move into later controlled switch planning only with an explicit runtime invariant:

```text
The genre-classifier process must initialize through the app-first / Essentia-first path. TensorFlow-first import order is unsupported for this candidate.
```

This decision does not perform a production migration and does not change production runtime files. It only states that the import-order blocker is deterministic, isolated from the current app-first path, and acceptable for future planning if guardrails preserve the invariant.

## Remaining risks

- TensorFlow-first imports may be introduced later by tests, scripts, monitoring, startup hooks, or future provider code.
- The failing path aborts the interpreter through TensorFlow/Essentia native code rather than raising a catchable Python exception.
- Documentation alone is not a sufficient guardrail; future candidate qualification should run the Roadmap 3.9 import-order smoke matrix.
- The evidence is import/model-load focused and does not replace long-running API stability, concurrency, memory, or rollout evidence.
- The candidate image used a bind-mounted checkout to run the validation script because the candidate image copies only `app/`; this does not change runtime package evidence but should be documented for reproducibility.

## Recommendation for Roadmap 3.10

Proceed with controlled switch planning only if Roadmap 3.10 includes import-order guardrails:

- Run `scripts/runtime_validation/import_order_smoke.py` in the candidate runtime before any switch planning decision.
- Require `classify_import`, `app_main_import`, `classify_then_tensorflow`, `app_then_tensorflow`, `model_load_essentia_first`, and `same_process_repeated_imports` to pass.
- Treat TensorFlow-first mixed imports as unsupported unless a future dependency iteration resolves duplicate `Bitcast` registration.
- Keep production Dockerfile, compose, requirements, provider default, `/classify` contract, and response shape unchanged until a separate production migration roadmap explicitly approves changes.

## Rollback considerations

No production rollback is required for Roadmap 3.9 because no production runtime files, app code, provider defaults, API contracts, or deployment configuration are changed.
