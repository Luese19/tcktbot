# Ubuntu Deployment Guide

This guide provides step-by-step instructions for deploying the Telegram Help Desk Bot on Ubuntu servers.

## Prerequisites

- Ubuntu 20.04 LTS or newer
- Python 3.9+
- Git
- Telegram Bot Token (from BotFather)
- Admin user IDs
- Spiceworks API endpoint and credentials (optional)

## Installation Steps

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python and Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

### 3. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/Luese19/tcktbot.git ticketingbot
cd ticketingbot
sudo chown -R $USER:$USER /opt/ticketingbot
```

### 4. Create Virtual Environment

```bash
cd /opt/ticketingbot
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

### 1. Create .env File

```bash
cp .env.example .env  # if available, otherwise create new
nano .env
```

### 2. Configure Environment Variables

Add the following to `.env`:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
GROUP_ID=your_group_id_here

# Admin Configuration
ADMIN_IDS=123456789,987654321,555555555

# Spiceworks Configuration (Optional)
SPICEWORKS_INSTANCE=your_instance.spiceworks.com
SPICEWORKS_API_KEY=your_api_key_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/ticketingbot/bot.log

# Application Configuration
APP_ENV=production
DEBUG=False
```

**Important:**

- Replace `BOT_TOKEN` with your token from BotFather
- Replace `ADMIN_IDS` with comma-separated user IDs
- Create multiple admin IDs for redundancy

### 3. Create Directories

```bash
sudo mkdir -p /var/log/ticketingbot
sudo mkdir -p /opt/ticketingbot/data/tickets/temp
sudo mkdir -p /opt/ticketingbot/data/employees
sudo mkdir -p /opt/ticketingbot/data/queue
sudo mkdir -p /opt/ticketingbot/data/usernames

sudo chown -R $(whoami):$(whoami) /opt/ticketingbot
sudo chmod -R 755 /opt/ticketingbot/data
sudo chmod -R 755 /var/log/ticketingbot
```

## Running the Bot

### Method 1: Manual Run (Testing)

```bash
cd /opt/ticketingbot
source venv/bin/activate
python main.py
```

### Method 2: Run as Systemd Service (Recommended for Production)

#### 1. Create Service File

```bash
sudo nano /etc/systemd/system/ticketingbot.service
```

#### 2. Add Service Configuration

```ini
[Unit]
Description=Telegram Help Desk Bot
After=network.target

[Service]
Type=simple
User=ticketbot
WorkingDirectory=/opt/ticketingbot
Environment="PATH=/opt/ticketingbot/venv/bin"
ExecStart=/opt/ticketingbot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 3. Create Service User

```bash
sudo useradd -r -m -s /bin/bash ticketbot
sudo chown -R ticketbot:ticketbot /opt/ticketingbot
sudo chown -R ticketbot:ticketbot /var/log/ticketingbot
```

#### 4. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable ticketingbot
sudo systemctl start ticketingbot
```

#### 5. Verify Service Status

```bash
sudo systemctl status ticketingbot
```

## Monitoring and Logs

### View Real-time Logs

```bash
sudo journalctl -u ticketingbot -f
```

### View Historical Logs

```bash
sudo journalctl -u ticketingbot --no-pager | tail -100
```

### View Application Logs

```bash
sudo tail -f /var/log/ticketingbot/bot.log
```

## Common Commands

### Check Bot Status

```bash
sudo systemctl status ticketingbot
```

### Restart Bot

```bash
sudo systemctl restart ticketingbot
```

### Stop Bot

```bash
sudo systemctl stop ticketingbot
```

### Start Bot

```bash
sudo systemctl start ticketingbot
```

### View Recent Logs

```bash
sudo journalctl -u ticketingbot -n 50
```

## Bot Commands

Once deployed, the bot responds to these admin commands in Telegram:

- `/start` - Display welcome message
- `/help` - Show available commands
- `/schedule` - Create a scheduled task (admin only)
- `/tasks` - List all scheduled tasks (admin only)
- `/delete` - Delete a scheduled task (admin only)

## Scheduled Tasks Features

The bot supports the following scheduled task types:

1. **Create Ticket** - Automatically create tickets at specified times
2. **Send Message** - Send automated messages to users
3. **Send Reminder** - Send reminders to admins or specific users

Schedule types:

- **One-time** - Run once at a specific date/time
- **Daily** - Run at the same time every day
- **Weekly** - Run on a specific day each week
- **Monthly** - Run on a specific day each month
- **Custom Cron** - Use cron expressions for complex schedules

## Troubleshooting

### Bot Not Starting

**Error:** `ModuleNotFoundError: No module named 'telegram'`

**Solution:**

```bash
cd /opt/ticketingbot
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration Not Loading

