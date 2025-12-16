FROM mevis_compute_worker:base

# This makes output not buffer and return immediately, nice for seeing results in stdout
ENV PYTHONUNBUFFERED 1
ENV DOCKER_API_VERSION 1.42

WORKDIR /app

# Add the application source (this layer will change when code changes)
ADD compute_worker .
COPY ./src/settings/logs_loguru.py /usr/bin

CMD celery -A compute_worker worker \
    -l info \
    -Q compute-worker \
    -n compute-worker@%n \
    --concurrency=1
