# Roadmap 4.23 — legacy_musicnn current model identity and preprocessing inspection

## Status

Completed as a documentation-only static inspection. No commit hash is recorded here.

## Scope

This inspection is limited to `genre-classifier`. It is a documentation/code-inspection safe-slice that reviews the current implementation only.

No production behavior was changed. No production classifier code, provider implementation, provider factory, default provider, API contract, response shape, controlled vocabulary, cache/runtime behavior, dependencies, Dockerfile, Docker Compose, tests, validators, model artifacts, or audio artifacts were changed.

## Current production baseline

- The default provider remains `legacy_musicnn`.
- The production classifier path remains legacy MusiCNN.
- The `/classify` contract is unchanged.
- The successful `/classify` response shape remains `ok`, `message`, `genres`, `genres_pretty`.
- `tidal-parser` was untouched.

## Inspection method

Static read-only inspection was performed in `/opt/music-tools/genre-classifier` using searches and file reads only. The reviewed areas included:

- provider selection and provider classes under `app/providers/`;
- service orchestration and preprocessing under `app/services/`;
- configuration under `app/core/settings.py`;
- model metadata under `app/models/`;
- API response wiring under `app/api/routes.py`;
- genre normalization and compatibility mapping under `app/genre_normalization.py` and `app/providers/compat.py`;
- relevant tests under `tests/`;
- Dockerfile, Docker Compose, and requirements.

Search terms included `legacy_musicnn`, `musicnn`, `MusiCNN`, `essentia`, `TensorflowPredict`, `TensorflowInputMusiCNN`, `TensorflowPredictMusiCNN`, `genres_pretty`, `provider`, and `factory`.

No inference was run. No `/classify` call was made. No model was downloaded. No dependency, runtime, Dockerfile, or Docker Compose changes were performed.

## Provider identity

Verified code evidence:

- Factory path: `app/providers/factory.py`.
- Production provider resolution starts at `get_genre_provider(settings)`, which calls `settings.get_configured_genre_provider_name()` and then `get_genre_provider_by_name(provider_name, settings)`.
- `get_genre_provider_by_name()` returns:
  - `StubGenreProvider()` for `"stub"`;
  - `LegacyMusiCNNProvider()` when `provider_name == settings.GENRE_PROVIDER_LEGACY`;
  - `LlmGenreProvider()` when `provider_name == settings.GENRE_PROVIDER_LLM`;
  - `ValueError` for unknown provider names.
- Default provider configuration is in `app/core/settings.py`:
  - `GENRE_PROVIDER_LEGACY = "legacy_musicnn"`;
  - `GENRE_PROVIDER_LLM = "llm"`;
  - `DEFAULT_GENRE_PROVIDER = "legacy_musicnn"`;
  - `get_configured_genre_provider_name()` reads `GENRE_PROVIDER` and falls back to `DEFAULT_GENRE_PROVIDER` for missing or blank values.
- Legacy provider implementation path: `app/providers/legacy_musicnn.py`.
- Legacy provider class: `LegacyMusiCNNProvider`.
- Legacy provider classification method: `LegacyMusiCNNProvider.classify(audio_path)`.
- Legacy provider wrapper function: `_run_legacy_musicnn_classification(audio_path)`.
- The wrapper imports `run_genre_classification` from `app.services.classify` lazily inside the function and returns its result.
- `LegacyMusiCNNProvider.classify()` maps legacy dictionaries with `tag` and `prob` into `ProviderGenreScore(tag=item["tag"], score=float(item["prob"]))`, then returns a `ProviderResult` with `provider_name="legacy_musicnn"` and `model_name=settings.MODEL_PB.stem`.
- Tests in `tests/test_settings.py` verify default provider resolution to `legacy_musicnn`.
- Tests in `tests/test_provider_factory.py` verify factory selection of `LegacyMusiCNNProvider` for `legacy_musicnn` and verify legacy provider result shape/model name mapping.

Open gaps:

- The factory does not log legacy provider selection, so provider identity evidence is code/test based rather than runtime log based in this inspection.
- The legacy provider is not a fully isolated implementation; it delegates to `app.services.classify.run_genre_classification()`.

## Model artifact / metadata identity

Verified code evidence:

- Model directory setting: `MODELS_DIR = BASE_DIR / "models"` in `app/core/settings.py`.
- Current model path setting: `MODEL_PB = MODELS_DIR / "msd-musicnn-1.pb"`.
- Current metadata path setting: `MODEL_JSON = MODELS_DIR / "msd-musicnn-1.json"`.
- Bundled files are present in the repository under:
  - `app/models/msd-musicnn-1.pb`;
  - `app/models/msd-musicnn-1.json`.
