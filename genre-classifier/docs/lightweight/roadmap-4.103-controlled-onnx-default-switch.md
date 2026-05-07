# Roadmap 4.103. Controlled ONNX default switch execution

## Summary

Roadmap 4.103 выполняет controlled default switch для `genre-classifier`:
default provider и default Docker target переведены на ONNX,
а legacy path сохранён как rollback path.

Это не release/tag и не миграция `tidal-parser`.
Контракт `/classify` и response shape не менялись.

## What changed

- `genre-classifier` default provider: `legacy_musicnn` -> `onnx_musicnn`
- `genre-classifier` default Docker target: `legacy-runtime` -> `onnx-runtime-slim`
- default service `genre-classifier` теперь использует external ONNX artifacts
- добавлен explicit rollback profile `genre-classifier-legacy`
- legacy provider/runtime сохранены как rollback path

## What did not change

- `tidal-parser` code не менялся
- `/classify` contract не менялся
- response shape не менялся
- `essentia-tensorflow==2.1b6.dev1389` остаётся в `requirements.txt`
- legacy provider/runtime не удалялись
- artifacts не коммитились в репозиторий

## Artifact verification

- host path: `/opt/music-tools-artifacts/genre-classifier/onnx`
- container path: `/opt/genre-classifier/onnx`
- `msd-musicnn-1.onnx` checksum matched expected value
- `msd-musicnn-1.json` checksum matched expected value

## Build, start, health

- `docker compose config` succeeded for the default service
- `docker compose --profile legacy config` succeeded for rollback profile
- `docker compose build genre-classifier` succeeded
- `docker compose up -d --force-recreate genre-classifier` succeeded
- `curl http://localhost:8021/health` returned `200`
- `curl http://localhost:8011/health` returned `200`

## Post-switch integration smoke

Smoke request:

```bash
POST /
url=https://tidal.com/track/498894205/u
force_refresh=0
audio=@genre-classifier/app/tmp/upload.mp3
```

Result:

- HTTP status: `200`
- content type: `text/html; charset=utf-8`
- `Audio genres` present
- `Итоговые жанры` present
- `Reference ID` error absent
- `genre-classifier` logs confirmed `provider_name=onnx_musicnn`
- `genre-classifier` logs confirmed `provider_class=OnnxMusiCNNProvider`
- `genre-classifier` logs confirmed `file_processing_succeeded`
- `genre-classifier` logs confirmed `POST /classify HTTP/1.1 200 OK`
- `tidal-parser` logs confirmed `stage outcome success stage=audio_classifier`

### Response excerpt

```html
<div class="audio-title">Audio genres</div>
<div class="pretty-box">indie rock, experimental rock, alternative rock, instrumental rock, indie, rock, instrumental, folk</div>

<div class="audio-title">Итоговые жанры</div>
<div class="pretty-box">indie rock, experimental rock, alternative rock, instrumental rock, indie, rock</div>
```

### Log excerpts

`genre-classifier`:

```text
event=genre_provider_selected provider_name=onnx_musicnn provider_class=OnnxMusiCNNProvider
event=file_processing_succeeded filename=upload.mp3 size_bytes=7470185
POST /classify HTTP/1.1 200 OK
```

`tidal-parser`:

```text
event=cache_lookup outcome=hit source=cache cache_key=https://tidal.com/track/498894205/u
event=stage outcome=success stage=audio_classifier duration_ms=1270
POST / HTTP/1.1 200 OK
```

## Rollback path

Rollback remains available via:

- `genre-classifier-legacy`
- `profiles: [legacy]`
- `target: legacy-runtime`
- `GENRE_PROVIDER=legacy_musicnn`

If a post-switch check fails in the future:

1. restore default provider to `legacy_musicnn`
2. restore default target to `legacy-runtime`
3. rebuild and recreate default `genre-classifier`
4. verify health
5. re-run legacy parser flow smoke

## Known risks

- Evidence still uses one parser request/audio fixture
- ONNX output drift remains expected and documented
- Default runtime depends on external ONNX artifacts
- Legacy rollback path must be kept

## Non-goals

- no `tidal-parser` code migration
- no `/classify` contract changes
- no response shape changes
- no removal of legacy runtime
- no model artifact commits
- no release/tag
