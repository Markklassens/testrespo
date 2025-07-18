# MarketMindAI Application Launch Scripts

This directory contains shell scripts to easily launch and manage the MarketMindAI application with PostgreSQL running in Docker.

## 🚀 Quick Start

### Prerequisites
- Docker installed and running
- Node.js installed
- Python 3 installed

### Launch the Application

```bash
./launch_marketmindai.sh
```

This script will:
1. Start PostgreSQL in a Docker container
2. Update backend configuration
3. Initialize the database
4. Start backend and frontend servers
5. Verify all connections

### Check Application Status

```bash
./status_marketmindai.sh
```

This script provides comprehensive status information about all components.

### Stop the Application

```bash
./stop_marketmindai.sh
```

This script will gracefully stop all components and optionally remove the PostgreSQL container.

## 📋 Application Details

### Services
- **Frontend**: React application running on http://localhost:3000
- **Backend**: FastAPI application running on http://localhost:8001
- **Database**: PostgreSQL 15 running in Docker container

### Database Configuration
The PostgreSQL container is configured with:
- **Container name**: `marketmindai-postgres`
- **Database**: `marketmindai`
- **User**: `marketmindai_user`
- **Password**: `marketmindai_password`
- **Port**: `5432`

### Test Credentials
- **User**: user@marketmindai.com / password123
- **Admin**: admin@marketmindai.com / admin123
- **SuperAdmin**: superadmin@marketmindai.com / superadmin123

## 🛠️ Useful Commands

### View Logs
```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log
```

### Docker Commands
```bash
# View PostgreSQL container
docker ps --filter "name=marketmindai-postgres"

# Connect to PostgreSQL
docker exec -it marketmindai-postgres psql -U marketmindai_user -d marketmindai

# View PostgreSQL logs
docker logs marketmindai-postgres
```

### API Endpoints
- **Health Check**: http://localhost:8001/api/health
- **Debug Info**: http://localhost:8001/api/debug/connectivity
- **API Documentation**: http://localhost:8001/docs

## 🔧 SuperAdmin Features

The SuperAdmin account has special debugging capabilities:
- Access to debug panel in any environment
- Ability to toggle connection status widget
- Advanced analytics and user management

## 📊 Monitoring

The status script provides real-time information about:
- Container status
- Port availability
- API health
- Database connectivity
- Process information
- Log files

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill processes using the ports
   sudo lsof -ti:3000,8001,5432 | xargs kill -9
   ```

2. **Docker Permission Issues**
   ```bash
   sudo usermod -aG docker $USER
   # Then logout and login again
   ```

3. **Database Connection Issues**
   ```bash
   # Check container logs
   docker logs marketmindai-postgres
   
   # Restart container
   docker restart marketmindai-postgres
   ```

4. **Frontend/Backend Not Starting**
   ```bash
   # Check logs
   tail -f /tmp/backend.log
   tail -f /tmp/frontend.log
   
   # Restart services
   ./stop_marketmindai.sh
   ./launch_marketmindai.sh
   ```

## 🔄 Development Workflow

1. **Daily Start**:
   ```bash
   ./launch_marketmindai.sh
   ```

2. **Check Status**:
   ```bash
   ./status_marketmindai.sh
   ```

3. **Development Work**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - Database: localhost:5432

4. **End of Day**:
   ```bash
   ./stop_marketmindai.sh
   ```

## 📁 File Structure

```
/app/
├── launch_marketmindai.sh    # Main launch script
├── stop_marketmindai.sh      # Stop script
├── status_marketmindai.sh    # Status checking script
├── README_SCRIPTS.md         # This file
├── backend/                  # Backend application
│   ├── server.py
│   ├── init_db.py
│   ├── seed_data.py
│   └── .env
└── frontend/                 # Frontend application
    ├── package.json
    └── src/
```

## 🎯 Features

- **Automated Setup**: One-command application launch
- **Docker Integration**: PostgreSQL running in isolated container
- **Health Monitoring**: Comprehensive status checking
- **Graceful Shutdown**: Proper cleanup of all processes
- **Development Ready**: Hot-reload enabled for both frontend and backend
- **SuperAdmin Tools**: Debug panel and widget controls

## 🔒 Security Notes

- Change default passwords in production
- Use environment variables for sensitive data
- Enable SSL/TLS for production deployments
- Regular security updates for all components

## 📝 Notes

- The scripts are designed to be idempotent (safe to run multiple times)
- Log files are automatically cleaned up on stop
- Database data persists between container restarts
- Frontend and backend support hot-reload for development