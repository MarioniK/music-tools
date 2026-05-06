# Roadmap 4.65 - Изолированный ONNX/MusiCNN output capture

## Статус

`completed`

Roadmap 4.65 предназначен для локального, изолированного capture реальных
ONNX outputs для официального `msd-musicnn-1.onnx` артефакта вне репозитория.
Этот шаг не меняет production runtime, не трогает provider wiring и не
утверждает production readiness.

## Что делает этот шаг

Roadmap 4.65:

- использует уже подтверждённый preprocessing path из Roadmap 4.64;
- генерирует стабильный patch через `essentia.standard.TensorflowInputMusiCNN`;
- проверяет legal fixture и SHA256 вне репозитория;
- проверяет SHA256 официального ONNX-моделя вне репозитория;
- пытается создать `onnxruntime.InferenceSession` в isolated venv;
- при доступном runtime выполняет реальный capture `activations` и
  `embeddings`;
- при повторном запуске сравнивает output tensors на той же fixture;
- пишет sanitized JSON report без fake outputs.

## Почему Roadmap 4.64 это позволяет

Roadmap 4.64 уже подтвердил, что локальный Essentia preprocessing путь даёт
стабильный patch нужной формы:

- raw observed shape: `[2948, 96]`;
- final patch shape: `[187, 96]`;
- repeated-run stability: `checked=true`, `stable=true`.

Это означает, что preprocessing input для ONNX lane уже доказан в отдельном
локальном evidence step. Roadmap 4.65 может опираться на этот результат, не
повторяя TensorFlow baseline и не используя `TensorflowPredictMusiCNN` как
oracle.

## Подтверждённые локальные артефакты

- Legal fixture: `/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3`
- Expected fixture SHA256:
  `d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628`
- ONNX model: `/tmp/music-tools-onnx-parity/msd-musicnn-1.onnx`
- ONNX model SHA256:
  `49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1`

Все эти артефакты остаются вне репозитория. Никакие fixture/audio/model files не
коммитятся.

## Почему это не strict legacy parity proof

Этот шаг не доказывает строгую legacy parity.

Причины:

- capture выполняется для ONNX артефакта, а не для production legacy path;
- TensorFlow baseline специально не запускается снова;
- сравнение TensorFlow vs ONNX на этом шаге не выполняется;
- semantics raw ONNX tensors не интерпретируются как production genre output;
- `/classify` не вызывается;
- provider implementation не добавляется;
- default provider `legacy_musicnn` остаётся неизменным.

## Что произошло в этой попытке

Helper `scripts/lightweight/musicnn_onnx_output_capture.py` был обновлён для
Roadmap 4.65 и затем запущен в isolated venv:

- Python: `3.11.2`
- Essentia import: `true`
- `essentia.standard` import: `true`
- `TensorflowInputMusiCNN` availability: `true`
- `onnxruntime` import: `true`
- `onnxruntime` version: `1.25.1`
- `onnxruntime` providers: `AzureExecutionProvider`, `CPUExecutionProvider`

В результате была создана реальная ONNX inference session, а output tensors
были получены локально без участия production runtime.

## Что было подтверждено

Helper подтвердил:

- 4.64 evidence валидна;
- fixture SHA256 совпадает;
- ONNX model существует и SHA256 записан;
- preprocessing patch воспроизводится локально;
- final patch shape остаётся `[187, 96]`;
- patch dtype: `float32`;
- finite values: `17952`.

Дополнительно были получены реальные ONNX outputs:

- input name: `melspectrogram`;
- input shape: `["unk__155", 187, 96]`;
- input type: `tensor(float)`;
- output names: `activations`, `embeddings`;
- output shapes: `["unk__156", 50]`, `["unk__157", 200]`;
- `activations` normalized shape: `[50]`;
- `embeddings` normalized shape: `[200]`;
- repeated-run stability: `checked=true`, `stable=true`, `tolerance=1e-6`,
  `max_abs_diff=0.0`, `mean_abs_diff=0.0`.

## Почему не использовался `TensorflowPredictMusiCNN`

`TensorflowPredictMusiCNN` не использовался намеренно:

- этот шаг не предназначен для TensorFlow baseline;
- oracle не нужен для фиксации raw ONNX output capture;
- Roadmap 4.64 уже подтвердил preprocessing input path без этого oracle;
- задача 4.65 состоит в isolated ONNX capture, а не в повторном TF proof.

## Почему `/classify` не вызывался

`/classify` не вызывался, потому что:

- это production contract path;
- задача этого шага локальная и не про интеграцию в сервис;
- вызов endpoint не нужен для capture ONNX raw outputs;
- шаг не должен менять response shape или provider logic.

## Почему это не provider implementation

Helper не подключается к production app и не реализует provider:

- не меняет factory;
- не меняет default provider;
- не меняет runtime shadow;
- не меняет Dockerfile;
- не меняет Docker Compose;
- не меняет requirements.

## Почему `legacy_musicnn` остаётся default

`legacy_musicnn` остаётся default provider, потому что Roadmap 4.65:

- не меняет production defaults;
- не утверждает production migration;
- не меняет `/classify` response shape;
- не объявляет production readiness;
- не включает runtime shadow.

## Observed ONNX metadata

Реальная ONNX Runtime session была создана в isolated venv:

- `onnx_runtime.session_created = true`;
- input metadata:
  - name: `melspectrogram`;
  - shape: `["unk__155", 187, 96]`;
  - type: `tensor(float)`;
- input shape adaptation:
  - requested shape: `[187, 96]`;
  - applied: `true`;
  - adaptation: `added_batch_dimension`;
  - result shape: `[1, 187, 96]`;
- output metadata:
  - `activations`: `["unk__156", 50]`, `tensor(float)`;
  - `embeddings`: `["unk__157", 200]`, `tensor(float)`.

Captured output statistics:

- `activations`
  - raw shape: `[1, 50]`
  - normalized shape: `[50]`
  - dtype: `float32`
  - min: `0.002573162317276001`
  - max: `0.2679290473461151`
  - mean: `0.036268118768930435`
  - finite values: `50`
  - nan count: `0`
  - inf count: `0`
  - top activation indices: `[4, 0, 3, 1, 6]`
  - top activation scores: `[0.2679290473461151, 0.17159512639045715, 0.1285322904586792, 0.11120280623435974, 0.09515172243118286]`
- `embeddings`
  - raw shape: `[1, 200]`
  - normalized shape: `[200]`
  - dtype: `float32`
  - min: `-5.961637020111084`
  - max: `5.52200984954834`
  - mean: `0.06967145204544067`
  - finite values: `200`
  - nan count: `0`
  - inf count: `0`

Repeated-run stability:

- checked: `true`
- stable: `true`
- tolerance: `1e-6`
- max_abs_diff: `0.0`
- mean_abs_diff: `0.0`

## Блокеры

Текущие блокеры Roadmap 4.65 отсутствуют.

`PRODUCTION_READINESS_NOT_PROVEN` остаётся управленческой оговоркой, но не
техническим blocker-ом этого локального capture шага.

## Следующий рекомендуемый шаг

Следующий шаг Roadmap 4.66 может сфокусироваться на:

- интерпретации ONNX/MusiCNN output tensors;
- контролируемом описании drift;
- аккуратной документации несоответствий между raw outputs и legacy genres;
- дальнейшем локальном evidence без изменения production provider logic.
