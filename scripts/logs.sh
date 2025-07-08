#!/bin/bash

# Log Viewer Script for MarketMindAI
# Usage: ./scripts/logs.sh [service] [lines]

SERVICE=${1:-all}
LINES=${2:-50}

echo "📋 Showing logs for: $SERVICE (last $LINES lines)"
echo "================================================"

case $SERVICE in
    "backend"|"api")
        docker logs --tail=$LINES -f marketmindai_backend
        ;;
    "frontend"|"web")
        docker logs --tail=$LINES -f marketmindai_frontend
        ;;
    "database"|"db"|"postgres")
        docker logs --tail=$LINES -f marketmindai_postgres
        ;;
    "redis")
        docker logs --tail=$LINES -f marketmindai_redis
        ;;
    "nginx")
        docker logs --tail=$LINES -f marketmindai_nginx
        ;;
    "all")
        echo "🔧 Backend Logs:"
        docker logs --tail=10 marketmindai_backend
        echo ""
        echo "🌐 Frontend Logs:"
        docker logs --tail=10 marketmindai_frontend
        echo ""
        echo "🗄️ Database Logs:"
        docker logs --tail=10 marketmindai_postgres
        echo ""
        echo "🔄 Redis Logs:"
        docker logs --tail=10 marketmindai_redis
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        echo "Available services: backend, frontend, database, redis, nginx, all"
        exit 1
        ;;
esac