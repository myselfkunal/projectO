# Monitoring & Backups

## Health checks
- Backend: http://yourdomain.com/health (or http://localhost:8000/health)
- Use Docker health status: `docker compose -f docker/docker-compose.prod.yml ps`

## Logs
- Backend logs: `docker logs -f docker-backend-1`
- Frontend logs: `docker logs -f docker-frontend-1`
- Nginx logs: `docker logs -f <nginx-container>`

## Backups (PostgreSQL)
Use the provided script: [scripts/backup-database.sh](scripts/backup-database.sh)

Windows PowerShell: [scripts/backup-database.ps1](scripts/backup-database.ps1)

### Example (Linux cron)
```
0 2 * * * /path/to/scripts/backup-database.sh
```

### Example (Windows Task Scheduler)
- Program/script: `powershell.exe`
- Add arguments: `-ExecutionPolicy Bypass -File C:\path\to\scripts\backup-database.ps1`

### Required env vars
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `BACKUP_DIR` (optional)
- `RETENTION_DAYS` (optional)

## Restore
Use [scripts/restore-database.sh](scripts/restore-database.sh)

Windows PowerShell: [scripts/restore-database.ps1](scripts/restore-database.ps1)
