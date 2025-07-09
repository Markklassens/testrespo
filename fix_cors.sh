#!/bin/bash

echo "🔧 Fixing CORS issues for GitHub Codespace..."

# Stop any running services
echo "🛑 Stopping existing services..."
sudo supervisorctl stop all 2>/dev/null || true
pkill -f "python.*server.py" 2>/dev/null || true
pkill -f "yarn.*start" 2>/dev/null || true

# Update supervisor configuration to use proper environment variables
echo "📝 Updating supervisor configuration..."

# Backend supervisor config
sudo tee /etc/supervisor/conf.d/marketmindai-backend.conf << 'EOF'
[program:marketmindai-backend]
directory=/app/backend
command=/app/backend/venv/bin/python server.py
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/marketmindai-backend.err.log
stdout_logfile=/var/log/supervisor/marketmindai-backend.out.log
user=codespace
environment=PATH="/app/backend/venv/bin",
           DATABASE_URL="postgresql://marketmindai:marketmindai123@localhost:5432/marketmindai",
           APP_URL="https://fictional-happiness-jjgp7p5p4gp4hq9rw-3000.app.github.dev",
           API_URL="https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev",
           CODESPACE_NAME="fictional-happiness-jjgp7p5p4gp4hq9rw"
EOF

# Frontend supervisor config  
sudo tee /etc/supervisor/conf.d/marketmindai-frontend.conf << 'EOF'
[program:marketmindai-frontend]
directory=/app/frontend
command=/usr/bin/yarn start
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/marketmindai-frontend.err.log
stdout_logfile=/var/log/supervisor/marketmindai-frontend.out.log
user=codespace
environment=PATH="/usr/bin:/usr/local/bin",
           REACT_APP_BACKEND_URL="https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev",
           REACT_APP_APP_NAME="MarketMindAI"
EOF

# Reload supervisor
echo "🔄 Reloading supervisor..."
sudo supervisorctl reread
sudo supervisorctl update

# Start services
echo "🚀 Starting services..."
sudo supervisorctl start all

# Wait a moment for services to start
sleep 5

# Check status
echo "📊 Service status:"
sudo supervisorctl status

echo ""
echo "✅ CORS fix complete!"
echo ""
echo "🌐 Updated URLs:"
echo "   Frontend: https://fictional-happiness-jjgp7p5p4gp4hq9rw-3000.app.github.dev"
echo "   Backend:  https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev"
echo "   API Docs: https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev/docs"
echo ""
echo "📋 To check logs:"
echo "   Backend:  sudo tail -f /var/log/supervisor/marketmindai-backend.out.log"
echo "   Frontend: sudo tail -f /var/log/supervisor/marketmindai-frontend.out.log"