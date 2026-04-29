# Roadmap 2.14 Shadow Log Review Checklist

## Purpose

This checklist is for manual review of runtime shadow observation signals after Roadmap 2.13 and during Roadmap 2.14.

This checklist is:

- not a canary rollout;
- not a provider cutover;
- not a quality approval;
- only a manual evidence review of runtime shadow logs.

## Scope

In scope:

- review runtime logs for shadow observation behavior;
- classify observed shadow outcomes;
- check diagnostic usefulness;
- check production isolation;
- decide whether follow-up should be limited canary discussion, runtime evidence artifacts, or additional hardening.

Out of scope:

- changing default provider;
- returning shadow result externally;
- changing `/classify` API;
- changing response shape;
- enabling canary serving;
- implementing artifact writing.

## Pre-checks

Before review, verify:

- [ ] `git status` is clean or contains only expected documentation changes;
- [ ] working directory is `/opt/music-tools/genre-classifier`;
- [ ] shadow config is intentional and local to the runtime environment;
- [ ] default provider remains `legacy_musicnn`;
- [ ] shadow remains disabled-by-default in committed config;
- [ ] no `tidal-parser` changes are involved.

## Suggested Log Commands

Run commands from:

```bash
cd /opt/music-tools/genre-classifier
```

Basic log review:

```bash
docker compose logs --tail=500
```

Focused shadow review:

```bash
docker compose logs --tail=500 | grep -E "shadow|provider_error|invalid_output|timeout|concurrency|sample"
```

Extended shadow review:

```bash
docker compose logs --tail=1000 | grep -E "shadow|runtime_shadow|shadow_execution"
```

## Runtime Event And Status Mapping

Runtime event names to search for:

- `genre_classifier.shadow.skipped`;
- `genre_classifier.shadow.started`;
- `genre_classifier.shadow.completed`;
- `genre_classifier.shadow.failed`;
- `genre_classifier.shadow.timeout`;
- `genre_classifier.shadow.comparison_recorded`;
- `genre_classifier.shadow.artifact_write_failed`.

Conceptual review outcome to runtime status mapping:

- `completed` -> event `genre_classifier.shadow.completed`, status `success`;
- `skipped_sample_rate` -> event `genre_classifier.shadow.skipped`, status `skipped_by_sampling`;
- `skipped_concurrency_limit` -> event `genre_classifier.shadow.skipped`, status `skipped_by_concurrency`;
- `skipped_by_config` -> event `genre_classifier.shadow.skipped`, status `skipped_by_config`;
- `timeout` -> event `genre_classifier.shadow.timeout`, status `timeout`;
- `provider_error` -> event `genre_classifier.shadow.failed`, status `provider_error`;
- `invalid_output` -> event `genre_classifier.shadow.failed`, status `invalid_output`;
- `comparison_error` -> event `genre_classifier.shadow.failed`, status `comparison_error`;
- `observer_error` -> event `genre_classifier.shadow.failed`, status `observer_error`.

Notes:

- checklist outcome names are review terminology;
- runtime logs should be interpreted using actual event/status pairs;
- `success` is the runtime status corresponding to the `completed` review outcome;
- `skipped_by_sampling` covers both sample rate `0` and random sampling exclusion.

## Outcomes To Count

Count each observed outcome and classify its meaning.

### `completed`

- [ ] Count:
- Expected meaning: shadow execution finished with runtime status `success` and comparison signals were logged.
- Normal/warning/blocking: normal at expected sample rate; warning if comparison payload is missing or unusable; blocking if `completed` includes invalid shadow output.
- Fields to look for: `event`, `request_id` or trace key, `provider`, `outcome`, `duration_ms`, `legacy_genres_count`, `shadow_genres_count`, `overlap_count`, `overlap_ratio`.

### `skipped_sample_rate`

- [ ] Count:
- Expected meaning: shadow execution was skipped by sampling policy with runtime status `skipped_by_sampling`.
- Normal/warning/blocking: normal when sample rate excludes the request or is `0`; warning if too noisy; blocking only if skip behavior contradicts configured sample rate.
- Fields to look for: `event`, `request_id` or trace key, `outcome`, `skip_reason`, configured sample rate if available.

