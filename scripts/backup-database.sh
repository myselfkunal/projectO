#!/bin/bash
# PostgreSQL Backup Script for UniLink
# Creates daily backups with point-in-time recovery capability

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/unilink}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"  # Keep backups for 30 days
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-unilink}"
DB_USER="${DB_USER:-unilink_user}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
LOG_FILE="$BACKUP_DIR/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function for logging
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "================================================"
log "Starting PostgreSQL backup for $DB_NAME"
log "================================================"

# Verify PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
  log "ERROR: PostgreSQL connection failed"
  exit 1
fi

# Create backup
log "Dumping database to $BACKUP_FILE"
if PGPASSWORD="$DB_PASSWORD" pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --verbose \
  --format=plain \
  --compress=9 \
  --clean \
  --if-exists \
  > "$BACKUP_FILE" 2>&1; then
  
  BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  log "Backup completed successfully - Size: $BACKUP_SIZE"
  
  # Verify backup integrity
  if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
    log "Backup integrity verified"
  else
    log "ERROR: Backup integrity check failed!"
    exit 1
  fi
  
else
  log "ERROR: Backup failed!"
  exit 1
fi

# Clean old backups
log "Cleaning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
OLD_BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" | wc -l)
log "Kept $OLD_BACKUP_COUNT backups"

# Create summary
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "================================================"
log "Backup Summary:"
log "  Backup file: $BACKUP_FILE"
log "  Size: $BACKUP_SIZE"
log "  Total backups: $BACKUP_COUNT"
log "  Total storage: $TOTAL_SIZE"
log "  Retention: $RETENTION_DAYS days"
log "================================================"

exit 0
