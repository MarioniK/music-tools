# music-tools

`music-tools` — монорепозиторий с двумя отдельными сервисами для извлечения, обогащения и нормализации музыкальных данных:

- `tidal-parser`
- `genre-classifier`

Сервисы живут в отдельных директориях, имеют отдельные Docker Compose конфигурации и не образуют одно runtime-окружение.

## Release Readiness

Roadmap 6 закрыт, и релиз `v0.7.0` готовится как общий release-summary для обоих сервисов.

- Release notes: [docs/releases/v0.7.0.md](docs/releases/v0.7.0.md)
- Service env examples:
  - [tidal-parser/.env.example](tidal-parser/.env.example)
  - [genre-classifier/.env.example](genre-classifier/.env.example)
- Current `genre-classifier` example default: `GENRE_PROVIDER=onnx_musicnn`
- `.sourcecraft/ci.yaml` is a critical GitHub -> SourceCraft sync file and should not be modified without an explicit direct instruction.

Схема pipeline:

`TIDAL -> parse_tidal -> Discogs -> MusicBrainz -> audio classifier -> merge -> cache`

Проект делает упор на устойчивость пайплайна, предсказуемость результата и безопасную деградацию при сбоях внешних API. Основная идея остаётся прежней: источники объединяются через простые и объяснимые правила, без скрытой магии.

## Что умеет `tidal-parser`

`tidal-parser` - основной сервис координации и UI.

Он умеет:

- парсить прямые TIDAL URL;
- принимать Qobuz canonical/open album links и доводить их до TIDAL resolver;
- принимать manual release line и selector `Тип` для `album` / `ep` / `track` и доводить их до TIDAL resolver;
- принимать Apple Music album/song links, извлекать provider identity и передавать её в TIDAL resolver;
- принимать Spotify album/track links, извлекать provider identity и передавать её в TIDAL resolver;
- обрабатывать Yandex Music track links через Odesli -> TIDAL direct bridge;
- обрабатывать Yandex Music album links через Odesli metadata -> TIDAL candidates/scoring fallback;
- показывать copy-first publication UI с release line, tags, Music prompt и candidate/scoring details там, где это уместно.

### TIDAL Open API credentials

Multi-provider resolver использует TIDAL Open API credentials для candidate lookup и safe handoff.

Нужные переменные окружения:

- `TIDAL_CLIENT_ID`
- `TIDAL_CLIENT_SECRET`

Их нужно положить в `tidal-parser/.env`.
Файл `tidal-parser/.env` намеренно находится в `.gitignore` и не должен попадать в commit.

```env
TIDAL_CLIENT_ID=your_client_id_here
TIDAL_CLIENT_SECRET=your_client_secret_here
```

Без этих credential values:

- прямой TIDAL URL parsing может по-прежнему работать там, где не требуется Open API lookup;
- provider/manual resolver candidate lookup может быть недоступен или деградировать;
- UI должен безопасно откатываться к fallback-поведению, а не фабриковать результаты.

Безопасные границы:

- внешний response shape для TIDAL parse не менялся;
- existing TIDAL URL flow сохранён;
- cache logic сохранена;
- provider links используют safe fallback, если resolver не уверен;
- Qobuz / manual / Apple / Spotify / Yandex используют общий downstream TIDAL candidates/scoring/safe handoff там, где это применимо.

## Что умеет `genre-classifier`

`genre-classifier` - отдельный сервис аудио-классификации.

Он принимает аудиофайл, нормализует его через `ffmpeg`, прогоняет через модель Essentia / MusiCNN и возвращает сырые предсказания и нормализованные жанры.

Текущий production runtime после controlled ONNX default switch:

- default provider: `onnx_musicnn`;
- default Docker target: `onnx-runtime-slim`;
- external ONNX artifacts: `/opt/music-tools-artifacts/genre-classifier/onnx`;
- legacy rollback profile: `genre-classifier-legacy` / `legacy-runtime` / `GENRE_PROVIDER=legacy_musicnn`.

Legacy MusicNN path остаётся сохранён как fallback/rollback context. `essentia-tensorflow` пока не удалён, потому что ONNX preprocessing по-прежнему использует Essentia path.

