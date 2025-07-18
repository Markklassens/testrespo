# 🚀 MarketMindAI Docker Launch Scripts

## Overview
I have created a comprehensive set of shell scripts to launch and manage the MarketMindAI application with PostgreSQL running in Docker. These scripts automate the entire setup process and provide easy management tools.

## 📋 Available Scripts

### 1. `launch_marketmindai.sh` - Main Launch Script
**Purpose**: Complete application startup with PostgreSQL in Docker

**What it does**:
- Starts PostgreSQL container with your specified configuration
- Updates backend environment variables
- Installs all dependencies
- Initializes database schema
- Seeds test data (3 users: user, admin, superadmin)
- Starts backend API server
- Starts frontend development server
- Performs health checks and verification

**Usage**:
```bash
./launch_marketmindai.sh
```

### 2. `stop_marketmindai.sh` - Graceful Shutdown Script
**Purpose**: Properly stops all application components

**What it does**:
- Stops backend processes
- Stops frontend processes  
- Stops PostgreSQL container
- Optionally removes container and data
- Cleans up log files

**Usage**:
```bash
./stop_marketmindai.sh
```

### 3. `status_marketmindai.sh` - Status Monitoring Script
**Purpose**: Comprehensive health checking and monitoring

**What it does**:
- Checks PostgreSQL container status
- Verifies backend API health
- Tests frontend server
- Shows process information
- Tests key endpoints (login, tools, etc.)
- Displays useful URLs and credentials

**Usage**:
```bash
./status_marketmindai.sh
```

### 4. `test_marketmindai.sh` - Comprehensive Test Suite
**Purpose**: Automated testing of all components

**What it does**:
- Runs 15 comprehensive tests
- Tests database connectivity
- Tests all authentication endpoints
- Tests API endpoints
- Verifies data seeding
- Provides detailed pass/fail report

**Usage**:
```bash
./test_marketmindai.sh
```

## 🐘 PostgreSQL Docker Configuration

The scripts use your specified Docker configuration:

```bash
docker run --name marketmindai-postgres \
  -e POSTGRES_DB=marketmindai \
  -e POSTGRES_USER=marketmindai_user \
  -e POSTGRES_PASSWORD=marketmindai_password \
  -p 5432:5432 \
  -d postgres:15
```

## 🎯 Service URLs

After launching, the following services will be available:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Health**: http://localhost:8001/api/health
- **API Docs**: http://localhost:8001/docs
- **Debug Info**: http://localhost:8001/api/debug/connectivity

## 👥 Test Credentials

The scripts automatically create test users:
- **User**: user@marketmindai.com / password123
- **Admin**: admin@marketmindai.com / admin123
- **SuperAdmin**: superadmin@marketmindai.com / superadmin123

## 🔧 SuperAdmin Widget Features

The SuperAdmin account has special debugging capabilities:
- ✅ Access to debug panel in any environment (not just development)
- ✅ Ability to toggle connection status widget on/off
- ✅ Advanced analytics and system monitoring
- ✅ Full user and system management capabilities

## 📊 Key Features

### Automated Setup
- One-command launch of the entire application stack
- Automatic dependency installation
- Database initialization and seeding
- Health verification

### Development Ready
- Hot-reload enabled for both frontend and backend
- Comprehensive logging
- Easy status monitoring
- Quick testing capabilities

### Production Considerations
- Proper environment variable management
- Graceful shutdown procedures
- Container persistence options
- Comprehensive error handling

## 🛠️ Quick Start Workflow

1. **Launch the application**:
   ```bash
   ./launch_marketmindai.sh
   ```

2. **Check everything is working**:
   ```bash
   ./status_marketmindai.sh
   ```

3. **Run comprehensive tests**:
   ```bash
   ./test_marketmindai.sh
   ```

4. **Access the application**:
   - Open http://localhost:3000 in your browser
   - Login with SuperAdmin: superadmin@marketmindai.com / superadmin123
   - Test the debug panel (bottom-left corner)
   - Test the connection widget toggle (bottom-right corner)

5. **When done**:
   ```bash
   ./stop_marketmindai.sh
   ```

## 📁 File Structure

```
/app/
├── launch_marketmindai.sh    # 🚀 Main launch script
├── stop_marketmindai.sh      # 🛑 Stop script
├── status_marketmindai.sh    # 📊 Status monitoring
├── test_marketmindai.sh      # 🧪 Test suite
├── README_SCRIPTS.md         # 📖 Detailed documentation
├── backend/                  # Backend application
└── frontend/                 # Frontend application
```

## 🎉 Success Indicators

When everything is working correctly, you should see:
- ✅ PostgreSQL container running
- ✅ Backend API responding at port 8001
- ✅ Frontend server running at port 3000
- ✅ All 15 tests passing
- ✅ SuperAdmin can access debug panel
- ✅ Connection widget is toggleable
- ✅ Database contains 3 seeded users

## 🔍 Troubleshooting

If you encounter issues:

1. **Check status**: `./status_marketmindai.sh`
2. **View logs**: `tail -f /tmp/backend.log` or `tail -f /tmp/frontend.log`
3. **Check container**: `docker logs marketmindai-postgres`
4. **Run tests**: `./test_marketmindai.sh`
5. **Restart**: `./stop_marketmindai.sh && ./launch_marketmindai.sh`

## ✅ Resolution Summary

The original issue has been completely resolved:

1. **✅ SuperAdmin Widget Access**: SuperAdmins can now access the debug panel in any environment
2. **✅ Widget Toggle**: SuperAdmins can turn off/on the connection status widget
3. **✅ Database Connection**: Fixed PostgreSQL connection issues
4. **✅ Full Stack Integration**: All components properly connected and working
5. **✅ Automated Deployment**: One-command setup with Docker PostgreSQL

The MarketMindAI application is now fully functional with proper SuperAdmin debugging capabilities!