- `ls -l app/models` showed `msd-musicnn-1.pb` at 3,197,999 bytes and `msd-musicnn-1.json` at 3,298 bytes.
- Dockerfile copies `app` into the image with `COPY app /app/app`, so the bundled model files are included in image builds through the application tree.
- `docker-compose.yml` mounts `./app/models:/app/app/models`, so Compose runtime also expects models from the local `app/models` directory.
- There is no inspected project code path that downloads these files at runtime.
- Requirements include `tensorflow==2.21.0` and `essentia-tensorflow==2.1b6.dev1389`; no `onnxruntime` dependency is present.
- Metadata file `app/models/msd-musicnn-1.json` declares:
  - `"name": "MSD MusiCNN"`;
  - `"type": "auto-tagging"`;
  - `"link": "https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.pb"`;
  - `"version": "1"`;
  - `"framework": "tensorflow"`;
  - `"framework_version": "1.15.0"`;
  - `"model_types": ["frozen_model"]`;
  - dataset name `"The Millon Song Dataset"` as written in the metadata;
  - 50 `classes`;
  - inference sample rate `16000`;
  - inference algorithm `TensorflowPredictMusiCNN`.
- Label source is `metadata.get("classes")` from `app/models/msd-musicnn-1.json`.
- Label order source is the JSON `classes` array order, zipped directly with `mean_scores`.

Comparison caution:

- The current code and bundled metadata strongly identify the production TensorFlow frozen model path as `msd-musicnn-1.pb` with matching `msd-musicnn-1.json` metadata.
- This inspection does not prove byte-level or numeric parity between the bundled `msd-musicnn-1.pb` and the official `msd-musicnn-1.onnx` artifact.
- This inspection does not compare PB and ONNX graph outputs.
- Therefore, current legacy_musicnn must not be claimed to be production-parity equivalent to official `msd-musicnn-1.onnx` based on this document alone.

## Preprocessing path

Verified code evidence:

- Upload orchestration lives in `app/services/classify.py`.
- `process_uploaded_audio()` writes the uploaded bytes to a temporary file under `settings.TMP_DIR`, creates a temporary `.wav`, calls `normalize_audio_file(upload_path, wav_path)`, then classifies the normalized WAV through the selected provider.
- `normalize_audio_file()` runs `ffmpeg` as:
  - `ffmpeg -y -i <input> -ac 1 -ar 16000 <output.wav>`.
- This produces mono audio at 16 kHz before provider classification.
- `app/services/classify.py` imports `MonoLoader` and `TensorflowPredictMusiCNN` from `essentia.standard` at module import time.
- `run_genre_classification(wav_path)` checks that `settings.MODEL_PB` and `settings.MODEL_JSON` exist.
- `run_genre_classification(wav_path)` loads JSON metadata and reads `classes`.
- Raw model input audio is loaded with:
  - `MonoLoader(filename=str(wav_path), sampleRate=16000)()`.
- Inference is run with:
  - `TensorflowPredictMusiCNN(graphFilename=str(settings.MODEL_PB))(audio)`.
- Scores are aggregated with `np.mean(activations, axis=0)`.
- The inspected code does not use `TensorflowInputMusiCNN` directly.
- The inspected code does not import `TensorflowPredict` directly.
- The metadata declares schema input shape `[187, 96]`, output shape `[1, 50]`, output node `model/Sigmoid`, and inference algorithm `TensorflowPredictMusiCNN`.

Coupling assessment:

- Preprocessing and inference are coupled in `run_genre_classification()` through the Essentia `TensorflowPredictMusiCNN` algorithm.
- Audio decoding/resampling is also partly outside Essentia because uploaded files are first normalized by `ffmpeg` to mono 16 kHz WAV.
- Essentia remains needed for the current production path because `MonoLoader` and `TensorflowPredictMusiCNN` are imported by `app/services/classify.py`.
- A future ONNX Runtime spike could theoretically replace only the TensorFlow inference call, but static code evidence is not enough to prove that this is sufficient because `TensorflowPredictMusiCNN` likely encapsulates MusiCNN-specific input preparation before graph execution.
- Proving an isolated inference replacement would require explicit preprocessing equivalence evidence, especially around whatever feature extraction/input framing `TensorflowPredictMusiCNN` applies internally.

## Labels and output path

Verified code evidence:

