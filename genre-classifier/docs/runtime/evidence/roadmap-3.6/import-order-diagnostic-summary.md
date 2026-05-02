# Roadmap 3.6 import-order diagnostic summary

Validation date: 2026-05-02

Candidate image:

```text
music-tools-genre-classifier-roadmap-3.6:py312-etf
sha256:174f0310d73fdf896beb753d58981e5465238a0060b89a56fa062556cc620d45
```

## Passing import orders

TensorFlow-only import passed.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-tensorflow-only.txt
```

Observed:

```text
tensorflow import ok
tensorflow 2.21.0
```

Essentia-only import passed.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-essentia-only.txt
```

Observed:

```text
essentia import ok
essentia 2.1-beta6-dev
essentia.standard import ok
MonoLoader True
TensorflowPredictMusiCNN True
```

Essentia first, then TensorFlow passed.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-essentia-then-tensorflow.txt
```

Observed:

```text
essentia first ok
TensorflowPredictMusiCNN True
tensorflow after essentia ok
tensorflow 2.21.0
```

Natural app import path passed.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-app-natural-path.txt
```

Observed:

```text
app.main natural import ok
app.services.classify natural import ok
```

Essentia before app import passed.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-essentia-before-app.txt
```

Observed:

```text
essentia explicit import ok
TensorflowPredictMusiCNN True
app.main after essentia import ok
app.services.classify after essentia import ok
```

## Failing import orders

TensorFlow first, then Essentia failed.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-tensorflow-then-essentia.txt
```

Observed before failure:

```text
tensorflow first ok
tensorflow 2.21.0
```

Error summary:

```text
F0000 ... RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

TensorFlow before app import failed with the same error.

Evidence:

```text
docs/runtime/evidence/roadmap-3.6/import-order-tensorflow-before-app.txt
```

Observed before failure:

```text
tensorflow explicit import ok
tensorflow 2.21.0
```

Error summary:

```text
F0000 ... RegisterAlreadyLocked(op_data_factory) is OK (ALREADY_EXISTS: Op with name Bitcast)
```

## API and production-compatible path impact

The natural app import path passed. Previous Roadmap 3.6 evidence also showed:

- candidate API startup passed
- candidate `/health` passed
- candidate `/classify` passed
- baseline-vs-candidate response shape parity passed
- repeated request smoke passed
- malformed upload parity passed

The issue appears tied to an explicit `import tensorflow` before loading Essentia/App code. The current service runtime path does not require an explicit TensorFlow import before app startup.

This does not affect the current production runtime because Roadmap 3.6 does not change production Dockerfile, production compose, production requirements, provider default, `/classify` contract, response shape, or `tidal-parser`.

## Roadmap 3.7 impact

This should block promoting Roadmap 3.6 to a clean `pass_for_controlled_runtime_switch_planning`.

Decision remains:

```text
needs_additional_runtime_candidate_iteration
```

Recommended next action:

- keep the candidate out of production
- document the supported import order if this candidate line continues
- investigate whether `tensorflow==2.21.0` and `essentia-tensorflow==2.1b6.dev1389` can safely support TensorFlow-first imports
- rerun import-order diagnostics after any dependency/runtime candidate iteration
- keep production files and app code unchanged until a separate approved migration task exists
