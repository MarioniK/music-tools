# Roadmap 4.55 - ONNX/MusiCNN pragmatic preprocessing strategy design

## Статус

Документационный design-slice.

`not_production_decision: true`
`alternative_candidate_search_in_scope: false`
`strict_legacy_parity_required: false`
`output_drift_allowed: true`
`preprocessing_required: true`
`preprocessing_identical_to_legacy_required: false`
`documented_reproducible_preprocessing_required: true`

Roadmap 4.55 не утверждает production provider, default-provider switch, `/classify`
contract change, response shape change, dependency change, runtime change,
Dockerfile/Compose change, production migration или альтернативные модели.

## AGENTS.md compliance

Этот артефакт подготовлен после чтения и соблюдения
`/opt/music-tools/AGENTS.md`.

Подтверждённые ограничения, соблюдённые здесь:

- работа ограничена `genre-classifier`;
- `tidal-parser` не затронут;
- Docker Compose не запускался;
- rebuild не запускался;
- `/classify` не вызывался;
- inference не запускался;
- production code не менялся;
- provider switch не утверждался;
- production migration не утверждалась;
- alternative candidate selection не выполнялся;
- dependency changes не вносились;
- model/audio files не менялись.

## Контекст Roadmap 4

Roadmap 4 перестраивает `genre-classifier` в сторону lighter-weight runtime,
не меняя внешний `/classify` contract и response shape.

Для этого roadmap:

- `legacy_musicnn` остаётся default provider;
- strict legacy parity больше не является mandatory gate;
- controlled, reproducible и documented output drift допускается;
- target candidate сейчас один: `official_onnx_musicnn`;
- preprocessing технически нужен, потому что ONNX/MusiCNN ожидает
  `melspectrogram [187, 96]`;
- preprocessing identical to `TensorflowPredictMusiCNN` не требуется;
- любая production-реализация и default switch остаются отдельными gates.

## Проверенные метаданные

Проверенная локальная metadata показывает ожидаемую форму входа и выходов:

- input name: `model/Placeholder`
- input shape tail: `[187, 96]`
- expected activations: `[50]`
- expected embeddings: `[200]`
- inference algorithm in legacy metadata: `TensorflowPredictMusiCNN`

Проверка выполнялась только как metadata inspection, без inference.

## Target Candidate

- target candidate: `official_onnx_musicnn`
- candidate count: `1`
- alternative candidate search in scope: `false`

## Reviewed preprocessing strategy options

### 1. Essentia standard feature extraction path

Описание: использовать Essentia standard algorithms, если они могут собрать
совместимый mel-spectrogram patch без `TensorflowPredictMusiCNN`.

Плюсы:

- концептуально ближе к текущему audio stack;
- сохраняет familiar runtime boundary;
- потенциально можно убрать TensorFlow из production path, сохранив
  воспроизводимую preprocessing story.

Минусы:

- может сохранять Essentia dependency;
- chain алгоритмов должен быть явно задокументирован;
- без отдельной approval-фазы нельзя считать это готовой production
  реализацией.

### 2. Lightweight numpy/scipy/librosa-style path

Описание: рассмотреть как design option only, без добавления зависимостей в
Roadmap 4.55.

Плюсы:

- explicit и хорошо документируемый путь;
- может быть проще для аудита.

Минусы:

- новые зависимости требуют отдельного approval;
- поведение может заметно отличаться от MusiCNN training preprocessing;
- не подходит как действие Roadmap 4.55, потому что dependency changes здесь
  запрещены.

### 3. Minimal custom numpy STFT/mel path

Описание: полностью свой STFT/mel pipeline на numpy.

Плюсы:

- минимальный набор потенциальных runtime dependencies;
- легко описывать пошагово.

Минусы:

- высокий риск subtle audio preprocessing mistakes;
- самый хрупкий путь для audio parity reasoning;
- слишком рискован для safe-slice без дополнительной validation phase.

### 4. Reuse existing Essentia audio loading + separate mel generation

Описание: оставить stable audio decoding/loading на Essentia и отделить
mel-generation от `TensorflowPredictMusiCNN`.

Плюсы:

- стабильная база для audio loading;
- позволяет строить reproducible preprocessing chain;
- лучше всего вписывается в local-only boundary и будущий provider boundary.

Минусы:

- всё равно нужен чёткий documented algorithm chain;
- без дальнейшей реализации остаётся design-only decision.

## Selected Strategy

Выбранная стратегия:

`Essentia standard audio loading + documented standalone mel-spectrogram generation path`,
предпочтительно на Essentia standard algorithms, если они доступны без
`TensorflowPredictMusiCNN`.

### Почему именно она

- она остаётся local-only;
- она не требует runtime network downloads;
- она не требует production dependency changes в Roadmap 4.55;
- она не требует strict legacy parity;
- она не использует `TensorflowPredictMusiCNN` как preprocessing oracle;
- она совместима с future provider boundary;
- она безопасна для дальнейшей evaluation-проверки на approved legal fixtures;
- она целится в `melspectrogram [187, 96]`, что соответствует ONNX input
  shape metadata.

## Rejected Options

- `Lightweight numpy/scipy/librosa-style path` rejected for now because
  dependencies are out of scope and require separate approval.
- `Minimal custom numpy STFT/mel path` rejected because риск subtle audio
  preprocessing ошибок слишком высок для этого safe-slice.
- pure legacy parity path rejected because strict legacy parity больше не
  mandatory gate.
- `TensorflowPredictMusiCNN`-based preprocessing reuse rejected because Roadmap
  4.55 explicitly does not use it as oracle for the new preprocessing design.

## Preprocessing Input

- input name: `melspectrogram`
- shape tail: `[187, 96]`

## Expected Outputs

- activations: `[50]`
- embeddings: `[200]`

## Prototype Acceptance Criteria for Roadmap 4.56

- ONNX input shape is correct:
  - input name: `melspectrogram`
  - shape tail: `[187, 96]`
- output is produced for 3 approved legal fixtures, if separately approved in
  Roadmap 4.56;
- output is stable across repeated runs;
- outputs have the expected shapes:
  - activations `[50]`
  - embeddings `[200]`
- labels are mapped using existing metadata/classes;
- output is mapped to controlled vocabulary;
- non-genre leakage is controlled;
- `/classify` contract remains unchanged;
- response shape remains unchanged;
- `legacy_musicnn` remains the default provider;
- provider implementation, default switch, and production migration are still
  separate gates.

## Contract and Response Shape

`classify_contract_unchanged_required: true`
`response_shape_unchanged_required: true`

Response shape remains:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## Safety and Approval Boundaries

- `legacy_musicnn_default_unchanged: true`
- `approved_for_provider_implementation: false`
- `approved_for_default_provider_switch: false`
- `approved_for_production: false`
- `approved_for_dependency_changes: false`
- `approved_for_classify_call: false`

## Summary Decision

Roadmap 4.55 confirms a pragmatic, documented, reproducible preprocessing
strategy design for the official ONNX/MusiCNN lane.

Это design-only артефакт. Он не утверждает реализацию, не меняет runtime и не
переводит сервис на ONNX.

## Next Step Recommendation

Roadmap 4.56 — ONNX/MusiCNN pragmatic preprocessing prototype scaffold

Рекомендуемый следующий шаг:

- собрать local-only prototype scaffold для выбранной preprocessing strategy;
- не менять provider factory;
- не менять default provider;
- не менять `/classify` contract;
- не менять response shape;
- не добавлять production dependencies;
- не выполнять production inference.
