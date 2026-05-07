# Roadmap 4.99. Legacy integration smoke

## Цель

Подтвердить текущий production baseline end-to-end:
`tidal-parser -> genre-classifier` в legacy-режиме.

## Что проверялось

- текущие контейнеры `tidal-parser` и `genre-classifier`;
- health обоих сервисов;
- один реальный parse-request через `tidal-parser`;
- response shape и отсутствие user-facing `Reference ID` ошибки;
- логи `tidal-parser` и `genre-classifier`;
- `file_processing_succeeded` в classifier-логе;
- стабильный baseline без ONNX default switch.

## Stable baseline

- `genre-classifier` default provider: `legacy_musicnn`
- `genre-classifier` default Docker target: `legacy-runtime`
- `genre-classifier/requirements.txt` содержит `essentia-tensorflow==2.1b6.dev1389`
- ONNX остаётся candidate, not default
- default switch не выполнялся

## Smoke input

Документированный parser endpoint в коде и тестах: `GET /api/parse?url=<TIDAL_URL>&force_refresh=0`.

Для runtime smoke использовался form route `POST /` с multipart upload, потому что именно он
проходит полный legacy parser-flow и передаёт аудиофайл в `genre-classifier`.

Команда:

```bash
curl -sS \
  -w '\nHTTP_STATUS:%{http_code}\nTOTAL_TIME:%{time_total}\nCONTENT_TYPE:%{content_type}\n' \
  -F url=https://tidal.com/track/498894205/u \
  -F force_refresh=0 \
  -F audio=@genre-classifier/app/tmp/upload.mp3 \
  http://127.0.0.1:8011/ \
  -o /tmp/music-tools-roadmap-4.99-form-response.out
```

## Health

- `tidal-parser`: `200 OK`
- `genre-classifier`: `200 OK`

## Result

- HTTP status: `200`
- content type: `text/html; charset=utf-8`
- total time: `9.950274s`
- response shape preserved: да
- audio classification present: да
- Reference ID error: нет

### Response excerpt

```html
<div class="row">
  <span class="label">Исполнитель:</span>
  <span>MISSIO</span>
</div>

<div class="row">
  <span class="label">Название:</span>
  <span>Bleed</span>
</div>

<div class="audio-block">
  <div class="audio-title">Audio genres</div>
  <div class="pretty-box">indie rock, alternative rock, electronic, indie, rock, alternative, electro, pop</div>
</div>

<div class="audio-block">
  <div class="audio-title">Итоговые жанры</div>
  <div class="pretty-box">electronic, indie rock, alternative rock, indie, rock, alternative</div>
</div>
```

## Log evidence

### tidal-parser

```text
2026-05-07 19:13:27,463 INFO tidal_parser request_id=2454d08f6d1747f089de6a51ce98c8f7 event=cache_lookup outcome=hit source=cache cache_key=https://tidal.com/track/498894205/u from_cache=true force_refresh=False
2026-05-07 19:13:37,378 INFO tidal_parser request_id=2454d08f6d1747f089de6a51ce98c8f7 event=stage outcome=success stage=audio_classifier duration_ms=9913
```

### genre-classifier

```text
2026-05-07 19:13:27,537 INFO genre_classifier event=file_processing_started filename=upload.mp3 size_bytes=7470185
2026-05-07 19:13:37,374 INFO genre_classifier event=file_processing_succeeded filename=upload.mp3 size_bytes=7470185
2026-05-07 19:13:37,374 INFO genre_classifier event=genre_classifier.shadow.skipped status=skipped_by_config
```

## Request / Reference ID

- request_id: `2454d08f6d1747f089de6a51ce98c8f7`
- Reference ID error: отсутствует

## Current stable baseline

- `legacy_musicnn` остаётся default provider
- `legacy-runtime` остаётся default Docker target
- `essentia-tensorflow==2.1b6.dev1389` остаётся в `requirements.txt`
- ONNX не включался как default

## Blockers / warnings

- Blockers: нет
- Warning: `provider_selected` зафиксирован как `legacy_musicnn` по текущему baseline; classifier-логи не печатают explicit provider_name

## Confirmations

- `AGENTS.md` read and followed
- legacy integration smoke only
- no ONNX profile
- no default switch
- no Docker build
- no Docker Compose up/run
- no direct `/classify` call
- no app code changes
- no Dockerfile changes
- no Compose changes
- no requirements changes
- no default provider changes
- no response shape changes
- no artifacts committed
- `tidal-parser` code untouched