- Label source: `classes` from `app/models/msd-musicnn-1.json`.
- Label order source: JSON `classes` order zipped with `mean_scores` in `run_genre_classification()`.
- Raw per-class scores are produced by averaging activations over axis 0 with `np.mean(activations, axis=0)`.
- Raw legacy result items are built as dictionaries:
  - `"tag": str(label).lower()`;
  - `"prob": round(float(score), 4)`.
- `run_genre_classification()` sorts raw pairs by descending `prob` and returns `pairs[:8]`.
- `LegacyMusiCNNProvider.classify()` converts those top 8 raw dictionaries to `ProviderGenreScore` values and returns `ProviderResult(provider_name="legacy_musicnn", model_name=settings.MODEL_PB.stem)`.
- `validate_and_normalize_provider_result(provider_result, top_n=8)`:
  - requires a `ProviderResult`;
  - accepts only `ProviderGenreScore` items;
  - normalizes tags by trimming, lowercasing, replacing hyphens/underscores with spaces, and collapsing whitespace;
  - drops empty tags and non-finite/non-numeric scores;
  - deduplicates by keeping the highest score per normalized tag;
  - sorts by descending score and then tag;
  - keeps top 8;
  - raises `RuntimeError("no valid provider genres")` if nothing valid remains.
- `map_validated_result_to_legacy_genres()` returns the public `genres` shape as `{"tag": item.tag, "prob": round(item.score, 4)}`.
- `map_validated_result_to_legacy_genres_pretty()` calls `normalize_audio_prediction_genres(raw_genres, min_prob=0.05)`.
- `normalize_audio_prediction_genres()`:
  - filters raw genres below `prob >= 0.05`;
  - normalizes tags from the filtered rows;
  - gives priority to compound tags such as `indie rock`, `experimental rock`, `jazz rock`, `alternative rock`, `instrumental rock`, and `electronic`;
  - then appends remaining normalized tags;
  - excludes non-genre descriptors listed in `NON_GENRE_DESCRIPTORS`, currently `female vocalists` and `male vocalists`;
  - returns at most 8 entries.
- `/classify` response is built in `app/api/routes.py` with `ok`, `message`, `genres`, and `genres_pretty` on success.

Threshold behavior:

- The model raw top 8 path does not apply a score threshold before selecting `genres`; it ranks by averaged activation score and truncates to 8.
- `genres_pretty` applies a compatibility threshold of `min_prob=0.05`.
- Validation applies top-N truncation but no minimum score threshold.

Controlled vocabulary and compatibility mapping:

- The legacy `genres_pretty` path uses `app/genre_normalization.py`, including non-genre descriptor filtering and compound-tag compatibility mapping.
- The canonical controlled vocabulary under `app/genres/vocabulary.py` is used by LLM postprocessing paths, not by the inspected legacy `genres_pretty` compatibility function.

## Comparison with official msd-musicnn-1 references

Roadmap 4.22 recorded official Essentia references:

- `msd-musicnn-1.onnx`;
- `msd-musicnn-1.pb`;
- `msd-musicnn-1.json`;
- source index: `https://essentia.upf.edu/models/feature-extractors/musicnn/`.

Static comparison only:

| Area | Static assessment | Evidence |
| --- | --- | --- |
| Model family | Compatible | Current metadata says `name` is `MSD MusiCNN`, links to the Essentia `feature-extractors/musicnn/msd-musicnn-1.pb` path, and uses `msd-musicnn-1.pb` / `msd-musicnn-1.json`. |
| PB artifact name | Compatible | Current settings and bundled files use `msd-musicnn-1.pb`. |
| JSON metadata name | Compatible | Current settings and bundled files use `msd-musicnn-1.json`. |
| ONNX artifact | Unclear | Roadmap 4.22 found official `msd-musicnn-1.onnx`, but this inspection did not download or compare the ONNX graph. |
| Labels | Partially compatible | Current labels come from `msd-musicnn-1.json`; this likely aligns with the official JSON name, but no external artifact hash or byte comparison was performed in Roadmap 4.23. |
| Preprocessing | Unclear | Current code relies on `TensorflowPredictMusiCNN`; the ONNX replacement path would need proof of equivalent feature extraction/input preparation. |
| Output semantics | Partially compatible | Current raw model output is a 50-class score vector averaged across activations and converted to top 8; public outputs also include validation, rounding, normalization, filtering, and `genres_pretty` compatibility mapping. |
| Public API parity | Unclear | Static code identifies current semantics, but no ONNX output comparison or `/classify` parity run was performed. |