### `skipped_concurrency_limit`

- [ ] Count:
- Expected meaning: shadow execution was skipped because the concurrency limit was already reached with runtime status `skipped_by_concurrency`.
- Normal/warning/blocking: normal under expected saturation tests; warning if frequent in ordinary traffic; blocking if slots appear leaked or requests queue instead of skipping.
- Fields to look for: `event`, `request_id` or trace key, `outcome`, `skip_reason`, `concurrency_limit`.

### `timeout`

- [ ] Count:
- Expected meaning: shadow execution exceeded its timeout budget and was isolated from production response handling.
- Normal/warning/blocking: normal only in deliberate timeout tests; warning if occasional in real review traffic; blocking if repeated or if classify fails.
- Fields to look for: `event`, `request_id` or trace key, `provider`, `outcome`, `duration_ms`, `timeout_ms`, `error_category`.

### `provider_error`

- [ ] Count:
- Expected meaning: shadow provider failed before producing a valid result.
- Normal/warning/blocking: warning if occasional; blocking if repeated, unexplained, or if classify fails.
- Fields to look for: `event`, `request_id` or trace key, `provider`, `outcome`, `duration_ms`, `error_category`.

### `invalid_output`

- [ ] Count:
- Expected meaning: shadow provider returned output that could not be accepted as a valid shadow result.
- Normal/warning/blocking: warning if rare; blocking if repeated or treated as `completed`.
- Fields to look for: `event`, `request_id` or trace key, `provider`, `outcome`, `duration_ms`, `error_category`.

## Required Diagnostic Fields

Fields that should be visible across the log set:

- `event`;
- `request_id` or equivalent trace key;
- `provider`;
- `outcome`;
- `skip_reason`;
- `duration_ms`;
- `timeout_ms`;
- `concurrency_limit`;
- `legacy_genres_count`;
- `shadow_genres_count`;
- `overlap_count`;
- `overlap_ratio`;
- `error_category`.

Not every field is required for every event. The review should still be able to reconstruct the overall runtime picture for each reviewed request or outcome group.

## Production Isolation Checks

Verify:

- [ ] production response remains legacy-only;
- [ ] shadow result is not returned externally;
- [ ] shadow failure does not cause classify failure;
- [ ] timeout does not fail classify;
- [ ] `provider_error` does not fail classify;
- [ ] `invalid_output` does not fail classify;
- [ ] no response shape change is observed.

## Noise Checks

Verify:

- [ ] no excessive logs when shadow is disabled;
- [ ] sample-rate skips are not too noisy;
- [ ] expected timeout does not produce unnecessary stacktrace noise;
- [ ] raw provider output is not logged at normal info level;
- [ ] duplicate logs do not obscure final outcome;
- [ ] event names are clear enough for manual review.

## Comparison Signal Checks

Verify:

- [ ] `completed` outcome includes useful comparison signals;
- [ ] `overlap_count` or `overlap_ratio` is available;
- [ ] legacy and shadow genre counts are available;
- [ ] comparison payload helps review behavior without exposing shadow result externally;
- [ ] logs are enough for safety review;
- [ ] logs may still be insufficient for quality review without artifacts.

## Blocking Findings

These findings should block limited canary discussion:

- shadow affects production response;
- shadow result appears in external response;
- response shape changes;
- default provider changes;
- repeated `timeout`;
- repeated `provider_error`;
- `invalid_output` treated as `completed`;
- missing request traceability;
- useless comparison payloads;
- concurrency slot leaks;
- logs too noisy or too weak for review.

## Review Summary Template

```text
Date:
Environment:
Commit:
Shadow config:
Requests reviewed:
completed:
skipped_sample_rate:
skipped_concurrency_limit:
timeout:
provider_error:
invalid_output:
Production isolation:
Diagnostic payload quality:
Noise level:
Comparison signal usefulness:
Blocking findings:
Recommended decision:
```

## Allowed Decisions

Allowed Roadmap 2.14 review decisions:

- proceed to limited canary discussion;
- add runtime evidence artifacts first;
- perform additional runtime hardening first;
- keep shadow observation only and block canary discussion.

These decisions do not implement canary serving, artifact writing, provider cutover, default provider changes, API changes, or response shape changes.
