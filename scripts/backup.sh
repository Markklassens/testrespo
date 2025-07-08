#!/bin/bash

# Database Backup Script for MarketMindAI
# Usage: ./scripts/backup.sh

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="marketmindai_postgres"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "🗄️ Creating database backup..."

# Check if container is running
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ PostgreSQL container is not running"
    exit 1
fi

# Create backup
docker exec $CONTAINER_NAME pg_dump -U marketmindai -d marketmindai > "$BACKUP_DIR/marketmindai_backup_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/marketmindai_backup_$DATE.sql"

echo "✅ Backup created: $BACKUP_DIR/marketmindai_backup_$DATE.sql.gz"

# Clean up old backups (keep last 7 days)
find $BACKUP_DIR -name "marketmindai_backup_*.sql.gz" -type f -mtime +7 -delete

echo "🧹 Cleaned up old backups (keeping last 7 days)"