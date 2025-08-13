#!/bin/bash

echo "🚀 Deploying Meta Ads Enterprise system..."

if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

required_vars=("FACEBOOK_ACCESS_TOKEN" "FACEBOOK_APP_ID" "FACEBOOK_APP_SECRET" "FACEBOOK_AD_ACCOUNT_ID")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "🛑 Stopping existing containers..."
docker-compose down

echo "📦 Pulling latest images..."
docker-compose pull

echo "🔨 Building updated images..."
docker-compose build --no-cache

echo "🚀 Starting services..."

echo "📊 Starting infrastructure services..."
docker-compose up -d postgres redis

echo "⏳ Waiting for database to be ready..."
sleep 15

echo "🔧 Starting backend services..."
docker-compose up -d backend celery-worker celery-beat

echo "⏳ Waiting for backend to be ready..."
sleep 10

echo "🌐 Starting frontend and proxy..."
docker-compose up -d frontend nginx

echo "📈 Starting monitoring services..."
docker-compose up -d prometheus grafana flower

echo "🏥 Running health checks..."
sleep 30

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ Database health check failed"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "Services status:"
docker-compose ps

echo ""
echo "Access URLs:"
echo "🌐 Frontend: http://localhost:3000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📊 Grafana: http://localhost:4000 (admin/admin123)"
echo "🌸 Flower: http://localhost:5555"
echo "📈 Prometheus: http://localhost:9090"
echo ""
echo "Default login:"
echo "📧 Email: admin@metaads.com"
echo "🔑 Password: admin123"
