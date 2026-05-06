# Roadmap 4.71 - ONNX/MusiCNN artifact checksum / provenance / license gate

## Status / Scope

- Статус: documentation / approval gate
- Production decision: нет
- Production readiness: не заявляется
- Runtime smoke: не выполняется
- Scope: зафиксировать checksum, provenance, license notes и delivery strategy для уже подготовленных ONNX/MusiCNN artifacts

## Context

Этот шаг следует после Roadmap 4.70 и использует уже собранные локальные evidence points для будущего disabled-by-default runtime smoke.

Неприкосновенные baseline-ограничения на этом этапе:

- `legacy_musicnn` остаётся default provider;
- `onnx_musicnn` остаётся disabled-by-default;
- `/classify` contract unchanged;
- response shape unchanged:
  - `ok`
  - `message`
  - `genres`
  - `genres_pretty`
- no production dependency change;
- no Dockerfile / Compose change;
- no runtime downloads by default;
- no implicit artifact discovery;
- no `/tmp` defaults;
- artifacts are not committed to repo;
- `approved_for_production: false`.

## Prior evidence

Опора для этого gate:

- Roadmap 4.64:
  - raw observed shape: `[2948, 96]`
  - final shaped patch: `[187, 96]`
  - repeated-run stability: `stable`
  - max_abs_diff: `0.0`
  - mean_abs_diff: `0.0`
- Roadmap 4.65:
  - `[187, 96]` patch accepted by official/local ONNX/MusiCNN
  - activations: `[50]`
  - embeddings: `[200]`
  - repeated-run stability: `stable`
- Roadmap 4.66:
  - classes count: `50`
  - activations count: `50`
  - count match: `true`
  - index order usable: `true`
  - candidate `genres` / `genres_pretty` shape compatible with current response shape
- Roadmap 4.67:
  - provider-safe design contract / mapping decision record
- Roadmap 4.68:
  - `onnx_musicnn` scaffold added as explicit opt-in only
  - `legacy_musicnn` remains default
- Roadmap 4.69:
  - artifact paths are explicit opt-in only
  - defaults remain `None`
  - no `/tmp` defaults
  - no implicit artifact discovery
- Roadmap 4.70:
  - runtime dependency migration separated from artifact packaging
  - runtime downloads by default prohibited
  - preferred first artifact delivery: explicit mounted artifacts
  - checksums, provenance and license notes required before any runtime smoke

## Artifact evidence inputs

Локальные artifacts для проверки:

- ONNX model artifact: `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`
- metadata/classes artifact: `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`

Проверки выполнялись только на чтение, без inference и без изменения production runtime.

## ONNX model artifact

- Artifact name: `msd-musicnn-1.onnx`
- Local path: `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`
- File size: `3168334` bytes
- SHA-256: `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`
- Committed to repo: `false`

Source / provenance notes:

- Candidate points to the official Essentia MusiCNN artifact family;
- metadata JSON contains `name: MSD MusiCNN`;
- metadata JSON contains `link: https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.pb`;
- metadata JSON contains model citation for the Essentia TensorFlow Audio Models paper;
- this gate does not claim a new source of truth beyond the official/local artifact and metadata pair.

License notes:

- local metadata JSON does not expose a dedicated `license` field;
- prior local evidence in Roadmap 4.20 documents the Essentia models page as CC BY-NC-SA 4.0 for MTG-created models, with proprietary license available on request;
- this gate records that note as license context for the artifact family, but does not claim separate legal approval.

## Metadata/classes artifact

- Artifact name: `msd-musicnn-1.json`
- Local path: `/tmp/music-tools-onnx-parity/msd-musicnn-1.json`
- File size: `3299` bytes
- SHA-256: `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe`
- Parsed classes count: `50`
- Labels order status: `usable`
- Committed to repo: `false`

Source / provenance notes:

- metadata declares `name: MSD MusiCNN`;
- metadata declares `release_date: 2020-03-31`;
- metadata declares `framework: tensorflow` and `framework_version: 1.15.0`;
- metadata declares the official source link to the MusiCNN `.pb` family;
- metadata includes the reference citation for the model family.

License notes:

- the JSON itself does not carry a dedicated license field;
- license context is inherited from the official Essentia model evidence already documented in prior roadmap work;
- no separate legal approval is claimed here.

## Checksum verification result

- ONNX model checksum verified locally and matched the known prior value.
- Metadata/classes checksum verified locally and matched the known prior value.
- No mismatch blocker was observed.

Verification summary:

- `ONNX_MODEL_CHECKSUM_MATCH`
- `METADATA_CLASSES_CHECKSUM_MATCH`

## Metadata/classes validation result

Лёгкая структура JSON подтверждена локально:

- artifact is readable JSON;
- top-level structure is a dictionary;
- `classes` list exists;
- `classes_count: 50`;
- `labels_order_status: usable`;
- first labels: `rock`, `pop`, `alternative`, `indie`, `electronic`;
- last labels: `rnb`, `indie pop`, `sad`, `House`, `happy`.

Это совместимо с уже подтверждённой shape-моделью Roadmap 4.66 и не меняет response shape.

## Provenance and license notes

Provenance status:

- provenance is documented at the artifact metadata level;
- official model-family link is present in the JSON;
- reference citation is present in the JSON;
- no new source of truth is introduced by this gate.

License status:

- explicit license field is absent from the local JSON artifact;
- license context is available from prior local roadmap evidence for the Essentia model family;
- no project legal approval is asserted here;
- no redistribution claim is made here.

## Delivery strategy

Approved delivery strategy for this stage:

- preferred initial delivery: `explicit_mounted_artifacts`
- image bundling: not approved here
- runtime downloads: not approved
- implicit discovery: not approved
- `/tmp` defaults: not approved

Operational constraints:

- artifact paths must remain explicit opt-in settings;
- artifact discovery must stay deterministic and disabled by default;
- runtime smoke, when later approved, should consume explicitly mounted artifacts or separately approved packaged artifacts only.

## Approval status

- `approved_for_runtime_smoke: false`
- `approved_for_production: false`
- `not_production_decision: true`

Reasoning:

- this gate captures evidence and delivery constraints only;
- it does not authorize runtime activation;
- it does not switch default provider;
- it does not approve production packaging;
- it does not change dependency/runtime files.

## Explicit non-goals

- no production migration;
- no runtime smoke execution;
- no ONNX inference execution;
- no TensorFlow baseline execution;
- no TensorFlow vs ONNX comparison;
- no `/classify` call;
- no `/classify` contract change;
- no response shape change;
- no production dependency change;
- no Dockerfile / Compose change;
- no provider/default change;
- no committed model files;
- no committed audio files;
- no committed wheel files;
- no committed venv files;
- no `tidal-parser` changes;
- no tag / release.

## Blockers

Текущих blockers по checksum-пройденным artifact checks не зафиксировано.

Наличие отдельного legal approval на license usage / redistribution не подтверждено, но для этого roadmap-step достаточно documented license context из локальных evidence.

## Next step recommendation

Если понадобится future disabled-by-default runtime smoke, следующий approved step должен отдельно подтвердить:

- explicit runtime dependency availability;
- explicit mount wiring;
- smoke-only execution boundary;
- error handling and rollback path;
- no default-provider change;
- no production migration claim.

## Rollback considerations

Rollback для этого шага простой и безопасный:

- удалить только новые documentation/report files;
- оставить existing provider scaffold и production baseline untouched;
- не трогать Dockerfile, Compose, dependencies or default provider;
- при необходимости вернуться к Roadmap 4.70 evidence as the last gate before checksum/provenance/license confirmation.
