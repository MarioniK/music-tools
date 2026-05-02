# Roadmap 3.9 Import-Order Matrix

This evidence matrix is for the non-production Python 3.12 + `essentia-tensorflow` runtime candidate only.

Run each scenario in a fresh process. TensorFlow-first failures can abort the interpreter, so a combined in-process runner would hide the exact failing scenario.

## Command template

From `/opt/music-tools/genre-classifier`:

```sh
docker run --rm \
  -v /opt/music-tools/genre-classifier:/app \
  music-tools-genre-classifier-roadmap-3.9:py312-etf \
  python scripts/runtime_validation/import_order_smoke.py <scenario>
```

## Matrix

| Scenario | Expected result | Evidence file | Observed result | Notes |
| --- | --- | --- | --- | --- |
| `essentia_first` | Pass | `import-order-essentia_first.txt` | Pass, `exit_code=0` | Imports `essentia` only. |
| `essentia_standard_first` | Pass | `import-order-essentia_standard_first.txt` | Pass, `exit_code=0` | Imports `essentia.standard` and confirms `MonoLoader` / `TensorflowPredictMusiCNN` symbols. |
| `tensorflow_first` | Pass or fail must be recorded | `import-order-tensorflow_first.txt` | Pass, `exit_code=0` | Imports `tensorflow` only; TensorFlow alone does not fail. |
| `tensorflow_then_essentia` | Known failing path under Roadmap 3.8 | `import-order-tensorflow_then_essentia.txt` | Fail, `exit_code=1` | Fails deterministically with duplicate `Bitcast` op registration. |
| `tensorflow_then_essentia_standard` | Known failing path under Roadmap 3.8 | `import-order-tensorflow_then_essentia_standard.txt` | Fail, `exit_code=1` | Fails deterministically with duplicate `Bitcast` op registration. |
| `tensorflow_then_musicnn_symbol` | Known failing path under Roadmap 3.8 | `import-order-tensorflow_then_musicnn_symbol.txt` | Fail, `exit_code=1` | Fails before resolving the MusiCNN symbol because importing `essentia.standard` triggers duplicate `Bitcast` registration. |
| `essentia_then_tensorflow` | Pass | `import-order-essentia_then_tensorflow.txt` | Pass, `exit_code=0` | Essentia-first import-order path remains stable. |
| `essentia_standard_then_tensorflow` | Pass | `import-order-essentia_standard_then_tensorflow.txt` | Pass, `exit_code=0` | App-relevant Essentia-standard-first path remains stable. |
| `classify_import` | Pass | `import-order-classify_import.txt` | Pass, `exit_code=0` | Production classification module import path remains stable. |
| `app_main_import` | Pass | `import-order-app_main_import.txt` | Pass, `exit_code=0` | Production app import path remains stable. |
| `classify_then_tensorflow` | Pass | `import-order-classify_then_tensorflow.txt` | Pass, `exit_code=0` | App/classify import before TensorFlow remains stable. |
| `app_then_tensorflow` | Pass | `import-order-app_then_tensorflow.txt` | Pass, `exit_code=0` | App import before TensorFlow remains stable. |
| `model_load_essentia_first` | Pass | `import-order-model_load_essentia_first.txt` | Pass, `exit_code=0` | Loads the existing MusiCNN `.pb` with Essentia first. |
| `model_load_tensorflow_first` | Known failing path under Roadmap 3.8 | `import-order-model_load_tensorflow_first.txt` | Fail, `exit_code=1` | TensorFlow-first model-load path fails with duplicate `Bitcast` registration. |
| `same_process_repeated_imports` | Pass | `import-order-same_process_repeated_imports.txt` | Pass, `exit_code=0` | Repeats the supported app/Essentia-first path three times in one process. |

## Evidence naming convention

Use one file per scenario:

```text
docs/runtime/evidence/roadmap-3.9/import-order-<scenario>.txt
```
