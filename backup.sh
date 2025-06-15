#!/bin/bash

# Exit on error
set -e

# Configuration
BACKUP_DIR="/path/to/backup/directory"
DB_NAME="upendo_bakery"
DB_USER="upendo_user"
MEDIA_DIR="media"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="upendo_bakery_backup_$DATE"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting backup process..."

# Backup PostgreSQL database
echo "Backing up database..."
pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz"

# Backup media files
echo "Backing up media files..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_media.tar.gz" $MEDIA_DIR

# Keep only last 7 days of backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "upendo_bakery_backup_*" -mtime +7 -delete

echo "Backup completed successfully!"
echo "Backup files:"
echo "- Database: ${BACKUP_NAME}_db.sql.gz"
echo "- Media: ${BACKUP_NAME}_media.tar.gz" 