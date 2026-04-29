# Roadmap 2.15 Controlled Shadow Evidence Plan

## Goal And Non-Goals

Roadmap 2.15 defines a controlled live evidence collection plan for enabled runtime shadow execution after v0.2.14.

Goal:

- verify enabled runtime shadow behavior using manual review;
- collect evidence through structured runtime logs;
- confirm production response immutability while shadow execution is enabled locally;
- produce evidence for a later decision artifact.

Non-goals:

- no canary rollout;
- no provider cutover;
- no default provider change;
- no external `/classify` API change;
- no response shape change;
- no shadow result returned externally;
- no runtime artifact writing implementation;
- no broad runtime redesign.

The default provider remains `legacy_musicnn`. Production response remains legacy-only.

## Runtime Review Config Strategy

Shadow execution must be enabled only through temporary runtime configuration for manual review.

Rules:

- keep committed defaults unchanged;
- do not edit committed config files to enable shadow;
- do not change Docker Compose files;
- use local shell environment variables or equivalent local runtime overrides only;
- return to the committed default runtime after each review scenario;
- record the exact runtime config used in the review notes.

Committed defaults expected after v0.2.14:

- `DEFAULT_SHADOW_ENABLED = False`;
- `DEFAULT_SHADOW_SAMPLE_RATE = 0.0`;
- `DEFAULT_SHADOW_TIMEOUT_SECONDS = 2.0`;
- `DEFAULT_SHADOW_MAX_CONCURRENT = 1`.

Suggested runtime config by scenario:

- completed/success: enable shadow, set sample rate to `1.0`, use normal timeout and available provider config;
- skipped_by_sampling: enable shadow, set sample rate to `0.0` or a low sample rate;
- skipped_by_concurrency: enable shadow, set sample rate to `1.0`, set max concurrency to `1`, issue overlapping requests;
- timeout: enable shadow, set sample rate to `1.0`, set a very small timeout;
- provider_error: enable shadow with runtime provider configuration that produces a controlled provider failure;
- invalid_output: enable shadow with a controlled provider/output path that produces invalid shadow output;
- production response immutability: compare `/classify` response shape and legacy fields for every scenario.

Do not commit any runtime review config.

## Required Live Scenarios

Each scenario must verify that `/classify` remains production legacy-only and that shadow behavior is visible only through diagnostics.

### completed/success

- shadow is enabled by local runtime config;
- sample rate allows execution;
- runtime logs show event `genre_classifier.shadow.completed`;
- runtime status is `success`;
- comparison signals are present;
- external response does not include shadow output.

### skipped_by_sampling

- shadow is enabled by local runtime config;
- sample rate excludes execution;
- runtime logs show event `genre_classifier.shadow.skipped`;
- runtime status is `skipped_by_sampling`;
- no shadow provider execution is required;
- external response remains unchanged.

### skipped_by_concurrency

- shadow is enabled by local runtime config;
- sample rate allows execution;
- max concurrency is saturated;
- runtime logs show event `genre_classifier.shadow.skipped`;
- runtime status is `skipped_by_concurrency`;
- requests are not queued for shadow execution;
- external response remains unchanged.

### timeout

- shadow is enabled by local runtime config;
- timeout budget is intentionally small;
- runtime logs show event `genre_classifier.shadow.timeout`;
- runtime status is `timeout`;
- HTTP response still succeeds or fails only according to the production legacy path;
- external response remains unchanged.

### provider_error

- shadow is enabled by local runtime config;
- provider failure is controlled and isolated;
- runtime logs show event `genre_classifier.shadow.failed`;
- runtime status is `provider_error`;
- classify does not fail because of the shadow provider;
- external response remains unchanged.

### invalid_output

- shadow is enabled by local runtime config;
- invalid shadow output is controlled and isolated;
- runtime logs show event `genre_classifier.shadow.failed`;
- runtime status is `invalid_output`;
- invalid output is not treated as `success`;
- external response remains unchanged.

### Production Response Immutability

For every scenario, verify:

- response status is controlled by the production legacy path;
- response shape does not change;
- `genres` remains legacy-derived;
- `genres_pretty` remains legacy-derived;
- no `shadow`, `llm`, `comparison`, `diagnostics`, or `canary` field appears externally.

## Evidence Expectations

Structured logs are sufficient for Roadmap 2.15 safety evidence when they show:

- event name;
- runtime status;
- request trace key if available;
- duration;
- timeout values when relevant;
- concurrency limit or skip reason when relevant;
- provider/error category when relevant;
- comparison counts when execution completes;
- shadow enabled flag and sample rate when available.

Structured logs may be insufficient for:

- detailed quality evaluation;
- genre-level disagreement review;
- prompt or raw provider response inspection;
- durable audit trails across many requests;
- statistical canary confidence.

Runtime artifact writing is not part of this roadmap step unless a separate decision explicitly adds it. Roadmap 2.15 can review whether artifacts are needed, but this plan does not implement artifact writing and does not require committed artifact config changes.

## Stop Conditions

Stop the review if any of these occur:

- production response mutates because of shadow execution;
- shadow result appears in the external response;
- response shape changes;
- shadow failure affects the HTTP response;
- sampling guard does not work;
- concurrency guard does not work;
- timeout policy does not isolate shadow execution;
- logs are insufficient to classify outcomes;
- logs are too noisy for manual review;
- committed defaults are accidentally changed;
- canary serving appears;
- provider cutover appears.

## Manual Review Checklist

Before running scenarios:

- [ ] working directory is `/opt/music-tools/genre-classifier`;
- [ ] `git status` contains only expected documentation changes;
- [ ] committed defaults remain unchanged;
- [ ] runtime review config is local and temporary;
- [ ] default provider remains `legacy_musicnn`;
- [ ] `/classify` contract is unchanged.

For each scenario:

- [ ] record runtime config;
- [ ] send one or more `/classify` requests;
- [ ] capture focused logs;
- [ ] classify event/status outcome;
- [ ] verify production response immutability;
- [ ] record whether comparison or error fields are useful;
- [ ] record noise level;
- [ ] record blockers.

After review:

- [ ] restore default runtime environment;
- [ ] confirm no committed defaults changed;
- [ ] summarize observed counts by outcome;
- [ ] document whether evidence is enough for a release discussion, artifact baseline, or hardening.

## Suggested Manual Smoke Commands

Run all commands from:

```bash
cd /opt/music-tools/genre-classifier
```

Check repository state:

```bash
git status
```

Inspect focused logs:

```bash
docker compose logs --tail=500 | grep -E "genre_classifier.shadow|shadow|runtime_shadow|shadow_execution|provider_error|invalid_output|timeout|concurrency|sample"
```

Inspect broader logs:

```bash
docker compose logs --tail=1000
```

Health check:

```bash
curl -s http://localhost:8021/health
```

Classify smoke should use the same local request method already used for `genre-classifier` manual testing. The review must not require committed config changes, Docker Compose changes, or external API shape changes.

## Follow-Up Options

After controlled evidence collection, choose one:

- direct release discussion, if enabled shadow behavior and production isolation are proven with useful logs;
- runtime evidence artifacts baseline, if logs are safe but insufficient for durable evidence or quality-oriented review;
- additional hardening, if guards, failures, taxonomy, traceability, or log usefulness are insufficient.

These follow-ups do not approve canary serving or provider cutover by themselves.
