@echo off
REM Stop and restart the bot properly
REM Ensures no ghost processes remain

echo.
echo 🛑 Stopping bot...
docker-compose down --remove-orphans

REM Remove lock file if it exists
set LOCK_FILE=%USERPROFILE%\.ticketingbot.lock
if exist "%LOCK_FILE%" (
    echo 🔓 Removing lock file: %LOCK_FILE%
    del /f /q "%LOCK_FILE%"
)

REM Wait a bit for cleanup
timeout /t 2 /nobreak

echo.
echo 🚀 Starting bot...
docker-compose up -d

echo.
echo ✅ Bot restarted!
echo View logs with: docker-compose logs -f
pause
