#!/bin/bash

# Stream Distribution Manager - Startup Script

set -e

echo "====================================="
echo "Stream Distribution Manager"
echo "====================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  WARNING: Please edit .env file and change the default passwords and API keys!"
    echo ""
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs

# Pull latest images
echo "🐳 Pulling Docker images..."
docker-compose pull

# Build application
echo "🔨 Building application..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Stream Distribution Manager is running!"
    echo ""
    echo "📊 Access the web UI at: http://localhost:8080"
    echo "🔑 Default API Key: your-secret-api-key-change-in-production"
    echo ""
    echo "📝 Useful commands:"
    echo "  - View logs:    docker-compose logs -f"
    echo "  - Stop:         docker-compose down"
    echo "  - Restart:      docker-compose restart"
    echo "  - Status:       docker-compose ps"
    echo ""
else
    echo "❌ Failed to start services. Check logs with: docker-compose logs"
    exit 1
fi
