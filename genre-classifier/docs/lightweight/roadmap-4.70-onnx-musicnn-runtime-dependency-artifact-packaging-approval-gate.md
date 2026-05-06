# Roadmap 4.70 - ONNX/MusiCNN runtime dependency / artifact packaging approval gate

## Status

- Status: approval/design gate
- Production readiness: not claimed
- Implementation: not performed

## Context and evidence inputs

This gate is based on the following prior roadmap evidence and design records:

- Roadmap 4.64 preprocessing evidence:
  - raw observed shape: `[2948, 96]`
  - final shaped patch: `[187, 96]`
  - repeated-run stability: `stable`
  - max_abs_diff: `0.0`
  - mean_abs_diff: `0.0`
- Roadmap 4.65 ONNX output evidence:
  - `[187, 96]` patch accepted by official/local ONNX/MusiCNN
  - activations: `[50]`
  - embeddings: `[200]`
  - repeated-run stability: `stable`
- Roadmap 4.66 semantic mapping evidence:
  - classes count: `50`
  - activations count: `50`
  - count match: `true`
  - index order usable: `true`
  - diagnostic `genres` / `genres_pretty` shape compatible
- Roadmap 4.67 provider design contract
- Roadmap 4.68 disabled-by-default provider scaffold
- Roadmap 4.69 config hardening:
  - explicit opt-in artifact paths
  - defaults `None`
  - no `/tmp` defaults
  - no implicit local fallback
  - no auto-discovery
  - graceful failure diagnostics

## Why this gate is needed

Roadmap 4.69 completed provider scaffold hardening, so the next risk is no longer the provider abstraction itself but runtime and artifact delivery.

This gate is required because:

- runtime dependency strategy and artifact packaging strategy must be separated from provider activation
- mounted artifacts versus bundled artifacts need explicit approval before implementation
- runtime downloads by default must remain prohibited
- `legacy_musicnn` must remain the default provider
- `/classify` must not be called in this gate
- production dependencies, Dockerfile, and Compose must remain unchanged in this gate

## Runtime dependency options

The runtime strategy should be treated as a later implementation decision, not as part of this approval gate.

Compared options:

- production image packaging later
  - possible future path, but not approved here
  - may materially affect image size and dependency footprint
- optional extra / separate requirements file later
  - possible future packaging shape
  - exact `onnxruntime` version must be selected in a later implementation gate
- external mounted/local-only runtime
  - evaluation-only, not a production solution
  - useful for probes, not for production delivery
- disposable/probe environment
  - remains evaluation-only
  - useful for validation, not for production deployment

Required constraints:

- `onnxruntime` CPU-only should be preferred unless a separate GPU/runtime decision is approved
- `Essentia` / `essentia-tensorflow` preprocessing runtime requires separate ABI/platform/version review
- using the isolated venv from previous roadmaps is evaluation-only, not production packaging
- lazy imports must remain
- app startup must not require ONNX/MusiCNN runtime dependencies unless the provider is explicitly selected

## Artifact packaging options

Artifact delivery must remain explicit and opt-in until a later gate approves a concrete packaging strategy.

Compared options:

- explicit mounted artifacts
  - preferred first delivery direction
  - keeps runtime boundaries clearer
  - supports controlled, reversible rollout
- image-bundled artifacts only after separate approval
  - possible later path
  - requires explicit size, provenance, and rollback review
- external artifact preparation step
  - required as part of a later delivery workflow
  - should include checksums, provenance, and license notes
- runtime download by default
  - prohibited

Required constraints:

- ONNX model artifact must not be committed to repo
- metadata/classes artifact must not be committed unless separately approved as small and license-safe metadata
- no audio files in repo
- no wheel/venv files in repo
- no `/tmp` defaults
- no implicit local path fallback
- no auto-discovery
- artifact paths must remain explicit opt-in settings or env vars
- checksums, provenance, and license notes are required before any runtime smoke

## Recommended direction

Preferred direction for the next implementation steps:

- keep `legacy_musicnn` as the default provider
- keep `onnx_musicnn` disabled by default
- no default switch
- no provider factory default change
- no `/classify` contract change
- no response shape change
- no production dependency change in this gate
- no Dockerfile or Compose change in this gate
- preferred first artifact delivery: explicit mounted artifacts
- preferred runtime delivery: future separate dependency packaging gate
- external artifact preparation step with checksums, provenance, and license notes
- runtime downloads by default prohibited
- image-bundled artifacts allowed only after separate approval

## Security and reproducibility requirements

Before any future implementation gate, the following must be explicitly approved and documented:

- exact dependency versions
- Python ABI compatibility
- platform compatibility
- image-size impact measurement
- ONNX model checksum
- metadata/classes checksum
- provenance source
- license notes
- no secrets in logs
- no private local paths in logs unless sanitized
- no network/runtime downloads by default
- no mutable remote artifacts in the production path

## Observability and failure behavior

Future diagnostics should distinguish between unsupported, failed, and degraded states for:

- missing `onnxruntime` dependency
- missing Essentia preprocessing runtime
- missing model path
- missing metadata/classes path
- missing model artifact
- missing metadata/classes artifact
- invalid metadata/classes JSON
- empty classes list
- classes/activations count mismatch
- checksum mismatch, if checksum verification is added later

Structured logs should include:

- provider key
- safe failure reason
- preserved `request_id` or correlation ID where already used

Do not log:

- secrets
- private paths that were not sanitized

## Image-size and rollback considerations

Image-size impact is unknown until future packaging is measured.

Potential impact:

- `onnxruntime` may increase image size
- Essentia runtime may increase image size materially

Rollback for this docs/report-only gate does not require Docker or dependency rollback.

Future rollback path:

- unset the provider selector
- fall back to `legacy_musicnn`
- remove artifact env vars
- remove mounted artifacts
- rollback the image only if future dependency or image changes are made

## Explicit non-goals

- no default provider switch
- no provider factory default change
- no `/classify` call
- no `/classify` contract change
- no response shape change
- no production inference
- no real ONNX inference
- no TensorFlow baseline
- no TensorFlow vs ONNX comparison
- no production dependency changes
- no Dockerfile changes
- no Compose changes
- no production migration
- no production readiness claim
- no ONNX/model files committed
- no audio files committed
- no wheel/venv files committed
- no `tidal-parser` changes
- no tag/release

## Future implementation gates

The approved future work should be split into separate gates:

- dependency packaging gate
- artifact packaging gate
- checksum/provenance/license gate
- disabled-by-default runtime smoke gate
- opt-in provider smoke gate
- output drift documentation gate
- production migration gate
- default switch gate
