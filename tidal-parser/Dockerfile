FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

RUN groupadd --system tidal-parser \
    && useradd --system --gid tidal-parser --home-dir /nonexistent --shell /usr/sbin/nologin tidal-parser \
    && mkdir -p /app/data \
    && chown -R tidal-parser:tidal-parser /app/data

USER tidal-parser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