This document does not assert production parity between current `legacy_musicnn` and official `msd-musicnn-1.onnx`.

## Parity feasibility assessment

Future local-only MusiCNN ONNX parity spike planning is reasonable but partially blocked.

Reasons it is reasonable:

- Current production model identity appears to be the same Essentia MSD MusiCNN family by name, paths, metadata link, dataset, class count, sample rate, and algorithm metadata.
- The current production code already uses `msd-musicnn-1.pb` and `msd-musicnn-1.json`, which correspond by name to the official references found in Roadmap 4.22.

Reasons it remains partially blocked:

- There is no byte-level or hash-level comparison between the bundled PB/JSON and official artifacts.
- There is no PB-vs-ONNX graph or numeric output comparison.
- The preprocessing performed inside `TensorflowPredictMusiCNN` is not decomposed in the current code.
- It is not yet proven that ONNX Runtime can replace only the TensorFlow inference portion while preserving current preprocessing and output semantics.

Recommended classification: continue only to local-only parity spike planning or deeper static inspection. Do not implement a provider, add `onnxruntime`, download model files into the repo, switch defaults, or run inference as part of Roadmap 4.23.

## Evidence gaps

- Exact byte/hash identity of bundled `app/models/msd-musicnn-1.pb` versus official `msd-musicnn-1.pb`.
- Exact byte/hash identity of bundled `app/models/msd-musicnn-1.json` versus official `msd-musicnn-1.json`.
- Exact relationship between official `msd-musicnn-1.pb` and official `msd-musicnn-1.onnx`.
- Label order equivalence between bundled JSON and official JSON.
- Preprocessing equivalence for `TensorflowPredictMusiCNN`, including feature extraction, framing, mel/spectrogram assumptions, and input tensor preparation.
- PB versus ONNX numeric comparability for the same audio input.
- Output aggregation equivalence, including activation shape and `np.mean(axis=0)`.
- Final `genres` and `genres_pretty` parity after validation, rounding, filtering, compatibility mapping, and descriptor removal.
- Latency, memory, runtime import-time, and cold-start evidence for any future ONNX path.

## No-go checklist

Roadmap 4.23 did not:

- download models;
- add model files;
- add `onnxruntime`;
- change dependencies;
- change Dockerfile or Docker Compose;
- change production code;
- change provider factory;
- change default provider;
- run inference;
- call `/classify`;
- change response shape;
- touch `tidal-parser`;
- create tag or release.

## Decision options

1. Continue to local-only MusiCNN ONNX parity spike planning.
2. Continue to deeper `legacy_musicnn` identity inspection.
3. Continue to preprocessing/label parity evidence review.
4. Pause MusiCNN ONNX path and return to Discogs400 mapping.
5. Reject official MusiCNN ONNX as a non-matching candidate.
6. Keep `legacy_musicnn` as the only production path.

## Recommended decision

Because current `legacy_musicnn` identity appears compatible with the Essentia MSD MusiCNN `msd-musicnn-1` family, the recommended next decision is to continue only to local-only parity spike planning, with explicit blockers tracked for artifact identity, preprocessing equivalence, and output parity.

If future inspection shows identity remains unclear, continue to deeper inspection before any runtime work. If future inspection shows identity mismatch, do not proceed to an ONNX parity spike.

In all cases:

- do not implement a provider;
- do not add `onnxruntime`;
- do not download model files into the repo;
- do not run inference without approval;
- keep `legacy_musicnn` as the production baseline and default provider.

## Explicit non-goals

- No implementation.
- No dependency, runtime, Docker, model, audio, provider, default provider, API, response shape, controlled vocabulary, cache semantic, or `tidal-parser` changes.
- No release or tag work.

## Allowed next steps

- Local-only parity spike planning.
- Deeper static inspection.
- Preprocessing/label parity evidence review.
- Manual external artifact download plan outside the repo after approval.

## Prohibited next steps

- Add `onnxruntime`.
- Add model files.
- Download model files into the repo.
- Implement provider.
- Wire provider factory.
- Switch default provider.
- Run shadow or canary.
- Run inference without approval.
- Call `/classify`.
- Change production contract.
- Touch `tidal-parser`.
- Docker slimming before parity proof.
- Tag or release.

## Rollback considerations

This is documentation-only. Rollback is limited to:

- remove/revert `genre-classifier/docs/lightweight/roadmap-4.23-legacy-musicnn-model-identity-preprocessing-inspection.md`;
- remove `/opt/music-tools/roadmap-4.23-report-and-diff.md`;
- no runtime rollback is needed.
