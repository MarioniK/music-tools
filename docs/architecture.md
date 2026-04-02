# Architecture

## Overview

Проект состоит из двух сервисов:

- `tidal-parser`
- `genre-classifier`

## Service roles

### tidal-parser
Основной сервис, который:
1. принимает ссылку TIDAL
2. извлекает базовые метаданные
3. ищет жанры релиза в Discogs
4. ищет год, страну и тип релиза в MusicBrainz
5. при наличии аудиофайла отправляет его в `genre-classifier`
6. объединяет результаты
7. формирует итоговый вывод для блога

### genre-classifier
Сервис, который:
1. принимает аудиофайл
2. нормализует его через ffmpeg
3. анализирует через модель MusiCNN
4. возвращает сырые и нормализованные жанры

## Data flow

TIDAL URL
→ tidal-parser
→ Discogs
→ MusicBrainz
→ optional audio upload
→ genre-classifier
→ final merge
→ blog output

## Networking

Оба сервиса подключены к общей docker-сети:

- `musicnet`

Внутренний URL classifier:

- `http://genre-classifier:8021/classify`

## Notes

- Discogs не всегда даёт год
- MusicBrainz может матчиться нестабильно, поэтому кэш и merge-логика важны
- genre-classifier не должен принимать финальные редакторские решения за весь пайплайн