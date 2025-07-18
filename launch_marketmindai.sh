#!/bin/bash

# MarketMindAI Application Launch Script
# This script launches PostgreSQL in Docker and starts the full application stack

set -e  # Exit on any error

echo "🚀 MarketMindAI Application Launch Script"
echo "=========================================="

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for PostgreSQL to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec marketmindai-postgres pg_isready -U marketmindai_user -d marketmindai >/dev/null 2>&1; then
            print_status "PostgreSQL is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    print_error "PostgreSQL failed to start within $max_attempts seconds"
    return 1
}

# Function to check if container is running
is_container_running() {
    docker ps --filter "name=$1" --filter "status=running" --quiet | grep -q .
}

# Function to check if container exists
container_exists() {
    docker ps -a --filter "name=$1" --quiet | grep -q .
}

# Check prerequisites
print_step "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists python3; then
    print_error "Python3 is not installed. Please install Python3 first."
    exit 1
fi

print_status "All prerequisites are met!"

# Step 1: Handle existing PostgreSQL container
print_step "Managing PostgreSQL container..."

if container_exists "marketmindai-postgres"; then
    if is_container_running "marketmindai-postgres"; then
        print_warning "PostgreSQL container is already running. Stopping it first..."
        docker stop marketmindai-postgres
    fi
    print_warning "Removing existing PostgreSQL container..."
    docker rm marketmindai-postgres
fi

# Step 2: Start PostgreSQL container
print_step "Starting PostgreSQL container..."

docker run --name marketmindai-postgres \
  -e POSTGRES_DB=marketmindai \
  -e POSTGRES_USER=marketmindai_user \
  -e POSTGRES_PASSWORD=marketmindai_password \
  -p 5432:5432 \
  -d postgres:15

if [ $? -eq 0 ]; then
    print_status "PostgreSQL container started successfully!"
else
    print_error "Failed to start PostgreSQL container"
    exit 1
fi

# Step 3: Wait for PostgreSQL to be ready
wait_for_postgres

# Step 4: Update backend environment variables
print_step "Updating backend environment variables..."

# Create new .env file for backend with Docker PostgreSQL configuration
cat > /app/backend/.env << EOF
# Database Configuration (Docker PostgreSQL)
DATABASE_URL=postgresql://marketmindai_user:marketmindai_password@localhost:5432/marketmindai

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-1752065848
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=rohushanshinde@gmail.com
SMTP_PASSWORD=pajb dmcp cegp pguz
SMTP_FROM_EMAIL=rohushanshinde@gmail.com
SMTP_USE_TLS=true

# Application Configuration
APP_NAME=MarketMindAI
APP_URL=http://localhost:3000
API_URL=http://localhost:8001
CODESPACE_NAME=

# Admin AI API Keys
ADMIN_GROQ_API_KEY=
ADMIN_CLAUDE_API_KEY=
EOF

print_status "Backend environment variables updated!"

# Step 5: Install backend dependencies
print_step "Installing backend dependencies..."

cd /app/backend
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Backend dependencies installed!"
else
    print_warning "requirements.txt not found, skipping dependency installation"
fi

# Step 6: Initialize database
print_step "Initializing database schema..."

if [ -f "init_db.py" ]; then
    python init_db.py
    print_status "Database schema initialized!"
else
    print_warning "init_db.py not found, skipping database initialization"
fi

# Step 7: Seed database with test data
print_step "Seeding database with test data..."

if [ -f "seed_data.py" ]; then
    python seed_data.py
    print_status "Database seeded with test data!"
else
    print_warning "seed_data.py not found, skipping data seeding"
fi

# Step 8: Test database connection
print_step "Testing database connection..."

python -c "
from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Step 9: Install frontend dependencies
print_step "Installing frontend dependencies..."

cd /app/frontend
if [ -f "package.json" ]; then
    if command_exists yarn; then
        yarn install
        print_status "Frontend dependencies installed with yarn!"
    else
        npm install
        print_status "Frontend dependencies installed with npm!"
    fi
else
    print_warning "package.json not found, skipping frontend dependency installation"
fi

# Step 10: Start backend server
print_step "Starting backend server..."

cd /app/backend
nohup python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Test backend health
print_step "Testing backend health..."

if curl -s http://localhost:8001/api/health > /dev/null; then
    print_status "Backend server is healthy!"
else
    print_error "Backend server failed to start properly"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Step 11: Start frontend server
print_step "Starting frontend server..."

cd /app/frontend
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Step 12: Final verification
print_step "Performing final verification..."

# Test backend API
if curl -s http://localhost:8001/api/health | grep -q "healthy"; then
    print_status "✅ Backend API is responding correctly"
else
    print_warning "⚠️ Backend API test failed"
fi

# Test database connection via API
if curl -s http://localhost:8001/api/debug/connectivity | grep -q "success"; then
    print_status "✅ Database connection via API is working"
else
    print_warning "⚠️ Database API test failed"
fi

# Test frontend (check if port 3000 is responding)
if curl -s http://localhost:3000 > /dev/null; then
    print_status "✅ Frontend server is responding"
else
    print_warning "⚠️ Frontend server test failed"
fi

echo ""
echo "🎉 MarketMindAI Application Launch Complete!"
echo "==========================================="
echo ""
echo "📋 Application Status:"
echo "  🐘 PostgreSQL: Running in Docker container 'marketmindai-postgres'"
echo "  🔧 Backend API: http://localhost:8001"
echo "  🌐 Frontend: http://localhost:3000"
echo "  📊 API Health: http://localhost:8001/api/health"
echo "  🔍 Debug Info: http://localhost:8001/api/debug/connectivity"
echo ""
echo "👥 Test User Credentials:"
echo "  📧 User: user@marketmindai.com / password123"
echo "  🔒 Admin: admin@marketmindai.com / admin123"
echo "  ⚡ SuperAdmin: superadmin@marketmindai.com / superadmin123"
echo ""
echo "🛠️ Useful Commands:"
echo "  View backend logs: tail -f /tmp/backend.log"
echo "  View frontend logs: tail -f /tmp/frontend.log"
echo "  Stop PostgreSQL: docker stop marketmindai-postgres"
echo "  Remove PostgreSQL: docker rm marketmindai-postgres"
echo ""
echo "Process IDs:"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the application:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  docker stop marketmindai-postgres"
echo ""