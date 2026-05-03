ARG PYTHON_BASE_IMAGE=python:3.12.13-slim-bookworm@sha256:58525e1a8dada8e72d6f8a11a0ddff8d981fd888549108db52455d577f927f77
FROM ${PYTHON_BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ffmpeg \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir --requirement /app/requirements.txt

COPY app /app/app

EXPOSE 8021

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8021"]
