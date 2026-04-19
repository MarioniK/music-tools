# Roadmap 2 — genre-classifier contract freeze

## Scope

Этот документ фиксирует фактический текущий контракт `genre-classifier` и его интеграцию со стороны `tidal-parser` как baseline перед следующем этапом roadmap. Документ описывает только текущее поведение по коду в репозитории и не предлагает новую реализацию.

## Текущее состояние

`genre-classifier` остаётся отдельным FastAPI-сервисом с узким назначением: принять загруженный аудиофайл, нормализовать его через `ffmpeg`, прогнать через MusiCNN-модель и вернуть сырые и нормализованные жанры. Со стороны `tidal-parser` classifier используется только как дополнительный источник жанров для UI-сценария с ручной загрузкой файла.

Внешний контракт сервиса небольшой, но интеграционный контракт шире его HTTP-ответа: часть гарантий задаётся tolerant reading в `tidal-parser`, merge-логикой и тем, что результаты audio-классификации не попадают в cache.

## Current external contract

### Endpoints

- `GET /`
  - локальный HTML UI для ручной проверки сервиса;
  - не используется `tidal-parser`.
- `GET /health`
  - ответ: `{"ok": true}`;
  - cheap liveness surface;
  - не даёт readiness/diagnostics по модели, `ffmpeg` или файловой системе.
- `POST /classify`
  - основной рабочий endpoint для внешней интеграции;
  - принимает `multipart/form-data` с полем `file`;
  - возвращает JSON.
- `POST /classify-form`
  - HTML form endpoint для локального UI;
  - не используется `tidal-parser`.

### Request shape

Для `POST /classify`:

- content type: `multipart/form-data`
- required field: `file`
- используется оригинальное имя файла, если оно есть
- upload validation:
  - файл не должен быть пустым;
  - максимальный размер: `20 MB`;
  - файл должен иметь расширение;
  - допустимые расширения: `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`

### Success shape

Текущий успешный ответ `POST /classify`:

```json
{
  "ok": true,
  "message": "Аудио проанализировано",
  "genres": [
    {"tag": "indie rock", "prob": 0.9123}
  ],
  "genres_pretty": [
    "indie rock"
  ]
}
```

Фактические свойства:

- `genres`:
  - список словарей;
  - каждый элемент содержит `tag` и `prob`;
  - `tag` lowercased на стороне classifier;
  - список отсортирован по убыванию `prob`;
  - максимум 8 элементов.
- `genres_pretty`:
  - список строк;
  - строится на стороне classifier через `normalize_audio_prediction_genres(...)`.

### Error paths

Для `POST /classify`:

- любой exception внутри upload validation / `ffmpeg` / model execution / metadata loading ловится в route;
- HTTP status: `400`;
- shape:

```json
{
  "ok": false,
  "error": "<runtime message>"
}
```

Фактические свойства:

- internal/runtime errors не различаются по типам на HTTP boundary;
- route не возвращает `500`;
- текст ошибки приходит из `str(e)` без дополнительной нормализации.

Для `POST /classify-form`:

- при ошибке возвращается HTML `index.html` со status `400`;
- ошибка также показывается через `str(e)`.

### Timeout / degraded behavior

На стороне `genre-classifier`:

- отдельного timeout policy нет;
- route ждёт завершения работы `process_uploaded_audio(...)` в executor;
- degraded partial result внутри самого сервиса не предусмотрен: либо full success JSON, либо `400`.

На стороне `tidal-parser`:

- вызов classifier делается через `requests.post(..., timeout=120)`;
- HTTP/network/JSON/runtime проблемы classifier трактуются как exception в `classify_audio_file(...)`;
- в UI-пути это исключение поднимается в `parse_form(...)` и превращается в общий server error response.

### Health / readiness surface

Сейчас service surface ограничен:

- `GET /health` существует;
- readiness endpoint нет;
- route не подтверждает доступность модели, `ffmpeg`, `tmp` directory или возможность выполнить реальную классификацию.

## Integration from tidal-parser

### Call site

Classifier вызывается из:

- `tidal-parser/app/main.py`
  - `classify_audio_file(...)`
  - `parse_form(...)`

Конфигурация URL:

- `tidal-parser/app/settings.py`
  - `DEFAULT_AUDIO_CLASSIFIER_URL = "http://genre-classifier:8021/classify"`
  - runtime access через `get_audio_classifier_url()`

### How tidal-parser calls classifier

`classify_audio_file(...)`:

- пишет загруженные байты во временный файл;
- отправляет `multipart/form-data` на classifier;
- использует timeout `120`;
- ожидает JSON-ответ;
- читает только:
  - `genres`
  - `genres_pretty`

### Fields actually used

`tidal-parser` реально использует:

- `genres` -> как `audio_genres_raw`
- `genres_pretty` -> как `audio_genres_pretty`

Поле `message` в integration logic не используется.

### Partial / empty / malformed responses

Текущее поведение `tidal-parser`:

- `raw = data.get("genres", [])`
- `pretty = data.get("genres_pretty", [])`
- `pretty = pretty or normalize_audio_genres(raw)`

Следствия:

