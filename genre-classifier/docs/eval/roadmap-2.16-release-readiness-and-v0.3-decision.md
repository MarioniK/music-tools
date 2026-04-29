# Roadmap 2.16 Release Readiness And v0.3 Decision

## Scope

Roadmap 2.16 is the release-readiness and v0.3.0 decision stage for `genre-classifier`.

This is a documentation/decision-only stage. It records the current migration state after v0.2.15, classifies remaining gaps, and defines the recommended v0.3.0 release positioning.

This step does not perform or approve:

- canary rollout;
- production cutover;
- default provider switch;
- `/classify` API change;
- response shape change;
- Python or runtime upgrade.

Scope boundaries:

- `genre-classifier` only;
- no `tidal-parser` changes;
- no runtime-code changes;
- no Dockerfile changes;
- no Docker Compose changes;
- no default provider change;
- no external `/classify` contract change;
- no response shape change.

## Current State After v0.2.15

Current release-readiness state:

- default provider remains `legacy_musicnn`;
- production response remains legacy-only;
- external `/classify` contract is unchanged;
- response shape is unchanged;
- controlled live evidence for enabled shadow execution has been collected;
- production response immutability has been confirmed;
- structured logs are considered sufficient for safety-oriented manual review;
- `invalid_output` remains a documented live evidence gap;
- canary rollout is not approved;
- cutover is not approved;
- `tidal-parser` was not changed.

Confirmed controlled live scenarios:

- baseline defaults;
- `skipped_by_sampling`;
- `completed` / `success`;
- `provider_error`;
- `timeout`;
- `skipped_by_concurrency`.

The v0.2.15 evidence supports release discussion for a migration milestone with legacy production behavior preserved. It does not support LLM production adoption, limited canary serving, or provider cutover.

## Completed Migration Goals

Roadmap 2 has completed the following migration foundation goals for `genre-classifier`:

- contract freeze;
- target architecture decision;
- service skeleton refactor;
- provider abstraction baseline;
- schema validation and compatibility mapping;
- LLM provider scaffold;
- local LLM runtime integration baseline;
- prompt discipline and controlled vocabulary baseline;
- comparative evaluation and shadow-readiness;
- curated evaluation and findings review;
- runtime shadow/canary readiness;
- runtime shadow execution baseline;
- runtime shadow observation review;
- controlled runtime shadow evidence collection.

These goals establish the LLM migration foundation while preserving the existing production behavior.

## Remaining Gaps

Remaining gaps before broader LLM adoption:

| gap | classification | release impact |
| --- | --- | --- |
| `invalid_output` live evidence gap | non-blocking for v0.3.0 as a migration milestone with legacy default; blocking before cutover or canary approval | v0.3.0 may proceed if positioned honestly as legacy-default migration foundation |
| no actual canary | non-blocking for v0.3.0 milestone; blocking for production LLM adoption | canary requires a separate explicit decision and rollout plan |
| no default-provider switch approval | expected state; non-blocking for v0.3.0 | default provider must remain `legacy_musicnn` |
| Python/runtime technical debt | non-blocking for v0.3.0 milestone; should be moved to post-v0.3 technical debt | do not mix runtime upgrade into the v0.3.0 decision |

The remaining gaps are material for production LLM adoption. They are not blockers for a v0.3.0 release that is explicitly scoped as a migration milestone with legacy production behavior.

## Release Decision Options

### Option A: v0.3.0 As Migration Milestone Release With Legacy Default

Summary:

- release v0.3.0 as the completion marker for Roadmap 2 LLM migration foundation;
- keep `legacy_musicnn` as the default provider;
- keep production responses legacy-only;
- keep `/classify` contract and response shape unchanged;
- leave canary, default-provider switch, and cutover for separate approval.

Pros:

- accurately reflects the completed Roadmap 2 foundation work;
- avoids pretending that LLM production adoption has happened;
- preserves production behavior and external compatibility;
- creates a clear version boundary before any future canary or cutover discussion;
- does not mix release readiness with runtime upgrades or broad hardening.

