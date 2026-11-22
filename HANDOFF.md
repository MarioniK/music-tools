# Передача контекста music-tools

Обновлено: 2026-11-22. Это снимок для продолжения; live-состояние проверять отдельно.

## Текущая задача и результат

- Сокращены и починены тесты (2026-11-22, всё закоммичено и отправлено в origin/main):
  - tidal-parser/tests: общие фикстуры post_form/get_api (conftest.py) и хелперы
    (helpers.py: patch_lookup, patch_build_result, forbid_lookup, tidal_* построители);
    тесты Qobuz, cache_safety, Apple Music, Spotify, Odesli переписаны на них,
    однотипные сценарии параметризованы. Тестов 261, покрытие 78% без изменений,
    объём tests/ 7183 -> 5784 строки.
  - genre-classifier: починены 42 падающих lightweight-теста. Причина — коммит ce42c37
    (roadmap 4.108) удалил parity-scaffold/*.json и roadmap-4.*.md, а валидатор и тесты на них
    опирались. Списки удалённых файлов в validate_evaluation_artifacts.py обнулены, из
    musicnn_onnx_parity_scaffold.py убрана проверка roadmap-4.32, удалены 38 тестов удалённых
    отчётов (27 в test_evaluation_artifacts_validator, 10 в test_parity_scaffold_dry_run_evidence,
    1 устаревший в test_musicnn_onnx_output_capture, написан под API 4.51).
- Мёртвый код validate_evaluation_artifacts.py удалён (faf51f4): 13 пустых *_REPORT_FILES, их циклы,
  16 функций проверок, 54 осиротевших константы/функции, 13 полей ValidationSummary и их вывод в CLI;
  4785 -> 2241 строка, из теста убраны проверки этих полей. 411 passed на полной копии в LXC 109.
- Ранее в этот день: кнопка копирования ссылки в поле ввода (tidal-parser, 857a52c), проверена владельцем.

## Подтверждённое состояние

- Коммиты 2026-11-22: 857a52c (кнопка), f01b98d, 8af67d4, 91b6360, a7e44e6, 3b68082, 5868802 (тесты
  parser), c83b1ef (тесты classifier). Commit, выкладка на сервер и push разрешены владельцем.
- Проверено на сервере (LXC 109): tidal-parser 261 passed, genre-classifier 411 passed
  (tests, включая lightweight), падений нет. Покрытие parser измерено coverage: 831 из 3825
  строк не покрыто (78%) до и после рефакторинга. Тяжёлый inference и /classify не запускались.
- Кнопка копирования: деплой без сборки (./app смонтирован, достаточно restart), /health 200.
- Ранее: 12c8d2c (убраны DTF-запросы из промта) развёрнут 2026-10-18; 7125a3c — 2026-10-11.

## Рабочий процесс и доступ

- Разработка идёт локально на Mac (~/music-tools). С Mac нет доступа к GitHub по SSH,
  поэтому коммиты едут на сервер через git bundle (scp на Proxmox, pct push в LXC 109,
  git pull --ff-only), push в GitHub выполняется с сервера (/opt/music-tools).
- SSH: ssh proxmox, затем pct exec 109. Прямого алиаса на 10.0.1.55 нет.
- Веб: https://tidal.intelihouse.by через Cloudflare Tunnel (коннектор cloudflared в LXC 100)
  на 10.0.1.55:8011. CLAUDE.md описывает инфраструктуру подробнее.

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

## Проверки на сервере (LXC 109)

Изолированные окружения вне Git: /root/.local/share/music-tools-test-envs/.
Локальный runner создаёт временную SQLite-базу для тестов парсера:

```bash
python3 /root/.local/share/music-tools-test-envs/run_tests.py tidal-parser
python3 /root/.local/share/music-tools-test-envs/run_tests.py genre-classifier tests -q
```

Не запускать тесты против production DB. На Mac pytest и зависимости не установлены.

## Отложено и ограничения

- OpenClaw и его копии Codex на сервере не трогать. Cursor удалён с сервера 2026-11-22
  (/root/.cursor-server и /root/.cursor).
- docs/ классификатора почищены (14a1ae5, 6f4d61c): удалены 194 файла без ссылок из живых файлов
  (1.5 МБ -> 304 КБ). Остались 31 используемый файл (код/тесты/README/CHANGELOG ссылаются),
  13 достижимых по цепочке доков, README в roadmap-3.5/*, roadmap-4.108-...cleanup.md и
  template-real-onnx-model-provenance.json. Тесты parser без уникального покрытия строк
  (177 из 260, жадно убираемых 144) проверены per-test coverage 2026-11-22 и оставлены: строчное
  покрытие не видит ассертов, удаление снизило бы защиту от регрессий. Возможная отдельная
  задача: 27 групп с идентичным набором строк (68 тестов) свернуть в parametrize.
- Туннель tidal.intelihouse.by проверен 2026-11-22 (журнал cloudflared в LXC 100 за 7 дней):
  ошибок на origin :8011 нет, UDP/QUIC-предпроверка проходит, снаружи 200; единственный обрыв
  с краем Cloudflare 2026-11-20 ~16:00. Записи от 2026-10-13 из журнала уже ушли, --protocol http2
  не нужен. Ошибки origin на других портах (18789, 8006, 8123, 7655 и др.) относятся не к парсеру.
  Токен туннеля частично попал в вывод при диагностике 2026-11-22: владелец решает, перевыпускать ли.
- Секреты не читать/печатать; обновление ключей пользователь отложил.
