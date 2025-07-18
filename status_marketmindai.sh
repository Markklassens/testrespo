#!/bin/bash

# MarketMindAI Application Status Script
# This script checks the status of all MarketMindAI components

echo "📊 MarketMindAI Application Status"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if container is running
is_container_running() {
    docker ps --filter "name=$1" --filter "status=running" --quiet | grep -q .
}

# Function to check if port is listening
is_port_listening() {
    netstat -tuln 2>/dev/null | grep -q ":$1 "
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected=$2
    
    if curl -s --max-time 5 "$url" | grep -q "$expected"; then
        return 0
    else
        return 1
    fi
}

echo ""
print_step "Checking PostgreSQL Container..."

if is_container_running "marketmindai-postgres"; then
    print_status "✅ PostgreSQL container is running"
    
    # Check if PostgreSQL is accepting connections
    if docker exec marketmindai-postgres pg_isready -U marketmindai_user -d marketmindai >/dev/null 2>&1; then
        print_status "✅ PostgreSQL is accepting connections"
    else
        print_warning "⚠️ PostgreSQL container is running but not accepting connections"
    fi
else
    print_error "❌ PostgreSQL container is not running"
fi

echo ""
print_step "Checking Backend API..."

if is_port_listening 8001; then
    print_status "✅ Backend port 8001 is listening"
    
    # Test backend health endpoint
    if test_endpoint "http://localhost:8001/api/health" "healthy"; then
        print_status "✅ Backend API is healthy"
        
        # Test database connectivity via API
        if test_endpoint "http://localhost:8001/api/debug/connectivity" "success"; then
            print_status "✅ Database connection via API is working"
        else
            print_warning "⚠️ Database connection via API failed"
        fi
    else
        print_warning "⚠️ Backend API is not responding to health checks"
    fi
else
    print_error "❌ Backend port 8001 is not listening"
fi

echo ""
print_step "Checking Frontend Server..."

if is_port_listening 3000; then
    print_status "✅ Frontend port 3000 is listening"
    
    # Test frontend endpoint
    if curl -s --max-time 5 "http://localhost:3000" > /dev/null; then
        print_status "✅ Frontend is responding"
    else
        print_warning "⚠️ Frontend is not responding"
    fi
else
    print_error "❌ Frontend port 3000 is not listening"
fi

echo ""
print_step "Process Information..."

# Backend processes
BACKEND_PIDS=$(ps aux | grep "[u]vicorn server:app" | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    print_status "✅ Backend processes running (PIDs: $BACKEND_PIDS)"
else
    print_error "❌ No backend processes found"
fi

# Frontend processes
FRONTEND_PIDS=$(ps aux | grep "[n]ode.*react-scripts" | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    print_status "✅ Frontend processes running (PIDs: $FRONTEND_PIDS)"
else
    print_error "❌ No frontend processes found"
fi

echo ""
print_step "Log Files..."

if [ -f "/tmp/backend.log" ]; then
    BACKEND_LOG_SIZE=$(du -sh /tmp/backend.log | cut -f1)
    print_status "✅ Backend log: /tmp/backend.log ($BACKEND_LOG_SIZE)"
else
    print_warning "⚠️ Backend log not found"
fi

if [ -f "/tmp/frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(du -sh /tmp/frontend.log | cut -f1)
    print_status "✅ Frontend log: /tmp/frontend.log ($FRONTEND_LOG_SIZE)"
else
    print_warning "⚠️ Frontend log not found"
fi

echo ""
print_step "Quick API Tests..."

# Test login endpoint
if curl -s --max-time 5 -X POST "http://localhost:8001/api/auth/login" \
   -H "Content-Type: application/json" \
   -d '{"email":"superadmin@marketmindai.com","password":"superadmin123"}' | grep -q "access_token"; then
    print_status "✅ SuperAdmin login endpoint working"
else
    print_warning "⚠️ SuperAdmin login endpoint failed"
fi

# Test tools endpoint
if curl -s --max-time 5 "http://localhost:8001/api/tools" | grep -q "tools"; then
    print_status "✅ Tools API endpoint working"
else
    print_warning "⚠️ Tools API endpoint failed"
fi

echo ""
echo "🎯 Quick Access URLs:"
echo "  🌐 Frontend: http://localhost:3000"
echo "  🔧 Backend API: http://localhost:8001"
echo "  📊 API Health: http://localhost:8001/api/health"
echo "  🔍 Debug Info: http://localhost:8001/api/debug/connectivity"
echo ""
echo "📋 Test Credentials:"
echo "  👤 User: user@marketmindai.com / password123"
echo "  🔒 Admin: admin@marketmindai.com / admin123"
echo "  ⚡ SuperAdmin: superadmin@marketmindai.com / superadmin123"
echo ""
echo "🛠️ Useful Commands:"
echo "  View backend logs: tail -f /tmp/backend.log"
echo "  View frontend logs: tail -f /tmp/frontend.log"
echo "  Stop application: ./stop_marketmindai.sh"
echo "  Restart application: ./launch_marketmindai.sh"
echo ""