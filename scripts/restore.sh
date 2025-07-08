#!/bin/bash

# Database Restore Script for MarketMindAI
# Usage: ./scripts/restore.sh <backup_file>

set -e

if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/marketmindai_backup_20241201_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1
CONTAINER_NAME="marketmindai_postgres"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if container is running
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ PostgreSQL container is not running"
    exit 1
fi

echo "🔄 Restoring database from: $BACKUP_FILE"

# Extract if gzipped
if [[ $BACKUP_FILE == *.gz ]]; then
    TEMP_FILE="/tmp/$(basename $BACKUP_FILE .gz)"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Drop existing database and recreate
docker exec $CONTAINER_NAME dropdb -U marketmindai marketmindai || true
docker exec $CONTAINER_NAME createdb -U marketmindai marketmindai

# Restore backup
docker exec -i $CONTAINER_NAME psql -U marketmindai -d marketmindai < "$RESTORE_FILE"

# Clean up temp file
if [[ $BACKUP_FILE == *.gz ]]; then
    rm "$TEMP_FILE"
fi

echo "✅ Database restored successfully"