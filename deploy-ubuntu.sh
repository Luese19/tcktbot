#!/bin/bash
# Automated setup script for deploying Ticketing Bot to Ubuntu

set -e  # Exit on error

echo "================================"
echo "Ticketing Bot Docker Setup"
echo "================================"

# Check if running as root/sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script should be run with sudo"
   exit 1
fi

# Create project directory
PROJECT_DIR="/opt/ticketing-bot"
mkdir -p $PROJECT_DIR
echo "✓ Created project directory: $PROJECT_DIR"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    apt-get update
    apt-get install -y docker.io
    systemctl enable docker
    systemctl start docker
    echo "✓ Docker installed and enabled"
else
    echo "✓ Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    apt-get install -y docker-compose
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose already installed"
fi

# Prompt for configuration
echo ""
echo "Please enter Telegram Bot configuration:"
read -p "Telegram Bot Token: " TELEGRAM_TOKEN
read -p "Company Name: " COMPANY_NAME
read -p "Support Email: " SUPPORT_EMAIL
read -p "Log Level (INFO/DEBUG/WARNING): " LOG_LEVEL
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Create .env file
cat > $PROJECT_DIR/.env <<EOF
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
COMPANY_NAME=$COMPANY_NAME
SUPPORT_EMAIL=$SUPPORT_EMAIL
LOG_LEVEL=$LOG_LEVEL
EOF
echo "✓ Created .env configuration file"

# Set permissions
chmod 600 $PROJECT_DIR/.env
echo "✓ Set proper permissions on .env file"

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Copy your project files to: $PROJECT_DIR"
echo "2. Navigate: cd $PROJECT_DIR"
echo "3. Build image: docker-compose build"
echo "4. Start bot: docker-compose up -d"
echo "5. View logs: docker-compose logs -f"
echo ""
