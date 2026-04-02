FROM local_compute_worker:base

ENV PYTHONUNBUFFERED 1
ENV DOCKER_API_VERSION 1.42

RUN apt-get update && apt-get install -y aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./compute_worker/celery_config.py ./compute_worker/compute_worker.py ./
COPY ./src/settings/logs_loguru.py /app/.venv/bin

CMD celery -A compute_worker worker \
    -l info \
    -Q compute-worker \
    -n compute-worker@%n \
    --concurrency=1