## Основные возможности

- устойчивый парсинг HTML с резервной логикой;
- обогащение через Discogs и MusicBrainz;
- ограниченные повторные попытки при временных сбоях внешних API;
- нормализация релизов и provider identity без forced wrong match;
- предсказуемое объединение данных без неявного перетирания более сильных данных;
- структурированное логирование;
- request correlation через `request_id` и понятные user-facing error paths;
- lightweight runtime metrics через `/metrics` и согласованный process-level `/health`;
- централизованный settings layer для runtime-конфигурации `tidal-parser`;
- генерация `blog_output` из финального результата.

## Быстрый старт

Сейчас у `tidal-parser` и `genre-classifier` отдельные `docker-compose.yml`. Единого compose для всего репозитория нет.

### 1. Создать общую Docker network

Оба compose-файла ожидают внешнюю сеть `musicnet`.

```bash
docker network create musicnet
```

### 2. Запустить `genre-classifier`

```bash
cd /opt/music-tools/genre-classifier
docker compose up --build -d
```

Сервис поднимается на `http://localhost:8021`.

### 3. Подготовить `.env` для `tidal-parser`

Минимум нужны:

- `DISCOGS_TOKEN`, если нужно обогащение через Discogs;
- `MUSICBRAINZ_CONTACT_EMAIL`, чтобы `tidal-parser` отправлял корректный контакт в `User-Agent` для запросов к MusicBrainz.

Для удобства добавлены service-scoped примеры:

- `tidal-parser/.env.example`
- `genre-classifier/.env.example`

`genre-classifier/.env.example` использует текущий production default `GENRE_PROVIDER=onnx_musicnn`.

```env
DISCOGS_TOKEN=your_discogs_token
MUSICBRAINZ_CONTACT_EMAIL=you@example.com
```

### 4. Запустить `tidal-parser`

```bash
cd /opt/music-tools/tidal-parser
docker compose up --build -d
```

UI открывается через `tidal-parser`:

```text
http://localhost:8011
```

## Пример использования

### Через UI

1. Открыть `http://localhost:8011`
2. Вставить ссылку на TIDAL, Qobuz, Apple Music, Spotify, Yandex Music или manual release line
3. При необходимости выбрать `Тип`
4. Получить итоговый результат и `blog_output`

В текущей версии основной пользовательский сценарий проходит через UI `tidal-parser`. API тоже доступен, но в этом README он не документируется подробно, чтобы не фиксировать лишний публичный контракт до следующей ревизии документации.

## Ограничения текущей версии

- `tidal-parser` не меняет внешний response shape для TIDAL parse;
- existing TIDAL URL flow сохранён;
- cache logic сохранена;
- Apple `album?...i=<song_id>` stable track identity остаётся follow-up;
- Yandex/Odesli может rate-limit;
- Yandex album может не иметь direct TIDAL URL;
- provider identity tag-policy polish может быть отдельным follow-up;
- `genre-classifier` остаётся отдельным сервисом и не входит в один runtime с `tidal-parser`;
- качество результата по-прежнему зависит от доступности и структуры внешних источников;
- обогащение через Discogs зависит от `DISCOGS_TOKEN`;
- внешние источники могут деградировать частично, поэтому часть полей может быть пустой даже при успешном общем результате.

## Документация

- Архитектура: [docs/architecture.md](docs/architecture.md)
- Release notes: [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md)
- Release notes v0.3.0: [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md)
- Release notes v0.4.0: [docs/releases/v0.4.0.md](docs/releases/v0.4.0.md)
- Release notes v0.5.0: [genre-classifier/docs/releases/v0.5.0.md](genre-classifier/docs/releases/v0.5.0.md)
- Release notes v0.6.0: [tidal-parser/docs/releases/v0.6.0.md](tidal-parser/docs/releases/v0.6.0.md)
- Release notes v0.7.0: [docs/releases/v0.7.0.md](docs/releases/v0.7.0.md)

## Лицензия

Проект распространяется под лицензией MIT. Полный текст лицензии находится в [LICENSE](LICENSE).
