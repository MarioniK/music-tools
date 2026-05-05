# Roadmap 4.29 - Real local-only MusiCNN ONNX artifact preparation approval gate

Status: proposed documentation-only approval gate / non-production-facing.

This document is a technical approval boundary for a possible future manual
local-only artifact preparation step. It is not production-facing and does not
record real artifact evidence.

## Scope

This stage may only approve a future manual local-only artifact preparation
step.

It does not prepare artifacts itself.

It does not approve inference.

It does not approve provider implementation.

It does not approve runtime/dependency changes.

It does not approve production migration.

## Why this gate is needed after Roadmap 4.28

Roadmap 4.28 protects the sample evidence report.

Real artifacts require a separate approval boundary before any local-only
preparation work begins.

This gate prevents sample/template metadata from being treated as real evidence.

This gate also prevents artifact preparation from sliding into inference,
provider implementation, dependency changes, runtime changes, or production
migration.

## Current production baseline

Roadmap 2 is closed by release `v0.3.0`.

Roadmap 3 is closed by release `v0.4.0`.

Roadmap 4.1-4.28 are completed and published.

The default provider remains `legacy_musicnn`.

The production classifier path remains legacy MusiCNN.

The current bundled artifacts are:

- `msd-musicnn-1.pb`
- `msd-musicnn-1.json`

The current preprocessing/inference path is:

- `ffmpeg`
- `MonoLoader`
- `TensorflowPredictMusiCNN`

The bundled `msd-musicnn-1.pb` and `msd-musicnn-1.json` remain the current
reference.

Baseline parity must be measured against current `legacy_musicnn` behavior
before any future runtime replacement.

The `/classify` contract is unchanged.

The response shape is unchanged:

- `ok`
- `message`
- `genres`
- `genres_pretty`

Runtime shadow remains disabled by default.

`tidal-parser` is untouched.

## Artifact discipline state after Roadmap 4.28

The metadata template exists.

The template validator exists.

The sample evidence report exists.

The sample evidence report validator exists.

The sample evidence report is sample-only and is not real evidence.

No real local artifacts have been prepared by Roadmap 4.29.

No model files are stored in repo by Roadmap 4.29.

No downloads are performed by Roadmap 4.29.

No inference is executed by Roadmap 4.29.

No `onnxruntime` dependency is added by Roadmap 4.29.

## Allowed future local-only artifacts after approval

Only the following future local-only artifacts may be prepared after explicit
approval:

- official/local `msd-musicnn-1.onnx`
- optional official/local `msd-musicnn-1.pb`
- official/local `msd-musicnn-1.json`
- current bundled `msd-musicnn-1.pb` hash reference
- current bundled `msd-musicnn-1.json` hash reference

"Current bundled hash reference" means measuring the existing bundled files for
comparison/evidence.

It does not mean copying model files into `docs/`, `tests/`, `app/`, or any
git-tracked path.

## Allowed local-only directory

The only approved future local-only working directory is:

```text
/tmp/music-tools-onnx-parity/
```

This directory is local-only, outside the repo, disposable, not committed, not
staged, and not used by production runtime.

## Forbidden locations

Downloaded model artifacts must not be placed in:

- repo root
- `docs/`
- `tests/`
- `app/`
- any git-tracked path
- any location under `/opt/music-tools/genre-classifier`

## Future manual preparation commands

The following commands are documentation only.

Do not execute these commands as part of Roadmap 4.29.

Create the future local-only working directory:

```bash
mkdir -p /tmp/music-tools-onnx-parity/
```

Measure SHA256 values:

```bash
sha256sum /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx
sha256sum /tmp/music-tools-onnx-parity/msd-musicnn-1.json
sha256sum /path/to/current/bundled/msd-musicnn-1.pb
sha256sum /path/to/current/bundled/msd-musicnn-1.json
```

macOS/BSD SHA256 fallback:

```bash
shasum -a 256 /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx
```

Measure file sizes:

```bash
stat -c '%n %s' /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx
stat -c '%n %s' /tmp/music-tools-onnx-parity/msd-musicnn-1.json
```

macOS/BSD file size fallback:

```bash
stat -f '%N %z' /tmp/music-tools-onnx-parity/msd-musicnn-1.onnx
```

Check git state:

```bash
git status --short
```

Check that the artifact path is outside the repo:

```bash
realpath /tmp/music-tools-onnx-parity/
pwd
```

Download commands are intentionally not provided in Roadmap 4.29 unless
explicitly approved in a future step.

## Future real evidence report fields

A future real evidence report must populate these fields:

- `artifact_role`
- `artifact_name`
- `source_url`
- `local_path`
- `file_size_bytes`
- `sha256`
- `provenance_notes`
- `license_notes`
- `downloaded_manually`
- `artifact_in_repo`
- `committed_to_repo`
- `approval_status`
- `review_status`
- `created_at`
- `checked_at`

The future report must satisfy these requirements:

- `artifact_in_repo: false`
- `committed_to_repo: false`
- `local_path` must point outside repo
- `file_size_bytes` must be measured, not guessed
- `sha256` must be measured, not placeholder
- provenance/license notes must be explicit

## Approval boundaries

These approvals are separate:

- approval to prepare local artifacts
- approval to run inference
- approval to add `onnxruntime`
- approval to implement provider
- approval to switch default provider
- approval to migrate production

Roadmap 4.29 may approve only future manual local artifact preparation, if the
checklist is accepted.

The following are not approved:

- inference
- `/classify` calls
- `onnxruntime` addition
- provider implementation
- provider factory changes
- default-provider switch
- runtime changes
- Dockerfile changes
- Docker Compose changes
- dependency changes
- production migration

## No-go checklist

- do not download official ONNX/PB/JSON artifacts in Roadmap 4.29
- do not add model files
- do not add audio fixtures
- do not add network/download logic
- do not add `onnxruntime`
- do not change provider code
- do not change provider factory
- do not change controlled vocabulary
- do not call `/classify`
- do not run inference
- do not import heavy runtime/provider modules
- do not change Dockerfile
- do not change Docker Compose
- do not change dependencies
- do not touch `tidal-parser`
- do not start shadow execution
- do not start canary rollout
- do not start LLM cutover
- do not start production migration

## Decision options

- approve future manual local-only artifact preparation
- revise approval gate checklist
- block until legal/provenance review is clearer
- block until local artifact storage path is confirmed
- keep `legacy_musicnn` as only production path

## Recommended decision

Approve only the next future manual local-only artifact preparation step if the
checklist is accepted.

Do not run inference.

Do not add `onnxruntime`.

Do not add model files to repo.

Do not change provider/default/runtime.

Keep `legacy_musicnn` as production baseline.

## Explicit non-goals

- no production classifier code
- no provider implementation
- no provider factory wiring
- no default provider switch
- no `/classify` contract changes
- no response shape changes
- no cache semantics changes
- no model files in repo
- no audio fixtures
- no inference
- no Docker/dependency/runtime changes
- no `tidal-parser` changes
- no tag/release work

## Allowed next steps

- review this approval gate
- if accepted, perform a separate future manual local-only artifact preparation step
- create a future real evidence report with measured SHA256/file size/provenance fields
- keep artifacts outside repo

## Prohibited next steps

- starting parity inference from this step
- adding `onnxruntime`
- implementing provider
- changing production default
- moving artifacts into repo
- calling `/classify`
- changing Docker/runtime/dependencies

## Rollback considerations

Rollback before commit is deletion of this Markdown document.

After commit, rollback is git revert of the documentation commit.

No runtime rollback is required because no runtime/code/dependency/model changes
are allowed.
