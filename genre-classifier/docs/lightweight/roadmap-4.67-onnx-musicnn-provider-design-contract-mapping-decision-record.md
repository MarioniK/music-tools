# Roadmap 4.67 - ONNX/MusiCNN provider design contract and mapping decision record

## Контекст и входные доказательства

Roadmap 4.67 не запускает inference и не меняет production runtime. Этот шаг
собирает уже подтверждённые локальные evidence в единый design record для
будущего, отдельно gated provider slice.

Опорные входы:

- Roadmap 4.64: preprocessing-only probe подтвердил `TensorflowInputMusiCNN`
  path и стабильный final patch shape `[187, 96]`, при этом raw observed shape
  была `[2948, 96]`, а repeated-run stability показала
  `max_abs_diff = 0.0` и `mean_abs_diff = 0.0`.
- Roadmap 4.65: isolated ONNX/MusiCNN output capture подтвердил реальный local
  ONNX Runtime capture с input `melspectrogram`, output names
  `activations` и `embeddings`, а также output shapes `[50]` и `[200]`
  соответственно, опять же со stable repeated-run evidence.
- Roadmap 4.66: semantic mapping smoke подтвердил, что activations `[50]`
  согласованы с metadata/classes `[50]`, index order usable, а top-N mapping
  можно собрать без leakage и без изменения `/classify` contract.

Эта точка не претендует на production readiness и не меняет default provider.
Baseline по-прежнему остаётся `legacy_musicnn`.

## Предложение по границе provider

Предлагаемый boundary для будущего шага:

- ONNX/MusiCNN provider остаётся за существующей provider abstraction;
- `/classify` response shape не меняется;
- contract для `tidal-parser` не меняется;
- default provider в этом шаге не переключается;
- runtime shadow остаётся disabled by default;
- provider implementation в этом шаге не делается.

Это design proposal, а не готовая production migration.

## Контракт preprocessing

Предлагаемый preprocessing contract для будущего provider lane:

- использовать `TensorflowInputMusiCNN`-based preprocessing;
- целевой final patch shape: `[187, 96]`;
- shaping policy должна быть deterministic;
- `TensorflowPredictMusiCNN` oracle не используется;
- strict legacy parity не требуется на этом шаге;
- preprocessing failure должен быть явным и диагностируемым.

Смысл этого контракта в том, чтобы опираться на уже подтверждённый
preprocessing path, но не превращать его в claim о полной эквивалентности с
legacy TensorFlow lane.

## Контракт inference

Предлагаемый inference contract:

- runtime: ONNX Runtime;
- artifact: official/local ONNX/MusiCNN model artifact;
- input name: `melspectrogram`;
- output names: `activations`, `embeddings`;
- expected shapes: `activations [50]`, `embeddings [200]`;
- model files не коммитятся в этом шаге;
- ONNX Runtime failure должен считаться отдельным degraded state;
- model artifact missing должен считаться отдельным degraded state.

Этот шаг фиксирует именно контракт ожиданий, а не поставку model artifact в
репозиторий.

## Контракт semantic mapping

Предлагаемый semantic mapping contract:

- activations index должен маппиться на `metadata/classes`;
- top-N extraction должна быть deterministic;
- mapping должен использовать controlled vocabulary;
- non-genre leakage должен фильтроваться;
- unmapped labels должны иметь explicit handling;
- `genres` и `genres_pretty` должны собираться из одного согласованного
  источника;
- `metadata/classes` count должен совпадать с activations count.

Ключевой вывод из 4.66: count match и index order usable уже подтверждены как
локальное evidence, поэтому в 4.67 можно обсуждать policy, а не перебирать
shape compatibility заново.

## Предложение по confidence и threshold policy

Для будущего slice предлагается зафиксировать policy отдельно:

- top-N count должен быть явно определён;
- score threshold должен быть явным и конфигурируемым;
- minimum confidence handling должен задавать поведение при слабых выходах;
- ordering должен оставаться deterministic даже при tie или near-tie scores;
- empty/degraded output должен быть предсказуемым и безопасным;
- любые threshold-решения требуют будущей validation перед default switch.

Это только proposal. В Roadmap 4.67 мы не утверждаем production threshold
values и не claim-им финальную quality bar.

## Поведение при сбоях и degraded states

Предлагаемое поведение при сбоях:

- preprocessing failure: вернуть диагностический degraded state;
- ONNX Runtime failure: вернуть диагностический degraded state;
- model artifact missing: вернуть диагностический degraded state;
- metadata/classes mismatch: считать contract violation;
- no confident labels: вернуть empty или degraded semantic result по явной
  policy;
- fallback to `legacy_musicnn` допускается только если он будет явно
  спроектирован позже, не в этом шаге.

Это важно для безопасной миграции: будущий provider не должен silently
маскировать ошибки и подменять их ложным успехом.

## Требования к observability

Для будущего slice нужны структурированные логи:

- provider name;
- `duration_ms`;
- preprocessing duration;
- inference duration;
- mapping duration;
- output counts;
- degraded reason;
- без секретов и без private local paths в логах.

Логи должны помогать разбирать состояние pipeline, но не должны раскрывать
локальные технические детали, которые не нужны для диагностики.

## Требования к runtime и dependency migration

Отдельные миграционные решения потребуются позже:

- decision on production `onnxruntime` dependency;
- decision on `Essentia` / `essentia-tensorflow` dependency surface;
- Docker image impact review;
- model artifact acquisition and storage policy;
- production dependency changes в Roadmap 4.67 не вносятся.

Здесь фиксируется именно migration boundary. Никакого production dependency
change в этом шаге нет.

## Будущий implementation slice

Минимальный будущий slice, который следует из этого decision record:

- disabled-by-default ONNX/MusiCNN provider scaffold;
- no default switch;
- no `/classify` contract change;
- tests for mapping and response shape;
- runtime migration as separate explicit gate.

Такой slice позволит развивать lane поэтапно, не ломая текущий baseline.

## Явные non-goals

Roadmap 4.67 не делает следующее:

- не provider implementation;
- не `/classify` integration;
- не default provider switch;
- не production migration;
- не Docker/runtime migration;
- не production dependency change;
- не strict legacy parity;
- не TensorFlow vs ONNX equivalence;
- не production readiness claim;
- не alternative model selection.

## Сводка решения

В этой точке принято только design решение о boundary и mapping policy:

- preprocessing опирается на подтверждённый `TensorflowInputMusiCNN` path;
- inference contract опирается на local ONNX Runtime evidence;
- semantic mapping опирается на confirmed classes/activations match;
- response shape и `/classify` contract остаются неизменными;
- default provider `legacy_musicnn` остаётся production baseline;
- дальнейшие runtime и dependency изменения выделяются в отдельный gated slice.

## Sanity summary

Санитизированный отчёт для этой точки:

- [`docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-provider-design-contract-report.json`](./evaluation/parity-scaffold/onnx-musicnn-provider-design-contract-report.json)

Ключевой смысл Roadmap 4.67:

- evidence из 4.64, 4.65 и 4.66 достаточно для design contract;
- production migration здесь не утверждается;
- provider/default logic untouched;
- classify contract untouched;
- response shape untouched.
