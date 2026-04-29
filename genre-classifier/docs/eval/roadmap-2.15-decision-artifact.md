# Roadmap 2.15 Decision Artifact

## Executive Summary

Roadmap 2.15 reviewed controlled enabled runtime shadow execution for `genre-classifier`.

Production response immutability was confirmed across the reviewed live scenarios. Default production behavior remains unchanged. Canary serving and provider cutover remain not approved.

## Scope

- `genre-classifier` only;
- no `tidal-parser` changes;
- no committed runtime behavior change from evidence collection;
- no `/classify` API changes;
- no response shape changes;
- no canary;
- no cutover;
- no runtime artifact writing.

Related commits:

- `554906b` - `docs/eval: add roadmap 2.15 controlled shadow evidence plan`
- `b05233a` - `docs/eval: add roadmap 2.15 live evidence review template`
- `12074a3` - `fix/runtime: support Python 3.6 event loop fallback`
- `dec5e90` - `docs/eval: fill roadmap 2.15 live evidence review`

Evidence sources:

- `docs/eval/roadmap-2.15-controlled-shadow-evidence-plan.md`
- `docs/eval/roadmap-2.15-live-evidence-review.md`

## Baseline Blocker

Initial `/classify` baseline failed in the container runtime:

```text
module 'asyncio' has no attribute 'get_running_loop'
```

Cause:

- the `genre-classifier` container uses Python 3.6;
- Python 3.6 does not provide `asyncio.get_running_loop`.

Resolution:

- commit `12074a3` added a minimal event loop compatibility fallback;
- after rebuild, `/health` returned `{"ok": true}`;
- after rebuild, `/classify` passed with the legacy-only response shape.

## Evidence Summary

| scenario | status | notes |
| --- | --- | --- |
| baseline defaults | pass | default service config skips shadow by config |
| skipped_by_sampling | pass | sample rate `0.0` produced `skipped_by_sampling` |
| completed/success | pass | stub LLM shadow path completed with `success` |
| provider_error | pass | local HTTP transport failure isolated as `provider_error` |
| timeout | pass | shadow timeout isolated from production response |
| skipped_by_concurrency | pass | overlapping requests produced `skipped_by_concurrency` |
| invalid_output | documented gap | not safely live-reproducible through current `/classify` runtime path without helper/change |

## Production Response Immutability

Production response invariants were preserved:

- response keys remained `ok`, `message`, `genres`, `genres_pretty`;
- forbidden fields were absent: `shadow`, `llm`, `comparison`, `diagnostics`, `debug`, `canary`;
- shadow outcome did not affect HTTP response status;
- shadow outcome did not affect response shape;
- production response remained legacy-only.

## Runtime Safety Findings

Observed safety findings:

- sampling guard works;
- concurrency guard works;
- timeout isolation works;
- provider error isolation works;
- default service config skips shadow by config;
- structured logs are sufficient for safety-oriented manual review.

## Known Gaps

Known gaps after Roadmap 2.15:

- `invalid_output` was not safely live-reproducible through the current `/classify` runtime path;
- structured logs are not a durable artifact trail;
- detailed genre-level disagreement review still needs artifact or evaluation support if required later;
- delayed provider logs may appear after timeout due to the slow `local_http` helper, but production response remains unaffected.

## Decision

Roadmap 2.15 evidence collection is sufficient for v0.2.15 release discussion.

Decision statements:

- no immediate runtime shadow hardening blocker identified;
- runtime evidence artifacts baseline is optional follow-up, not an immediate blocker;
- canary remains not approved;
- cutover remains not approved;
- default provider remains `legacy_musicnn`.

This decision does not approve canary serving, provider cutover, default provider changes, external API changes, response shape changes, or runtime artifact writing.

## Recommended Follow-Ups

Recommended follow-ups:

- direct v0.2.15 release tagging after decision artifact review;
- optional Roadmap 2.16 runtime evidence artifacts baseline;
- optional `invalid_output` helper or test-only evidence improvement;
- later Python runtime upgrade as a separate roadmap step, not mixed into this evidence decision.
