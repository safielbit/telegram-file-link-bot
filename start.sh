#!/bin/bash

# Koyeb startup script
echo "Starting Telegram File Link Bot on Koyeb..."

# Set default port if not provided
export PORT=${PORT:-5000}

# Start the application
exec python main.py