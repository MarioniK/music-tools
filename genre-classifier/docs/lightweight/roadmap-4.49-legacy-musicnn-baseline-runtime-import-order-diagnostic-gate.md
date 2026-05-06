# Roadmap 4.49 Legacy MusiCNN Baseline Runtime Import-Order Diagnostic Gate

Roadmap 4.49 is an import-order confirmation gate for the legacy MusiCNN
runtime. It exists to confirm that the previously known TensorFlow/Essentia
import policy still lets a future local baseline helper safely reach the legacy
`TensorflowPredictMusiCNN` import path in an isolated one-off container. It is
not a baseline capture, not an ONNX execution path, not a TensorFlow-vs-ONNX
comparison, and not a production migration decision.

## Prior Import-Order Knowledge

Import-order sensitivity was already known from the Python/runtime modernization
work. `docs/runtime/roadmap-3.6-reproducible-modern-tensorflow-runtime-candidate.md`
records that Essentia-first and natural app import paths passed, while
TensorFlow-first import paths failed with the Bitcast duplicate registration
error.

Roadmap 4.49 should therefore be read as a confirmation gate in the one-off
baseline diagnostic context, not as discovery from scratch. The
`tensorflow_then_essentia` case is an expected-bad regression-trap case. The safe
policy remains:

- do not import TensorFlow explicitly before Essentia;
- prefer Essentia-first and production-like `legacy_musicnn` import paths;
- access `TensorflowPredictMusiCNN` through `essentia.standard`;
- use a fresh Python process for future helper or baseline work.

## Previous Blocker

Roadmap 4.48 confirmed that the one-off bind-mounted strategy can make local
fixtures visible to the container, but legacy baseline capture was blocked before
inference. The blocker was duplicate TensorFlow op registration:

- `ALREADY_EXISTS: Op with name Bitcast`

## Diagnostic Method

The compose service was discovered from the service directory with
`docker compose config --services`; the actual service name was
`genre-classifier`. The running service was not mutated. Each diagnostic case ran
in a fresh Python process through a one-off `docker compose run --rm --no-deps`
container.

The diagnostic matrix:

| Case | Import order | Result | Category |
| --- | --- | --- | --- |
| `tensorflow_then_essentia` | `tensorflow`, `essentia`, `essentia.standard` | failed | `bitcast_duplicate_registration` |
| `essentia_then_tensorflow` | `essentia`, `essentia.standard`, `tensorflow` | passed | `none` |
| `essentia_standard_only` | `essentia.standard` | passed | `none` |
| `tensorflow_predict_musicnn_import_without_explicit_tensorflow` | `from essentia.standard import TensorflowPredictMusiCNN` | passed | `none` |
| `legacy_path_like_import_order` | `essentia.standard`, `es.TensorflowPredictMusiCNN` | passed | `none` |

## Decision

Decision status: `safe_import_order_found`.

The safe order is to avoid importing TensorFlow explicitly before Essentia. The
future helper should import `essentia.standard` first, then access
`TensorflowPredictMusiCNN` through that module or import the symbol without a
preceding explicit TensorFlow import.

Selected helper policy for a future Roadmap 4.50:

- use a fresh Python process for baseline helper execution;
- keep the helper CLI-only and local-only;
- do not import TensorFlow explicitly before Essentia;
- import `essentia.standard` first;
- keep ONNX imports, ONNX execution, `/classify` calls, provider wiring, and
  production routes out of the helper;
- commit only sanitized JSON notes, not raw runtime log dumps.

## Remaining Blockers

No import-order blocker remains for the tested legacy-relevant import paths.
This diagnostic still does not permit baseline output capture. A separately
scoped step must decide and run that capture.

## Explicit Non-Goals

- no baseline capture;
- no ONNX execution;
- no TensorFlow-vs-ONNX comparison;
- no `/classify` calls;
- no production dependency changes;
- no Dockerfile or Compose changes;
- no provider factory or default-provider changes;
- no response-shape changes;
- no `tidal-parser` changes.

## Artifact

The committed diagnostic report is:

- `docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-import-order-diagnostic-report.json`
