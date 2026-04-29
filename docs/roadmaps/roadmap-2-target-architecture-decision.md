# Roadmap 2 — genre-classifier target architecture decision

- Status: Accepted
- Stage: Roadmap 2.2
- Depends on: `roadmap-2-contract-freeze.md`

## Scope

Этот документ фиксирует целевое архитектурное направление для следующего этапа развития `genre-classifier` после contract freeze. Это decision document, а не implementation plan: он не меняет текущий runtime, не вводит новый inference stack и не меняет внешний orchestration contract.

## Current baseline

Текущий baseline зафиксирован в [docs/roadmaps/roadmap-2-contract-freeze.md](roadmap-2-contract-freeze.md).

На текущем этапе уже зафиксировано:

- внешний integration contract между `tidal-parser` и `genre-classifier`;
- роль classifier как дополнительного жанрового источника, а не основного orchestration layer;
- недопустимость неявного изменения cache semantics, merge semantics и внешнего HTTP contract.

## Decision scope

Нужно зафиксировать:

- целевое направление миграции away from Tensor/Essentia stack;
- допустимую форму LLM-based inference;
- ограничения на output discipline;
- допустимую схему rollout;
- implementation baseline для следующего этапа.

Вне scope:

- кодовая миграция;
- смена публичного API;
- выбор конкретного продакшн-провайдера и окончательного model artifact;
- инфраструктурное внедрение fallback path;
- рефакторинг `tidal-parser` вне необходимого integration baseline.

## Options considered

### Option A — local small instruct model + schema-constrained output

Описание:

- inference выполняется локально в `genre-classifier`;
- модель относится к small-to-medium instruction-tuned class;
- ответ модели ограничивается schema-constrained JSON;
- vocabulary контролируется на стороне inference/output validation.

Плюсы:

- минимальная зависимость от внешнего провайдера;
- лучшее соответствие текущему deployment shape отдельного сервиса;
- проще сохранить текущий orchestration contract без remote coupling;
- лучше контролируются latency envelope, observability и fallback semantics внутри сервиса.

Минусы:

- выше локальные runtime-требования;
- потребуется аккуратный контроль model/runtime compatibility;
- качество зависит от выбранной локальной модели и дисциплины prompt/schema.

### Option B — remote LLM provider + strict schema

Описание:

- inference уходит во внешний provider;
- сервис остаётся adapter/boundary layer;
- output также ограничивается schema-constrained JSON.

Плюсы:

- быстрее старт по качеству моделей;
- меньше локальных model-management задач.

Минусы:

- сильнее внешний operational dependency;
- выше чувствительность к latency, quota и provider failure;
- сложнее сохранить простую и дешёвую operational модель текущего classifier;
- remote-first path хуже сочетается с текущим frozen contract и этапным rollout без дополнительной сложности.

### Option C — hybrid local primary + remote fallback

Описание:

- локальный inference — основной путь;
- remote fallback допускается как опциональный controlled path;
- единый service contract остаётся поверх provider abstraction.

Плюсы:

- сохраняет local-first baseline;
- оставляет controlled escape hatch при слабом локальном результате или runtime issue;
- лучше поддерживает phased rollout.

Минусы:

- как primary architecture слишком рано добавляет operational complexity;
- требует заранее продуманной provider boundary, policy и observability;
- на текущем этапе это скорее направление расширения, чем стартовая реализация.

## Trade-off summary

### Local vs remote

Для текущего roadmap local path предпочтительнее как primary architecture. Он лучше соответствует уже существующему deployment shape отдельного сервиса и уменьшает число новых отказных режимов на этапе миграции. Remote path допускается только как возможное расширение после стабилизации локального inference.

### Sync vs async boundary

Текущий frozen contract между сервисами синхронный HTTP. На этом этапе нет основания менять boundary на async job pattern. Следующий этап должен сохранять sync request/response shape и укладываться в существующую orchestration модель `tidal-parser`.

### Provider adapter vs hard single-provider coupling

Для будущей реализации нужен provider boundary внутри `genre-classifier`, а не жёсткая привязка к одному runtime/provider implementation. Это важно даже при local-first решении, потому что migration path может включать смену локального backend или controlled remote fallback.

### Controlled vocabulary vs freer generation

Свободная генерация жанров для текущего pipeline нежелательна. Merge semantics, blog output и жанровая нормализация ожидают ограниченный и предсказуемый выходной набор. Поэтому controlled vocabulary предпочтителен как часть semantic contract следующего этапа.

### Schema-constrained JSON vs freeform + parsing

Freeform output с последующим parsing не подходит как baseline миграции. Для следующего этапа нужен strict JSON с явной schema validation, чтобы сохранить интеграционный контракт и уменьшить риск скрытого drift в `genres` / `genres_pretty`.

