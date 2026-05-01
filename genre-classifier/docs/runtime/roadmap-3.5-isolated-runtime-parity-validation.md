# Roadmap 3.5 — Isolated runtime parity validation

## 1. Goal

Compare the current production `genre-classifier` runtime with the Roadmap 3.4 experimental candidate in isolated containers.

- production baseline image: built from the current production `genre-classifier/Dockerfile`
- candidate image: `music-tools-genre-classifier-roadmap-3.4:py312-etf`

Passing this stage only means the Python 3.12 + `essentia-tensorflow` candidate may proceed to Roadmap 3.6 deeper migration planning.

## 2. Scope

- `genre-classifier` only
- docs
- validation scripts
- comparison scripts
- evidence artifacts
- decision artifact for Roadmap 3.5

## 3. Non-goals

- No `tidal-parser` changes.
- No production `Dockerfile` change.
- No production `docker-compose.yml` change.
- No `requirements.txt` change.
- No app code change.
- No production Python/runtime upgrade.
- No provider default change.
- No `/classify` contract change.
- No response shape change.
- No runtime shadow enablement by default.
- No provider switch.
- No canary rollout.
- No LLM cutover.
- No LLM production adoption.
- No commit, tag, or push.

## 4. Roadmap 3.4 findings summary

Roadmap 3.4 found that Python 3.12 + `essentia-tensorflow` passed the primary compatibility smoke chain:

- Docker build passed.
- Dependency resolution passed.
- TensorFlow import passed.
- Essentia import passed.
- `TensorflowPredictMusiCNN` was available.
- App imports passed.
- MusiCNN `.pb` model discovery and loading passed.
- ffmpeg smoke passed.
- API startup passed.
- `/health` passed.
- `/classify` returned the expected legacy response shape on `app/tmp/upload.mp3`.
- Default provider remained `legacy_musicnn`.
- Runtime shadow remained disabled by default.

Roadmap 3.4 did not compare production runtime and candidate runtime side by side, and did not approve production migration.

## 5. Production baseline runtime

Baseline runtime identity: current production `genre-classifier` Dockerfile/runtime.

Planned validation command shape:

```sh
docker build \
  -t music-tools-genre-classifier-roadmap-3.5:baseline \
  .

docker rm -f genre-classifier-roadmap-3.5-baseline 2>/dev/null || true

docker run -d \
  --name genre-classifier-roadmap-3.5-baseline \
  -p 8021:8021 \
  music-tools-genre-classifier-roadmap-3.5:baseline
```

Actual Roadmap 3.5 validation port mapping was adjusted because host port `8021` was already occupied by an existing `genre-classifier` container:

- host port: `8321`
- container port: `8021`
- effective base URL: `http://127.0.0.1:8321`

The production Dockerfile was not changed.

## 6. Candidate runtime

Candidate runtime identity: Python 3.12 + `essentia-tensorflow` image from Roadmap 3.4.

Planned validation command shape:

```sh
docker rm -f genre-classifier-roadmap-3.5-py312-etf 2>/dev/null || true

docker run -d \
  --name genre-classifier-roadmap-3.5-py312-etf \
  -p 8121:8021 \
  music-tools-genre-classifier-roadmap-3.4:py312-etf
```

Actual Roadmap 3.5 validation port mapping was adjusted because host port `8021` was already occupied by an existing `genre-classifier` container:

- host port: `8421`
- container port: `8021`
- effective base URL: `http://127.0.0.1:8421`

The candidate image was used only as an isolated validation runtime.

## 7. Residual dependency risks

Known residual risks inherited from Roadmap 3.4:

- TensorFlow resolved to `2.21.0`; production uses TensorFlow `1.15.0`.
- numpy resolved to `2.4.4`; production uses numpy `1.19.5`.
- protobuf resolved to `7.34.1`; production uses protobuf `3.11.3`.
- h5py resolved to `3.14.0`; production uses h5py `2.10.0`.
- Candidate base OS is Debian bookworm via Python 3.12 slim; production baseline is Ubuntu 18.04.3 LTS through `mtgupf/essentia-tensorflow:latest`.
- The validated fixture set remains small and local-only.
- Roadmap 3.5 short repeated smoke does not prove long-running stability, concurrency behavior, or production readiness.
- Dependency pinning and reproducible candidate image strategy remain Roadmap 3.6 work.

## 8. Fixture strategy

Primary valid fixture:

- `app/tmp/upload.mp3`

