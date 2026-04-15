# Dockerized Ticketing Bot - Ubuntu Deployment Guide

## Prerequisites

- Ubuntu 20.04+ server
- Docker installed
- Docker Compose installed (optional but recommended)
- Your Telegram Bot Token and configuration details

## Installation Steps

### 1. Install Docker and Docker Compose

```bash
# Update package manager
sudo apt-get update   
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io

# Enable Docker to start on boot
sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose
sudo apt-get install -y docker-compose

# Add your user to docker group (optional, to avoid sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone or Transfer Your Project

```bash
# Option A: Clone from git (if repository is available)
git clone <your-repo-url> /opt/ticketing-bot 
cd /opt/ticketing-bot

# Option B: Transfer via SCP/SFTP
# On your local machine:
scp -r /path/to/TICKETINGBOT user@your-ubuntu-server:/opt/ticketing-bot

# Then on the server:
cd /opt/ticketing-bot
```

### 3. Set Up Environment Variables

```bash
# Create .env file in the project root
sudo nano /opt/ticketing-bot/.env
```

Add the following content:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
COMPANY_NAME=Your Company Name
COMPANY_EMAIL_DOMAIN=company.com
SUPPORT_EMAIL=support@yourcompany.com
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=helpdesk@company.com
SMTP_PASSWORD=your_password
LOG_LEVEL=INFO
ADMIN_USER_IDS=123456789
```

Save and exit (Ctrl+X, then Y, then Enter)

### 4. Build the Docker Image

```bash
cd /opt/ticketing-bot

# Option A: Using docker-compose (recommended)
sudo docker-compose build

# Option B: Using docker directly
sudo docker build -t ticketing-bot:latest .
```

### 5. Deploy the Container

```bash
# Option A: Using docker-compose (recommended)
sudo docker-compose up -d

# Option B: Using docker directly
sudo docker run -d \
  --name ticketing-bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN \
  -e COMPANY_NAME="$COMPANY_NAME" \
  -e SUPPORT_EMAIL=$SUPPORT_EMAIL \
  -v /opt/ticketing-bot/data:/app/data \
  -v /opt/ticketing-bot/logs:/app/logs \
  ticketing-bot:latest
```

### 6. Verify Deployment

```bash
# Check if container is running
sudo docker-compose ps
# or
sudo docker ps | grep ticketing-bot

# View logs
sudo docker-compose logs -f
# or
sudo docker logs -f ticketing-bot

# Check container health
sudo docker inspect --format='{{.State.Health.Status}}' ticketing-bot
```

## Managing the Bot

### Start/Stop/Restart

```bash
# Using docker-compose
sudo docker-compose start
sudo docker-compose stop
sudo docker-compose restart

# Using docker directly
sudo docker start ticketing-bot
sudo docker stop ticketing-bot
sudo docker restart ticketing-bot
```

### View Logs

```bash
# Real-time logs
sudo docker-compose logs -f

# Last 100 lines
sudo docker-compose logs --tail 100

# Specific time period
sudo docker-compose logs --since 2024-04-15
```

### Access Data Files

```bash
# Data is persisted in mounted volumes
ls -la /opt/ticketing-bot/data/
ls -la /opt/ticketing-bot/logs/

# View tickets
cat /opt/ticketing-bot/data/tickets/*.json

# View requests
cat /opt/ticketing-bot/data/queue/requests.json
```

### Update Configuration

```bash
# Edit .env file
sudo nano /opt/ticketing-bot/.env

# Restart the container to apply changes
sudo docker-compose restart
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
sudo docker-compose logs

# Verify environment variables
sudo docker-compose config

# Check if Telegram token is valid
# Test with curl: curl -X GET https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### Permission issues with data files

```bash
# Fix permissions
sudo chown -R 1000:1000 /opt/ticketing-bot/data
sudo chown -R 1000:1000 /opt/ticketing-bot/logs
sudo chmod -R 755 /opt/ticketing-bot/data
sudo chmod -R 755 /opt/ticketing-bot/logs
```

### Container keeps restarting

```bash
# Check restart policy
sudo docker inspect ticketing-bot | grep -A 5 "RestartPolicy"

# View system logs
sudo journalctl -u docker -n 50

# Check docker daemon logs
sudo tail -f /var/log/docker.log
```

## Advanced Configuration

### Use Systemd Service (Optional)

Create `/etc/systemd/system/ticketing-bot.service`:

```ini
[Unit]
Description=Ticketing Bot Container
After=docker.service
Requires=docker.service

[Service]
Type=exec
WorkingDirectory=/opt/ticketing-bot
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ticketing-bot
sudo systemctl start ticketing-bot
sudo systemctl status ticketing-bot
```

### Auto-restart and Health Checks

The Dockerfile includes:

- `restart: unless-stopped` - automatically restarts on failure
- Health checks every 30 seconds
- Proper signal handling for graceful shutdown

### Monitoring with Portainer (Optional)

```bash
# Install Portainer for GUI container management
sudo docker volume create portainer_data
sudo docker run -d \
  -p 8000:8000 \
  -p 9000:9000 \
  --name=portainer \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

# Access at http://your-server-ip:9000
```

## Security Best Practices

1. **Use private repository** - Store your image in a private Docker registry
2. **Limit environment variables** - Never hardcode sensitive data in Dockerfile
3. **Use read-only filesystems** - Consider adding `--read-only` flag if applicable
4. **Enable Docker daemon TLS** - For remote Docker access
5. **Regular image updates** - Rebuild image regularly to get security patches
6. **Set resource limits** - Add memory and CPU limits in docker-compose.yml:

```yaml
services:
  ticketingbot:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Backup Strategy

```bash
# Backup data directory
sudo tar -czf /backup/ticketing-bot-data-$(date +%Y%m%d).tar.gz /opt/ticketing-bot/data

# Backup Docker image
sudo docker save ticketing-bot:latest | gzip > /backup/ticketing-bot-image-$(date +%Y%m%d).tar.gz

# Restore from backup
sudo docker load < /backup/ticketing-bot-image-latest.tar.gz
```

## Next Steps

1. Test the bot with your Telegram token
2. Monitor logs and performance
3. Set up automated backups
4. Consider containerizing any dependent services (databases, caches, etc.)
5. Implement CI/CD pipeline to automatically build and push images

## Support

For issues or questions:

- Check application logs: `sudo docker-compose logs`
- Review Telegram Bot API documentation: <https://core.telegram.org/bots>
- Check Docker documentation: <https://docs.docker.com/>