Risks:

- readers may overinterpret v0.3.0 as an LLM production cutover unless release notes are explicit;
- `invalid_output` remains a live evidence gap;
- future canary approval still needs a separate decision artifact and operational plan.

Honest positioning:

- v0.3.0 is a migration milestone release, not an LLM production cutover.

Recommended decision: choose Option A.

### Option B: v0.3.0 Only After Separate Cutover Approval

Summary:

- delay v0.3.0 until a separate decision approves production cutover or default-provider switch.

Pros:

- avoids any possible ambiguity between migration completion and production adoption;
- forces remaining production-adoption questions to be resolved before the version bump.

Risks:

- incorrectly couples migration foundation completion to cutover approval;
- delays marking completed Roadmap 2 work;
- increases pressure to combine canary, cutover, and release readiness into one step;
- may encourage scope creep into API, runtime, or operational changes.

Honest positioning:

- this option is stricter than needed for a legacy-default migration milestone and should be used only if v0.3.0 is required to mean production LLM adoption.

### Option C: Delay v0.3.0 For One More Narrow Hardening Step

Summary:

- perform one additional narrow hardening step before tagging v0.3.0, such as test-only `invalid_output` evidence improvement or documentation cleanup.

Pros:

- may reduce one known evidence gap before release;
- can improve confidence if the additional step stays narrowly scoped.

Risks:

- may expand into runtime changes, helper code, or non-release-critical work;
- does not change the core release decision because canary and cutover would still remain unapproved;
- can blur the line between release readiness and future production adoption.

Honest positioning:

- useful only if the team wants extra polish before the milestone; not required for a legacy-default v0.3.0 decision.

## Recommended v0.3.0 Positioning

v0.3.0 completes the Roadmap 2 LLM migration foundation for `genre-classifier` while preserving legacy production behavior. Provider `legacy_musicnn` remains the default. The `/classify` contract and response shape remain unchanged. Production responses remain legacy-only. Canary rollout, default-provider switch, and production cutover are explicitly not part of v0.3.0 and require separate approval.

## Invariants

Required invariants for v0.3.0:

- `/classify` contract unchanged;
- response shape unchanged;
- default provider remains `legacy_musicnn`;
- production response remains legacy-only;
- shadow execution cannot affect production response;
- default config must not execute shadow;
- `tidal-parser` unchanged;
- no cache or external consumer impact;
- canary and cutover require a separate explicit decision.

## Manual Factual Checklist Before v0.3.0

Checklist scoped only to `genre-classifier`:

- [ ] check `git status` from `/opt/music-tools`;
- [ ] confirm the final decision commit;
- [ ] confirm default provider remains `legacy_musicnn`;
- [ ] run build from `/opt/music-tools/genre-classifier` with `docker compose build`;
- [ ] start the service with `docker compose up -d`;
- [ ] check health on `localhost:8021` if that port is used;
- [ ] run baseline `/classify` smoke with the existing known-good payload;
- [ ] inspect logs with `docker compose logs --tail=120`;
- [ ] confirm shadow execution does not run under default config.

## Rollback Considerations

Rollback considerations:

- docs-only decision commit can be reverted with `git revert`;
- tag `v0.3.0` can be deleted locally and remotely only if necessary;
- runtime rollback is usually unnecessary because the default provider remains `legacy_musicnn`;
- if someone manually enabled shadow config, disable the shadow-related config and restart `genre-classifier`;
- cutover rollback does not apply because cutover is out of scope.

## Explicitly Out Of Scope For v0.3.0

The following are explicitly out of scope for v0.3.0:

- canary rollout;
- production cutover;
- default provider switch;
- LLM as source of truth;
- API changes;
- response shape changes;
- `tidal-parser` changes;
- cache changes;
- Docker/Python runtime upgrade;
- dependency refresh;
- broad performance optimization;
- new model selection process.
