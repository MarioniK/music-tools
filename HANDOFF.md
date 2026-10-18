# Передача контекста music-tools

Обновлено: 2026-10-18. Это снимок для продолжения; live-состояние проверять отдельно.

## Текущая задача и результат

- Удалены заголовок «DTF-запросы» и генерация четырёх запросов из
  tidal-parser/app/music_prompt.py; лишнего пустого блока нет.
- Остальные данные и порядок сохранены; последняя строка по заданию:
  «Правила оформления и источников: по инструкциям проекта».
- Обновлены тесты, добавлена точная проверка промта ENIGMA — Voyageur (2003).
- Отдельного флага DTF-запросов нет. UI-ссылки My DTF в Search helpers
  не относятся к копируемому промту и в этой задаче не менялись.

## Подтверждённое состояние

- Начальный HEAD: 980d6bc, main синхронизирована с origin/main; дерево было чистым.
- Изменение: 12c8d2c; commit/push и production deploy разрешены пользователем
  2026-10-18, коммит отправлен в origin/main.
- Проверка: run_tests.py tidal-parser tests/test_music_prompt.py -q — 28 passed.
  git diff --check — без ошибок. Тесты используют временную SQLite-базу.
- Общий run_tests.py tidal-parser остановлен (код 130), поскольку долго
  не выдавал результат; успешный полный прогон этой задачи не подтверждён.
- Production пересобран через docker compose up --build -d tidal-parser;
  контейнер заменён, /health healthy, UI HTTP 200. Проверка ENIGMA — Voyageur
  внутри нового контейнера подтвердила отсутствие DTF-запросов и новую строку правил.
- Постбилд-очистка: docker builder prune -f и docker image prune -f;
  освобождено 880.4 kB, удалён старый образ без тега; тома не затронуты.
  На / свободно 7.8G (занято 75%).
- Ранее: 7125a3c развёрнут 2026-10-11; тогда 260 тестов парсера прошли.
  Классификатор: 407 passed / 42 failed (historical/lightweight), core: 255 passed.

## Важные решения и точки входа

- app/music_prompt.py в tidal-parser: единый build_music_prompt для двух веток UI.
  Только данные релиза, реальные TIDAL/Qobuz ссылки и дополнительные задачи;
  постоянные правила и поиск по claude/dtf_index.txt — в пользовательском проекте.
- Теги: main.py/build_blog_output, genre_normalization.py/genre_to_blog_tag.
  nostalgia <2015, catalog 2015–2025, new только 2026; EP отдельно от album;
  #newrelease #dailylist только single/track 2026; &/and → n; #nostalgie.
- Для неизвестных типа/периода промт сообщает «неизвестен», факты не додумывает.
- entity_type — тип ссылки; release_kind — тип релиза (PROJECT_RULES.md).
- Сервисы общаются по HTTP в musicnet: tidal-parser :8011, genre-classifier :8021.
  У каждого свой docker-compose.yml. Парсер монтирует ./app и ./data;
  перезапуск загружает Python, пересборка сохраняет код и внутри образа.
- Код provider defaults/ONNX и внешние модели классификатора не менять попутно;
  архитектура — docs/architecture.md, подробнее runtime — README.md по необходимости.

## Проверки на этом хосте

Изолированные окружения вне Git: /root/.local/share/music-tools-test-envs/.
Локальный runner создаёт временную SQLite-базу для тестов парсера:

```bash
python3 /root/.local/share/music-tools-test-envs/run_tests.py tidal-parser
python3 /root/.local/share/music-tools-test-envs/run_tests.py genre-classifier tests -q --ignore=tests/lightweight
```

Эти пути специфичны для хоста; при их отсутствии подготовить venv по импортам
тестов и requirements нужного сервиса. Не запускать тесты против production DB.

## Отложено и ограничения

- Cursor Server пока оставлен по просьбе пользователя: удалить после ещё пары
  проверенных изменений и нового подтверждения. Старый Codex-бинарник его
  расширения уже удалён; OpenClaw и его копии Codex не трогать.
- Исправление 42 historical/lightweight тестов классификатора — отдельная задача.
- Секреты не читать/печатать; обновление ключей пользователь отложил.
- Старый временный AGENT_REPORT.md удалён при предыдущем коммите.
