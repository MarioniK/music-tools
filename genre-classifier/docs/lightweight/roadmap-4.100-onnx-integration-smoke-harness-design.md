# Roadmap 4.100 - ONNX integration smoke harness design

## Summary

Roadmap 4.100 фиксирует безопасный дизайн будущего integration smoke для цепочки
`tidal-parser -> genre-classifier-onnx`.
Это documentation-only шаг. Он не запускает smoke, не меняет default provider,
не меняет compose-конфигурацию production path и не трогает runtime defaults.

## What was verified

### 1. `tidal-parser` classifier URL source

Фактический источник URL для audio classifier находится в
[`tidal-parser/app/settings.py`](/opt/music-tools/tidal-parser/app/settings.py).

- default value: `http://genre-classifier:8021/classify`
- env var: `AUDIO_CLASSIFIER_URL`
- getter: `get_audio_classifier_url()`
- call site: `tidal-parser/app/main.py` вызывает getter внутри
  `classify_audio_file()`

Это важно, потому что URL читается не как baked-in constant в request pipeline,
а через функцию, которая обращается к `os.getenv`. Значит:

- override возможен без изменения app code;
- override работает на уровне процесса/container env;
- для безопасного smoke не нужно менять production default value;
- для уже запущенного процесса потребуется отдельный smoke container или
  controlled restart of a non-production instance.

### 2. Compose findings

`tidal-parser/docker-compose.yml` присутствует в репозитории и использует
`env_file: .env`, но не задаёт `AUDIO_CLASSIFIER_URL` прямо в tracked compose.

`genre-classifier/docker-compose.yml` уже содержит:

- default service `genre-classifier` на target `legacy-runtime`;
- optional service `genre-classifier-onnx` behind profile `onnx`;
- host port mapping `8022:8021` для ONNX candidate;
- `GENRE_PROVIDER=onnx_musicnn` for the ONNX candidate service;
- external artifacts mount from `/opt/music-tools-artifacts/genre-classifier/onnx`.

Port conflict risk is low:

- legacy service uses host port `8021`;
- ONNX candidate service uses host port `8022`;
- container ports are both `8021`, but they are isolated by different host binds
  and different container names.

### 3. Recommended candidate URL

For a smoke container that shares the Docker network, the best candidate URL is:

`http://genre-classifier-onnx:8021/classify`

If an operator chooses to call the ONNX container from the host instead of from a
networked parser container, the host-mapped URL would be:

`http://localhost:8022/classify`

The recommended smoke path should prefer the internal Docker network URL because
it matches the real `tidal-parser -> genre-classifier` service boundary.

## Harness options

### Option A - recommended

- run the ONNX candidate service/profile on the alternate port;
- run a one-off `tidal-parser` smoke container with
  `AUDIO_CLASSIFIER_URL=http://genre-classifier-onnx:8021/classify`;
- keep the production `tidal-parser` container untouched;
- keep the legacy classifier service running as the stable baseline.

Why this is preferred:

- no production mutation;
- no default switch;
- no code change required;
- the smoke follows the real parser-flow boundary;
- legacy and ONNX can coexist for comparison.

### Option B - not preferred

- temporarily set `AUDIO_CLASSIFIER_URL` on the existing production
  `tidal-parser` container;
- restart that container only for smoke.

Why this is riskier:

- mutates the production container environment;
- increases the chance of accidental baseline drift;
- requires recovery steps after the smoke.

### Option C - conditional fallback

- use a tiny wrapper harness that injects `AUDIO_CLASSIFIER_URL` before
  starting or importing `tidal-parser`;
- only use this if a safe one-off parser wrapper already exists and can reuse the
  current code path without app changes.

This is a valid design fallback, but Option A is cleaner because the override is
explicitly isolated from production runtime.

## Recommended harness

`one_off_tidal_parser_with_classifier_url_override`

Reason:

- it uses the existing env-driven URL override path;
- it does not require a default provider switch;
- it does not require `tidal-parser` code change;
- it keeps the legacy service intact while targeting ONNX only for smoke;
- it maps directly to the future 4.101 execution step.

## Future 4.101 smoke criteria

The future smoke should succeed only if all of the following hold:

- `tidal-parser` returns a successful response through the ONNX candidate URL;
- `genre-classifier` logs show `provider_name=onnx_musicnn`;
- no user-facing `Reference ID` error is returned;
- response shape remains preserved;
- full parser-flow completes without 5xx;
- legacy baseline remains unchanged after the smoke;
- the ONNX candidate remains a candidate, not the default.

## Guardrails

- Do not switch the default provider.
- Do not mutate production `tidal-parser` environment unless explicitly approved.
- Do not change `docker-compose.yml` unless a later roadmap slice needs it.
- Do not change `requirements.txt`.
- Do not touch ONNX artifacts.
- Do not combine harness design with a default switch.
- Do not run smoke in this step.

## Decision

The safest future smoke path is:

`legacy baseline remains untouched -> start ONNX candidate on profile/alternate port
-> run one-off parser container with explicit AUDIO_CLASSIFIER_URL override ->
collect logs and response -> restore baseline unchanged`

