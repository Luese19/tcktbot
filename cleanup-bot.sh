#!/bin/bash
# Force kill all bot instances and cleanup

echo "💀 Force killing all bot instances..."
pkill -f "python.*main.py" || true

# Remove lock file
LOCK_FILE="$HOME/.ticketingbot.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "🔓 Removing lock file: $LOCK_FILE"
    rm -f "$LOCK_FILE"
fi

# Also stop Docker container
echo "🛑 Stopping Docker container..."
docker-compose down --remove-orphans 2>/dev/null || true

sleep 1
echo "✅ All processes cleaned up!"
