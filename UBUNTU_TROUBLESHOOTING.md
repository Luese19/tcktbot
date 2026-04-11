# Ubuntu Deployment Troubleshooting Guide

Quick troubleshooting steps for common issues.

## 🔴 Bot Won't Start

### Check 1: Configuration Error

```bash
python3 -c "from bot.config.settings import settings; print('✅ Config OK')"
```

**If error:** Check `.env` file has all required variables:

```bash
grep -E "TELEGRAM_BOT_TOKEN|SMTP_SERVER|SPICEWORKS_EMAIL" .env
```

### Check 2: Python/Dependencies

```bash
source venv/bin/activate
python3 -c "import telegram; print(telegram.__version__)"
```

**If error:** Reinstall dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Check 3: Bot Token Invalid

```bash
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

**If error 401:** Get new token from [@BotFather](https://t.me/botfather)

### Check 4: Port/Firewall

Bot uses polling (no incoming ports), but needs outgoing internet:

```bash
curl -s https://api.telegram.org | head
```

If blocked, check firewall allowing outbound HTTPS (port 443).

---

## 🟡 Bot Crashes Frequently

### Check Logs

```bash
sudo tail -100 /var/log/telegram-bot/bot.log | grep -i "error\|exception"
```

### Common Causes

#### Out of Memory

```bash
# Check memory
free -h

# Monitor process
watch -n 1 'ps aux | grep python3 | grep -v grep'

# Restart to free memory
sudo systemctl restart telegram-bot
```

#### API Rate Limit

```bash
# Check logs
grep "rate limit\|429" /var/log/telegram-bot/bot.log

# Solution: Bot logs off and reconnects (automatic)
```

#### SMTP Connection Failed

```bash
# Test SMTP
telnet smtp.gmail.com 587

# If connection denied: Check firewall/ISP blocking port 587
# Solution: Use port 465 (SSL) instead of 587 (TLS)
```

---

## 🟠 Reactions Not Creating Tickets

### Check 1: Feature Enabled

```bash
grep -E "REACTION_TICKET_ENABLED|IT_TEAM_USER_IDS" .env
```

Should show:

```
REACTION_TICKET_ENABLED=true
IT_TEAM_USER_IDS=5139651410
```

### Check 2: User ID Correct

```bash
# Get your Telegram ID
tail -f /var/log/telegram-bot/bot.log | grep -i "user_id\|reaction"
```

React to a message, check logs for your ID.

### Check 3: Message Cache Working

```bash
# Detailed cache logs
tail -f /var/log/telegram-bot/bot.log | grep CACHE
```

Should show:

```
[CACHE] Stored message 123 in chat -456
[CACHE] Found message 123: Your message text
```

### Debug: Manual Test

```bash
cd /opt/ticketingbot
source venv/bin/activate
python3 << 'EOF'
from bot.services.message_cache_service import MessageCacheService
MessageCacheService.store_message(-123456, 100, "Test message", "TestUser")
result = MessageCacheService.get_message(-123456, 100)
print(f"Cached: {result}")
EOF
```

---

## 🔵 Tickets Not in Spiceworks

### Check 1: SMTP Settings

```bash
python3 << 'EOF'
import smtplib
from bot.config.settings import settings

try:
    server = smtplib.SMTP(settings.email.SMTP_SERVER, settings.email.SMTP_PORT)
    server.starttls()
    server.login(settings.email.SMTP_USERNAME, settings.email.SMTP_PASSWORD)
    print("✅ SMTP Connection OK")
    server.quit()
except Exception as e:
    print(f"❌ SMTP Error: {e}")
EOF
```

### Check 2: Email Address

```bash
grep SPICEWORKS_EMAIL .env
```

Should point to your support inbox, e.g.:

```
SPICEWORKS_EMAIL=help@company.on.spiceworks.com
```

### Check 3: Email Logs

```bash
# Check email was sent
grep -i "sent\|email\|smtp" /var/log/telegram-bot/bot.log | tail -20

# Look for full error trace
grep -A 5 "error\|exception" /var/log/telegram-bot/bot.log
```

### Check 4: Gmail App Password

If using Gmail:

1. Enable 2FA on account
2. Generate [App Password](https://support.google.com/accounts/answer/185833)
3. Use app password in `.env`, not account password

---

## 📊 Performance Issues

### High CPU Usage

```bash
# Check what's consuming CPU
top -p $(pgrep -f "python3 main.py")

# Or
ps aux | grep "python3 main.py" | grep -v grep

# Check number of threads
ps -eLf | grep "python3 main.py" | wc -l
```

**Solution:** Restart bot

```bash
sudo systemctl restart telegram-bot
```

### Slow Response

```bash
# Check disk I/O
iostat -x 1

# Check network
iftop  # If installed: sudo apt install iftop

# Check bot response time in logs
grep "ms:\|seconds:" /var/log/telegram-bot/bot.log | tail -10
```

---

## 🔐 Security Issues

### Logs Exposed

```bash
# Check .env permissions
ls -la .env

# Should be: -rw------- (600)
chmod 600 .env
```

### Bot Token Exposed

```bash
# Check if token in repository
git log -S "TELEGRAM_BOT_TOKEN" --source --all

# If exposed, regenerate token with @BotFather
```

### SMTP Password Logged

```bash
# Check if password in logs
grep -r "$SMTP_PASSWORD" /var/log/telegram-bot/

# Should NOT find anything
```

---

## 🆘 Getting Help

### Generate Debug Info

```bash
cat > /tmp/debug-info.txt << 'EOF'
=== System Info ===
$(lsb_release -a)
$(python3 --version)
$(uname -a)

=== Bot Status ===
$(sudo systemctl status telegram-bot)

=== Recent Logs ===
$(sudo tail -50 /var/log/telegram-bot/bot.log)

=== Configuration ===
$(grep -v PASSWORD .env)

=== Dependencies ===
$(pip list | grep telegram)
EOF

cat /tmp/debug-info.txt
```

Share this info when debugging.

---

## 📞 Useful Commands Reference

```bash
# Service Management
sudo systemctl start telegram-bot
sudo systemctl stop telegram-bot
sudo systemctl restart telegram-bot
sudo systemctl status telegram-bot

# Logs
sudo journalctl -u telegram-bot -n 100
sudo tail -f /var/log/telegram-bot/bot.log
tail -f bot/logs/bot.log

# Configuration
nano .env
source venv/bin/activate
python3 verify_setup.py

# Cleanup
rm -rf bot/logs/*
rm -rf bot/data/queue/*
sudo systemctl restart telegram-bot

# Monitoring
watch sudo systemctl status telegram-bot
ps aux | grep python3
free -h
df -h
```

---

**Last Updated:** 2026-04-11
