# PostgreSQL Backup Script (Windows PowerShell)
# Requires pg_dump in PATH

$ErrorActionPreference = 'Stop'

$BACKUP_DIR = $env:BACKUP_DIR
if (-not $BACKUP_DIR) { $BACKUP_DIR = "C:\backups\unilink" }
$RETENTION_DAYS = $env:RETENTION_DAYS
if (-not $RETENTION_DAYS) { $RETENTION_DAYS = 30 }
$DB_HOST = $env:DB_HOST
if (-not $DB_HOST) { $DB_HOST = "localhost" }
$DB_PORT = $env:DB_PORT
if (-not $DB_PORT) { $DB_PORT = "5432" }
$DB_NAME = $env:DB_NAME
if (-not $DB_NAME) { $DB_NAME = "unilink" }
$DB_USER = $env:DB_USER
if (-not $DB_USER) { $DB_USER = "unilink_user" }
$DB_PASSWORD = $env:DB_PASSWORD

if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
  throw "pg_dump not found in PATH. Install PostgreSQL client tools or add to PATH."
}

New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sqlFile = Join-Path $BACKUP_DIR "backup_$timestamp.sql"
$zipFile = Join-Path $BACKUP_DIR "backup_$timestamp.zip"

$env:PGPASSWORD = $DB_PASSWORD

Write-Output "Starting backup to $sqlFile"
& pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --verbose --format=plain --clean --if-exists | Out-File -FilePath $sqlFile -Encoding UTF8

Write-Output "Compressing $sqlFile"
Compress-Archive -Path $sqlFile -DestinationPath $zipFile -Force
Remove-Item $sqlFile -Force

# Cleanup old backups
$cutoff = (Get-Date).AddDays(-[int]$RETENTION_DAYS)
Get-ChildItem -Path $BACKUP_DIR -Filter "backup_*.zip" | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force

Write-Output "Backup complete: $zipFile"
