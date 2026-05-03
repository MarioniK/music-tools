# Roadmap 4.2 — Offline lightweight candidate evaluation harness design

## Status

- proposed design / documentation-only safe-slice
- scope: non-production-facing

## Goals

- design an offline evaluation harness for lightweight classifier candidates
- define the evaluation manifest structure
- define fixture categories
- define baseline output capture
- define candidate output capture
- define comparison rules
- define resource metrics
- define report format
- define warnings and failures
- define approval gates before any production-facing work

## Non-goals

- no production code changes
- no provider implementation
- no runtime changes
- no dependency changes
- no Dockerfile changes
- no Docker Compose changes
- no default-provider switch
- no `/classify` contract changes
- no response shape changes
- no shadow execution
- no canary rollout
- no LLM cutover
- no `tidal-parser` changes
- no tag work
- no release work

## Baseline

`legacy_musicnn` is the only production baseline for Roadmap 4 evaluation.

All lightweight candidates must be evaluated against captured `legacy_musicnn` outputs before any provider implementation, shadow execution, canary rollout, or production migration is considered. Candidate results should be treated as research evidence only until explicit approval gates are passed.

Current production response fields remain unchanged:

- `ok`
- `message`
- `genres`
- `genres_pretty`

## Proposed offline evaluation harness design

The future harness should run outside the production request path. It should execute a fixed manifest of local fixtures, capture `legacy_musicnn` baseline results, capture candidate results under the same fixture set, normalize both outputs into a shared comparison model, and produce a markdown report plus machine-readable artifacts.

The harness design has these parts:

- evaluation manifest: a versioned YAML or JSON file describing fixture identity, file location, category, provenance, duration, tags, and expected quality notes
- fixture categories: a balanced set of representative, ambiguous, adjacent, hybrid, production-relevant, and negative/edge samples
- baseline output capture: a reproducible artifact for `legacy_musicnn` outputs and metrics
- candidate output capture: a parallel artifact for each candidate family, model, and runtime
- normalized comparison model: a provider-neutral comparison layer for normalized genres, vocabulary compatibility, top-N overlap, failures, warnings, and resource deltas
- report format: a markdown summary for human review and approval decisions
- resource metrics: latency, p95 latency, startup/import time, peak memory, model size, dependency/runtime weight, and image-size impact where applicable
- failure/warning handling: explicit warning categories that make incomplete or risky evidence visible
- known gaps format: a required section for missing coverage, missing metrics, licensing uncertainty, or unresolved candidate risks

The design should preserve `legacy_musicnn` as the default provider throughout Roadmap 4 evaluation. Offline evidence may support a later spike, but it must not imply production adoption.

## Manifest structure

The future manifest should be versioned and stored as YAML or JSON. It should be stable enough to rerun baseline and candidate comparisons across commits.

Example conceptual shape:

```yaml
schema_version: "1"
manifest_id: "roadmap_4_lightweight_eval_v1"
baseline_provider: "legacy_musicnn"
fixtures:
  - id: "fixture_clear_rock_001"
    path: "evaluation/fixtures/lightweight/clear_rock_001.wav"
    category: "clear_mainstream_genres"
    duration_seconds: 30.0
    source_type: "local_fixture"
    licensing:
      status: "known"
      provenance: "internal test fixture"
      notes: "approved for local offline evaluation"
    tags:
      - "rock"
      - "mainstream"
      - "clean_mix"
    expected_quality_notes: "Should produce a stable broad rock-family genre."
```

Required manifest fields:

- `schema_version`
- `manifest_id`
- `baseline_provider`
- `fixtures`
- fixture `id`
- fixture `path`
- fixture `category`
- fixture `duration_seconds`
- fixture `source_type`
- fixture licensing/provenance
- fixture `tags`
- fixture `expected_quality_notes`

The manifest should avoid embedding model-specific expectations. Expected notes should describe evaluation intent, not force a candidate to mimic one exact label when the audio is genuinely ambiguous.

## Fixture categories

The first manifest should cover these categories:

- clear mainstream genres: audio with obvious broad labels such as rock, pop, hip-hop, electronic, jazz, or classical
- adjacent / overlapping genres: audio where nearby genres may reasonably compete, such as indie rock versus alternative rock or house versus techno
- hybrid material: audio that intentionally combines multiple genre signals
- ambiguous / low-confidence audio: short, noisy, sparse, or stylistically unclear samples where low confidence or broad output may be acceptable
- production-relevant samples: representative samples from realistic user workflows, with licensing and provenance suitable for local evaluation
- negative / edge fixtures: empty files, unreadable files, unsupported formats, very short files, silence, corrupted files, or non-audio inputs

