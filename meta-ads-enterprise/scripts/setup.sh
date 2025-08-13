#!/bin/bash

echo "🚀 Setting up Meta Ads Enterprise system..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual credentials before running the system."
fi

echo "📁 Creating directories..."
mkdir -p logs
mkdir -p models
mkdir -p static
mkdir -p uploads

echo "🔐 Setting permissions..."
chmod +x scripts/*.sh

echo "📦 Pulling Docker images..."
docker-compose pull

echo "🔨 Building custom images..."
docker-compose build

echo "🌐 Creating Docker networks..."
docker network create meta-ads-network 2>/dev/null || true

echo "🗄️  Initializing database..."
docker-compose up -d postgres
sleep 10

echo "🔄 Running database migrations..."
docker-compose exec postgres psql -U postgres -d metaads -f /docker-entrypoint-initdb.d/init.sql

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run: docker-compose up -d"
echo "3. Access the system at:"
echo "   - Frontend: http://localhost:3000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Grafana: http://localhost:4000"
echo "   - Flower: http://localhost:5555"
echo ""
echo "Default admin credentials:"
echo "   Email: admin@metaads.com"
echo "   Password: admin123"
