# music-tools

`music-tools` — монорепозиторий с двумя сервисами для извлечения, обогащения и нормализации музыкальных данных:

- `tidal-parser` — main API/orchestration service;
- `genre-classifier` — audio classification service.

Схема pipeline:

`TIDAL -> parse_tidal -> Discogs -> MusicBrainz -> audio classifier -> merge -> cache`

Проект делает упор на устойчивость пайплайна, предсказуемость результата и прозрачную обработку данных. Здесь нет сложной "магии": источники объединяются через простые и объяснимые правила, а сбои внешних API по возможности обрабатываются через безопасную деградацию. После `v0.1` проект стал устойчивее в работе с внешними интеграциями, лучше наблюдается в эксплуатации и аккуратнее управляется через конфигурацию. После Roadmap 3 production runtime `genre-classifier` модернизирован с Python 3.6 / TensorFlow 1.15 до Python 3.12.13 / TensorFlow 2.21.0 без изменения production-контракта.

## Архитектура

### `tidal-parser`

Основной сервис координации и UI.

Что делает:
- парсит TIDAL-страницу через HTML + JSON-LD с резервной логикой;
- извлекает базовые метаданные;
- обогащает релиз через Discogs и MusicBrainz;
- при наличии аудиофайла вызывает `genre-classifier`;
- нормализует жанры;
- объединяет данные с учётом качества источников;
- формирует `blog_output`;
- кэширует результат;
- различает пользовательские ошибки и внутренние сбои на входном слое.

### `genre-classifier`

Отдельный сервис аудио-классификации.

Что делает:
- принимает аудиофайл;
- нормализует его через `ffmpeg`;
- прогоняет через модель Essentia / MusiCNN;
- возвращает сырые предсказания и нормализованные жанры.

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
- нормализация жанров в едином внутреннем формате;
- предсказуемое объединение данных без неявного перетирания более сильных данных;
- структурированное логирование;
- request correlation через `request_id` и более понятные user-facing error paths;
- lightweight runtime metrics через `/metrics` и согласованный process-level `/health`;
- централизованный settings layer для runtime-конфигурации `tidal-parser`;
- корректное разделение допустимой деградации результата и фатальных ошибок;
- генерация `blog_output` из финального результата.

## Статус релиза v0.5.0

`v0.5.0` фиксирует ONNX default runtime для `genre-classifier`.

ONNX MusiCNN стал default provider, default target переключён на `onnx-runtime-slim`, а legacy MusicNN path остался как rollback/fallback context. `/classify` contract и response shape не менялись. `tidal-parser` code в этом switch не менялся.

Детали: [docs/releases/v0.5.0.md](docs/releases/v0.5.0.md) и [genre-classifier/docs/onnx-runtime.md](genre-classifier/docs/onnx-runtime.md).

## Статус релиза v0.3.0

`v0.3.0` завершает Roadmap 2 как LLM migration foundation для `genre-classifier`.

`legacy_musicnn` остаётся default provider. `/classify` API и response shape не менялись. Production responses остаются legacy-only. Canary rollout, production cutover и default-provider switch не входят в `v0.3.0`.

Детали: [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md) и [genre-classifier/docs/eval/roadmap-2.16-release-readiness-and-v0.3-decision.md](genre-classifier/docs/eval/roadmap-2.16-release-readiness-and-v0.3-decision.md).

## Краткая схема работы

- `tidal-parser` — точка входа для UI и API;
- `genre-classifier` — изолированный сервис для работы с аудио;
- сервисы общаются по HTTP внутри Docker network;
- Docker Compose конфигурации service-scoped и разделены по сервисам;
- Discogs и MusicBrainz используются как внешние источники метаданных;
- итоговый результат собирается в слое координации и затем кэшируется;
- каждый сервис сейчас запускается своим `docker-compose.yml`.

## Быстрый старт

Сейчас у `tidal-parser` и `genre-classifier` отдельные `docker-compose.yml`. Единого compose для всего репозитория пока нет.

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
2. Вставить ссылку на TIDAL `track` или `album`
3. При необходимости приложить аудиофайл для жанровой классификации
4. Получить итоговый результат и `blog_output`

В текущей версии основной пользовательский сценарий проходит через UI `tidal-parser`. API тоже доступен, но в этом README он не документируется подробно, чтобы не фиксировать лишний публичный контракт до следующей ревизии документации.

## Ограничения текущей версии

- проект развивается как монорепозиторий с раздельным запуском сервисов, без единого compose для всего стека;
- `genre-classifier` остаётся отдельным сервисом; canary rollout, LLM production adoption и lighter non-TensorFlow model migration остаются будущей работой;
- качество результата зависит от доступности и структуры TIDAL HTML;
- обогащение через Discogs зависит от `DISCOGS_TOKEN`;
- внешние источники могут деградировать частично, поэтому часть полей может быть пустой даже при успешном общем результате;
- жанровая классификация не делает семантическое сопоставление и не пытается "угадывать" синонимы.

## Roadmap

- привести запуск монорепозитория к более цельной dev-схеме;
- удержать ONNX default runtime и отдельно рассматривать дальнейшие runtime-эксперименты только будущими этапами;
- рассмотреть LLM production adoption и lighter non-TensorFlow classifier migration в отдельной Roadmap 4 или позже;
- расширить покрытие проверок smoke/integration;
- улучшить документацию по окружению и эксплуатации.

## Документация

- Архитектура: [docs/architecture.md](docs/architecture.md)
- Release notes: [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md)
- Release notes v0.3.0: [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md)
- Release notes v0.4.0: [docs/releases/v0.4.0.md](docs/releases/v0.4.0.md)

## Лицензия

Проект распространяется под лицензией MIT. Полный текст лицензии находится в [LICENSE](LICENSE).