## Decision

### Primary direction

Основное целевое направление:

- local small-to-medium instruction-tuned model;
- local-first inference;
- внешний service boundary для этой migration phase остаётся synchronous HTTP;
- schema-constrained JSON output;
- controlled vocabulary;
- provider boundary внутри сервиса;
- без remote-first architecture как primary path.

### Remote fallback direction

Remote fallback допускается только как optional later direction, а не как стартовая архитектура миграции. На текущем этапе он не является baseline implementation target.

### Explicit non-decision

Сейчас не фиксируются:

- конкретный model family;
- конкретный provider;
- конкретный inference runtime;
- конкретный schema library;
- конкретная hardware expectation beyond local small-model direction.

## Target-level decisions

### Inference model class

- целевой класс: small-to-medium instruction-tuned model;
- модель должна быть пригодна для controlled JSON generation;
- migration direction уходит от Tensor/Essentia-specific inference path.

### Output discipline

- response discipline: strict JSON;
- JSON должен проходить schema validation;
- жанры должны оставаться в controlled vocabulary;
- semantic compatibility classifier output с frozen downstream expectations должна сохраняться, включая текущее поведение `genres` и `genres_pretty`;
- `genres` и `genres_pretty` должны оставаться выводимыми в форме, совместимой с frozen external contract.

### Fallback strategy

- local-first;
- remote path — только optional controlled fallback later;
- remote-first не принимается как primary architecture на этом этапе.

### Python target direction

- preferred target direction: Python `3.13`;
- Python `3.12` remains acceptable if compatibility blocks `3.13` during implementation;
- это направление для следующего implementation stage, а не немедленное изменение текущего runtime.

### Observability expectations

Следующий этап должен учитывать:

- structured logs;
- request correlation;
- model/runtime version visibility;
- latency metrics;
- validation counters;
- fallback counters;
- error counters.

Это operational requirement для будущей миграции, а не причина менять текущую observability модель уже сейчас.

### Rollout shape

Целевой rollout:

1. implementation baseline;
2. shadow/comparison;
3. limited rollout;
4. cutover;
5. legacy removal.

Этот порядок фиксируется как migration shape. Он не означает, что все шаги будут выполнены в одном коммите или одном релизе.

## Implementation baseline for the next stage

Следующий практический этап должен сделать только baseline для новой архитектуры:

- выделить внутреннюю provider boundary в `genre-classifier`;
- описать target schema для model output;
- зафиксировать controlled vocabulary boundary;
- подготовить runtime/version baseline для нового inference path;
- сохранить frozen HTTP contract без изменения внешнего API.

### What we are not doing yet

На следующем этапе всё ещё сознательно не делаем:

- production cutover;
- remote fallback implementation;
- смену orchestration contract;
- cache behavior changes;
- merge behavior redesign;
- readiness/health redesign;
- массовый refactor `tidal-parser`.

### Open questions before code

- какой именно model/runtime candidate подходит под local-first baseline;
- какой минимальный controlled vocabulary boundary нужен для совместимости с текущим merge path;
- как именно version/runtime metadata будет surfaced в logs/metrics;
- какой validation failure policy нужен между raw model output и frozen HTTP response;
- как будет организован comparison path со старым classifier behavior на shadow stage.

## Potential implementation touchpoints

Ниже перечислены только те файлы, чья значимость уже подтверждается текущим contract freeze и текущей integration boundary:

- `docs/roadmaps/roadmap-2-contract-freeze.md`
- `genre-classifier/app/main.py`
- `genre-classifier/app/genre_normalization.py`
- `genre-classifier/tests/test_upload_validation.py`
- `genre-classifier/tests/test_genre_normalization.py`
- `tidal-parser/app/main.py`
- `tidal-parser/app/settings.py`

## Roadmap 2.16 — release readiness and v0.3 decision

- Tag: pending `v0.3.0`
- Commit: `e7b7a0d` — `docs/eval: add roadmap 2.16 release readiness decision`

Roadmap 2.16 records the release-readiness decision after v0.2.15 for `genre-classifier`.

Decision summary:

- v0.3.0 should be positioned as a migration milestone release, not an LLM production cutover;
- default provider remains `legacy_musicnn`;
- production response remains legacy-only;
- external `/classify` contract and response shape were not changed;
- canary rollout, default-provider switch, and production cutover are explicitly out of scope;
- `invalid_output` live evidence gap is non-blocking for the v0.3.0 milestone, but blocking before canary or cutover approval;
- no actual canary and no default-provider switch approval are non-blocking for v0.3.0, but blocking for production LLM adoption;
- Python/runtime technical debt is moved to post-v0.3 technical debt and is not mixed into the release decision;
- `tidal-parser` was not changed.