**Error:** `RuntimeError: Configuration not loaded`

**Solution:**

1. Verify `.env` file exists in `/opt/ticketingbot`
2. Check file permissions: `sudo chmod 644 /opt/ticketingbot/.env`
3. Verify all required variables are set

### Permission Denied

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:**

```bash
sudo chown -R ticketbot:ticketbot /opt/ticketingbot
sudo chmod -R 755 /opt/ticketingbot
```

### Bot Token Invalid

**Error:** `Unauthorized` or `Invalid bot token`

**Solution:**

1. Verify token in `.env` is correct
2. Get new token from BotFather if needed
3. Restart service: `sudo systemctl restart ticketingbot`

### Scheduled Tasks Not Running

**Error:** Jobs are created but not executing

**Possible Causes:**

- Service isn't running: `sudo systemctl status ticketingbot`
- Check logs: `sudo journalctl -u ticketingbot -f`
- Verify scheduler is initialized
- Check system time is correct: `date`

## Performance Optimization

### 1. Increase File Descriptors

```bash
sudo nano /etc/security/limits.conf
```

Add:

```
ticketbot soft nofile 65536
ticketbot hard nofile 65536
```

### 2. Configure Swapfile (if low RAM)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. Monitor Resource Usage

```bash
# Install htop
sudo apt install htop
htop
```

## Security Recommendations

1. **Use SSH Keys** - Configure SSH key authentication instead of passwords
2. **Firewall** - Only expose necessary ports
3. **Environment Variables** - Never commit `.env` to git
4. **Regular Updates** - Keep Python packages updated
5. **Backups** - Regularly backup data and configurations
6. **Log Rotation** - Configure logrotate for bot logs

### Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/ticketingbot
```

Add:

```
/var/log/ticketingbot/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ticketbot ticketbot
    sharedscripts
    postrotate
        systemctl reload ticketingbot > /dev/null 2>&1 || true
    endscript
}
```

## Backup and Recovery

### Create Backup

```bash
sudo tar -czf ticketingbot-backup-$(date +%Y%m%d).tar.gz /opt/ticketingbot/data
```

### Restore from Backup

```bash
sudo tar -xzf ticketingbot-backup-20260413.tar.gz -C /opt/ticketingbot/
sudo chown -R ticketbot:ticketbot /opt/ticketingbot/data
```

## Updating the Bot

### Pull Latest Changes

```bash
cd /opt/ticketingbot
git pull origin main
```

### Update Dependencies

```bash
cd /opt/ticketingbot
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Restart Service

```bash
sudo systemctl restart ticketingbot
```

## Technical Details

- **Python Version:** 3.9+
- **Main Framework:** python-telegram-bot 21.8
- **Scheduler:** APScheduler
- **Storage:** Local JSON files in `/opt/ticketingbot/data`
- **Logging:** Python logging module with file rotation

## Support and Debugging

### Enable Debug Mode

1. Edit `.env` and set `DEBUG=True`
2. Set `LOG_LEVEL=DEBUG`
3. Restart service: `sudo systemctl restart ticketingbot`

### Collect Debug Information

```bash
echo "=== System Info ==="
uname -a

echo "=== Python Version ==="
python3 --version

echo "=== Service Status ==="
sudo systemctl status ticketingbot

echo "=== Recent Logs ==="
sudo journalctl -u ticketingbot -n 100

echo "=== Bot Log ==="
sudo tail -50 /var/log/ticketingbot/bot.log
```

## Additional Resources

- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)

## License

See LICENSE file in repository

---

**Last Updated:** April 13, 2026
