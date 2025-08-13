#!/bin/bash

echo "💾 Starting backup process..."

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Backup directory: $BACKUP_DIR"

echo "🗄️  Backing up database..."
docker-compose exec -T postgres pg_dump -U postgres metaads > "$BACKUP_DIR/database.sql"

if [ $? -eq 0 ]; then
    echo "✅ Database backup completed"
else
    echo "❌ Database backup failed"
    exit 1
fi

echo "📦 Backing up Redis data..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 5
docker cp $(docker-compose ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis.rdb"

if [ $? -eq 0 ]; then
    echo "✅ Redis backup completed"
else
    echo "❌ Redis backup failed"
fi

echo "⚙️  Backing up configuration files..."
cp .env "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  .env file not found"
cp docker-compose.yml "$BACKUP_DIR/"
cp -r monitoring/ "$BACKUP_DIR/"

echo "📋 Backing up logs..."
mkdir -p "$BACKUP_DIR/logs"
cp -r logs/* "$BACKUP_DIR/logs/" 2>/dev/null || echo "⚠️  No logs found"

echo "🤖 Backing up ML models..."
mkdir -p "$BACKUP_DIR/models"
cp -r models/* "$BACKUP_DIR/models/" 2>/dev/null || echo "⚠️  No ML models found"

echo "🗜️  Creating compressed archive..."
tar -czf "$BACKUP_DIR.tar.gz" -C backups "$(basename $BACKUP_DIR)"

if [ $? -eq 0 ]; then
    echo "✅ Compressed archive created: $BACKUP_DIR.tar.gz"
    rm -rf "$BACKUP_DIR"
else
    echo "❌ Failed to create compressed archive"
    exit 1
fi

echo "🧹 Cleaning up old backups..."
find backups/ -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup process completed successfully!"
echo "📦 Backup file: $BACKUP_DIR.tar.gz"
