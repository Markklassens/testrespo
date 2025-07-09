#!/bin/bash

# MarketMindAI Deployment Script
# Usage: ./deploy.sh [environment]
# Environments: dev, prod

set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME="marketmindai"

echo "🚀 Deploying MarketMindAI to $ENVIRONMENT environment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs/nginx logs/backend backups nginx ssl redis

# Set environment variables
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🔧 Setting up production environment..."
    if [ ! -f .env.production ]; then
        echo "❌ .env.production file not found. Please create it with your production settings."
        exit 1
    fi
    
    # Copy production environment
    cp .env.production .env
    
    # Build and deploy with production configuration
    echo "🏗️ Building Docker images for production..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml build --no-cache
    else
        docker compose -f docker-compose.prod.yml build --no-cache
    fi
    
    echo "🔄 Stopping existing containers..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml down
    else
        docker compose -f docker-compose.prod.yml down
    fi
    
    echo "🚀 Starting production services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker compose -f docker-compose.prod.yml up -d
    fi
    
    # Wait for services to be healthy
    echo "⏳ Waiting for services to be healthy..."
    if command -v docker-compose &> /dev/null; then
        timeout 300 bash -c 'until docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; do sleep 5; done'
    else
        timeout 300 bash -c 'until docker compose -f docker-compose.prod.yml ps | grep -q "healthy"; do sleep 5; done'
    fi
    
else
    echo "🔧 Setting up development environment..."
    
    # Build and deploy with development configuration
    echo "🏗️ Building Docker images for development..."
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
    else
        docker compose build --no-cache
    fi
    
    echo "🔄 Stopping existing containers..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    
    echo "🚀 Starting development services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    # Wait for services to be healthy
    echo "⏳ Waiting for services to be healthy..."
    if command -v docker-compose &> /dev/null; then
        timeout 300 bash -c 'until docker-compose ps | grep -q "healthy"; do sleep 5; done'
    else
        timeout 300 bash -c 'until docker compose ps | grep -q "healthy"; do sleep 5; done'
    fi
fi

# Check service health
echo "🔍 Checking service health..."
if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

# Wait a bit more for services to fully start
sleep 10

# Check if services are running
if command -v docker-compose &> /dev/null; then
    BACKEND_STATUS=$(docker-compose -f $COMPOSE_FILE ps backend | grep "Up" || echo "Down")
    FRONTEND_STATUS=$(docker-compose -f $COMPOSE_FILE ps frontend | grep "Up" || echo "Down")
    DB_STATUS=$(docker-compose -f $COMPOSE_FILE ps postgres | grep "Up" || echo "Down")
else
    BACKEND_STATUS=$(docker compose -f $COMPOSE_FILE ps backend | grep "Up" || echo "Down")
    FRONTEND_STATUS=$(docker compose -f $COMPOSE_FILE ps frontend | grep "Up" || echo "Down")
    DB_STATUS=$(docker compose -f $COMPOSE_FILE ps postgres | grep "Up" || echo "Down")
fi

echo "📊 Service Status:"
echo "   Backend: $BACKEND_STATUS"
echo "   Frontend: $FRONTEND_STATUS"
echo "   Database: $DB_STATUS"

if [[ "$BACKEND_STATUS" == *"Up"* ]] && [[ "$FRONTEND_STATUS" == *"Up"* ]] && [[ "$DB_STATUS" == *"Up"* ]]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Application URLs:"
    if [ "$ENVIRONMENT" = "prod" ]; then
        echo "   Frontend: https://your-domain.com"
        echo "   Backend API: https://your-domain.com/api"
        echo "   Admin Panel: https://your-domain.com/admin"
    else
        echo "   Frontend: http://localhost:3000"
        echo "   Backend API: http://localhost:8001/api"
        echo "   Admin Panel: http://localhost:3000/admin"
    fi
    echo ""
    echo "📝 Default Admin Credentials:"
    echo "   Email: admin@marketmindai.com"
    echo "   Password: admin123"
else
    echo "❌ Deployment failed. Check the logs:"
    echo "   Backend logs: docker logs marketmindai_backend"
    echo "   Frontend logs: docker logs marketmindai_frontend"
    echo "   Database logs: docker logs marketmindai_postgres"
    exit 1
fi

# Show logs
echo ""
echo "📋 Recent logs:"
echo "--- Backend Logs ---"
if command -v docker-compose &> /dev/null; then
    docker-compose -f $COMPOSE_FILE logs --tail=10 backend
else
    docker compose -f $COMPOSE_FILE logs --tail=10 backend
fi
echo ""
echo "--- Frontend Logs ---"
if command -v docker-compose &> /dev/null; then
    docker-compose -f $COMPOSE_FILE logs --tail=10 frontend
else
    docker compose -f $COMPOSE_FILE logs --tail=10 frontend
fi