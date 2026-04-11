@echo off
REM Stop all Python processes and restart the bot
echo Stopping all Python processes...
taskkill /im python.exe /F 2>nul

echo Waiting 2 seconds...
timeout /t 2 /nobreak

echo Starting Telegram Help Desk Bot...
cd /d "%~dp0"
python bot/main.py

pause
