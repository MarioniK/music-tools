# Roadmap 4.93: optional ONNX slim `/classify` smoke via Compose profile

Цель этого шага была ограничена только проверкой HTTP-boundary для optional ONNX slim сервиса через Compose profile `onnx`.

Что подтверждено:

- optional сервис `genre-classifier-onnx` успешно поднят через `docker compose --profile onnx up -d genre-classifier-onnx`;
- health endpoint ответил `200`;
- `/classify` на optional сервисе ответил `200`;
- форма ответа сохранилась: `ok`, `message`, `genres`, `genres_pretty`;
- `genres` и `genres_pretty` не пустые;
- default legacy path не менялся;
- production readiness не заявляется.

Использованный fixture:

`/tmp/music-tools-onnx-parity/fixtures/john_bartmann__earning_happiness__cc0.mp3`

Фактический ответ `/classify`:

```json
{
  "ok": true,
  "message": "Аудио проанализировано",
  "genres": [
    {
      "tag": "electronic",
      "prob": 0.4209
    },
    {
      "tag": "dance",
      "prob": 0.2404
    },
    {
      "tag": "house",
      "prob": 0.1625
    },
    {
      "tag": "electro",
      "prob": 0.1121
    },
    {
      "tag": "electronica",
      "prob": 0.1058
    },
    {
      "tag": "pop",
      "prob": 0.0791
    },
    {
      "tag": "rock",
      "prob": 0.0723
    },
    {
      "tag": "indie",
      "prob": 0.0688
    }
  ],
  "genres_pretty": [
    "indie rock",
    "electronic",
    "dance",
    "house",
    "electro",
    "electronica",
    "pop",
    "rock"
  ]
}
```

Логи optional контейнера зафиксировали:

- startup `uvicorn` без ошибок старта приложения;
- `GET /health` -> `200`;
- `POST /classify` -> `200 OK`;
- provider selection: `onnx_musicnn`;
- сохранение shadow-логики в `skipped_by_config`.

