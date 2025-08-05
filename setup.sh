#!/bin/bash

echo "🚀 Reactor Backend API Setup"
echo "=============================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created! Edit it to customize your settings."
else
    echo "✅ .env file already exists."
fi

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected!"
    echo ""
    echo "Choose your setup method:"
    echo "1) Local development (Python)"
    echo "2) Docker development"
    echo "3) Docker production"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            echo "📦 Installing Python dependencies..."
            pip install -r requirements.txt
            echo "✅ Dependencies installed!"
            echo "🚀 Starting server..."
            python app.py
            ;;
        2)
            echo "🐳 Building and starting with Docker Compose..."
            docker-compose up --build
            ;;
        3)
            echo "🏭 Building production image..."
            docker build -f Dockerfile.prod -t reactor-backend:prod .
            echo "✅ Production image built!"
            echo "🚀 Starting production container..."
            docker run -d \
                --name reactor-backend \
                -p 8080:8080 \
                -v $(pwd)/data:/app/data \
                reactor-backend:prod
            echo "✅ Container started! API available at http://localhost:8080"
            ;;
        *)
            echo "❌ Invalid choice. Please run the script again."
            exit 1
            ;;
    esac
else
    echo "🐍 Docker not found. Using local Python setup..."
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed!"
    echo "🚀 Starting server..."
    python app.py
fi 