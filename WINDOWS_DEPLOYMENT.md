# Windows Deployment Guide 🪟

Deploy the Telegram Help Desk Bot on a Windows PC with easy setup and troubleshooting.

## Quick Start (5 minutes)

### Prerequisites

- **Windows 10/11** (any version)
- **Python 3.8+** ([Download from python.org](https://www.python.org/downloads/))
- **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))
- **Gmail Account** with App Password (for email sending)

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. **Important:** Check "Add Python to PATH" during installation
3. Verify installation:
```bash
python --version
```

### Step 2: Clone/Setup Bot Files

Navigate to your desired location and clone the repository:

```bash
cd d:\
git clone https://github.com/yourusername/ticketingbot.git
cd ticketingbot
```

Or if already in the folder:
```bash
cd /d "%~dp0"
```

### Step 3: Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

**Expected output:** Your command prompt should show `(venv)` prefix.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure .env File

Create a `.env` file in the root directory:

```bash
copy .env.example .env
```

Edit `.env` with your values (use Notepad or VS Code):

```ini
# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=your_token_here

# Company Settings
COMPANY_NAME=Your Company Name
COMPANY_EMAIL_DOMAIN=company.com

# Email Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_USE_TLS=true

# Spiceworks Integration
SPICEWORKS_EMAIL=support@company.com

# Admin Password (minimum 16 characters)
ADMIN_PASSWORD=YourSecureAdminPassword123!

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/bot.log

# Features
QUEUE_ENABLED=false
REACTION_TICKET_ENABLED=false
CONVERSATION_TIMEOUT_MINUTES=30
```

### Step 6: Run the Bot

#### Option A: Using the Batch File (Easiest)

Double-click `start_bot.bat` in the folder. A command window will open and the bot will start.

#### Option B: From Command Prompt

```bash
# Activate virtual environment
venv\Scripts\activate

# Run the bot
python bot/main.py
```

---

## Detailed Setup Instructions 📋

### 1. Python Installation

#### Windows 10/11:

