# Roadmap 4.50 Scoped Baseline Helper And Baseline-Only Capture

Roadmap 4.50 completed a scoped legacy MusiCNN baseline-only capture for the
three local legal CC0 fixtures prepared outside the repository. This step
captures the current legacy baseline behavior only; it is not an ONNX execution,
not a TensorFlow-vs-ONNX comparison, not a full numeric parity run, and not a
production migration decision.

## Why Baseline-Only

The purpose of this gate is to preserve sanitized evidence from the existing
legacy MusiCNN runtime before any candidate runtime work proceeds. The captured
values are baseline observations for later review. They do not approve an ONNX
provider, production inference path, default-provider switch, release, tag, or
numeric parity claim.

## Import Policy

Roadmap 4.49 confirmed the safe runtime policy for this container: import
Essentia first, avoid an explicit TensorFlow import before Essentia, access
`TensorflowPredictMusiCNN` through `essentia.standard`, and use a fresh Python
process. Roadmap 4.50 used that policy for both the runtime visibility check and
the helper execution.

The helper is `scripts/lightweight/musicnn_legacy_baseline_capture.py`. It is
CLI-only and local-only. It does not import the production app, provider
factory, ONNX, or TensorFlow explicitly before Essentia. It normalizes each
fixture through ffmpeg, loads mono 16 kHz audio with Essentia, runs the legacy
MusiCNN graph, and writes sanitized JSON output.

## One-Off Bind Mount

Execution used the approved `one_off_compose_run_bind_mount` strategy from the
`genre-classifier` Compose directory. The external fixture directory was mounted
read-only into a one-off `docker compose run --rm --no-deps` container. The
helper itself was also mounted read-only because the existing image does not
bind-mount the whole repository. A temporary output directory outside the repo
received the raw local capture output.

No Compose file was changed. No Dockerfile was changed. No rebuild was run. The
already running service was not mutated, and `docker cp` was not used as the
primary fixture path.

## Out Of Scope

ONNX comparison is out of scope because this is only the legacy baseline capture
gate. Full numeric parity is out of scope because no candidate output was
executed or compared. `/classify` is not called because the task is scoped to a
CLI helper and must not touch the public API contract or response shape.

Production dependencies, Docker, Compose, provider factory wiring, and default
provider selection remain untouched. `legacy_musicnn` remains the baseline.

## Result

The one-off container saw all three expected MP3 fixtures. The Essentia-first
runtime check passed, and `TensorflowPredictMusiCNN` was available through
`essentia.standard`. Baseline-only capture succeeded for all three fixtures.

Sanitized fixture evidence:

| Fixture | SHA256 |
| --- | --- |
| `john_bartmann_earning_happiness_cc0` | `d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628` |
| `john_bartmann_happy_clappy_cc0` | `4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e` |
| `john_bartmann_home_at_last_cc0` | `0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75` |

Committed artifact:

- `docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json`

## Next Step

Use the sanitized baseline report as input to a separately approved future
comparison step. Keep ONNX execution, full numeric parity, provider
implementation, default-provider switching, and `/classify` calls gated until
they are explicitly approved.
