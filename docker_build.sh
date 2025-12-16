docker build -f Dockerfile.compute_worker.base -t codalab/compute_worker:base .

docker build -f Dockerfile.compute_worker.app -t codalab/compute_worker:latest .