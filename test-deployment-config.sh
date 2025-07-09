#!/bin/bash

# Configuration Test Script for MarketMindAI Docker Deployment
# This script validates the Docker setup without actually running containers

echo "🔍 MarketMindAI Docker Configuration Test"
echo "======================================="

PASSED=0
FAILED=0

# Function to check status
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ PASS: $1"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAIL: $1"
        FAILED=$((FAILED + 1))
    fi
}

# Check configuration files
echo -e "\n1. Configuration Files"
[ -f "/app/.env" ]
check_status ".env file exists"

[ -f "/app/docker-compose.yml" ]
check_status "docker-compose.yml exists"

[ -f "/app/backend/Dockerfile" ]
check_status "Backend Dockerfile exists"

[ -f "/app/frontend/Dockerfile" ]
check_status "Frontend Dockerfile exists"

[ -f "/app/backend/init.sql" ]
check_status "Database init.sql exists"

# Check environment variables
echo -e "\n2. Environment Variables"
if [ -f "/app/.env" ]; then
    grep -q "POSTGRES_DB=marketmindai" /app/.env
    check_status "POSTGRES_DB configured"
    
    grep -q "POSTGRES_USER=marketmindai" /app/.env
    check_status "POSTGRES_USER configured"
    
    grep -q "POSTGRES_PASSWORD=" /app/.env
    check_status "POSTGRES_PASSWORD configured"
    
    grep -q "REACT_APP_BACKEND_URL=" /app/.env
    check_status "REACT_APP_BACKEND_URL configured"
fi

# Check frontend environment
echo -e "\n3. Frontend Environment"
if [ -f "/app/frontend/.env" ]; then
    grep -q "REACT_APP_BACKEND_URL=http://localhost:8001" /app/frontend/.env
    check_status "Frontend backend URL configured for local"
fi

# Check backend dependencies
echo -e "\n4. Backend Dependencies"
[ -f "/app/backend/requirements.txt" ]
check_status "requirements.txt exists"

grep -q "fastapi" /app/backend/requirements.txt
check_status "FastAPI dependency listed"

grep -q "psycopg2-binary" /app/backend/requirements.txt
check_status "PostgreSQL driver listed"

# Check database configuration
echo -e "\n5. Database Configuration"
[ -f "/app/backend/database.py" ]
check_status "Database configuration exists"

grep -q "create_engine" /app/backend/database.py
check_status "SQLAlchemy database configuration detected"

# Check Docker Compose configuration
echo -e "\n6. Docker Compose Configuration"
if [ -f "/app/docker-compose.yml" ]; then
    grep -q "postgres:15-alpine" /app/docker-compose.yml
    check_status "PostgreSQL service configured"
    
    grep -q "redis:7-alpine" /app/docker-compose.yml
    check_status "Redis service configured"
    
    grep -q "backend:" /app/docker-compose.yml
    check_status "Backend service configured"
    
    grep -q "frontend:" /app/docker-compose.yml
    check_status "Frontend service configured"
    
    grep -q "DATABASE_URL=postgresql" /app/docker-compose.yml
    check_status "Database connection configured"
fi

# Check build process
echo -e "\n7. Build Process"
cd /app/frontend
if [ -f "package.json" ] && [ -f "yarn.lock" ]; then
    # Test if build would work
    echo "Testing frontend build process..."
    yarn build > /dev/null 2>&1
    check_status "Frontend builds successfully"
fi

cd /app/backend
if [ -f "requirements.txt" ]; then
    echo "Testing backend dependencies..."
    python3 -c "import fastapi, sqlalchemy, psycopg2" 2>/dev/null
    check_status "Backend dependencies available"
fi

# Check port configuration
echo -e "\n8. Port Configuration"
if [ -f "/app/docker-compose.yml" ]; then
    grep -q "3000:80" /app/docker-compose.yml
    check_status "Frontend port mapping configured"
    
    grep -q "8001:8001" /app/docker-compose.yml
    check_status "Backend port mapping configured"
    
    grep -q "5432:5432" /app/docker-compose.yml
    check_status "PostgreSQL port mapping configured"
fi

# Check health checks
echo -e "\n9. Health Checks"
if [ -f "/app/docker-compose.yml" ]; then
    grep -q "healthcheck:" /app/docker-compose.yml
    check_status "Health checks configured"
fi

# Check deployment script
echo -e "\n10. Deployment Script"
[ -f "/app/deploy.sh" ]
check_status "Deploy script exists"

[ -x "/app/deploy.sh" ]
check_status "Deploy script is executable"

if [ -f "/app/deploy.sh" ]; then
    grep -q "docker compose" /app/deploy.sh
    check_status "Deploy script supports Docker Compose v2"
fi

# Summary
echo -e "\n======================================"
echo "🎯 Configuration Test Summary"
echo "======================================"
echo "✅ PASSED: $PASSED checks"
echo "❌ FAILED: $FAILED checks"

if [ $FAILED -eq 0 ]; then
    echo -e "\n🚀 ALL CONFIGURATION CHECKS PASSED!"
    echo -e "\nThe Docker deployment should work in a proper Docker environment."
    echo -e "\nTo deploy:"
    echo "   1. Ensure Docker and Docker Compose are installed and running"
    echo "   2. Run: ./deploy.sh dev"
    echo "   3. Access frontend at: http://localhost:3000"
    echo "   4. Access backend API at: http://localhost:8001"
    echo -e "\nServices configured:"
    echo "   - PostgreSQL database (port 5432)"
    echo "   - Redis cache (port 6379)"
    echo "   - FastAPI backend (port 8001)"
    echo "   - React frontend (port 3000)"
    exit 0
else
    echo -e "\n⚠️  Some configuration checks failed."
    echo "Please review the failed checks above before deployment."
    exit 1
fi