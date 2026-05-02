# Roadmap 3.9 Decision Inputs

## Candidate under investigation

- Service: `genre-classifier`
- Runtime candidate: Python 3.12 + `essentia-tensorflow`
- Candidate artifact: `docker/runtime-candidates/py312-essentia-tensorflow/`
- Production migration: out of scope

## Required evidence

- One fresh-process result per import-order scenario.
- Runtime identity for each scenario where practical: Python executable/version and key package versions.
- Model-load evidence for both Essentia-first and TensorFlow-first paths.
- Clear statement of whether TensorFlow-first import order is accepted as an explicit runtime invariant or remains a blocker.

## Decision questions

1. Does the production app-first path remain stable in the Python 3.12 + `essentia-tensorflow` candidate?
2. Does TensorFlow-first import order still fail with duplicate `Bitcast` op registration?
3. If TensorFlow-first still fails, is app-first / Essentia-first import order acceptable as an explicit invariant for this candidate?
4. What guardrails would be required before any later production switch planning?

## Initial decision posture

Pending evidence. Until Roadmap 3.9 accepts the import-order behavior as an explicit invariant or resolves it, the candidate must not be used for production switch planning.
