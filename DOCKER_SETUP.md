# MarketMindAI Docker Setup & Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git

### Development Setup

1. **Clone and setup the repository:**
```bash
git clone <your-repository-url>
cd marketmindai
```

2. **Run development environment:**
```bash
./deploy.sh dev
```

3. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- Admin Panel: http://localhost:3000/admin

## 🏭 Production Deployment

### 1. Prepare Environment

1. **Copy and configure production environment:**
```bash
cp .env.production .env
# Edit .env with your production values
```

2. **Update domain configurations:**
- Edit `nginx/sites-enabled/marketmindai`
- Replace `your-domain.com` with your actual domain
- Update CORS origins in `.env`

### 2. SSL Certificate Setup

```bash
# Create SSL directory
mkdir -p ssl

# Option 1: Let's Encrypt (recommended)
# Install certbot and obtain certificates
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/

# Option 2: Self-signed (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem -out ssl/fullchain.pem
```

### 3. Deploy to Production

```bash
./deploy.sh prod
```

## 📋 Configuration Files

### Environment Variables (.env.production)

```bash
# Database
POSTGRES_DB=marketmindai
POSTGRES_USER=marketmindai
POSTGRES_PASSWORD=your-secure-database-password

# JWT Security
SECRET_KEY=your-very-long-random-secret-key-for-jwt-tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Service (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Application URLs
APP_URL=https://your-domain.com
REACT_APP_BACKEND_URL=https://your-domain.com/api

# Security
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## 🗄️ Database Management

### Backup Database
```bash
./scripts/backup.sh
```

### Restore Database
```bash
./scripts/restore.sh ./backups/marketmindai_backup_20241201_120000.sql.gz
```

### Manual Database Access
```bash
# Connect to database
docker exec -it marketmindai_postgres psql -U marketmindai -d marketmindai

# View tables
\dt

# Check user data
SELECT id, email, username, user_type, is_verified FROM users;
```

## 📊 Monitoring & Logs

### View Logs
```bash
# All services
./scripts/logs.sh all

# Specific service
./scripts/logs.sh backend
./scripts/logs.sh frontend
./scripts/logs.sh database

# Follow logs in real-time
./scripts/logs.sh backend 100
```

### Health Checks
```bash
# Check service status
docker-compose ps

# Backend health
curl http://localhost:8001/api/health

# Frontend health (production)
curl https://your-domain.com/health
```

## 🔧 Maintenance Commands

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
./deploy.sh prod
```

### Scale Services (if needed)
```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale with load balancer (requires nginx config update)
```

### Clean Up
```bash
# Remove unused containers and images
docker system prune -a

# Remove old backups (older than 30 days)
find ./backups -name "*.sql.gz" -type f -mtime +30 -delete
```

## 🔒 Security Considerations

### Production Security Checklist
- [ ] Strong passwords for database and Redis
- [ ] Valid SSL certificates
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers implemented
- [ ] Regular backups scheduled
- [ ] Log monitoring setup
- [ ] Firewall configured
- [ ] Keep Docker images updated

### Default Admin Account
**⚠️ Important: Change default admin credentials after first login**

- Email: `admin@marketmindai.com`
- Password: `admin123`

### Create New Admin User
```bash
# Access backend container
docker exec -it marketmindai_backend python

# In Python shell:
from backend.database import get_db
from backend.models import User
from backend.auth import get_password_hash
import uuid

db = next(get_db())
admin_user = User(
    id=str(uuid.uuid4()),
    email="new-admin@yourdomain.com",
    username="newadmin",
    full_name="New Admin",
    hashed_password=get_password_hash("your-secure-password"),
    user_type="superadmin",
    is_active=True,
    is_verified=True
)
db.add(admin_user)
db.commit()
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Frontend not loading
```bash
# Check frontend logs
./scripts/logs.sh frontend

# Rebuild frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

#### 2. Database connection errors
```bash
# Check database logs
./scripts/logs.sh database

# Reset database (⚠️ DATA LOSS)
docker-compose down
docker volume rm marketmindai_postgres_data
./deploy.sh prod
```

#### 3. SSL certificate issues
```bash
# Verify certificate files
ls -la ssl/
openssl x509 -in ssl/fullchain.pem -text -noout

# Restart nginx
docker-compose restart nginx
```

#### 4. Performance issues
```bash
# Monitor resource usage
docker stats

# Check disk space
df -h
docker system df
```

## 📈 Performance Optimization

### Production Optimizations Included
- ✅ Nginx reverse proxy with caching
- ✅ Gzip compression
- ✅ Static asset caching
- ✅ Database connection pooling
- ✅ Redis caching
- ✅ Rate limiting
- ✅ Security headers
- ✅ Health checks

### Additional Optimizations
```bash
# Enable Redis caching in backend
# Add to backend/.env
REDIS_URL=redis://redis:6379

# Monitor Redis usage
docker exec -it marketmindai_redis redis-cli monitor
```

## 🆘 Support

### Getting Help
1. Check logs first: `./scripts/logs.sh all`
2. Verify service health: `docker-compose ps`
3. Check disk space: `df -h`
4. Review configuration files

### Backup Strategy
- Automated daily backups: Set up cron job
- Keep 7 days of daily backups
- Weekly full system backup
- Test restore procedures regularly

```bash
# Add to crontab for daily backups
0 2 * * * /path/to/marketmindai/scripts/backup.sh
```