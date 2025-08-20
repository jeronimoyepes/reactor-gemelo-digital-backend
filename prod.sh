#!/bin/bash

# Production startup script for Reactor Backend API
# This script starts the production environment without hot reloading

echo "🚀 Starting Reactor Backend API in Production Mode"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ No .env file found. Please create a .env file with production settings."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start the production environment
echo "🔨 Building production container..."
docker-compose build

echo "🚀 Starting production server..."
docker-compose up -d

echo ""
echo "🎉 Production server started!"
echo "📱 API available at: http://localhost:8080"
echo "🔍 Health check: http://localhost:8080/health"
echo "📁 Hot reloading is DISABLED for production"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop the server: docker-compose down"



