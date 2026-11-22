# music-tools

Основные инструкции для агента: `AGENTS.md`, текущее состояние: `HANDOFF.md`, правила предметной области: `PROJECT_RULES.md`. Здесь только то, чего нет в этих файлах.

## Где работает прод
- LXC 109 `docker` на Proxmox, IP 10.0.1.55, рабочая копия репозитория `/opt/music-tools` (ветка `main`, `origin` = `git@github.com:MarioniK/music-tools.git`).
- SSH только через хост Proxmox: `ssh proxmox`, затем `pct exec 109 -- …`. Прямого алиаса на 10.0.1.55 нет.
- Веб: https://tidal.intelihouse.by → Cloudflare Tunnel (коннектор cloudflared в LXC 100, служба `cloudflared`, токен в unit-файле; не выводить аргументы процесса) → `http://10.0.1.55:8011`. Классификатор: порт 8021.
- Артефакты ONNX: `/opt/music-tools-artifacts/genre-classifier/onnx` (вне git).

## Как деплоили
- Правки вносились прямо на сервере в `/opt/music-tools`, затем коммит и push в GitHub; ветка `main` на сервере и `origin/main` совпадали.
- Применение: `docker compose up --build -d <сервис>` из каталога сервиса. Затем `docker builder prune -f` и `docker image prune -f`; проверка `/health` и HTTP 200 у UI.
- Тесты: `run_tests.py <сервис> …`. Полный прогон долгий, обычно запускают точечно.
- Commit, push и deploy только по разрешению владельца для текущей задачи (см. `AGENTS.md`).

## Эта локальная копия
- Разработка ведётся здесь, на Mac. С Mac нет доступа к GitHub (нет SSH-ключа), поэтому `git push` идёт через сервер: коммиты передаются на сервер через `git bundle` (`pct push` в LXC 109, затем `git pull --ff-only <bundle> main` в `/opt/music-tools`), оттуда `git push origin main`.
- Актуальность: перед работой сверяй `git log` на сервере (`ssh proxmox 'pct exec 109 -- git -C /opt/music-tools log --oneline -3'`) с локальным; если на сервере есть коммиты, которых нет здесь, сначала получи их через `git bundle` с сервера.
- Любое изменение рабочей копии на сервере (pull, deploy) и push только по разрешению владельца.
- Клон создан 2026-11-22 из `git bundle` с сервера.
