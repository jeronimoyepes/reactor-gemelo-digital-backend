#!/bin/bash

# Development startup script for Reactor Backend API
# This script starts the development environment with hot reloading enabled

echo "🚀 Starting Reactor Backend API in Development Mode"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating default .env file..."
    cat > .env << EOF
# Database
DB_PATH=users.db

# Server Configuration
HOST=localhost
PORT=8080
DEBUG=true

# Admin User
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123

# Uploads Directory
UPLOADS_DIR=uploads

# Experiment Processing Configuration
TRIES_TO_FAIL_EXPERIMENT=3
EXPERIMENT_TIMEOUT_MINUTES=15

# Development Settings
RELOADER=true
DEBUG_PYTHON=false
DEBUG_WAIT=false

# File Upload Configuration
MAX_FILE_SIZE_MB=100
EOF
    echo "✅ Created default .env file"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down

# Build and start the development environment
echo "🔨 Building development container..."
docker-compose -f docker-compose.dev.yml build

echo "🚀 Starting development server..."
docker-compose -f docker-compose.dev.yml up

echo ""
echo "🎉 Development server started!"
echo "📱 API available at: http://localhost:8080"
echo "🔍 Health check: http://localhost:8080/health"
echo "📁 Hot reloading is ENABLED - your changes will automatically restart the server!"
echo ""
echo "To stop the server, press Ctrl+C or run: docker-compose -f docker-compose.dev.yml down"
