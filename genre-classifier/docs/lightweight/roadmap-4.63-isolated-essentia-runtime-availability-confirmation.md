# Roadmap 4.63 - Isolated Essentia runtime availability confirmation evidence

## Purpose

Этот шаг фиксирует post-push successful import-level confirmation для isolated
Essentia runtime отдельным committed evidence artifact.

Это отдельный evidence sync step после Roadmap 4.62, чтобы не смешивать
historical blocked-state acquisition с фактическим post-push подтверждением
доступности runtime на уровне import.

## Почему это отдельный шаг после 4.62

Roadmap 4.62 остаётся историческим blocked-state artifact:

- `OFFLINE_LOCAL_ESSENTIA_WHEEL_NOT_AVAILABLE`
- `DOCKER_CONTAINER_PROBE_UNAVAILABLE`
- import probe на момент commit не выполнялся
- `TensorflowInputMusiCNN` на тот момент не был подтверждён

Roadmap 4.63 не переписывает 4.62 как success. Он отдельно фиксирует, что
после push был получен успешный import-level confirmation в isolated venv.

## Isolated runtime

- venv path: `/tmp/music-tools-onnx-parity/venv`
- installed package: `essentia-tensorflow==2.1b6.dev1389`
- local-only dependencies:
  - `numpy==2.4.4`
  - `PyYAML==6.0.3`
  - `six==1.17.0`
- runtime Essentia version: `2.1-beta6-dev`

## Import-level confirmation

- `import essentia`: `true`
- `import essentia.standard`: `true`
- `TensorflowInputMusiCNN available`: `true`

## Wheel evidence

- wheel filename:
  `essentia_tensorflow-2.1b6.dev1389-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`
- wheel sha256: `not_available`
- wheel sha256 reason: wheel file not retained in pip cache after direct install

## Warning classification

Observed TensorFlow warnings mention missing CUDA libraries, including
`libcudart.so.11.0` and `libcuda.so.1`.

Classification: `cuda_libraries_missing_but_cpu_import_available`

Это не blocker для CPU import-level availability evidence.

## Explicit non-goals

- no preprocessing probe
- no `[187, 96]` patch generation
- no ONNX execution
- no ONNX output capture
- no `/classify` call
- no TensorFlow baseline
- no TensorFlow vs ONNX comparison
- no provider implementation
- no default provider switch
- no production dependency changes
- no Dockerfile/Compose changes
- no `tidal-parser` changes

## Next step

Roadmap 4.64 - isolated `TensorflowInputMusiCNN` preprocessing-only patch
generation probe.
