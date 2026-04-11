# Telegram Help Desk Bot - Ubuntu Deployment Guide

Complete guide for deploying the Telegram Help Desk Bot on Ubuntu servers.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Production Deployment](#production-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### System Access

- Root or sudo privileges
- SSH access to Ubuntu server
- Git installed (for cloning repository)

### Required Accounts

- **Telegram Bot Token** - Create via [@BotFather](https://t.me/botfather)
- **Spiceworks Account** - For ticket submission via email
- **SMTP Email Account** - For sending emails to Spiceworks

### Information to Gather

- Telegram Bot Token
- SMTP server credentials (address, port, username, password)
- Spiceworks email address (where tickets are sent)
- Company domain
- Admin user IDs

---

## 🖥️ System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Ubuntu 20.04 LTS or newer |
| **Python** | Python 3.8+ |
| **RAM** | 512 MB minimum (1GB recommended) |
| **Storage** | 2GB minimum |
| **Network** | Internet access for Telegram API |

### Ubuntu Version Check

```bash
lsb_release -a
python3 --version
```

---

## 📦 Installation Steps

### 1. System Updates

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl
```

### 2. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/ticketingbot.git
cd ticketingbot
sudo chown -R $USER:$USER .
```

Or download and extract if not using git:

```bash
cd /opt
sudo wget https://your-repo-url/ticketingbot.zip
sudo unzip ticketingbot.zip
cd ticketingbot
```

### 3. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 5. Create Required Directories

```bash
mkdir -p bot/data/queue
mkdir -p bot/logs
chmod 755 bot/data
chmod 755 bot/logs
```

### 6. Verify Installation

```bash
python3 verify_setup.py
```

Expected output:

```
✅ Python version OK
✅ Dependencies installed
✅ Directory structure OK
```

---

## ⚙️ Configuration

### 1. Create `.env` File

```bash
cp .env.template .env
nano .env
```

Or create new file:

```bash
cat > .env << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Company Configuration
COMPANY_EMAIL_DOMAIN=yourcompany.com
COMPANY_NAME=Your Company Name

# Email/SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Spiceworks Configuration
SPICEWORKS_EMAIL=help@yourcompany.on.spiceworks.com

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/bot.log

# Application Configuration
MAX_MESSAGE_LENGTH=4000
CONVERSATION_TIMEOUT_MINUTES=30

# Group Mention Configuration
QUEUE_ENABLED=false

# Reaction-based Ticket Creation (IT Team)
IT_TEAM_USER_IDS=5139651410,987654321
TICKET_REACTION_TRIGGERS=🎫,👍,✅
REACTION_TICKET_ENABLED=true

# Admin Settings (optional)
ADMIN_USER_IDS=123456789
ADMIN_PASSWORD=secure_password
EOF
```

### 2. Configure Variables

Edit `.env` with your values:

```bash
nano .env
```

**Key Configuration Values:**

| Variable | Example | Notes |
|----------|---------|-------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` | Get from @BotFather |
| `SMTP_SERVER` | `smtp.gmail.com` | Gmail: smtp.gmail.com, Office365: smtp.office365.com |
| `SMTP_PORT` | `587` | Standard TLS port |
| `SMTP_USERNAME` | `bot@company.com` | Email account for sending |
| `SMTP_PASSWORD` | `app-specific-password` | Use app password, not account password |
| `IT_TEAM_USER_IDS` | `5139651410` | Comma-separated Telegram user IDs |

### 3. Get IT Team User IDs

Each team member can get their ID by:

1. Messaging `@userinfobot` on Telegram
2. Bot responds with their user ID

Or from bot logs:

```bash
tail -f logs/bot.log | grep "user_id"
```

### 4. Verify Configuration

```bash
python3 -c "from bot.config.settings import settings; print('✅ Configuration loaded successfully')"
```

---

## 🚀 Running the Bot

### 1. Manual Startup (Testing)

```bash
source venv/bin/activate
cd bot
python3 main.py
```

Expected output:

```
Initializing Telegram Help Desk Bot...
2026-04-11 10:00:00 | helpdesk_bot | INFO | Bot polling started
```

### 2. Systemd Service (Production)

Create service file:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Paste:

```ini
[Unit]
Description=Telegram Help Desk Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/ticketingbot
Environment="PATH=/opt/ticketingbot/venv/bin"
ExecStart=/opt/ticketingbot/venv/bin/python3 /opt/ticketingbot/bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-bot/bot.log
StandardError=append:/var/log/telegram-bot/error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo mkdir -p /var/log/telegram-bot
sudo chown ubuntu:ubuntu /var/log/telegram-bot

sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

Check status:

```bash
sudo systemctl status telegram-bot
```

View logs:

```bash
sudo tail -f /var/log/telegram-bot/bot.log
```

---

## 📊 Production Deployment

### 1. Security Hardening

```bash
# Restrict .env permissions
chmod 600 /opt/ticketingbot/.env

# Create dedicated user
sudo useradd -m -s /bin/bash botuser
sudo chown -R botuser:botuser /opt/ticketingbot

# Limit file access
sudo chmod 750 /opt/ticketingbot
```

### 2. Firewall Configuration (if needed)

Ubuntu's bot uses Telegram polling (no incoming ports needed):

```bash
# UFW already blocks all by default
sudo ufw allow 22/tcp  # SSH only
sudo ufw enable
```

### 3. Log Rotation

Create log rotation config:

```bash
sudo nano /etc/logrotate.d/telegram-bot
```

Paste:

```
/opt/ticketingbot/bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload telegram-bot > /dev/null 2>&1 || true
    endscript
}
```

### 4. Backup Strategy

Create daily backup:

```bash
cat > /opt/ticketingbot/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/telegram-bot"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/bot-$(date +%Y%m%d).tar.gz \
    -C /opt ticketingbot \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git'
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/ticketingbot/backup.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/ticketingbot/backup.sh") | crontab -
```

---

## 📈 Monitoring & Maintenance

### 1. Check Bot Status

```bash
# Service status
sudo systemctl status telegram-bot

# Bot is running if you see:
# ● telegram-bot.service - Telegram Help Desk Bot
#    Loaded: loaded
#    Active: active (running)
```

### 2. View Live Logs

```bash
# Real-time logs
sudo tail -f /var/log/telegram-bot/bot.log

# Filter for reactions
sudo tail -f /var/log/telegram-bot/bot.log | grep REACTION

# Filter for errors
sudo tail -f /var/log/telegram-bot/bot.log | grep ERROR
```

### 3. Monitor Performance

```bash
# Check memory usage
ps aux | grep "python3 main.py"

# Check disk usage
df -h

# Check log size
du -sh /opt/ticketingbot/bot/logs/
```

### 4. Restart Bot

```bash
# Restart bot
sudo systemctl restart telegram-bot

# Stop bot
sudo systemctl stop telegram-bot

# Start bot
sudo systemctl start telegram-bot
```

### 5. Update Bot Code

```bash
cd /opt/ticketingbot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

---

## 🔧 Troubleshooting

### Bot Not Starting

1. **Check configuration:**

   ```bash
   python3 -c "from bot.config.settings import settings; print(settings.bot.TOKEN)"
   ```

2. **Check logs:**

   ```bash
   sudo journalctl -u telegram-bot -n 50
   ```

3. **Test manually:**

   ```bash
   cd /opt/ticketingbot
   source venv/bin/activate
   python3 bot/main.py
   ```

### Connection Issues

```bash
# Test Telegram API
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe" | python3 -m json.tool

# Test SMTP connection
python3 << 'EOF'
import smtplib
conn = smtplib.SMTP("smtp.gmail.com", 587)
conn.starttls()
conn.login("email@gmail.com", "password")
print("✅ SMTP connection OK")
EOF
```

### Message Cache Not Working

```bash
# Check if messages are being cached
tail -f logs/bot.log | grep CACHE

# Restart service to clear cache
sudo systemctl restart telegram-bot
```

### High Memory Usage

```bash
# Check for memory leaks
ps aux | grep "python3 main.py"
watch -n 1 'ps aux | grep python3'

# Restart bot to free memory
sudo systemctl restart telegram-bot
```

### Email Not Sending

1. **Check SMTP settings:**

   ```bash
   grep SMTP .env
   ```

2. **Test email sending:**

   ```bash
   python3 -c "from bot.services.spiceworks_service import SpiceworksService; print(SpiceworksService)"
   ```

3. **Check logs for errors:**

   ```bash
   tail -f logs/bot.log | grep -i "email\|smtp\|mail"
   ```

---

## 📝 Common Commands

```bash
# Activate environment
source /opt/ticketingbot/venv/bin/activate

# View bot status
sudo systemctl status telegram-bot

# Restart bot
sudo systemctl restart telegram-bot

# View logs
sudo tail -f /var/log/telegram-bot/bot.log

# Update code
cd /opt/ticketingbot && git pull && pip install -r requirements.txt

# Clean up cache
rm -rf /opt/ticketingbot/bot/data/queue/*

# Backup configuration
cp /opt/ticketingbot/.env /opt/ticketingbot/.env.backup
```

---

## 🆘 Support

For issues, check:

1. **Logs:** `/var/log/telegram-bot/bot.log`
2. **Configuration:** Verify all `.env` variables
3. **Dependencies:** Run `pip list` to verify installations
4. **Telegram API:** Test with `curl` commands above

---

## 📚 Additional Resources

- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [Systemd Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**Last Updated:** 2026-04-11  
**Version:** 1.0
