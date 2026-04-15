# Docker Quick Reference

## Build the Image

```bash
# Build with docker-compose (recommended)
docker-compose build

# Build with docker directly
docker build -t ticketing-bot:latest .
```

## Run Locally (for testing)

```bash
# Using docker-compose
docker-compose up -d
docker-compose logs -f

# Stop
docker-compose down
```

## Deploy to Ubuntu Server

### Quick Start (3 steps)

```bash
# 1. Transfer project to server
scp -r . user@your-server:/opt/ticketing-bot

# 2. SSH into server
ssh user@your-server
cd /opt/ticketing-bot

# 3. Set up environment and deploy
sudo bash deploy-ubuntu.sh

# 4. Start the bot
sudo docker-compose up -d
```

### Manual Setup on Ubuntu

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker & Compose
sudo apt-get install -y docker.io docker-compose

# Create .env file with your settings
sudo nano .env
# Add: TELEGRAM_TOKEN, COMPANY_NAME, SUPPORT_EMAIL, LOG_LEVEL

# Build and run
sudo docker-compose build
sudo docker-compose up -d

# Check status
sudo docker-compose ps
sudo docker-compose logs -f
```

## Container Management

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs
docker logs -f ticketing-bot
docker-compose logs -f

# Stop container
docker stop ticketing-bot
docker-compose stop

# Restart container
docker restart ticketing-bot
docker-compose restart

# Remove container
docker rm ticketing-bot
docker-compose down

# Execute command in running container
docker exec -it ticketing-bot bash

# Inspect container
docker inspect ticketing-bot
```

## Image Management

```bash
# List images
docker images

# View image details
docker inspect ticketing-bot:latest

# Remove image
docker rmi ticketing-bot:latest

# Tag image
docker tag ticketing-bot:latest myregistry/ticketing-bot:v1.0

# Push to registry
docker push myregistry/ticketing-bot:v1.0
```

## Data & Volumes

```bash
# View volume mount points
docker inspect ticketing-bot | grep -A 10 Mounts

# Backup data
tar -czf backup-data.tar.gz data/ logs/

# Restore from backup
tar -xzf backup-data.tar.gz

# Access files from host
ls -la data/
ls -la logs/
```

## Troubleshooting

```bash
# Check if container is running
docker ps | grep ticketing-bot

# View full logs
docker logs ticketing-bot | tail -100

# Check container stats
docker stats ticketing-bot

# Validate docker-compose.yml
docker-compose config

# Check docker daemon health
docker system info

# Remove stopped containers and dangling images
docker system prune

# Force remove everything (WARNING: destructive)
docker system prune -a
```

## Environment Variables

See `.env.example` for template. Key variables:

- `TELEGRAM_TOKEN` - Your Telegram bot token (required)
- `COMPANY_NAME` - Name of your company
- `SUPPORT_EMAIL` - Support email for the bot
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING)

## Performance & Resources

```bash
# View resource usage
docker stats

# Limit container resources (in docker-compose.yml)
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M

# Monitor in real-time
docker stats --no-stream=false
```

## Security

```bash
# Run container as read-only
docker-compose exec -e READONLY=true

# Check for vulnerabilities (if you have Trivy installed)
trivy image ticketing-bot:latest

# View privileged mode status
docker inspect --format='{{.HostConfig.Privileged}}' ticketing-bot
```

## Common Issues

### Container exits immediately
```bash
docker logs ticketing-bot  # Check error messages
docker-compose logs  # Better output with compose
```

### Permission denied
```bash
sudo docker-compose up  # Use sudo for permission issues
sudo chown -R 1000:1000 data logs  # Fix file ownership
```

### Port already in use
```bash
docker ps  # Find container using port
docker stop <container_id>  # Stop the container
```

### Out of disk space
```bash
docker system prune -a  # Remove unused images/containers
docker system df  # Check disk usage
```