Optional local-only valid fixtures found during inventory:

- `app/tmp/normalized.wav`
- `app/tmp/tmpafc28hj_.mp3`
- `app/tmp/tmpcip33cuv.wav`

Malformed / unsupported local-only fixtures:

```sh
mkdir -p /tmp/roadmap-3.5-fixtures
: > /tmp/roadmap-3.5-fixtures/empty.mp3
printf 'this is not an mp3 file\n' > /tmp/roadmap-3.5-fixtures/fake.mp3
printf 'plain text unsupported upload\n' > /tmp/roadmap-3.5-fixtures/unsupported.txt
```

Fixture details are recorded in `docs/runtime/evidence/roadmap-3.5/fixture-manifest.md`.

## 9. Validation methodology

All commands were run from `/opt/music-tools/genre-classifier`.

The originally documented host ports `8021` and `8121` were adjusted during execution because host port `8021` was already occupied by an existing `genre-classifier` container. The actual isolated runtime base URLs were:

- baseline: `http://127.0.0.1:8321`
- candidate: `http://127.0.0.1:8421`

Executed validation flow:

1. Built and started the baseline runtime.
2. Captured baseline `/health`.
3. Captured baseline `/classify` for `app/tmp/upload.mp3`.
4. Captured 10 repeated baseline `/classify` responses for the same fixture.
5. Captured baseline malformed/unsupported upload responses.
6. Captured baseline latency evidence from curl `TIME_TOTAL`.
7. Captured baseline memory evidence with `docker stats --no-stream`.
8. Captured baseline logs with `docker logs --tail 300`.
9. Started the candidate runtime.
10. Repeated the same checks for the candidate.
11. Compared saved outputs with `scripts/runtime_validation/compare_classify_outputs.py`.
12. Recorded final observations and decision in this artifact.

Evidence paths:

- baseline: `docs/runtime/evidence/roadmap-3.5/baseline/`
- candidate: `docs/runtime/evidence/roadmap-3.5/candidate-py312-etf/`
- comparison: `docs/runtime/evidence/roadmap-3.5/comparison/classify-comparison.md`

## 10. Comparison matrix

Status after execution: **Roadmap 3.5 isolated runtime parity validation passed for deeper migration planning**.

| Area | Baseline evidence | Candidate evidence | Result |
|---|---|---|---|
| Container startup | Uvicorn startup complete; listening on `0.0.0.0:8021` | Uvicorn startup complete; listening on `0.0.0.0:8021` | Pass |
| `/health` | HTTP `200` | HTTP `200` | Pass |
| Valid `/classify` | HTTP `200`, valid JSON | HTTP `200`, valid JSON | Pass |
| HTTP status parity | `200` | `200` | Pass |
| Response shape parity | `ok`, `message`, `genres`, `genres_pretty` | `ok`, `message`, `genres`, `genres_pretty` | Pass |
| Top-N genre overlap | 8 genres | 8 genres | Pass, `8/8` |
| Score comparison | baseline scores captured | candidate scores captured | Pass; minimal drift only |
| Repeated request stability | 10 repeated requests captured; HTTP `200` | 10 repeated requests captured; HTTP `200` | Pass for short smoke |
| Malformed upload behavior | HTTP `400`; process stayed alive | HTTP `400`; process stayed alive | Pass |
| Memory | `680.4MiB / 4GiB`, `16.61%`, PIDS `139` | `461.6MiB / 4GiB`, `11.27%`, PIDS `9` | Pass for short smoke |
| Logs | startup complete; CPU/GPU warnings; fake upload ffmpeg error | startup complete; CPU/GPU warnings; fake upload ffmpeg error | Pass; no startup blocker or crash observed |

## 11. Response shape parity evidence

Expected legacy success response shape:

- top-level `ok`
- top-level `message`
- top-level `genres`
- top-level `genres_pretty`
- each `genres` item contains `tag`
- each `genres` item contains `prob`
- `genres_pretty` is a list

Primary fixture result for `app/tmp/upload.mp3`:

| Runtime | HTTP status | JSON parseability | Top-level keys | Shape issues |
|---|---:|---|---|---|
| baseline | `200` | pass | `ok`, `message`, `genres`, `genres_pretty` | none |
| candidate | `200` | pass | `ok`, `message`, `genres`, `genres_pretty` | none |

Conclusion: **response shape parity passed** for the valid primary fixture. Legacy success response keys did not disappear.

