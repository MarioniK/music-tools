# Roadmap 4.46 Scoped Existing-Container Legacy MusiCNN Baseline Output Capture

Roadmap 4.46 is a baseline-only evidence step for the existing legacy MusiCNN runtime. Its scope is `existing_container_local_only`: discover the running `genre-classifier` Compose service, verify import-only runtime readiness, verify fixture visibility in that existing container, and record sanitized baseline evidence or exact blockers.

This is not an ONNX comparison, not a full numeric parity run, and not a production migration. It does not approve provider implementation, a default provider switch, ONNX execution, or production use. It does not change the `/classify` contract or response shape, and `/classify` is not called.

The local legal fixtures remain outside the repository. Audio files, model files, virtual environments, dependency files, Dockerfile, and Compose files are not committed or changed. No Docker rebuild is performed. `tidal-parser` is outside the scope of this roadmap and remains untouched.

The Roadmap 4.46 result is captured in:

- `docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json`

For this run, the existing container was available and import-only TensorFlow and Essentia checks passed, but the external fixture path was not visible inside the container. Baseline output capture was therefore blocked without modifying Compose, copying fixtures into the repo, invoking ONNX, or calling `/classify`.

The next step is a fixture visibility or non-production mount strategy approval gate for the existing local container, not ONNX comparison or numeric parity.

`legacy_musicnn` remains the baseline.
