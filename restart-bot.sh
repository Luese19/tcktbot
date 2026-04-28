#!/bin/bash
# Stop and restart the bot properly
# Ensures no ghost processes remain

echo "🛑 Stopping bot..."
docker-compose down --remove-orphans

# Remove lock file if it exists
LOCK_FILE="$HOME/.ticketingbot.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "🔓 Removing lock file: $LOCK_FILE"
    rm -f "$LOCK_FILE"
fi

# Wait a bit for cleanup
sleep 2

echo "🚀 Starting bot..."
docker-compose up -d

echo "✅ Bot restarted!"
echo "View logs with: docker-compose logs -f"