Malformed and `/health` responses intentionally do not use the success `/classify` shape; the comparison report lists missing success keys for those non-success responses, but they are not Roadmap 3.5 response-shape blockers.

## 12. Top-N genre comparison

Primary fixture: `app/tmp/upload.mp3`.

Baseline genres:

| Rank | Genre | Score |
|---:|---|---:|
| 1 | `electronic` | `0.3894` |
| 2 | `indie` | `0.3884` |
| 3 | `rock` | `0.1950` |
| 4 | `indie rock` | `0.1836` |
| 5 | `alternative` | `0.1556` |
| 6 | `electro` | `0.1237` |
| 7 | `pop` | `0.1012` |
| 8 | `electronica` | `0.0754` |

Candidate genres:

| Rank | Genre | Score |
|---:|---|---:|
| 1 | `electronic` | `0.3894` |
| 2 | `indie` | `0.3884` |
| 3 | `rock` | `0.1951` |
| 4 | `indie rock` | `0.1836` |
| 5 | `alternative` | `0.1557` |
| 6 | `electro` | `0.1237` |
| 7 | `pop` | `0.1012` |
| 8 | `electronica` | `0.0754` |

Comparison result:

- genres length: `8` vs `8`
- genre sequence: exact match
- top-1: exact match, `electronic`
- top-N overlap: `8/8`
- `genres_pretty`: exact match

`genres_pretty` for both runtimes:

```text
indie rock
alternative rock
electronic
indie
rock
alternative
electro
pop
```

Conclusion: **top-N genre comparison passed** for the available primary fixture.

## 13. Score comparison

Primary fixture latency and score evidence:

| Runtime | HTTP status | TIME_TOTAL | Top-1 |
|---|---:|---:|---|
| baseline | `200` | `7.323479` | `electronic` |
| candidate | `200` | `6.559398` | `electronic` |

Observed score differences:

| Genre | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| `rock` | `0.1950` | `0.1951` | `+0.0001` |
| `alternative` | `0.1556` | `0.1557` | `+0.0001` |

All other listed scores were equal at the captured precision.

Conclusion: score drift was minimal and is **not a Roadmap 3.5 blocker**.

## 14. Performance evidence

Latency evidence was captured through curl `TIME_TOTAL`.

Primary valid fixture:

- baseline `upload.classify`: `7.323479s`
- candidate `upload.classify`: `6.559398s`

Malformed / unsupported uploads:

| Fixture | Baseline TIME_TOTAL | Candidate TIME_TOTAL |
|---|---:|---:|
| `empty.mp3` | `0.002545s` | `0.001995s` |
| `fake.mp3` | `0.168435s` | `0.083204s` |
| `unsupported.txt` | `0.003325s` | `0.001682s` |

Repeated request samples visible in comparison were approximately:

- baseline repeated upload requests: `6.51s` to `7.52s`
- candidate repeated upload requests: `5.86s` to `6.31s`

Conclusion: no unacceptable latency degradation was observed in the short Roadmap 3.5 smoke. This is not long-running performance proof.

## 15. Memory evidence

Memory evidence from `docker stats --no-stream`:

| Runtime | Memory usage / limit | Memory % | PIDS |
|---|---:|---:|---:|
| baseline | `680.4MiB / 4GiB` | `16.61%` | `139` |
| candidate | `461.6MiB / 4GiB` | `11.27%` | `9` |

Conclusion: no short-smoke memory blocker was observed. This does not prove long-running memory stability.

## 16. Repeated request stability

Ten repeated `/classify` requests were captured for both baseline and candidate using `app/tmp/upload.mp3`.

Observed repeated request behavior:

- HTTP status remained `200` for repeated upload requests.
- JSON parseability remained pass.
- response shape remained stable.
- top-1 remained `electronic`.
- genre sequence remained stable.
- top-N overlap remained `8/8`.
- candidate repeated latency samples visible in comparison were around `5.86s` to `6.31s`.
- baseline repeated latency samples visible in comparison were around `6.51s` to `7.52s`.

Conclusion: repeated request stability passed for a short Roadmap 3.5 smoke only. This is not long-running stability proof.

## 17. Malformed/unsupported upload evidence

Required local-only malformed/unsupported fixtures:

- `/tmp/roadmap-3.5-fixtures/empty.mp3`
- `/tmp/roadmap-3.5-fixtures/fake.mp3`
- `/tmp/roadmap-3.5-fixtures/unsupported.txt`

Baseline results:

