#!/bin/bash

# MarketMindAI Application Stop Script
# This script stops all components of the MarketMindAI application

set -e  # Exit on any error

echo "🛑 MarketMindAI Application Stop Script"
echo "======================================="

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

# Step 1: Stop backend processes
print_step "Stopping backend processes..."

# Find and kill Python processes running the backend
BACKEND_PIDS=$(ps aux | grep "[u]vicorn server:app" | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    echo $BACKEND_PIDS | xargs kill -TERM 2>/dev/null || true
    sleep 2
    # Force kill if still running
    echo $BACKEND_PIDS | xargs kill -KILL 2>/dev/null || true
    print_status "Backend processes stopped"
else
    print_warning "No backend processes found"
fi

# Step 2: Stop frontend processes
print_step "Stopping frontend processes..."

# Find and kill Node.js processes running the frontend
FRONTEND_PIDS=$(ps aux | grep "[n]ode.*react-scripts" | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    echo $FRONTEND_PIDS | xargs kill -TERM 2>/dev/null || true
    sleep 2
    # Force kill if still running
    echo $FRONTEND_PIDS | xargs kill -KILL 2>/dev/null || true
    print_status "Frontend processes stopped"
else
    print_warning "No frontend processes found"
fi

# Step 3: Stop PostgreSQL container
print_step "Stopping PostgreSQL container..."

if is_container_running "marketmindai-postgres"; then
    docker stop marketmindai-postgres
    print_status "PostgreSQL container stopped"
else
    print_warning "PostgreSQL container is not running"
fi

# Step 4: Optional cleanup
read -p "Do you want to remove the PostgreSQL container and data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Removing PostgreSQL container..."
    docker rm marketmindai-postgres 2>/dev/null || true
    print_status "PostgreSQL container removed"
fi

# Step 5: Clean up log files
print_step "Cleaning up log files..."

rm -f /tmp/backend.log /tmp/frontend.log
print_status "Log files cleaned up"

# Step 6: Verify cleanup
print_step "Verifying cleanup..."

# Check for remaining processes
REMAINING_BACKEND=$(ps aux | grep "[u]vicorn server:app" | wc -l)
REMAINING_FRONTEND=$(ps aux | grep "[n]ode.*react-scripts" | wc -l)

if [ $REMAINING_BACKEND -eq 0 ] && [ $REMAINING_FRONTEND -eq 0 ]; then
    print_status "✅ All application processes stopped successfully"
else
    print_warning "⚠️ Some processes might still be running"
fi

# Check container status
if is_container_running "marketmindai-postgres"; then
    print_warning "⚠️ PostgreSQL container is still running"
else
    print_status "✅ PostgreSQL container stopped"
fi

echo ""
echo "🎉 MarketMindAI Application Stop Complete!"
echo "=========================================="
echo ""
echo "All components have been stopped:"
echo "  🔧 Backend API: Stopped"
echo "  🌐 Frontend: Stopped"
echo "  🐘 PostgreSQL: Stopped"
echo ""
echo "To start the application again, run:"
echo "  ./launch_marketmindai.sh"
echo ""