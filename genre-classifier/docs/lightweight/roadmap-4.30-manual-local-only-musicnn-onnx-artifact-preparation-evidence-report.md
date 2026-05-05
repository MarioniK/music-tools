# Roadmap 4.30 - Manual local-only MusiCNN ONNX artifact preparation evidence report

Status: prepared for review / local-only artifact metadata evidence / non-production-facing.

## Purpose

Roadmap 4.30 records real local-only metadata evidence for official MusiCNN
ONNX/PB/JSON artifacts prepared outside the repository.

This is an artifact preparation and metadata evidence step only.

This is not a production decision.

This is not an inference step.

This does not approve parity scaffolding, provider implementation, runtime
changes, dependency changes, Docker changes, or production migration.

## Current production baseline

The default provider remains `legacy_musicnn`.

The production classifier path remains legacy MusiCNN.

The current preprocessing/inference path remains:

- `ffmpeg`
- `MonoLoader`
- `TensorflowPredictMusiCNN`

The `/classify` contract is unchanged.

The response shape is unchanged:

- `ok`
- `message`
- `genres`
- `genres_pretty`

The current bundled production baseline artifacts are:

- `app/models/msd-musicnn-1.pb`
- `app/models/msd-musicnn-1.json`

These existing bundled artifacts were measured for comparison only. They were
not newly downloaded, moved, deleted, staged, or committed by Roadmap 4.30.

## Local-only path

The approved local-only artifact directory used for this evidence step is:

```text
/tmp/music-tools-onnx-parity/
```

This path is non-portable, disposable, local-only, outside
`/opt/music-tools/genre-classifier`, and not part of production runtime.

## Prepared artifacts

The following official/local artifacts were manually prepared only under
`/tmp/music-tools-onnx-parity/`:

- `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`
- `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`
- `/tmp/music-tools-onnx-parity/msd-musicnn-1.pb`

The PB file was prepared because the official source index exposes it next to
the ONNX and JSON files, and it is safe and useful for identity/hash comparison
against the existing bundled production baseline PB.

No official/local artifact was placed under `docs/`, `tests/`, `app/`, or any
path under `/opt/music-tools/genre-classifier`.

## Measured SHA256 and file sizes

| Artifact | Scope | Size bytes | SHA256 |
| --- | --- | ---: | --- |
| `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx` | official/local temp artifact | 3168334 | `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1` |
| `/tmp/music-tools-onnx-parity/msd-musicnn-1.json` | official/local temp artifact | 3299 | `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe` |
| `/tmp/music-tools-onnx-parity/msd-musicnn-1.pb` | optional official/local temp artifact | 3197999 | `cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e` |
| `app/models/msd-musicnn-1.pb` | existing production baseline artifact | 3197999 | `cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e` |
| `app/models/msd-musicnn-1.json` | existing production baseline artifact | 3298 | `24842b068b5c09dce033a0bcb41d450e4e469352b799e831ac7728c93bbfb6be` |

The official/local PB matches the current bundled PB by SHA256.

The official/local JSON and current bundled JSON do not match by SHA256 and
differ by one byte in measured file size. This is recorded as metadata evidence
only and does not change production behavior.

This JSON difference is an evidence gap and review item. It is not parity
evidence, does not approve inference, and must be reviewed before any parity
scaffold.

## Source, provenance, and license notes

Allowed source index:

```text
https://essentia.upf.edu/models/feature-extractors/musicnn/
```

Confirmed official/local artifact URLs:

- `https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.onnx`
- `https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.json`
- `https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.pb`

The source index lists:

- `msd-musicnn-1.json`, dated 16-May-2023, size 3299 bytes
- `msd-musicnn-1.onnx`, dated 18-May-2023, size 3168334 bytes
- `msd-musicnn-1.pb`, dated 16-May-2023, size 3197999 bytes

Essentia documentation states that MTG-created models are licensed under
CC BY-NC-SA 4.0 and are also available under proprietary license upon request.
License review remains required before any inference, redistribution, or
production use.

## Handling of current bundled PB/JSON

The current bundled artifacts are existing production baseline files under
`app/models/`.

They are not official/local temp artifacts.

They were not newly downloaded.

They were measured only to provide current baseline hash and file-size
comparison evidence.

`git ls-files` did not list `app/models/msd-musicnn-1.pb` or
`app/models/msd-musicnn-1.json`; `git status --ignored` reported both as
ignored files. This means they are present in the service tree for the current
runtime baseline, but they are not committed tracked artifacts in this worktree.

## Explicit confirmations

Official/local artifacts are outside the repository under
`/tmp/music-tools-onnx-parity/`.

Official/local artifact paths are non-portable and local-only.

No inference was run.

ONNX Runtime was not run.

TensorFlow inference was not run.

`/classify` was not called.

`onnxruntime` was not added.

No dependencies were added.

No provider factory was changed.

No default provider was changed.

No production runtime path was changed.

No Dockerfile was changed.

No Docker Compose file was changed.

No `/classify` contract or response shape was changed.

No model files were added to the repository.

No official/local model files were staged or committed.

`tidal-parser` was not touched.

## Review gate

This report is prepared for review only.

It does not approve inference.

It does not approve production use.

It does not convert artifact hash comparison into parity evidence.

It does not approve storing official/local artifacts in the repository.

It does not approve adding download scripts, network download logic, runtime
dependencies, provider changes, or Docker changes.

## Decision options

- Accept the local-only metadata evidence as sufficient to plan a future parity
  scaffold.
- Request a manual license/provenance review before any future scaffold.
- Request additional hash or source verification before any future scaffold.
- Reject the artifacts and keep Roadmap 4 blocked at metadata-only evidence.

## Recommended next step

Review real local-only artifact metadata evidence before any parity scaffold.
