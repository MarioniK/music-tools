# Roadmap 4.52: ONNX preprocessing alignment investigation gate

Roadmap 4.52 нужен не для миграции на ONNX и не для смены default provider, а для честной проверки одного узкого вопроса: можно ли получить вход `melspectrogram [187, 96]` для `msd-musicnn-1.onnx` способом, который явно согласуется с текущим legacy `TensorflowPredictMusiCNN` preprocessing path.

## Зачем нужен этот gate

Roadmap 4.51 правильно остановил ONNX-side capture, потому что на тот момент был подтверждён только сам ONNX artifact и его metadata, но не был доказан воспроизводимый путь генерации входного `melspectrogram`, согласованный с production legacy MusicNN chain. Без этого ONNX output capture был бы преждевременным и мог бы создать ложное ощущение parity.

## Что было проверено

- Коммитнутый baseline evidence: `docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json`
- ONNX metadata из локального артефакта `msd-musicnn-1.onnx`
- Committed TF model metadata из `app/models/msd-musicnn-1.json`
- Production legacy path в `app/services/classify.py`
- Legacy provider wrapper в `app/providers/legacy_musicnn.py`
- Default provider и response contract в `app/core/settings.py` и `app/api/routes.py`

## Что найдено

- `legacy_musicnn` остаётся baseline и default provider.
- `/classify` contract не менялся: `ok`, `message`, `genres`, `genres_pretty`.
- Production legacy path использует `ffmpeg`, `MonoLoader(sampleRate=16000)` и `TensorflowPredictMusiCNN`.
- В репо-коде не найдено явное exposure промежуточного `melspectrogram`.
- Локальный Essentia probe не смог подтвердить preprocessing chain names или параметры.
- Для legacy preprocessing path остаются неизвестными `frame_size`, `hop_size`, `mel_bands`, `patch_length`, `tensor_layout`, `normalization`.

## Почему capture не делался

ONNX fixture output capture не был запущен, потому что alignment между legacy preprocessing chain и ONNX input producer всё ещё не доказан. Вместо fake outputs зафиксирован blocked status и sanitised blockers.

## Почему это не final parity decision

Roadmap 4.52 только проверяет preprocessing alignment gate. Он не утверждает numeric parity, не переключает provider, не меняет runtime defaults и не меняет `/classify` response shape.

## Итог

Status для Roadmap 4.52: `blocked`.

Причина: reproducible producer для ONNX `melspectrogram [187, 96]` пока не evidenced, а legacy intermediate tensor не exposed in repo code.

