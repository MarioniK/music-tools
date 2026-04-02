# Music Tools

Набор сервисов для музыкального пайплайна.

## Сервисы

### `tidal-parser`
Главный orchestration layer.

Функции:
- разбор ссылок TIDAL
- получение жанров релиза через Discogs
- получение года, страны и типа релиза через MusicBrainz
- вызов `genre-classifier`
- формирование итоговых жанров
- генерация вывода для блога

### `genre-classifier`
Отдельный сервис анализа аудио.

Функции:
- принимает аудиофайл
- нормализует его через ffmpeg
- прогоняет через модель Essentia / MusiCNN
- возвращает сырые и мягко нормализованные жанры

## Запуск

### genre-classifier
```bash
cd /opt/music-tools/genre-classifier
docker compose up -d