Fixture coverage should be reviewed before each evaluation phase. A candidate should not pass a gate based only on easy mainstream samples.

## Baseline output format

The baseline artifact should capture `legacy_musicnn` output for every fixture in the manifest.

Required baseline artifact fields:

- `schema_version`
- `run_id`
- `provider`
- runtime metadata
- `fixture_results`
- fixture result `ok`
- fixture result `message`
- fixture result `genres`
- fixture result `genres_pretty`
- fixture result `normalized_genres`
- fixture result `warnings`
- fixture result `metrics`

Example conceptual shape:

```json
{
  "schema_version": "1",
  "run_id": "baseline_2026_roadmap_4_eval_v1",
  "provider": "legacy_musicnn",
  "runtime": {
    "python": "3.12.13",
    "tensorflow": "2.21.0",
    "essentia_tensorflow": "2.1b6.dev1389"
  },
  "fixture_results": [
    {
      "fixture_id": "fixture_clear_rock_001",
      "ok": true,
      "message": "ok",
      "genres": ["rock"],
      "genres_pretty": "Rock",
      "normalized_genres": ["rock"],
      "warnings": [],
      "metrics": {
        "latency_ms": 420.0,
        "peak_memory_mb": 512.0
      }
    }
  ]
}
```

The baseline artifact should be immutable evidence for a specific manifest, code revision, and runtime identity.

## Candidate output format

Each candidate artifact should mirror the baseline artifact and add candidate-specific model metadata.

Required candidate artifact fields:

- `schema_version`
- `run_id`
- `provider`
- `candidate_family`
- model name/version/source/license
- `fixture_results`
- fixture result `ok`
- fixture result `message`
- fixture result `genres`
- fixture result `genres_pretty`
- fixture result `normalized_genres`
- fixture result `warnings`
- fixture result `metrics`

Example conceptual shape:

```json
{
  "schema_version": "1",
  "run_id": "candidate_onnx_audio_2026_roadmap_4_eval_v1",
  "provider": "offline_onnx_candidate",
  "candidate_family": "ONNX Runtime audio classifier",
  "model": {
    "name": "example-audio-tagging-model",
    "version": "research-only",
    "source": "model registry or local path",
    "license": "to be verified"
  },
  "fixture_results": [
    {
      "fixture_id": "fixture_clear_rock_001",
      "ok": true,
      "message": "ok",
      "genres": ["rock"],
      "genres_pretty": "Rock",
      "normalized_genres": ["rock"],
      "warnings": [],
      "metrics": {
        "latency_ms": 85.0,
        "peak_memory_mb": 180.0
      }
    }
  ]
}
```

Candidate artifacts must not be interpreted as production readiness on their own. They are inputs to comparison and approval gates.

## Normalized comparison model

The comparison layer should compare baseline and candidate outputs after applying the same normalized genre vocabulary rules.

Required comparison dimensions:

- normalized genre comparison: compare normalized provider outputs, not only display strings
- controlled vocabulary hit rate: measure the percentage of candidate output terms that map to the supported genre vocabulary
- OOV rate: measure out-of-vocabulary terms and report examples
- top-1 match: compare the candidate's top normalized genre with the baseline top normalized genre where ordering exists
- top-3/top-5 overlap: measure overlap between baseline and candidate top-N normalized genres where ranked outputs are available
- empty output detection: flag successful calls that return no usable genres
- major genre shift detection: flag broad-family changes such as electronic to classical or hip-hop to metal
- failure comparison: distinguish shared failures from candidate-only failures and baseline-only failures
- resource delta: compare candidate latency, p95 latency, startup/import time, peak memory, model size, dependency/runtime weight, and image-size impact where applicable

The model should separate quality disagreement from operational improvement. A candidate that is smaller and faster but frequently shifts major genre families should not pass provider or production gates.

## Report format

The future markdown report should be human-readable and suitable for review before approval decisions.

Required report sections:

- summary
- scope
- baseline provider
- candidate provider
- manifest
- fixture coverage
- aggregate comparison
- controlled vocabulary results
- OOV results
- top-N overlap
- resource metrics
- failures and warnings
- known gaps
- decision
- approval gate status
- appendix with per-fixture results

