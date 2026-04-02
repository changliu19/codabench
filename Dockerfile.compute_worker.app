FROM codalab/compute_worker:base

ENV PYTHONUNBUFFERED 1
ENV DOCKER_API_VERSION 1.42

WORKDIR /app

ADD compute_worker .
COPY ./src/settings/logs_loguru.py /.venv/bin

CMD celery -A compute_worker worker \
    -l info \
    -Q compute-worker \
    -n compute-worker@%n \
    --concurrency=1
