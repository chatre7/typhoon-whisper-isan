# Docker Deployment Guide

This guide covers deploying the Typhoon ASR API using Docker.

## Quick Start

```bash
# Clone or navigate to project directory
cd typhoon-isan

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f typhoon-asr-api

# Test the API
curl http://localhost:8000/
```

## Building the Image

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d --build

# Rebuild only
docker-compose build

# Pull pre-built image (if available)
docker-compose pull
```

### Using Docker CLI

```bash
# Build the image
docker build -t typhoon-asr-api:latest .

# Build with specific tag
docker build -t typhoon-asr-api:v2.0.0 .

# Build with no cache
docker build --no-cache -t typhoon-asr-api:latest .
```

## Running the Container

### With Docker Compose

```bash
# Start in detached mode
docker-compose up -d

# Start with logs visible
docker-compose up

# Start specific service
docker-compose up typhoon-asr-api

# Scale (if needed)
docker-compose up -d --scale typhoon-asr-api=2
```

### With Docker CLI

```bash
# Basic run
docker run -d \
  -p 8000:8000 \
  --name typhoon-asr \
  typhoon-asr-api:latest

# Run with volume for model cache
docker run -d \
  -p 8000:8000 \
  -v typhoon-models:/app/.cache/huggingface \
  --name typhoon-asr \
  typhoon-asr-api:latest

# Run with custom environment variables
docker run -d \
  -p 8000:8000 \
  -e PYTHONUNBUFFERED=1 \
  -e HF_HOME=/app/.cache/huggingface \
  --name typhoon-asr \
  typhoon-asr-api:latest
```

## GPU Support

### Prerequisites

1. Install NVIDIA Container Toolkit:

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. Verify GPU access:

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Enable GPU in Docker Compose

Edit `docker-compose.yml` and uncomment:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Then restart:

```bash
docker-compose down
docker-compose up -d --build
```

### Enable GPU with Docker CLI

```bash
docker run -d \
  --gpus all \
  -p 8000:8000 \
  --name typhoon-asr \
  typhoon-asr-api:latest
```

## Managing Containers

### Docker Compose Commands

```bash
# View logs
docker-compose logs -f
docker-compose logs -f --tail=100

# Stop containers
docker-compose stop

# Start stopped containers
docker-compose start

# Restart containers
docker-compose restart

# Remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# View container status
docker-compose ps
```

### Docker CLI Commands

```bash
# View logs
docker logs -f typhoon-asr
docker logs -f --tail=100 typhoon-asr

# Stop container
docker stop typhoon-asr

# Start stopped container
docker start typhoon-asr

# Restart container
docker restart typhoon-asr

# Remove container
docker rm typhoon-asr

# Remove container and force stop
docker rm -f typhoon-asr

# Execute commands in running container
docker exec -it typhoon-asr bash
docker exec typhoon-asr python -c "import torch; print(torch.cuda.is_available())"
```

## Volume Management

### List Volumes

```bash
# List all volumes
docker volume ls

# Inspect model cache volume
docker volume inspect typhoon-isan_model-cache
```

### Backup Model Cache

```bash
# Create backup
docker run --rm \
  -v typhoon-isan_model-cache:/source \
  -v $(pwd)/backup:/backup \
  alpine \
  tar czf /backup/model-cache-backup.tar.gz -C /source .

# Restore from backup
docker run --rm \
  -v typhoon-isan_model-cache:/target \
  -v $(pwd)/backup:/backup \
  alpine \
  tar xzf /backup/model-cache-backup.tar.gz -C /target
```

### Clean Up Volumes

```bash
# Remove specific volume
docker volume rm typhoon-isan_model-cache

# Remove all unused volumes
docker volume prune

# Remove all unused volumes without confirmation
docker volume prune -f
```

## Health Checks

The container includes health checks that run every 30 seconds:

```bash
# View health status
docker inspect --format='{{.State.Health.Status}}' typhoon-asr

# View detailed health logs
docker inspect typhoon-asr | jq '.[0].State.Health'
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs typhoon-asr-api

# Check container status
docker ps -a

# Inspect container
docker inspect typhoon-asr
```

### Out of Memory

```bash
# Limit memory usage in docker-compose.yml
services:
  typhoon-asr-api:
    mem_limit: 4g
    memswap_limit: 4g
```

### Model Download Issues

```bash
# Clear model cache
docker-compose down -v
docker-compose up -d

# Or manually
docker volume rm typhoon-isan_model-cache
```

### Permission Issues

```bash
# Run with specific user
docker run -d \
  -p 8000:8000 \
  --user $(id -u):$(id -g) \
  --name typhoon-asr \
  typhoon-asr-api:latest
```

## Production Deployment

### Using Docker Compose for Production

```yaml
version: '3.8'

services:
  typhoon-asr-api:
    build: .
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - model-cache:/app/.cache/huggingface
    environment:
      - PYTHONUNBUFFERED=1
    mem_limit: 4g
    cpus: 2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  model-cache:
```

### Behind Nginx Reverse Proxy

```nginx
upstream typhoon-asr {
    server localhost:8000;
}

server {
    listen 80;
    server_name asr.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://typhoon-asr;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Performance Optimization

### Build Optimization

```dockerfile
# Use multi-stage build (add to Dockerfile)
FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install uv && uv pip install --system -r pyproject.toml

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Resource Limits

```bash
# Limit CPU and memory
docker run -d \
  -p 8000:8000 \
  --cpus="2" \
  --memory="4g" \
  --name typhoon-asr \
  typhoon-asr-api:latest
```

## Monitoring

### Container Stats

```bash
# Live stats
docker stats typhoon-asr

# Docker Compose stats
docker-compose stats
```

### Export Metrics

```bash
# Get metrics from FastAPI
curl http://localhost:8000/metrics
```

## Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or with Docker CLI
docker stop typhoon-asr
docker rm typhoon-asr
docker build -t typhoon-asr-api:latest .
docker run -d -p 8000:8000 --name typhoon-asr typhoon-asr-api:latest
```
