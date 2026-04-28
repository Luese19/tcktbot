# Bot Rebuild & Migration Guide

## Problem Fixed

**Error:** `Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`

### Root Causes

1. Multiple bot instances trying to use the same Telegram token simultaneously
2. Two duplicate `main.py` files (root and bot/ directory) causing confusion
3. No process locking mechanism to prevent multiple instances
4. Missing proper signal handling for graceful shutdown

---

## Changes Made

### 1. **Process Manager** (`utils/process_manager.py`)

- ✅ Prevents multiple bot instances from running simultaneously
- ✅ Uses file-based locking (`~/.ticketingbot.lock`)
- ✅ Detects and reports running instances
- ✅ Handles graceful shutdown with signal handlers

### 2. **Unified Entry Point** (Root `main.py`)

- ✅ Single, authoritative bot entry point
- ✅ Process locking check BEFORE any module imports
- ✅ Proper initialization sequence
- ✅ All handlers properly configured
- ✅ Better error handling and logging

### 3. **Deprecated bot/main.py**

- ⚠️ Replaced with deprecation warning
- 🚫 Will exit immediately if run directly
- 📝 Directs users to use the root `main.py`

### 4. **Docker Configuration**

- ✅ Updated `Dockerfile` to use root `main.py`
- ✅ Added `ENTRYPOINT` for better signal handling
- ✅ Uses `-u` flag for unbuffered output
- ✅ Removed duplicate code copies

### 5. **Docker Compose Updates**

- ✅ Added `stop_grace_period: 30s` for proper cleanup
- ✅ Added `stop_signal: SIGINT` for graceful shutdown
- ✅ Added `PYTHONUNBUFFERED=1` for real-time logs
- ✅ Added `security_opt` for enhanced security

### 6. **Management Scripts**

Created helper scripts for common operations:

| Script | Purpose |
|--------|---------|
| `restart-bot.sh` | Gracefully stop and restart the bot |
| `restart-bot.bat` | Windows version of restart script |
| `cleanup-bot.sh` | Force kill all bot instances and cleanup |
| `logs-bot.sh` | Stream bot logs in real-time |

---

## How to Use

### ✅ Correct Way to Run the Bot

**Option 1: Direct Python (Development)**

```bash
cd d:\TICKETINGBOT
python main.py
```

**Option 2: Docker (Production)**

```bash
cd d:\TICKETINGBOT
docker-compose up -d
```

**Option 3: With Logs**

```bash
docker-compose up -d
docker-compose logs -f
```

### ❌ DO NOT Do This

- ❌ Don't run `bot/main.py` directly
- ❌ Don't start multiple instances
- ❌ Don't run `python main.py` from the `bot/` directory

---

## If You See "Multiple Instances" Error

**Step 1: Stop all bot processes**

```bash
# Linux/Mac
pkill -f "python.*main.py"

# Windows (PowerShell)
Get-Process | Where-Object {$_.Name -like "*python*"} | Stop-Process -Force
```

**Step 2: Remove lock file**

```bash
# Linux/Mac
rm ~/.ticketingbot.lock

# Windows (PowerShell)
Remove-Item $env:USERPROFILE\.ticketingbot.lock -Force
```

**Step 3: Stop Docker container (if running)**

```bash
docker-compose down --remove-orphans
```

**Step 4: Restart the bot**

```bash
python main.py
# OR
docker-compose up -d
```

---

## Troubleshooting

### Bot won't start

1. Check `.env` file exists and has `TELEGRAM_BOT_TOKEN`
2. Verify no other instances are running (see above)
3. Check logs: `docker-compose logs -f` or look in `logs/bot.log`

### "Configuration not loaded" error

1. Ensure `.env` file is in the root `d:\TICKETINGBOT` directory
2. Verify all required environment variables are set
3. Check file permissions

### Docker issues

```bash
# Rebuild the image
docker-compose build --no-cache

# Completely restart
docker-compose down --remove-orphans -v
docker-compose up -d
```

---

## Deployment Checklist

- [ ] ✅ Process manager implemented
- [ ] ✅ Single entry point in root `main.py`
- [ ] ✅ Docker properly configured
- [ ] ✅ Lock file cleanup working
- [ ] ✅ Signal handlers implemented
- [ ] ✅ Test locally: `python main.py`
- [ ] ✅ Test in Docker: `docker-compose up -d`
- [ ] ✅ Verify logs working
- [ ] ✅ Stop old bot instances if any

---

## Reference

**Files Changed:**

- `main.py` - ✅ Updated (unified entry point)
- `utils/process_manager.py` - ✅ Created (process locking)
- `bot/main.py` - ✅ Deprecated (now shows warning)
- `Dockerfile` - ✅ Updated (proper entry point)
- `docker-compose.yml` - ✅ Updated (signal handling)

**New Scripts:**

- `restart-bot.sh` - Graceful restart
- `restart-bot.bat` - Windows restart
- `cleanup-bot.sh` - Force cleanup
- `logs-bot.sh` - Stream logs

---

**Last Updated:** 2026-04-28
**Status:** Ready for Production ✅
