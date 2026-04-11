#!/bin/bash
# Telegram Help Desk Bot - Ubuntu Quick Install Script
# Usage: bash install.sh

set -e

echo "🚀 Telegram Help Desk Bot - Ubuntu Installation Script"
echo "========================================================"

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root or with sudo"
   exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Step 1: Update system
print_info "Step 1/8: Updating system packages..."
apt update
apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl
print_success "System updated"

# Step 2: Clone/verify repository
print_info "Step 2/8: Setting up bot directory..."
if [ ! -d "/opt/ticketingbot" ]; then
    mkdir -p /opt
    print_info "Clone the repository to /opt/ticketingbot"
    print_info "Run: git clone <repo-url> /opt/ticketingbot"
    exit 1
fi
print_success "Bot directory exists"

# Step 3: Create virtual environment
print_info "Step 3/8: Creating Python virtual environment..."
cd /opt/ticketingbot
python3 -m venv venv
source venv/bin/activate
print_success "Virtual environment created"

# Step 4: Install dependencies
print_info "Step 4/8: Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
print_success "Dependencies installed"

# Step 5: Create necessary directories
print_info "Step 5/8: Creating directories..."
mkdir -p bot/data/queue
mkdir -p bot/logs
chmod 755 bot/data
chmod 755 bot/logs
print_success "Directories created"

# Step 6: Check configuration
print_info "Step 6/8: Checking configuration..."
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "Please create .env file with required variables"
    exit 1
fi
print_success ".env file found"

# Step 7: Create systemd service
print_info "Step 7/8: Setting up systemd service..."
CURRENT_USER=$(who | awk '{print $1}' | head -1)
cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Help Desk Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=/opt/ticketingbot
Environment="PATH=/opt/ticketingbot/venv/bin"
ExecStart=/opt/ticketingbot/venv/bin/python3 /opt/ticketingbot/bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-bot/bot.log
StandardError=append:/var/log/telegram-bot/error.log

[Install]
WantedBy=multi-user.target
EOF

mkdir -p /var/log/telegram-bot
chown $CURRENT_USER:$CURRENT_USER /var/log/telegram-bot
chown -R $CURRENT_USER:$CURRENT_USER /opt/ticketingbot

systemctl daemon-reload
systemctl enable telegram-bot
print_success "Systemd service created"

# Step 8: Start service
print_info "Step 8/8: Starting bot service..."
systemctl start telegram-bot
sleep 2

if systemctl is-active --quiet telegram-bot; then
    print_success "Bot service started successfully!"
else
    print_error "Failed to start bot service"
    print_info "Check logs: journalctl -u telegram-bot -n 50"
    exit 1
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "=================================================="
echo ""
print_info "Bot is running as systemd service"
echo ""
echo "📋 Common Commands:"
echo "   View status:  sudo systemctl status telegram-bot"
echo "   View logs:    sudo tail -f /var/log/telegram-bot/bot.log"
echo "   Restart:      sudo systemctl restart telegram-bot"
echo "   Stop:         sudo systemctl stop telegram-bot"
echo ""
print_info "First run will show if bot connects to Telegram successfully"
echo ""
