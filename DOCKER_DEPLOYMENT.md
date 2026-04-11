# Docker Deployment Guide

Deploy the Telegram Ticketing Bot using Docker for easy setup and management.

## Prerequisites

- Docker and Docker Compose installed
- `.env` file configured (copy and edit from `.env.example`)
- Docker daemon running

## Quick Start

### 1. Prepare Environment
```bash
# Copy and configure .env
cp .env.example .env
# Edit .env with your actual credentials
nano .env
```

### 2. Build and Run
```bash
# Build the Docker image
docker-compose build

# Start the bot
docker-compose up -d

# Check logs
docker-compose logs -f ticketingbot
```

### 3. Verify Running
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs ticketingbot

# Stop bot
docker-compose down
```

## Docker Configuration

### Image Details
- **Base Image:** `python:3.11-slim` (minimal, security-focused)
- **User:** Non-root user `botuser` (1000:1000)
- **Security:** No new privileges, read-only filesystem where possible
- **Size:** ~200 MB (slim base image)

### Volumes
```yaml
volumes:
  - ./logs:/app/logs           # Persistent logs
  - ./bot/data:/app/bot/data   # Persistent tickets/queue
```

### Resource Limits
- **CPU:** Limited to 1 core (max), 0.5 core (reserved)
- **Memory:** Limited to 512 MB (max), 256 MB (reserved)
- Adjust values in `docker-compose.yml` based on your hardware

### Restart Policy
- `restart: unless-stopped` - Automatically restart on failure, unless manually stopped

### Logging
- **Driver:** json-file
- **Max size:** 10 MB per file
- **Backups:** 5 previous logs kept

## Production Deployment

### Option 1: Docker Swarm (Simple)
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml ticketingbot

# Monitor
docker service logs -f ticketingbot_ticketingbot
```

### Option 2: Kubernetes (Advanced)
See `kubernetes/` directory for Helm charts or kustomize templates.

### Option 3: Managed Container Services
- **AWS ECS:** Use ECR registry, ECS task definition
- **Google Cloud Run:** Deploy containerized bot
- **Azure Container Instances:** Simple serverless deployment

## Building Custom Images

### Build for specific architecture
```bash
# ARM64 (Raspberry Pi, Apple Silicon)
docker buildx build --platform linux/arm64 -t ticketingbot:arm64 .

# AMD64 (x86)
docker buildx build --platform linux/amd64 -t ticketingbot:amd64 .

# Multi-arch
docker buildx build --platform linux/amd64,linux/arm64 -t ticketingbot:latest .
```

### Tag and push to registry
```bash
# Tag image
docker tag ticketingbot:latest myregistry.azurecr.io/ticketingbot:latest

# Push to registry
docker push myregistry.azurecr.io/ticketingbot:latest
```

## Monitoring

### Check Bot Health
```bash
# View real-time logs
docker-compose logs -f --tail=50 ticketingbot

# Monitor resource usage
docker stats ticketingbot

# Check container status
docker-compose ps
```

### View Log Files
```bash
# Logs directory on host
ls -la logs/

# Stream logs
tail -f logs/bot.log | grep ERROR

# Full logs with timestamps
docker-compose logs --timestamps ticketingbot
```

## Troubleshooting

### Bot won't start
```bash
# Check logs
docker-compose logs ticketingbot

# Common issues:
# 1. Invalid TELEGRAM_BOT_TOKEN
# 2. Invalid SMTP credentials
# 3. Permission denied on logs/ directory

# Fix permissions
sudo chown -R $USER:$USER logs bot/data
```

### High memory usage
```bash
# Check memory stats
docker stats ticketingbot

# Reduce in docker-compose.yml:
# memory: 256M (instead of 512M)
```

### Port conflicts (if using ports)
```bash
# List port usage
sudo netstat -tlnp | grep 8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

## Backup and Restore

### Backup Data
```bash
# Backup volumes
docker run --rm -v ticketingbot_logs:/logs -v ticketingbot_data:/data \
  -v $(pwd)/backups:/backup alpine tar czf /backup/bot-backup.tar.gz /logs /data

# Backup .env
cp .env .env.backup
```

### Restore Data
```bash
# Stop bot
docker-compose down

# Restore from backup
docker run --rm -v ticketingbot_logs:/logs -v ticketingbot_data:/data \
  -v $(pwd)/backups:/backup alpine tar xzf /backup/bot-backup.tar.gz -C /

# Start bot
docker-compose up -d
```

## Security Best Practices

1. **Image Security**
   - [ ] Use specific Python version (not latest)
   - [ ] Run non-root user (botuser)
   - [x] Multi-stage build to reduce image size
   - [x] No new privileges flag enabled

2. **Environment Secrets**
   - [ ] Use Docker secrets (Swarm) or Kubernetes secrets
   - [ ] Never hardcode credentials in Dockerfile
   - [ ] Use `.env` file with restricted permissions: `chmod 600 .env`

3. **Network Security**
   - [ ] Run behind firewall/reverse proxy
   - [ ] No exposed ports unless necessary
   - [ ] Use HTTPS for any external communication

4. **Container Security**
   - [ ] Regular image updates
   - [ ] Scan images for vulnerabilities: `docker scan ticketingbot`
   - [ ] Use Docker Content Trust for signed images
   - [ ] Keep Docker daemon updated

## Environment Variables (Docker)

All environment variables come from `.env` file:
```bash
env_file:
  - .env
```

Alternatively, pass via command line:
```bash
docker run -e TELEGRAM_BOT_TOKEN=xxxxx ticketingbot:latest
```

Or use Docker secrets (Swarm/Kubernetes):
```bash
docker secret create telegram_token -
docker service create --secret telegram_token ticketingbot
```

## Performance Tuning

### Increase Resources (if needed)
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

### Optimize Startup
- Reduce LOG_LEVEL to INFO in production
- Pre-build images on CI/CD (faster deployment)
- Use `docker-compose up -d` for background startup

### Monitor Performance
```bash
# CPU/Memory usage
docker stats --no-stream ticketingbot

# Network I/O
docker stats --no-stream --format "table {{.Container}}\t{{.NetIO}}"

# Disk usage of image
docker images ticketingbot --format "{{.Size}}"
```

## Updates and Upgrades

### Update Bot Code
```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build --no-cache

# Restart with new image
docker-compose up -d
```

### Update Dependencies
1. Update `requirements.txt`
2. Rebuild: `docker-compose build --no-cache`
3. Test in staging
4. Deploy to production

## Cleanup

### Remove unused resources
```bash
# Stop containers
docker-compose down

# Remove images
docker rmi ticketingbot:latest

# Prune unused images/containers
docker system prune -a
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v4
  with:
    push: true
    tags: myregistry.azurecr.io/ticketingbot:${{ github.sha }}
    registry: myregistry.azurecr.io
```

### GitLab CI
```yaml
build-docker:
  image: docker:latest
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

---
**Last Updated:** 2026-04-11
