# Roadmap 4.51 - ONNX-side output capture preparation / execution approval gate

## Status

Prepared for review / local-only evidence gate / non-production-facing.

Roadmap 4.51 confirms the ONNX-side capture prerequisites against the committed
legacy MusiCNN baseline evidence from Roadmap 4.50 and the approved external
fixture set prepared outside the repository. It does not approve production
migration, provider implementation, default-provider switching, `/classify`
contract changes, or final parity decision making.

## Scope

This slice is limited to a local-only ONNX-side output capture preparation
check for the official MusiCNN ONNX artifact.

The gate is intentionally narrow:

- verify the committed legacy baseline evidence;
- verify the external legal CC0 fixture set;
- verify the official/local ONNX artifact identity and metadata;
- verify the isolated local ONNX Runtime environment;
- record whether ONNX-side capture can proceed safely.

This slice does not:

- run TensorFlow baseline inference again;
- call `/classify`;
- change provider wiring;
- change the default provider;
- change production dependencies;
- change Dockerfiles or Compose files;
- rebuild Docker images;
- commit audio files, model files, or virtual environments;
- make a final parity decision.

## Baseline evidence

Committed baseline evidence:

- `docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json`

Recorded baseline evidence:

- baseline availability: `true`;
- fixture count: `3`;
- fixture ids:
  - `john_bartmann_earning_happiness_cc0`
  - `john_bartmann_happy_clappy_cc0`
  - `john_bartmann_home_at_last_cc0`
- expected output shapes:
  - `[30, 50]`
  - `[35, 50]`
  - `[86, 50]`

## External fixture evidence

The external fixture set remains outside the repository and is not committed.
The sanitized fixture evidence records:

| Fixture id | SHA256 | Audio format | Source artist | License |
| --- | --- | --- | --- | --- |
| `john_bartmann_earning_happiness_cc0` | `d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628` | mp3 | John Bartmann | CC0 1.0 Universal / public domain |
| `john_bartmann_happy_clappy_cc0` | `4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e` | mp3 | John Bartmann | CC0 1.0 Universal / public domain |
| `john_bartmann_home_at_last_cc0` | `0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75` | mp3 | John Bartmann | CC0 1.0 Universal / public domain |

The fixture provenance notes are present and align with the approved local-only
evaluation workspace. No audio file was committed to the repository.

## ONNX artifact evidence

Official/local artifacts are present outside the repository:

- ONNX model artifact available: `true`;
- ONNX metadata artifact available: `true`;
- model SHA256: `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`;
- metadata SHA256: `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe`;
- artifact-in-repo: `false`.

The ONNX metadata probe reports:

- input names: `melspectrogram`;
- input shape tail: `[187, 96]`;
- output names: `activations`, `embeddings`;
- output shape tails: `[50]`, `[200]`.

## Isolated environment

The isolated local ONNX Runtime environment is available and used for metadata
inspection.

- isolated env used: `true`;
- onnxruntime available: `true`;
- onnxruntime version: `1.25.1`.

## Capture result

ONNX-side capture is not executed yet.

The blocked execution result is intentional and evidence-based:

- `onnx_capture_succeeded: false`;
- `onnx_outputs: []`;
- blocker: `PREPROCESSING_ALIGNMENT_UNKNOWN`.

The blocker exists because the ONNX input preprocessing path has not yet been
evidenced to the standard required for execution approval. No fake outputs were
generated.

## Decision

Capture preparation is complete enough to record a blocked execution gate, but
not enough to approve ONNX-side output capture execution.

## Next step

Provide explicit ONNX preprocessing alignment evidence before any execution
approval or numeric comparison work is attempted.
