# Передача контекста music-tools

Обновлено: 2026-10-18. Это снимок для продолжения; live-состояние проверять отдельно.

## Текущая задача

- Подготовка передачи завершена: компактные AGENTS.md, HANDOFF.md и вход из README.
- Пользователь разрешил коммит и push этих документов 2026-10-18; результат
  проверить через Git. Следующая функциональная задача пока не задана.
- Новый чат: «Работай в /opt/music-tools. Прочитай AGENTS.md и HANDOFF.md,
  проверь git status и продолжи задачу: <задача>».

## Подтверждённое состояние

- Базовый коммит приложения: 7125a3c, main. Актуальный HEAD смотреть в Git.
- Документация проверена через git diff --check; runtime не менялся.
- 2026-10-11: 7125a3c отправлен в origin/main, образ tidal-parser пересобран,
  контейнер заменён; /health healthy, UI HTTP 200. Сегодня production не проверялся.
- Тогда прошли 260 тестов парсера на хосте и в образе; 47 предупреждений
  Starlette TemplateResponse. Полный классификатор: 407 passed / 42 failed
  (удалённые исторические evidence-файлы и рассинхрон теста/скрипта), core: 255 passed.

## Важные решения и точки входа

- app/music_prompt.py в tidal-parser: единый build_music_prompt для двух веток UI.
  Только данные релиза, реальные TIDAL/Qobuz ссылки, DTF-запросы, дополнительные
  задачи; постоянные правила находятся в пользовательском проекте «Музыка».
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
