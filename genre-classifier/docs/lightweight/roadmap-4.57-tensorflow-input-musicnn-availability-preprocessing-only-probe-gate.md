# Roadmap 4.57 - TensorflowInputMusiCNN availability and preprocessing-only probe gate

## Цель

Roadmap 4.57 проверяет узкий local-only вопрос: можно ли использовать
`TensorflowInputMusiCNN` как preprocessing-only candidate для pragmatic
ONNX/MusiCNN lane без перехода к production provider implementation, default
switch или изменения `/classify` contract.

Это не strict parity lane. Здесь не требуется доказать идентичность legacy
preprocessing path и не делается production decision.

## Почему `TensorflowInputMusiCNN`

`TensorflowInputMusiCNN` - это официальный алгоритм Essentia для
MusiCNN-specific mel-bands.

Для Roadmap 4.57 он подходит лучше, чем `TensorflowPredictMusiCNN`, потому что:

- нужен preprocessing-only path, а не prediction oracle;
- `TensorflowPredictMusiCNN` уже содержит inference semantics и поэтому не
  должен использоваться как preprocessing oracle;
- pragmatic ONNX/MusiCNN lane допускает контролируемый output drift, но требует
  воспроизводимый preprocessing gate;
- цель этого шага - подтвердить доступность и пробируемость mel path, а не
  заявлять strict legacy parity.

## Что было проверено

- прочитан `AGENTS.md`;
- проверены Roadmap 4.55 и 4.56 evidence reports;
- проверены legal fixtures вне репозитория:
  `/tmp/music-tools-onnx-parity/fixtures/`;
- проверены SHA256 и provenance notes для approved CC0 fixtures;
- проверен isolated env `onnxruntime` version;
- проверен `essentia.standard` import status в isolated env;
- проверен system Python import status, только как safe check;
- проверен local-only helper `scripts/lightweight/musicnn_tensorflow_input_probe.py`;
- сгенерирован evidence report:
  `docs/lightweight/evaluation/evidence/roadmap-4.57-tensorflow-input-musicnn-availability-probe-report.json`.

## Граница исполнения

Helper честно разделяет две операции:

- `--isolated-python` используется для availability checks;
- preprocessing-probe выполняется в интерпретаторе, который запустил helper.

Если нужно прогнать preprocessing-probe именно в approved isolated env, helper
следует запускать так:

```bash
/tmp/music-tools-onnx-parity/venv/bin/python \
  scripts/lightweight/musicnn_tensorflow_input_probe.py \
  --mode preprocessing-probe
```

## Результат

`TensorflowInputMusiCNN` в approved isolated env сейчас недоступен, потому что
`essentia` не импортируется. В system Python тот же blocker.

Следствие:

- preprocessing probe не дал patch `[187, 96]`;
- repeated-run stability не проверялась, потому что patch не был произведён;
- fake output не создавался;
- production approval не выдавался;
- provider/default logic не менялись.

## Блокеры

- `ESSENTIA_IMPORT_FAILED`
- `TENSORFLOW_INPUT_MUSICNN_IMPORT_FAILED`
- `TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE`
- `GENERIC_MELBANDS_FALLBACK_BLOCKED`

## Следующая рекомендация

Если `TensorflowInputMusiCNN` станет доступен в approved isolated env, нужно
снова запустить preprocessing-probe и отдельно проверить, можно ли стабильно
собрать patch `[187, 96]` без обращения к `TensorflowPredictMusiCNN`.

Если доступность не появится, Roadmap 4.57 остаётся blocked evidence gate и не
даёт оснований для production migration.

## Без production decision

Этот шаг не утверждает production readiness, не меняет provider/default logic,
не меняет `/classify` contract и не трогает `tidal-parser`.