1. Go to [python.org](https://www.python.org/downloads/)
2. Click **Download Python 3.11** (or latest 3.8+)
3. Run the installer
4. **IMPORTANT:** Check the box: ✅ "Add Python to PATH"
5. Click "Install Now"
6. Wait for completion

**Verify:**
```bash
# Open PowerShell or Command Prompt and type:
python --version
pip --version
```

### 2. Project Setup

Navigate to your project folder:

```bash
# Option 1: Using PowerShell/Command Prompt
cd d:\TICKETINGBOT

# Option 2: Right-click folder → Open in Terminal
```

### 3. Virtual Environment Setup

Virtual environments isolate project dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see (venv) in your prompt
```

**Troubleshooting:**
- If you get "is not recognized" error, Python is not in PATH (reinstall with PATH option checked)
- If venv creation fails, try: `python -m pip install --upgrade pip`

### 4. Install Dependencies

With venv activated:

```bash
pip install -r requirements.txt
```

This installs:
- `python-telegram-bot` - Telegram API wrapper
- `python-dotenv` - Environment variables
- `requests` - HTTP library
- `apscheduler` - Task scheduling
- `secure-smtplib` - Email sending
- `colorlog` - Pretty logging

### 5. Configure Credentials

Create `.env` file:

```bash
# Copy template
copy .env.example .env

# Edit with Notepad
notepad .env
```

**Required Settings:**

| Setting | Example | Where to Get |
|---------|---------|--------------|
| `TELEGRAM_BOT_TOKEN` | `123456789:ABCDefGHIjklMNOpqrsTUVwxyz` | [@BotFather](https://t.me/botfather) on Telegram |
| `ADMIN_PASSWORD` | `MySecurePassword123!` | Create yourself (min 16 chars) |
| `SMTP_USERNAME` | `your-email@gmail.com` | Your Gmail address |
| `SMTP_PASSWORD` | `xxxx xxxx xxxx xxxx` | [Gmail App Password](#gmail-setup) |
| `SPICEWORKS_EMAIL` | `support@company.com` | Your Spiceworks email |
| `COMPANY_EMAIL_DOMAIN` | `company.com` | Your company domain |

#### Gmail Setup

To get Gmail App Password:

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click "Security" on the left
3. Scroll to "App passwords" (requires 2FA enabled)
4. Select "Mail" → "Windows Computer"
5. Copy the 16-character password
6. Paste into `.env` as `SMTP_PASSWORD`

### 6. Create Data Directories

The bot needs folders to store data:

```bash
# Run from project root
mkdir logs
mkdir bot\data\tickets
mkdir bot\data\queue
mkdir bot\data\temp
```

These already exist in the repo, but verify they're present.

---

## Running the Bot 🚀

### Method 1: Batch File (Recommended for Beginners)

1. Navigate to the project folder
2. Double-click `start_bot.bat`
3. A command window opens and the bot starts
4. Keep the window open for the bot to keep running

**To stop:** Close the command window or press `Ctrl+C`

### Method 2: Command Prompt/PowerShell

```bash
# Navigate to project root
cd d:\TICKETINGBOT

# Activate virtual environment
venv\Scripts\activate

# Run the bot
python bot/main.py
```

**Output should show:**
```
[2025-04-11 10:30:00] INFO: Starting Telegram bot...
[2025-04-11 10:30:01] INFO: Bot is polling...
```

### Method 3: Windows Terminal (Modern)

1. Open Windows Terminal (Windows 11)
2. Navigate to project: `cd d:\TICKETINGBOT`
3. Run:
```bash
venv\Scripts\activate
python bot/main.py
```

---

## Running as a Background Service (Advanced) 🔧

To keep the bot running even when you're not logged in:

### Option A: Windows Task Scheduler (Easy)

1. Open **Task Scheduler** (Press `Win+R`, type `taskschd.msc`)
2. Click "Create Basic Task..." on the right
3. Name it: `Telegram Help Desk Bot`
4. Trigger: "At startup"
5. Action: "Start a program"
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `bot/main.py`
   - Start in: `C:\path\to\TICKETINGBOT`
6. ✅ Click Finish

The bot will now start automatically on Windows startup.

### Option B: NSSM (Non-Sucking Service Manager)

For more control (recommended):

```bash
# Download NSSM from https://nssm.cc/download
# Extract it, then:

cd C:\nssm-2.24\win64
nssm install TicketingBot "C:\path\to\venv\Scripts\python.exe" "bot/main.py" "C:\path\to\TICKETINGBOT"

# Start service
nssm start TicketingBot

# View status
nssm status TicketingBot

# Stop service
nssm stop TicketingBot
```

### Option C: Docker on Windows (Enterprise)

If you prefer containers:

```bash
# Install Docker Desktop for Windows
# Then:

docker-compose up -d
docker-compose logs -f
```

See `DOCKER_DEPLOYMENT.md` for details.

---

## Verify Setup ✅

Before using in production:

### 1. Test Bot Configuration

```bash
# With venv activated:
python -c "from bot.config.settings import settings; print('✅ Config loaded successfully')"
```

**Expected:** ✅ Config loaded successfully

**If error:** Check your `.env` file syntax (use `=` not `:`)

### 2. Test Email Configuration

```bash
python -c "
from bot.services.ticket_service import TicketService
import asyncio

async def test():
    try:
        service = TicketService()
        print('✅ Email configured correctly')
    except Exception as e:
        print(f'❌ Email error: {e}')

asyncio.run(test())
"
```

### 3. Test Bot Connection

Open Telegram:
1. Search for your bot (by username from @BotFather)
2. Click `/start`
3. Bot should respond with menu

**If bot doesn't respond:**
- Check the command prompt for errors
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Verify bot is still running (look for "polling" message)

### 4. Test Ticket Creation

1. In Telegram, send `/start` to your bot
2. Follow the workflow to create a test ticket
3. Check your Spiceworks inbox for the ticket
4. Check `logs/bot.log` for any errors

---

## Troubleshooting 🔧

### "Python is not recognized"

**Problem:** `python: The term 'python' is not recognized`

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org)
2. **Check:** ✅ "Add Python to PATH" during installation
3. Restart Command Prompt and try again

Alternatively, use full path:
```bash
C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe bot/main.py
```

### "No module named bot"

**Problem:** `ModuleNotFoundError: No module named 'bot'`

**Solution:**
```bash
# Make sure you're in the project root directory
cd d:\TICKETINGBOT

# Verify you see bot/ folder
dir /b

# Make sure venv is activated (should see (venv) in prompt)
venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt
```

### "Connection refused" or "Bot not responding"

**Problem:** Bot starts but doesn't respond to Telegram messages

**Solution:**
1. Check `TELEGRAM_BOT_TOKEN` in `.env` is correct
   - Get new one: Message @BotFather on Telegram
   - Copy exact token (no extra spaces)
2. Ensure bot is still running in the command window
3. Search for bot by exact username in Telegram
4. Check `logs/bot.log` for error messages

### "SMTP authentication failed"

**Problem:** Can't send emails

**Solution:**
1. Verify Gmail 2FA is **enabled** (required for app passwords)
   - Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Generate **App Password** (not regular password)
   - Click "App passwords"
   - Select Mail → Windows Computer
   - Copy the 16-character password (includes spaces)
3. Update `.env`:
   ```ini
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   SMTP_USERNAME=your-email@gmail.com
   ```
4. Restart bot

### "Port already in use"

**Problem:** `Address already in use`

**Solution:**
```bash
# Find process using the port (if applicable)
# Close any other instance of the bot

# Or kill Python process:
taskkill /im python.exe /F

# Then restart bot
python bot/main.py
```

### "Permission denied" for logs

**Problem:** Can't write to `logs/` folder

**Solution:**
```bash
# Create logs folder if missing
mkdir logs

# Or run Command Prompt as Administrator
```

---

## Performance Tuning 🏎️

For production environments:

### Logging

```ini
# Production
LOG_LEVEL=INFO
LOG_FILE_PATH=C:\TicketingBot\logs\bot.log

# Development
LOG_LEVEL=DEBUG
LOG_FILE_PATH=./logs/bot.log
```

### Conversation Timeout

```ini
CONVERSATION_TIMEOUT_MINUTES=30
```

Prevents users from getting stuck in conversations.

### Queue Mode

```ini
QUEUE_ENABLED=true
CONCURRENT_TICKET_CREATION=1
```

For high-traffic environments, queue tickets to prevent overwhelming Spiceworks.

---

## Monitoring 📊

### Check Bot Logs

```bash
# View last 50 lines
type logs\bot.log | tail -50

# Or in PowerShell
Get-Content logs\bot.log -Tail 50
```

### Monitor Running Process

```bash
# List running Python processes
tasklist | findstr python

# Get details
Get-Process | Where-Object {$_.ProcessName -eq "python"}
```

### Automated Restarts (Optional)

If bot crashes, restart it automatically:

1. **Windows Task Scheduler** (see Background Service section)
2. **Batch script with loop:**

```batch
@echo off
:restart_bot
python bot/main.py
REM Bot crashed, restart after 5 seconds
timeout /t 5
goto restart_bot
```

---

## Common Bot Commands 📖

Once running, users can:

- `/start` - Create new ticket
- `/lookup` - Check existing tickets
- `/help` - Show help menu
- `/admin` - Admin panel (requires `ADMIN_PASSWORD`)

Admin commands (after `/admin`):
- `/list` - View all tickets
- `/view {id}` - View specific ticket
- `/delete {id}` - Delete ticket
- `/reply {id} {message}` - Add note to ticket

---

## Deployment Checklist ✅

Before going to production:

- [ ] Python 3.8+ installed and in PATH
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with all required settings
- [ ] `TELEGRAM_BOT_TOKEN` verified (test with @BotFather)
- [ ] Gmail App Password configured (`SMTP_PASSWORD`)
- [ ] `ADMIN_PASSWORD` is strong (min 16 characters)
- [ ] Email test successful (ticket creation sends email)
- [ ] Bot responds to `/start` command in Telegram
- [ ] Test ticket created and appears in Spiceworks
- [ ] Logs directory exists and is writable
- [ ] Bot runs successfully for at least 5 minutes without errors
- [ ] Scheduled to restart on boot (using Task Scheduler or NSSM)

---

## Next Steps

### For Development
- Run bot locally with `LOG_LEVEL=DEBUG` to see detailed logs
- Test all features: ticket creation, email, admin panel, lookup
- Check `logs/bot.log` after testing

### For Production
- Switch to `LOG_LEVEL=INFO`
- Set up automatic restarts using Task Scheduler or NSSM
- Monitor performance and logs regularly
- Back up `.env` file securely (never commit to git)
- See `DEPLOYMENT_CHECKLIST.md` for complete pre-deployment verification

### For Docker Users
- See `DOCKER_DEPLOYMENT.md` for containerized setup
- Useful if you plan to migrate to cloud (Azure, AWS, etc.)

---

## Getting Help

### Check Logs

All issues are logged to `logs/bot.log`. Start there:

```bash
# View errors
type logs\bot.log | findstr ERROR

# View warnings
type logs\bot.log | findstr WARNING
```

### Common Issues

1. **Bot not responding?** → Check `.env` token and logs
2. **Email not sending?** → Verify Gmail settings and app password
3. **Crashes on startup?** → Check `.env` syntax
4. **Permission errors?** → Run as Administrator

### Support

- Telegram Bot API issues: Check [@BotFather](https://t.me/botfather)
- Gmail issues: Visit [myaccount.google.com](https://myaccount.google.com)
- Python issues: Check [python.org](https://www.python.org)
