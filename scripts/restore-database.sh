#!/bin/bash
# PostgreSQL Restore Script for UniLink
# Restores database from backup files

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/unilink}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-unilink}"
DB_USER="${DB_USER:-unilink_user}"
LOG_FILE="$BACKUP_DIR/restore.log"

# Function for logging
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Show usage
if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file>"
  echo ""
  echo "Available backups:"
  ls -lh "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null || echo "No backups found"
  exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
  log "ERROR: Backup file not found: $BACKUP_FILE"
  exit 1
fi

log "================================================"
log "Starting PostgreSQL restore"
log "================================================"
log "Source: $BACKUP_FILE"
log "Target Database: $DB_NAME on $DB_HOST:$DB_PORT"
log ""

# Confirm restore
read -p "WARNING: This will overwrite database '$DB_NAME'. Continue? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
  log "Restore cancelled"
  exit 1
fi

# Verify PostgreSQL connection
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
  log "ERROR: PostgreSQL connection failed"
  exit 1
fi

# Drop existing database and recreate
log "Dropping existing database..."
PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d postgres \
  -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>&1 | tee -a "$LOG_FILE"

log "Creating database..."
PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d postgres \
  -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>&1 | tee -a "$LOG_FILE"

# Restore from backup
log "Restoring from backup..."
if PGPASSWORD="$DB_PASSWORD" gunzip -c "$BACKUP_FILE" | \
   PGPASSWORD="$DB_PASSWORD" psql \
   -h "$DB_HOST" \
   -p "$DB_PORT" \
   -U "$DB_USER" \
   -d "$DB_NAME" \
   --single-transaction 2>&1 | tee -a "$LOG_FILE"; then
  
  log "================================================"
  log "Restore completed successfully!"
  log "================================================"
  
  # Verify restore
  TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
  
  log "Tables in database: $TABLE_COUNT"
  
else
  log "ERROR: Restore failed!"
  exit 1
fi

exit 0