| Fixture | HTTP status | TIME_TOTAL | Response behavior |
|---|---:|---:|---|
| `empty.mp3` | `400` | `0.002545` | `{"ok":false,"error":"Файл пустой"}` |
| `fake.mp3` | `400` | `0.168435` | ffmpeg processing error returned; process stayed alive |
| `unsupported.txt` | `400` | `0.003325` | `{"ok":false,"error":"Неподдерживаемый формат файла"}` |

Candidate results:

| Fixture | HTTP status | TIME_TOTAL | Response behavior |
|---|---:|---:|---|
| `empty.mp3` | `400` | `0.001995` | `{"ok":false,"error":"Файл пустой"}` |
| `fake.mp3` | `400` | `0.083204` | ffmpeg processing error returned; process stayed alive |
| `unsupported.txt` | `400` | `0.001682` | `{"ok":false,"error":"Неподдерживаемый формат файла"}` |

`fake.mp3` returns detailed ffmpeg stderr in both runtimes. This is existing behavior and not a Roadmap 3.5 parity blocker. Future hardening may sanitize ffmpeg errors, but Roadmap 3.5 intentionally made no app behavior change.

Conclusion: malformed/unsupported upload behavior passed parity smoke and did not crash either process.

## 18. Logs review

Reviewed:

- `docs/runtime/evidence/roadmap-3.5/baseline/docker-logs-tail-300.txt`
- `docs/runtime/evidence/roadmap-3.5/candidate-py312-etf/docker-logs-tail-300.txt`

Observed:

- both runtimes reached Uvicorn `Application startup complete`;
- both runtimes listened on `0.0.0.0:8021` inside the container;
- TensorFlow CUDA/GPU related warnings were present in the CPU-only environment;
- both runtimes logged an ffmpeg processing error for `fake.mp3`;
- no startup blocker was observed in captured logs;
- no process crash after malformed uploads was observed in captured logs.

Conclusion: logs review found no Roadmap 3.5 blocker. This summary is limited to the captured `docker logs --tail 300` files.

## 19. Blockers

Roadmap 3.5 blocker criteria:

- app import failure
- API startup failure
- `TensorflowPredictMusiCNN` unavailable
- model load failure
- `/classify` fails on valid fixture
- incompatible response shape difference
- legacy response keys disappear
- provider default changes
- runtime shadow enabled by default
- invalid upload crashes the process
- repeated requests produce unstable output without explanation
- memory grows sharply during short repeated smoke
- latency degrades unacceptably
- logs show TensorFlow/Essentia runtime errors

Current blockers: **none observed in the captured Roadmap 3.5 evidence**.

Residual limitations:

- fixture coverage is limited to the available primary fixture plus malformed upload smoke;
- repeated request evidence is short smoke only;
- concurrency and long-running stability were not proven;
- production dependency pinning and rollout mechanics were not evaluated.

## 20. Decision

Decision: **pass_for_deeper_migration_planning**.

Python 3.12 + `essentia-tensorflow` candidate passed isolated parity validation on the available primary fixture and malformed upload smoke. Candidate may proceed to Roadmap 3.6 deeper migration planning.

This decision does not approve:

- production runtime migration
- production Dockerfile replacement
- production compose replacement
- production requirements replacement
- provider switch
- canary rollout
- LLM cutover
- LLM production adoption

Allowed Roadmap 3.5 pass meaning:

- Python 3.12 + `essentia-tensorflow` candidate may proceed to Roadmap 3.6 deeper migration planning.

## 21. Recommendation for Roadmap 3.6

Proceed to deeper migration planning with explicit approval gates before touching production runtime files.

Recommended Roadmap 3.6 scope:

- broader curated fixture corpus;
- pinned dependency strategy;
- reproducible candidate image;
- explicit production Dockerfile proposal;
- rollback image strategy;
- startup and memory budget;
- longer stability and concurrency validation;
- decision gate before touching production runtime files.

Roadmap 3.6 should continue to treat provider switch, canary rollout, LLM cutover, and LLM production adoption as out of scope unless separately approved.

## 22. Rollback considerations

Roadmap 3.5 does not modify production runtime files. Rollback is to stop and remove the isolated validation containers:

```sh
docker rm -f genre-classifier-roadmap-3.5-baseline 2>/dev/null || true
docker rm -f genre-classifier-roadmap-3.5-py312-etf 2>/dev/null || true
```

Do not reference `music-tools-genre-classifier-roadmap-3.4:py312-etf` from production compose during Roadmap 3.5.