- если `genres_pretty` отсутствует или пустой, `tidal-parser` пересобирает pretty genres из `genres`;
- если `genres` пустой и `genres_pretty` пустой, classifier считается успешным, но audio effect фактически отсутствует;
- если JSON не объектный или `.get(...)` недоступен, это поднимается как exception;
- malformed JSON / non-2xx / timeout / request error не считаются degraded success, а идут как failure path.

### Influence on merge and cache semantics

Classifier влияет только на in-memory post-processing в `parse_form(...)`:

- после успешного `build_result(...)` и только если пользователь загрузил `audio`;
- `result["audio_genres_raw"]` и `result["audio_genres_pretty"]` заполняются classifier output;
- `result["final_genres"]` пересчитывается через `merge_final_genres(...)`;
- `result["blog_output"]` пересчитывается после merge.

Важное текущее поведение:

- audio classification не участвует в `parse_api`;
- audio classification не записывается в cache;
- cache сохраняется в `build_result(...)` до UI-level audio merge;
- `from_cache` принудительно сбрасывается в `False` после audio classification;
- `force_refresh == 1` без повторной загрузки файла не повторяет audio analysis и только добавляет `audio_note`.

## Contract layers

### Explicit contract

То, что явно видно на HTTP surface:

- `POST /classify` существует и принимает `multipart/form-data` с полем `file`;
- success response содержит `ok`, `message`, `genres`, `genres_pretty`;
- error response содержит `ok=false`, `error`;
- `GET /health` возвращает `{"ok": true}`.

### Implicit contract

То, что не оформлено отдельной схемой, но реально используется:

- `genres` — список словарей с ключами `tag` и `prob`;
- `genres_pretty` — список строк и может отсутствовать, если caller готов построить fallback;
- classifier URL по умолчанию — `http://genre-classifier:8021/classify`;
- timeout со стороны caller — `120`;
- classifier output допускается как частично полезный только в варианте `genres` без `genres_pretty`.

### Semantic contract

То, что важно для поведения системы в целом:

- classifier — дополнительный жанровый источник, а не обязательная часть базового metadata pipeline;
- classifier влияет на merge только в UI flow с upload;
- classifier не должен менять cache semantics;
- classifier failure не должен silently превращаться в cached audio result;
- classifier output должен оставаться совместимым с `merge_final_genres(...)` и `build_blog_output(...)`.

## Invariants that must not break in the next stage

- `POST /classify` должен остаться доступным по тому же назначению как интеграционная точка для `tidal-parser`.
- Request должен оставаться совместимым с `multipart/form-data` и полем `file`.
- Success response должен продолжать содержать usable `genres` и `genres_pretty` или эквивалентно совместимый fallback path для current caller.
- `genres` должен оставаться списком структур, из которых caller может извлечь raw tags и probabilities.
- `genres_pretty` должен оставаться списком нормализованных genre strings или быть безопасно опциональным при наличии `genres`.
- Failure path не должен silently masquerade as success.
- Audio classification не должна внезапно начать влиять на cache persistence без отдельного осознанного изменения orchestration semantics.
- `tidal-parser` должен иметь возможность продолжать tolerant reading частичного classifier response.
- `/health` не должен начинать заявлять readiness внешних зависимостей без явного изменения его назначения.

## Risk zones for the next stage

- смена JSON shape у `POST /classify`;
- удаление или переименование `genres` / `genres_pretty`;
- изменение типа `genres` элементов;
- перевод error paths в другой status/shape без совместимого слоя;
- изменение синхронности/latency так, что текущий timeout `120` перестанет быть реалистичным;
- скрытое изменение жанровой нормализации, которое сдвинет merge semantics;
- добавление cache coupling между classifier output и `tidal-parser`;
- смешение internal UI endpoint `classify-form` с внешним интеграционным контрактом;
- readiness claims в `/health`, не соответствующие фактической ливнес-проверке.

## Key files and functions for the next stage

### genre-classifier

- `genre-classifier/app/main.py`
  - `validate_upload(...)`
  - `normalize_audio_file(...)`
  - `run_genre_classification(...)`
  - `normalize_genres(...)`
  - `process_uploaded_audio(...)`
  - `classify(...)`
  - `health()`
- `genre-classifier/app/genre_normalization.py`
- `genre-classifier/tests/test_upload_validation.py`
- `genre-classifier/tests/test_genre_normalization.py`
- `genre-classifier/docker-compose.yml`

### tidal-parser

- `tidal-parser/app/settings.py`
  - `DEFAULT_AUDIO_CLASSIFIER_URL`
  - `get_audio_classifier_url()`
- `tidal-parser/app/main.py`
  - `classify_audio_file(...)`
  - `normalize_audio_genres(...)`
  - `merge_final_genres(...)`
  - `parse_form(...)`
  - `build_result(...)`
  - `_build_cache_payload(...)`
  - `get_cached_result(...)`

## Out of scope for this document

- выбор нового стека для classifier;
- LLM-based migration design;
- новый API;
- изменения merge strategy;
- изменения cache strategy;
- runtime refactor в `tidal-parser` или `genre-classifier`.
