# Roadmap 3.5 Fixture Manifest

## Valid Fixtures

| Fixture | Local path | Purpose | Audio committed? | Notes |
|---|---|---|---|---|
| Primary upload fixture | `app/tmp/upload.mp3` | Primary baseline fixture for production runtime vs Python 3.12 + `essentia-tensorflow` candidate parity validation. | Existing repo/local file only; do not add new audio. | Found during Roadmap 3.5 inventory. Size observed locally: `7470185` bytes. |
| Normalized WAV candidate | `app/tmp/normalized.wav` | Optional secondary valid fixture if a second local-only audio sample is needed. | Existing repo/local file only; do not add new audio. | Found during inventory. Treat as optional because the primary acceptance path uses `app/tmp/upload.mp3`. |
| Temporary MP3 candidate | `app/tmp/tmpafc28hj_.mp3` | Optional local-only exploratory fixture. | Existing repo/local file only; do not add new audio. | Looks like a temporary app artifact; do not rely on it as a curated corpus fixture. |
| Temporary WAV candidate | `app/tmp/tmpcip33cuv.wav` | Optional local-only exploratory fixture. | Existing repo/local file only; do not add new audio. | Looks like a temporary app artifact; do not rely on it as a curated corpus fixture. |

## Malformed / Unsupported Fixtures

Create these local-only fixtures under `/tmp` before validation:

```sh
mkdir -p /tmp/roadmap-3.5-fixtures
: > /tmp/roadmap-3.5-fixtures/empty.mp3
printf 'this is not an mp3 file\n' > /tmp/roadmap-3.5-fixtures/fake.mp3
printf 'plain text unsupported upload\n' > /tmp/roadmap-3.5-fixtures/unsupported.txt
```

| Fixture | Local path | Purpose | Audio committed? |
|---|---|---|---|
| Empty MP3 upload | `/tmp/roadmap-3.5-fixtures/empty.mp3` | Validate that a zero-byte upload returns an error without crashing the process. | No, local-only. |
| Fake MP3 upload | `/tmp/roadmap-3.5-fixtures/fake.mp3` | Validate that a text payload with an `.mp3` extension returns an error without crashing the process. | No, local-only. |
| Unsupported text upload | `/tmp/roadmap-3.5-fixtures/unsupported.txt` | Validate unsupported upload behavior and process stability. | No, local-only. |

## Git Hygiene

Do not add new heavyweight audio fixtures to git for Roadmap 3.5. This manifest records fixture paths and purpose only.
