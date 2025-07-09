#!/bin/bash

# Deployment Verification Script for MarketMindAI
# This script verifies that all components are ready for deployment

echo "🔍 MarketMindAI Deployment Verification"
echo "======================================"

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

# Check Docker
echo -e "\n1. Docker Installation"
docker --version > /dev/null 2>&1
check_status "Docker is installed"

docker ps > /dev/null 2>&1
check_status "Docker daemon is running"

# Check Docker Compose
echo -e "\n2. Docker Compose"
if command -v docker-compose &> /dev/null; then
    docker-compose version > /dev/null 2>&1
    check_status "Docker Compose (v1) is available"
elif docker compose version &> /dev/null; then
    docker compose version > /dev/null 2>&1
    check_status "Docker Compose (v2) is available"
else
    echo "❌ FAIL: Docker Compose not available"
    FAILED=$((FAILED + 1))
fi

# Check Frontend
echo -e "\n3. Frontend Build"
cd /app/frontend
if [ -f "yarn.lock" ]; then
    echo "✅ PASS: yarn.lock exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: yarn.lock missing"
    FAILED=$((FAILED + 1))
fi

if [ -f "package.json" ]; then
    echo "✅ PASS: package.json exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: package.json missing"
    FAILED=$((FAILED + 1))
fi

# Test yarn build
echo "Testing yarn build..."
yarn build > /dev/null 2>&1
check_status "Frontend builds successfully"

# Check build output
if [ -d "build" ] && [ -f "build/index.html" ]; then
    echo "✅ PASS: Build artifacts created"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Build artifacts missing"
    FAILED=$((FAILED + 1))
fi

# Check Backend
echo -e "\n4. Backend Dependencies"
cd /app/backend
if [ -f "requirements.txt" ]; then
    echo "✅ PASS: requirements.txt exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: requirements.txt missing"
    FAILED=$((FAILED + 1))
fi

if [ -f "server.py" ]; then
    echo "✅ PASS: server.py exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: server.py missing"
    FAILED=$((FAILED + 1))
fi

# Check Docker configurations
echo -e "\n5. Docker Configuration"
cd /app
if [ -f "docker-compose.yml" ]; then
    echo "✅ PASS: docker-compose.yml exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: docker-compose.yml missing"
    FAILED=$((FAILED + 1))
fi

if [ -f "docker-compose.prod.yml" ]; then
    echo "✅ PASS: docker-compose.prod.yml exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: docker-compose.prod.yml missing"
    FAILED=$((FAILED + 1))
fi

if [ -f "frontend/Dockerfile" ]; then
    echo "✅ PASS: Frontend Dockerfile exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Frontend Dockerfile missing"
    FAILED=$((FAILED + 1))
fi

if [ -f "backend/Dockerfile" ]; then
    echo "✅ PASS: Backend Dockerfile exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Backend Dockerfile missing"
    FAILED=$((FAILED + 1))
fi

# Check deploy script
echo -e "\n6. Deploy Script"
if [ -f "deploy.sh" ]; then
    echo "✅ PASS: deploy.sh exists"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: deploy.sh missing"
    FAILED=$((FAILED + 1))
fi

if [ -x "deploy.sh" ]; then
    echo "✅ PASS: deploy.sh is executable"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: deploy.sh not executable"
    FAILED=$((FAILED + 1))
fi

# Summary
echo -e "\n======================================"
echo "🎯 Verification Summary"
echo "======================================"
echo "✅ PASSED: $PASSED checks"
echo "❌ FAILED: $FAILED checks"

if [ $FAILED -eq 0 ]; then
    echo -e "\n🚀 ALL CHECKS PASSED! Deployment is ready."
    echo -e "\nTo deploy:"
    echo "   Development: ./deploy.sh dev"
    echo "   Production:  ./deploy.sh prod"
    exit 0
else
    echo -e "\n⚠️  Some checks failed. Please fix the issues above."
    exit 1
fi