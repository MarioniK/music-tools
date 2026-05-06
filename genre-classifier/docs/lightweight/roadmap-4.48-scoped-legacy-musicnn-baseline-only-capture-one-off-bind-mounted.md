# Roadmap 4.48 Scoped Legacy MusiCNN Baseline Capture

Roadmap 4.48 attempted a scoped, baseline-only capture of real `legacy_musicnn`
outputs for three legal CC0 fixtures stored outside the repository. The goal was
to collect sanitized baseline evidence only. This was not an ONNX run, not a
TensorFlow-vs-ONNX comparison, not a full numeric parity run, and not a
production migration decision.

## Approved Strategy

The selected fixture visibility strategy was `one_off_compose_run_bind_mount`.
The run used `docker compose run --rm` from the `genre-classifier` service
directory with the external fixture workspace bind-mounted read-only into the
one-off container. The already running service was not mutated.

The fixture policy remained unchanged:

- audio files stay outside the repository;
- fixture provenance notes stay outside the repository;
- committed reports include only sanitized fixture IDs and hashes;
- no private full local paths, audio bytes, model bytes, or traceback dumps are
  published.

## What Was Run

From the `genre-classifier` directory:

- `git status --short`
- `git rev-parse --show-toplevel`
- `git rev-parse HEAD`
- `python3 -m json.tool` against the external fixture provenance file
- `sha256sum` for the three external MP3 fixtures
- `ls -lah` for the external fixture directory
- `docker compose config --services`
- `docker compose ps`
- `docker compose run --rm` with a read-only fixture bind mount for import and
  fixture visibility checks

The discovered compose service name was `genre-classifier`.

## Result

Capture was blocked. The one-off container saw the mounted fixture directory and
the three expected MP3 files. TensorFlow imported and reported version `2.21.0`.
The required import-check command then exited non-zero while attempting to
complete the Essentia import path, aborting with duplicate TensorFlow op
registration. Because the approved runtime check failed, no baseline capture was
run and no outputs were fabricated.

Sanitized fixture evidence:

| Fixture | SHA256 |
| --- | --- |
| `john_bartmann_earning_happiness_cc0` | `d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628` |
| `john_bartmann_happy_clappy_cc0` | `4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e` |
| `john_bartmann_home_at_last_cc0` | `0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75` |

Blocked report artifact:

- `docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json`

Blockers:

- `ONE_OFF_COMPOSE_RUN_FAILED`
- `ESSENTIA_IMPORT_FAILED`

## Explicit Non-Goals

- no ONNX execution;
- no TensorFlow-vs-ONNX comparison;
- no full numeric parity;
- no `/classify` calls;
- no production dependency changes;
- no Dockerfile or Compose changes;
- no provider/default changes;
- no `tidal-parser` changes.

## Next Step

Investigate a safe import order or runtime smoke path for the one-off baseline
container, then rerun the same baseline-only capture with the approved read-only
bind mount. Keep ONNX execution, `/classify`, and numeric parity out of scope
until separately approved.