The decision section should use explicit language such as `do not proceed`, `approved for offline spike only`, `approved for provider implementation planning`, or `blocked pending missing evidence`. It should not imply canary rollout or default-provider switch unless those gates are separately approved.

## Resource metrics

Resource metrics should be captured per fixture when practical and aggregated at run level.

Required metrics:

- latency
- p95 latency
- startup/import time
- peak memory
- model size
- dependency/runtime weight
- Docker image size impact if applicable
- cold/warm execution distinction if applicable

Cold execution should include process startup, imports, model load, and first inference where applicable. Warm execution should measure repeated inference after the model is loaded. If a metric cannot be captured, the report must include `runtime_metric_missing`.

## Failure and warning handling

The harness should preserve failures and warnings as first-class evidence rather than hiding them in logs.

Required warning categories:

- `fixture_missing`
- `fixture_unreadable`
- `baseline_failed`
- `candidate_failed`
- `empty_output`
- `oov_terms_detected`
- `major_genre_shift`
- `license_unknown`
- `model_provenance_unknown`
- `runtime_metric_missing`
- `comparison_incomplete`

Failures should be classified by fixture and aggregated in the report. A report with `comparison_incomplete`, unknown licensing, or missing model provenance should not pass beyond offline research gates.

## Known gaps format

Each report should include a known gaps section with explicit bullets for:

- missing fixture coverage
- missing or unreliable runtime metrics
- unresolved licensing or provenance questions
- unsupported candidate model behavior
- incomplete normalization or vocabulary mapping
- quality concerns by fixture category
- resource regressions that need a follow-up measurement

Known gaps must be carried forward until closed or explicitly accepted at an approval gate.

## First candidate families for future offline spike

Roadmap 4.2 recommends only two first candidate families for a future offline spike. This document does not implement either candidate.

Recommended first candidates:

- ONNX Runtime audio classifier
- small audio tagging model

ONNX Runtime is a good first candidate because it may reduce dependency weight compared with the current TensorFlow/Essentia path, has a portable model format, and can be measured clearly for startup, inference latency, memory, and model packaging cost. Risks to check include model availability, conversion quality, unsupported operators, runtime package size, licensing, and whether genre outputs can be mapped cleanly into the controlled vocabulary.

A small audio tagging model is a good first candidate because it may preserve audio-specific signal while reducing model size and runtime footprint. Risks to check include tag-to-genre mismatch, OOV output, inconsistent model provenance, license compatibility, uneven quality across fixture categories, and whether the model is truly lighter once dependencies are included.

The LLM provider foundation from earlier roadmap work remains research-only. It is not an automatic Roadmap 4 production target and should not be treated as the default lightweight migration path without a separate approval process covering quality, latency, cost, privacy, determinism, and rollback.

## Approval gates

Offline spike implementation:

- requires approval of the manifest shape, fixture categories, report format, and evidence storage approach
- must remain offline and non-production-facing

Provider implementation:

- requires completed offline comparison evidence for at least one candidate family
- requires explicit approval before adding implementation code or dependencies
- must preserve the existing `/classify` contract and response shape

Shadow execution:

- requires explicit approval after offline evidence review
- requires an observation plan, resource limits, warning thresholds, and rollback criteria
- must keep runtime shadow disabled by default unless separately approved

Canary rollout:

- requires explicit approval after shadow evidence review
- requires traffic scope, monitoring, rollback criteria, and success/failure thresholds

Default provider switch:

- requires explicit approval before changing the default provider away from `legacy_musicnn`
- requires contract preservation evidence, quality evidence, resource evidence, and rollback notes

Production migration:

- requires explicit approval after canary evidence review
- requires operational readiness, documentation updates, release planning, and rollback planning

LLM adoption:

- requires a separate explicit approval path
- requires review of cost, latency, privacy, reliability, determinism, output quality, and rollback behavior
- must not be assumed from Roadmap 4 lightweight classifier evaluation alone

## Rollback considerations

Roadmap 4.2 is documentation-only. Rollback is file removal or commit revert for this artifact:

```text
docs/lightweight/roadmap-4.2-offline-evaluation-harness-design.md
```

No runtime rollback is required. There is no cache migration, dependency rollback, Docker rollback, provider rollback, or production traffic rollback for this safe-slice.
