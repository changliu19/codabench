docker build -f Dockerfile.compute_worker.base -t local_compute_worker:base .

docker build -f Dockerfile.compute_worker.app -t local_compute_worker:latest .
