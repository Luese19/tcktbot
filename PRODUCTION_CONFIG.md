# Production Configuration Guide

This document provides guidance for configuring the bot for production deployment.

## Critical Production Settings

### Logging

```bash
# PRODUCTION (recommended)
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/ticketingbot/bot.log

# DEVELOPMENT ONLY
LOG_LEVEL=DEBUG
LOG_FILE_PATH=./logs/bot.log
```

**Why:** DEBUG level generates verbose logging that impacts performance and creates unnecessary noise. INFO level captures important events without excessive output.

### Message Handling

```bash
# Recommended for production
CONVERSATION_TIMEOUT_MINUTES=30
MAX_MESSAGE_LENGTH=4000
```

- **CONVERSATION_TIMEOUT_MINUTES**: How long to wait for user response before timing out
- **MAX_MESSAGE_LENGTH**: Maximum characters per message to prevent abuse

### Ticket Validation

```bash
# Field lengths (prevent abuse, ensure data quality)
MIN_NAME_LENGTH=2
MAX_NAME_LENGTH=100
MIN_ISSUE_LENGTH=5
MAX_ISSUE_LENGTH=200
MIN_DESCRIPTION_LENGTH=10
MAX_DESCRIPTION_LENGTH=2000

# File upload limits
MAX_FILE_SIZE_MB=10
MAX_ATTACHMENTS_PER_TICKET=5
```

### Email Configuration

#### Gmail/Google Workspace

1. Enable 2-Factor Authentication on your email account
2. Generate App Password:
   - Visit: <https://myaccount.google.com/apppasswords>
   - Select "Mail" and "Windows Computer" (or your OS)
   - Copy the 16-character password
3. Use this password in `SMTP_PASSWORD` (NOT your regular password)

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
SMTP_USE_TLS=true
```

#### Other Email Providers

Contact your email provider for SMTP settings.

### Queue Configuration

#### Option 1: Direct Ticket Creation (Default)

```bash
QUEUE_ENABLED=false
```

- Tickets created immediately when users use /start
- Each ticket creates a Spiceworks entry right away
- Better for low-traffic environments

#### Option 2: Queued Ticket Creation

```bash
QUEUE_ENABLED=true
QUEUE_TIMEOUT_MINUTES=30
REQUEST_TIMEOUT_MINUTES=60
CONCURRENT_TICKET_CREATION=1
```

- Group mentions are queued and processed sequentially
- Prevents overwhelming Spiceworks API
- Better for high-traffic environments

### Feature Flags

#### Reaction-Based Tickets

```bash
REACTION_TICKET_ENABLED=true
IT_TEAM_USER_IDS=123456789,987654321,555666777
TICKET_REACTION_TRIGGERS=👍,🎫,✅
```

**To find your Telegram user ID:**

1. Send a message to @userinfobot
2. It will reply with your numeric ID
3. Use that ID in IT_TEAM_USER_IDS

## Environment Setup

### Directory Structure

```
/opt/ticketingbot/
├── venv/                   # Virtual environment
├── bot/
│   ├── config/
│   ├── handlers/
│   ├── services/
│   ├── data/              # Tickets, queue storage
│   └── main.py
├── logs/                  # Bot logs (10MB rotation)
├── .env                   # Configuration (NEVER commit)
├── requirements.txt
├── DEPLOYMENT_CHECKLIST.md
└── README.md
```

### Permissions (Linux/Ubuntu)

```bash
# Create bot user
sudo useradd -m -s /bin/bash ticketbot

# Set directory ownership
sudo chown -R ticketbot:ticketbot /opt/ticketingbot

# Set directory permissions
sudo chmod 755 /opt/ticketingbot
sudo chmod 755 /opt/ticketingbot/log

# Virtual environment and data permissions
sudo chmod 755 /opt/ticketingbot/bot/data
sudo chmod 755 /opt/ticketingbot/venv
```

## Monitoring Configuration

### Log Rotation (Automatic)

- **Max file size:** 10 MB
- **Backup files:** 5 previous logs kept
- **Automatic rotation:** Yes
- **Log location:** Configured in LOG_FILE_PATH

### Log Retention

```bash
# Keep logs for 180 days (adjust as needed)
# Example cron job to delete old logs:
0 0 * * * find /var/log/ticketingbot -name "*.log.*" -mtime +180 -delete
```

## Scaling Considerations

### Single Server

- Recommended for: < 1,000 users/month
- Setup: One bot instance with systemd service

### High Traffic

- Recommended for: > 10,000 users/month
- Setup: Multiple bot instances with load balancer
- Use QUEUE_ENABLED=true to manage Spiceworks load
- Set CONCURRENT_TICKET_CREATION=1 or 2

### Redundancy

- Run multiple bot instances on different servers
- Share data via NFS or sync service
- Monitor with health check commands

## Security Configuration

### Admin Authentication

```bash
# Strong password (minimum 16 characters recommended)
ADMIN_PASSWORD=MyS3cur3P@ssw0rd!WithNumbers123
ADMIN_USER_IDS=123456789,987654321
```

### Credentials Best Practices

1. ✅ Use Gmail App Passwords, not regular passwords
2. ✅ Store .env in secure location with restricted permissions
3. ✅ Rotate credentials every 90 days
4. ✅ Never log passwords or tokens
5. ✅ Use HTTPS for any log transfer/monitoring
6. ✅ Restrict file access: `chmod 600 .env`

### Rate Limiting

- Telegram API enforces rate limits automatically
- Monitor logs for rate limit warnings
- Typical limits: 30 messages/second per user

## Testing Before Production

### 1. Configuration Check

```bash
python -c "from bot.config.settings import settings; print('✅ OK')"
```

### 2. Email Test

```bash
python verify_setup.py
```

### 3. Ticket Creation

- Send /start to bot
- Complete full ticket creation flow
- Verify ticket appears in Spiceworks

### 4. Admin Functions

- Use /admin command
- Test /list, /view, /delete operations

### 5. Group Features

- Test group mentions (if enabled)
- Test reaction tickets (if enabled with IT team)

## Troubleshooting

### Bot Not Starting

```bash
# Check for configuration errors
python -c "from bot.config.settings import settings"

# Check logs
tail -f logs/bot.log

# Verify TELEGRAM_BOT_TOKEN is valid
```

### Emails Not Sending

```bash
# Verify SMTP credentials work
python -c "
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your-email@gmail.com', 'your-app-password')
print('✅ SMTP works')
"
```

### High Memory Usage

- Reduce LOG_LEVEL to INFO
- Monitor conversation timeout settings
- Check for handler memory leaks in logs

## Automation & Updates

### Automatic Restarts

Using systemd (recommended):

```ini
[Service]
Restart=always
RestartSec=10
```

### Log Monitoring

```bash
# Follow logs in real-time
journalctl -u ticketingbot -f

# Search for errors
journalctl -u ticketingbot | grep ERROR
```

### Scheduled Maintenance

- Cleanup runs: 1st of each month at 00:00 UTC
- Check cleanup logs for issues
- No manual action needed

---
**Last Updated:** 2026-04-11
