# Roadmap 4.15 - ONNX Offline Evidence Review Decision Gate

Status: documentation-only offline review gate.

## Scope

Roadmap 4.15 reviews the Roadmap 4.14 ONNX offline evaluation evidence package
shape and records the next-step decision gate before any further ONNX candidate
experiment.

This is not a production decision. It does not approve provider implementation,
provider factory wiring, a default provider switch, runtime shadow execution,
canary rollout, or production migration.

The current production provider remains `legacy_musicnn`. The production
classifier path remains the legacy MusiCNN path. The `/classify` contract is
unchanged, and the production response shape remains:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## Reviewed evidence package

Reviewed Roadmap 4.14 documentation:

- `docs/lightweight/roadmap-4.14-onnx-offline-evaluation-evidence-package.md`

Reviewed Roadmap 4.14 evidence package artifact:

- `docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json`

The reviewed package is explicitly sample evidence. It is example-only and is
not a production decision. It must not be used as proof that a real ONNX model,
label mapping, license, runtime behavior, quality result, or production
migration path has been approved.

## Current evidence status

Current status is `blocked`.

The repository contains an example ONNX evidence package with placeholder
provenance, illustrative label mapping, example static outputs, and sample
report references. It does not contain approved real model provenance for a
specific local ONNX model, an approved label mapping for that model, captured
real ONNX inference output, reviewed model license evidence, accepted runtime
metrics, or production migration approval.

`docs/lightweight/evaluation/evidence/example-onnx-evidence-package.json`
already records:

- `decision_status`: `blocked`
- `not_production_decision`: `true`
- `baseline_provider`: `legacy_musicnn`
- `candidate_family`: `onnx_runtime`
- model provenance approval: `not_approved`
- label mapping approval: `not_approved`
- production provider: `not_requested`
- default provider switch: `not_requested`
- shadow or canary: `not_requested`

## Closed gates

The following gates are closed for Roadmap 4.15:

- Evidence package format exists for offline review.
- The package records allowed decision statuses.
- The package carries `not_production_decision: true`.
- The package keeps `legacy_musicnn` as the baseline provider.
- The package records approval gates and no-go checklist items.
- The package warns that no inference was run and `/classify` was not called.
- The package does not request provider factory wiring, default provider switch,
  shadow execution, canary rollout, or production migration.

These closed gates only confirm documentation and artifact-shape readiness. They
do not approve implementation or runtime work.

## Open gates

The following gates remain open before any ONNX candidate can move beyond
documentation and offline evidence work:

- Approved real local ONNX model provenance is missing.
- Approved label mapping for the specific model is missing.
- Reviewed model license evidence is missing.
- Real candidate output from an explicitly local ONNX model path is missing.
- Real baseline-vs-candidate comparison evidence is missing.
- Runtime metrics from a real local-only smoke run are missing.
- Major genre shift review is missing.
- OOV rate review is missing.
- Fixture coverage review is incomplete.
- Separate approval for any provider implementation is missing.
- Separate approval for any shadow, canary, or migration path is missing.

## No-go checklist status

Active no-go items for the current repository state:

- `provenance_not_approved`
- `label_mapping_not_approved`
- `model_hash_mismatch`
- `label_count_mismatch`
- `candidate_output_missing`
- `generated_report_missing`
- `major_genre_shift_unresolved`
- `oov_rate_unknown_or_too_high`
- `runtime_metrics_missing`
- `model_license_unclear`
- `production_dependency_required`
- `provider_switch_requested_prematurely`
- `shadow_canary_requested_prematurely`

The example package also lists `validator_failed` and `tests_failed` as sample
no-go categories. Roadmap 4.15 does not reinterpret those sample placeholders as
production evidence. Any active no-go item must prevent provider implementation,
provider wiring, shadow/canary execution, and production migration.

## Risks

- Example artifacts may be mistaken for real production-readiness evidence.
- A future ONNX candidate could be connected to provider wiring before model
  provenance and label mapping are approved.
- Adding ONNX Runtime or model dependencies too early would change the service
  runtime before offline gates are closed.
- Static outputs can preserve response shape while still hiding major quality,
  OOV, label-mapping, or license problems.
- Shadow/canary planning without real local evidence could create a migration
  path that is not supported by reviewed artifacts.

## Decision

Decision status for the current repository state: `blocked`.

Required decision fields:

- `not_production_decision: true`
- production provider switch: not approved
- shadow/canary: not approved
- production migration: not approved

Decision status meanings:

- `continue`: evidence is sufficient for a specifically named next step.
- `revise`: real artifacts exist, but they require correction or additional
  offline evidence before continuing.
- `reject`: reviewed evidence supports stopping this candidate path.
- `blocked`: required evidence or approvals are missing, so no implementation,
  runtime, shadow/canary, or migration step is allowed.

Levels of `continue` are distinct and must not be collapsed:

- `continue to another offline-only local experiment`
- `continue to provider implementation`
- `continue to shadow/canary`
- `continue to production migration`

For the current state, no `continue` level is approved. The only potentially
allowable future direction is offline-only work, and only after the required
evidence gates are closed and separately reviewed.

## Decision rationale

The repository has an example package that demonstrates the Roadmap 4.14 schema
and review vocabulary, but it does not include approved real artifacts. The
sample package is intentionally blocked because provenance, mapping, license,
runtime metrics, and production approvals are incomplete.

Because no approved real ONNX model provenance, model-specific label mapping,
real local inference output, reviewed license evidence, or accepted runtime
metrics are present, Roadmap 4.15 cannot approve any step that changes runtime
behavior or production architecture.

## Allowed next steps

Allowed next steps are limited to safe offline documentation and evidence work:

- Prepare an approved real local ONNX model provenance artifact.
- Prepare an approved label mapping for the specific model.
- Improve offline evaluation fixtures without adding copyrighted audio
  artifacts.
- Revise or update the evidence package with real artifacts.
- Review model license and source provenance.
- Improve static validators for documentation and evidence shape only.
- Only after separate approval, run local-only ONNX smoke inference with an
  explicit local model path.

## Prohibited next steps

Roadmap 4.15 explicitly prohibits:

- production provider implementation;
- provider factory wiring;
- default provider switch;
- shadow execution;
- canary rollout;
- production migration;
- Docker/runtime dependency changes;
- adding `onnxruntime` to production requirements;
- adding TFLite, sklearn, model, or other runtime model dependencies;
- adding model files;
- downloading model files;
- adding network or download logic;
- adding copyrighted audio fixtures;
- real inference as part of this decision gate;
- calling `/classify`;
- `/classify` contract changes;
- `/classify` response changes;
- changes to `ok`, `message`, `genres`, or `genres_pretty`;
- runtime changes;
- Dockerfile changes;
- Docker Compose changes;
- `tidal-parser` changes;
- LLM cutover;
- tag, release, commit, or push.

## Rollback considerations

Rollback for Roadmap 4.15 is documentation-only. Remove this file:

- `docs/lightweight/roadmap-4.15-onnx-offline-evidence-review-decision-gate.md`

No production classifier code, provider factory, default provider, runtime
dependencies, Docker configuration, model files, audio artifacts, `/classify`
contract, response shape, shadow execution, canary configuration, or
`tidal-parser` files are changed by this decision gate.
