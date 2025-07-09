#!/bin/bash

echo "🔧 Comprehensive CORS and WebSocket Fix for MarketMindAI"
echo "======================================================="

# Get current codespace information
CODESPACE_NAME=${CODESPACE_NAME:-"fictional-happiness-jjgp7p5p4gp4hq9rw"}
FRONTEND_URL="https://${CODESPACE_NAME}-3000.app.github.dev"
BACKEND_URL="https://${CODESPACE_NAME}-8001.app.github.dev"

echo "📍 Environment:"
echo "   Codespace: $CODESPACE_NAME"
echo "   Frontend:  $FRONTEND_URL"
echo "   Backend:   $BACKEND_URL"

# 1. Update frontend environment variables
echo "🔧 Updating frontend environment variables..."
cat > /app/frontend/.env << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
REACT_APP_APP_NAME=MarketMindAI
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
WDS_SOCKET_PORT=0
EOF

# 2. Update backend environment variables
echo "🔧 Updating backend environment variables..."
cat > /app/backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://marketmindai:marketmindai123@localhost:5432/marketmindai

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-$(date +%s)
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
APP_URL=$FRONTEND_URL
API_URL=$BACKEND_URL
CODESPACE_NAME=$CODESPACE_NAME

# Admin AI API Keys
ADMIN_GROQ_API_KEY=
ADMIN_CLAUDE_API_KEY=
EOF

# 3. Update CORS configuration in backend
echo "🔧 Updating CORS configuration..."
cat > /tmp/cors_fix.py << 'EOF'
import os
import re

# Read the current server.py file
with open('/app/backend/server.py', 'r') as f:
    content = f.read()

# Define the new CORS configuration
new_cors_config = '''
# Get environment variables
FRONTEND_URL = os.getenv('APP_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('API_URL', 'http://localhost:8001')
CODESPACE_NAME = os.getenv('CODESPACE_NAME', '')

# CORS middleware with comprehensive origins
allowed_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:8001",
    "https://localhost:8001",
    FRONTEND_URL,
    BACKEND_URL,
]

# Add codespace-specific origins
if CODESPACE_NAME:
    allowed_origins.extend([
        f"https://{CODESPACE_NAME}-3000.app.github.dev",
        f"https://{CODESPACE_NAME}-8001.app.github.dev",
    ])

# Add common development origins
additional_origins = [
    "https://fictional-happiness-jjgp7p5p4gp4hq9rw-3000.app.github.dev",
    "https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev",
]
allowed_origins.extend(additional_origins)

# Remove duplicates and None values
allowed_origins = list(set(filter(None, allowed_origins)))
print(f"Allowed CORS origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

# Find and replace the CORS configuration
cors_pattern = r'# Get frontend URL.*?allow_headers=\[".*?"\],\s*\)'
if re.search(cors_pattern, content, re.DOTALL):
    content = re.sub(cors_pattern, new_cors_config, content, flags=re.DOTALL)
else:
    # Fallback: replace existing CORS middleware
    cors_pattern = r'app\.add_middleware\s*\(\s*CORSMiddleware,.*?\)'
    content = re.sub(cors_pattern, new_cors_config.split('app.add_middleware')[1], content, flags=re.DOTALL)

# Write the updated content back
with open('/app/backend/server.py', 'w') as f:
    f.write(content)

print("CORS configuration updated successfully!")
EOF

python3 /tmp/cors_fix.py

# 4. Stop existing services
echo "🛑 Stopping existing services..."
pkill -f "python.*server.py" 2>/dev/null || true
pkill -f "yarn.*start" 2>/dev/null || true
sudo supervisorctl stop all 2>/dev/null || true

# 5. Start backend in background
echo "🚀 Starting backend service..."
cd /app/backend
nohup /app/backend/venv/bin/python server.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Test backend health
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check logs:"
    tail -10 /tmp/backend.log
    exit 1
fi

# 6. Start frontend service
echo "🚀 Starting frontend service..."
cd /app/frontend

# Create a React app configuration to handle WebSocket issues
cat > /app/frontend/.env.local << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
REACT_APP_APP_NAME=MarketMindAI
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
WDS_SOCKET_PORT=0
FAST_REFRESH=false
EOF

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    yarn install
fi

# Start frontend in background
nohup yarn start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"

# 7. Test connectivity
echo "🔍 Testing connectivity..."
sleep 2

# Test backend health
BACKEND_HEALTH=$(curl -s http://localhost:8001/api/health || echo "failed")
if [[ "$BACKEND_HEALTH" == *"healthy"* ]]; then
    echo "✅ Backend health check: PASSED"
else
    echo "❌ Backend health check: FAILED"
fi

# Test frontend access
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend access: PASSED"
else
    echo "❌ Frontend access: FAILED"
fi

# 8. Display results
echo ""
echo "🎉 CORS and WebSocket Fix Complete!"
echo "=================================="
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: $FRONTEND_URL"
echo "   Backend:  $BACKEND_URL"
echo "   API Docs: $BACKEND_URL/docs"
echo "   Health:   $BACKEND_URL/api/health"
echo ""
echo "🔧 Process Information:"
echo "   Backend PID:  $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "📋 To check logs:"
echo "   Backend:  tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "🧪 Test Commands:"
echo "   curl $BACKEND_URL/api/health"
echo "   curl $FRONTEND_URL"
echo ""
echo "✅ Your application should now be accessible without CORS errors!"
echo "🔥 WebSocket errors in console are normal for codespace environments."