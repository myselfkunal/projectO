# PostgreSQL Restore Script (Windows PowerShell)
# Usage: .\restore-database.ps1 -BackupZip "C:\backups\unilink\backup_YYYYMMDD_HHMMSS.zip"
# Requires pg_restore/psql in PATH

param(
  [Parameter(Mandatory=$true)]
  [string]$BackupZip
)

$ErrorActionPreference = 'Stop'

$DB_HOST = $env:DB_HOST
if (-not $DB_HOST) { $DB_HOST = "localhost" }
$DB_PORT = $env:DB_PORT
if (-not $DB_PORT) { $DB_PORT = "5432" }
$DB_NAME = $env:DB_NAME
if (-not $DB_NAME) { $DB_NAME = "unilink" }
$DB_USER = $env:DB_USER
if (-not $DB_USER) { $DB_USER = "unilink_user" }
$DB_PASSWORD = $env:DB_PASSWORD

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
  throw "psql not found in PATH. Install PostgreSQL client tools or add to PATH."
}

$tempDir = Join-Path $env:TEMP "unilink_restore"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

Write-Output "Extracting $BackupZip"
Expand-Archive -Path $BackupZip -DestinationPath $tempDir -Force

$sqlFile = Get-ChildItem -Path $tempDir -Filter "backup_*.sql" | Select-Object -First 1
if (-not $sqlFile) { throw "No .sql file found in archive." }

$env:PGPASSWORD = $DB_PASSWORD
Write-Output "Restoring $($sqlFile.FullName)"
& psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $sqlFile.FullName

Remove-Item -Recurse -Force $tempDir
Write-Output "Restore complete"
