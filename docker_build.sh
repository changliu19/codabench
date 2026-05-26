#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-codalab/codabench-compute-worker}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORM="${PLATFORM:-linux/amd64}"

docker build \
  --platform "${PLATFORM}" \
  -f packaging/container/Containerfile.compute_worker \
  -t "${IMAGE_NAME}:${IMAGE_TAG}" \
  .

docker tag "${IMAGE_NAME}:${IMAGE_TAG}" local_compute_worker:latest
