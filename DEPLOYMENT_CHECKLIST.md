# Deployment Checklist ✅

Complete this checklist before deploying the bot to production.

## Pre-Deployment Configuration

### Security & Credentials
- [ ] Create a new `.env` file (never commit the actual .env)
  - COPY from `.env.example` as template
  - **Never add actual credentials to .env.example**
- [ ] Verify `.env` is in `.gitignore` ✅ (Already configured)
- [ ] Generate strong ADMIN_PASSWORD (minimum 16 characters)
- [ ] Use Gmail App Password (not regular password) for SMTP_PASSWORD
- [ ] Verify TELEGRAM_BOT_TOKEN is valid from @BotFather
- [ ] Ensure SPICEWORKS_EMAIL is correct
- [ ] Set strong credentials for email services

### Environment Variables
- [ ] Set `LOG_LEVEL=INFO` for production (not DEBUG)
- [ ] Configure absolute `LOG_FILE_PATH` for production server
- [ ] Set appropriate `CONVERSATION_TIMEOUT_MINUTES` (suggested: 30)
- [ ] Configure `ADMIN_USER_IDS` with actual Telegram user IDs
- [ ] Set `QUEUE_ENABLED=false` for direct ticket creation (or true for queuing)

### Feature Flags
- [ ] Set `REACTION_TICKET_ENABLED=true` or `false` based on needs
- [ ] If reaction-based tickets enabled:
  - [ ] Populate `IT_TEAM_USER_IDS` with real Telegram user IDs
  - [ ] Configure `TICKET_REACTION_TRIGGERS` (emoji list)

### Email Configuration
- [ ] Test SMTP connection before deployment
- [ ] Verify `COMPANY_EMAIL_DOMAIN` matches your company domain
- [ ] Ensure email is sent from approved Spiceworks account
- [ ] Test email delivery to verify HTML formatting works

## Pre-Deployment Checks

### Code Quality
- [x] All print() statements replaced with logger calls
- [x] Configuration errors use stderr/logger (not print)
- [ ] Review error handlers in all feature handlers
- [ ] Check for any hardcoded debug values
- [ ] Verify all TODO/FIXME comments addressed

### Dependencies
- [ ] All packages in requirements.txt are: 
  - Pinned to specific versions ✅
  - Up to date (check for security patches)
  - Tested with Python 3.8+
- [ ] `python-telegram-bot>=21.8` verified compatible

### Logging
- [ ] Logging configured for rotation (10MB per file, 5 backups) ✅
- [ ] Log directory permissions allow bot to write
- [ ] Log level set to INFO for production (not DEBUG)
- [ ] Sensitive info NOT logged (passwords, tokens, PII)

### Data Management
- [ ] Verify `bot/data/` directory exists with proper permissions
- [ ] Backup existing tickets/queue data before upgrade
- [ ] Review cleanup scheduler (runs 1st of month at 00:00 UTC)

## Deployment Steps

### 1. Server Setup
```bash
# Install Python 3.8+
python --version  # Verify 3.8+

# Create directory for bot
mkdir -p /opt/ticketingbot
cd /opt/ticketingbot

# Clone repository
git clone <your-repo-url> .

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy and edit .env
cp .env.example .env
# Edit .env with your actual credentials
nano .env  # or: vim, code, etc.

# Verify config loads correctly
python -c "from bot.config.settings import settings; print('✅ Config loaded')"
```

### 3. Database/Data Directories
```bash
# Create necessary directories
mkdir -p logs bot/data/tickets bot/data/queue bot/data/temp

# Set proper permissions (Ubuntu/Linux)
chmod 755 logs bot/data bot/data/*
```

### 4. Service Installation (Linux/Ubuntu)

#### Option A: Systemd Service (Recommended)
Create `/etc/systemd/system/ticketingbot.service`:
```ini
[Unit]
Description=Telegram Ticketing Bot
After=network.target

[Service]
Type=simple
User=ticketbot
WorkingDirectory=/opt/ticketingbot
Environment="PATH=/opt/ticketingbot/venv/bin"
ExecStart=/opt/ticketingbot/venv/bin/python bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ticketingbot
sudo systemctl start ticketingbot
```

#### Option B: Docker (Enterprise)
See `DOCKER_DEPLOYMENT.md` for containerized deployment.

### 5. Verification
```bash
# Check bot is running
sudo systemctl status ticketingbot

# Check logs
sudo journalctl -u ticketingbot -f

# Or direct log check
tail -f logs/bot.log
```

### 6. Post-Deployment Tests
- [ ] Bot responds to `/start` command in private chat
- [ ] Bot accepts ticket creation workflow
- [ ] Email integration works (check inbox)
- [ ] Group mention creates ticket (if enabled)
- [ ] Reaction-based ticket creation works (if enabled)
- [ ] Admin commands work (`/admin`, `/list`, etc.)
- [ ] Ticket lookup works (`/lookup`)
- [ ] Log files are being written correctly

## Monitoring & Maintenance

### Daily
- [ ] Check logs for errors: `tail logs/bot.log | grep ERROR`
- [ ] Monitor Spiceworks inbox for tickets

### Weekly
- [ ] Review log file size (should rotate at 10MB)
- [ ] Check for unhandled exceptions
- [ ] Verify bot is still responsive

### Monthly
- [ ] Cleanup scheduler runs (1st of month, 00:00 UTC)
- [ ] Check database cleanup completed
- [ ] Archive old logs

### Security
- [ ] Never expose `.env` file or credentials
- [ ] Use strong ADMIN_PASSWORD
- [ ] Restrict bot token exposure
- [ ] Monitor Telegram API rate limits
- [ ] Keep dependencies updated

## Rollback Plan

If deployment fails:
1. Stop the bot: `sudo systemctl stop ticketingbot`
2. Restore previous backup
3. Check logs for root cause
4. Fix and re-test locally before re-deploying

## Production Environment Variables (Reference)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=<real-bot-token>

# Company
COMPANY_NAME=<your-company>
COMPANY_EMAIL_DOMAIN=<company.domain>

# Email (use App Password for Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<company-email>
SMTP_PASSWORD=<gmail-app-password>
SMTP_USE_TLS=true
SPICEWORKS_EMAIL=<spiceworks-email>

# Admin
ADMIN_PASSWORD=<strong-password-16+chars>
ADMIN_USER_IDS=<user-ids>

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=/opt/ticketingbot/logs/bot.log

# Features
QUEUE_ENABLED=false
REACTION_TICKET_ENABLED=true
IT_TEAM_USER_IDS=<user-ids>
TICKET_REACTION_TRIGGERS=👍
```

## Support & Troubleshooting

See `UBUNTU_DEPLOYMENT.md` and `UBUNTU_TROUBLESHOOTING.md` for detailed Ubuntu-specific guidance.

---
**Last Updated:** 2026-04-11
