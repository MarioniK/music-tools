# Roadmap 4.92 - legacy vs ONNX slim direct benchmark

Статус: local-only direct benchmark, не production decision.

## Контекст

- Использован shared fixture `/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3`.
- Docker build не запускался явно; использовались one-off `docker compose run` запуски.
- Docker Compose `up` не запускался.
- `/classify` не вызывался.
- Network HTTP smoke не запускался.
- Default provider не менялся.

## Команды benchmark

```bash
cd /opt/music-tools/genre-classifier
python3 docs/lightweight/evaluation/parity-scaffold/legacy_vs_onnx_slim_direct_benchmark.py \
  --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3 \
  --runs 3 \
  --output docs/lightweight/evaluation/parity-scaffold/legacy-vs-onnx-slim-direct-benchmark-report.json \
  --markdown-output docs/lightweight/roadmap-4.92-legacy-vs-onnx-slim-direct-benchmark.md
```

### Legacy container run

```bash
docker compose run --rm --no-deps genre-classifier python3 /tmp/.../legacy_vs_onnx_slim_direct_benchmark.py --child-run --provider legacy --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3
```

### ONNX slim container run

```bash
docker compose --profile onnx run --rm --no-deps genre-classifier-onnx python3 /tmp/.../legacy_vs_onnx_slim_direct_benchmark.py --child-run --provider onnx --audio-path /tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3
```

## Legacy benchmark

- Available: `True`.
- Runs: `3`.
- `total_seconds`: 4.431046, 4.047481, 3.883374
- `preprocessing_seconds`: n/a, n/a, n/a
- `inference_seconds`: 2.605142, 2.406992, 2.362946
- `mapping_seconds`: 0.001192, 0.000366, 0.000411
- `max_rss_kb`: `630336`
- `genres`: electronic, dance, house, electronica, chillout, electro, pop, indie
- `genres_pretty`: electronic, dance, house, electronica, chillout, electro, pop, indie
- `response_compatible_shape`: `True`
- `repeated_run_stable`: `True`

## ONNX slim benchmark

- Available: `True`.
- Runs: `3`.
- `total_seconds`: 2.159099, 2.191430, 2.121862
- `preprocessing_seconds`: 0.601052, 0.650098, 0.579728
- `inference_seconds`: 0.055483, 0.052686, 0.051069
- `mapping_seconds`: 0.000210, 0.000259, 0.000203
- `max_rss_kb`: `295236`
- `genres`: electronic, rock, indie, pop, dance, alternative, progressive rock, electronica
- `genres_pretty`: indie rock, alternative rock, electronic, rock, indie, pop, dance, alternative
- `response_compatible_shape`: `True`
- `repeated_run_stable`: `True`

## Comparison

- `avg_total_seconds_legacy`: `4.120634`
- `avg_total_seconds_onnx_slim`: `2.157464`
- `speedup_ratio_legacy_div_onnx`: `1.909943`
- `memory_delta_kb`: `335100`
- `response_shape_match`: `True`
- `output_drift_documented`: `True`
- Drift note: Observed drift is controlled and reproducible.

## Decision signal

- `onnx_slim_runtime_functional`: `True`
- `legacy_comparison_completed`: `True`
- `performance_benefit_confirmed`: `True`
- Recommendation: ONNX slim path is faster or comparable and stays contract-compatible; keep it as an optional candidate, but this benchmark is not a production approval.

## Blockers / warnings

- Blockers: none
- Warnings: none

## Confirmations

- `AGENTS.md` read and followed.
- Legacy direct benchmark attempted.
- ONNX slim direct benchmark completed.
- No `docker compose up`.
- No server start.
- No `/classify` call.
- No network HTTP call.
- No production dependency changes.
- No Dockerfile changes.
- No Compose changes.
- No default provider changes.
- No response shape changes.
- No production readiness claim.
- No artifacts committed.
- `tidal-parser` untouched.
