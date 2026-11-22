# Передача контекста music-tools

Обновлено: 2026-11-22. Это снимок для продолжения; live-состояние проверять отдельно.

## Текущая задача и результат

- В tidal-parser/app/templates/index.html добавлена кнопка копирования ссылки
  рядом с полем ввода (слева от кнопки очистки): копирует текущее значение поля,
  скрыта при пустом поле, после копирования на 1,2 с показывает «✓».
  Для этого в общую функцию подписи добавлен необязательный data-copied-label;
  остальные кнопки Copy работают как раньше. Стили — static/style.css
  (.copy-url-btn), отступ текста в поле увеличен до 80px.
- Версия style.css в ссылке заменена на v=copy-url-button (сброс кеша браузера).

## Подтверждённое состояние

- Изменение: 857a52c; commit, выкладка на сервер и push в origin/main разрешены
  пользователем 2026-11-22. Владелец проверил кнопку на живом сервере: работает.
- Деплой без сборки: ./app смонтирован, достаточно docker compose restart tidal-parser;
  после рестарта /health 200, публичная страница отдаёт новую кнопку и CSS.
- Локально проверено в браузере на отрендеренном шаблоне (jinja2): кнопка не
  пересекается с крестиком, скрывается при пустом поле, реальный клик даёт «✓».
  Автотестов на эти элементы UI нет; тесты парсера в этой задаче не запускались.
- Ранее: 12c8d2c (убраны DTF-запросы из промта) развёрнут 2026-10-18; 7125a3c — 2026-10-11,
  тогда 260 тестов парсера прошли. Классификатор: 407 passed / 42 failed
  (historical/lightweight), core: 255 passed.

## Рабочий процесс и доступ

- Разработка идёт локально на Mac (~/music-tools). С Mac нет доступа к GitHub по SSH,
  поэтому коммиты едут на сервер через git bundle (scp на Proxmox, pct push в LXC 109,
  git pull --ff-only), push в GitHub выполняется с сервера (/opt/music-tools).
- SSH: ssh proxmox, затем pct exec 109. Прямого алиаса на 10.0.1.55 нет.
- Веб: https://tidal.intelihouse.by через Cloudflare Tunnel (коннектор в LXC 108)
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
python3 /root/.local/share/music-tools-test-envs/run_tests.py genre-classifier tests -q --ignore=tests/lightweight
```

Не запускать тесты против production DB. На Mac pytest и зависимости не установлены.

## Отложено и ограничения

- Cursor Server на сервере пока оставлен по просьбе пользователя: удалить после
  нового подтверждения. OpenClaw и его копии Codex не трогать.
- Исправление 42 historical/lightweight тестов классификатора — отдельная задача.
- Полный прогон тестов tidal-parser после 12c8d2c и 857a52c не подтверждён.
- Туннель tidal.intelihouse.by: 2026-10-13 в логах cloudflared были обрывы QUIC
  (timeout, DNS i/o timeout); мера (--protocol http2) обсуждалась, но не применялась.
- Секреты не читать/печатать; обновление ключей пользователь отложил.
