#!/bin/bash
# Monitor bot logs in real-time

echo "📋 Bot Logs (streaming)..."
echo "Press Ctrl+C to exit"
echo ""

docker-compose logs -f ticketingbot
