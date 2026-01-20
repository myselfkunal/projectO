# Phase 4 Components - Complete Index

## Component 1: Error Tracking (Sentry)

### Backend Implementation
- **File:** `backend/app/core/sentry.py`
- **Lines:** 80
- **Purpose:** Initialize Sentry, filter sensitive data, capture errors

**Key Functions:**
- `init_sentry()` - Initialize Sentry with integrations
- `before_send_sentry()` - Filter sensitive data before sending

**Configuration:**
- `SENTRY_DSN` - Sentry project DSN
- `SENTRY_TRACES_SAMPLE_RATE` - Performance sample rate (0.1 = 10%)
- `ENVIRONMENT` - Environment name (production/staging)
- `APP_VERSION` - Application version

**Integrations:**
- FastAPI integration
- SQLAlchemy integration
- ASGI integration

### Frontend Implementation
- **File:** `frontend/src/utils/sentry.ts`
- **Lines:** 100
- **Purpose:** Frontend error tracking and monitoring

**Exported Functions:**
- `initSentry()` - Initialize Sentry
- `captureException()` - Capture errors
- `captureMessage()` - Log messages
- `setSentryUser()` - Set user context
- `clearSentryUser()` - Clear user
- `addBreadcrumb()` - Add debug breadcrumb

**Configuration (.env.production):**
```
VITE_SENTRY_DSN=https://...
VITE_ENVIRONMENT=production
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Features:**
- ✅ Real-time error monitoring
- ✅ Performance tracking (traces)
- ✅ Replay capture (session recording)
- ✅ Breadcrumbs for debugging
- ✅ User identification
- ✅ Sensitive data filtering

### Usage
```bash
# Backend - automatic initialization
# Errors caught automatically by middleware

# Frontend - manual usage
import { captureException, setSentryUser } from './utils/sentry'
captureException(error, { context: 'data' })
setSentryUser(userId, email, username)
```

---

## Component 2: SSL/TLS Certificates

### Setup Script
- **File:** `scripts/setup-ssl.sh`
- **Lines:** 100
- **Purpose:** Automated certificate setup and renewal

**Usage:**
```bash
# Staging (for testing)
sudo bash scripts/setup-ssl.sh unilink.example.com admin@email.com --staging

# Production (real certificate)
sudo bash scripts/setup-ssl.sh unilink.example.com admin@email.com
```

**What It Does:**
1. Checks prerequisites (Certbot)
2. Installs dependencies if needed
3. Requests certificate from Let's Encrypt
4. Creates renewal hook for nginx reload
5. Sets up cron job for auto-renewal

**Certificate Paths:**
- `fullchain.pem` - Certificate chain
- `privkey.pem` - Private key
- `cert.pem` - Certificate only

### Nginx Configuration
- **File:** `docker/nginx-ssl.conf`
- **Lines:** 150
- **Purpose:** Secure HTTPS configuration

**Features:**
- HTTP → HTTPS redirect
- TLSv1.2 + TLSv1.3 only
- Modern cipher suites
- Session caching
- Security headers:
  - HSTS (Strict-Transport-Security)
  - X-Frame-Options
  - X-Content-Type-Options
  - X-XSS-Protection
  - Referrer-Policy
  - Permissions-Policy

**Server Blocks:**
- `:80` - HTTP redirect
- `:443` - HTTPS with API & frontend proxy

**Proxy Locations:**
- `/` → Frontend (localhost:3000)
- `/api/` → Backend API (localhost:8000)
- `/ws/` → WebSocket (localhost:8000)

### Verification
```bash
# Check certificate
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run

# Test HTTPS
curl -I https://yourdomain.com

# SSL labs score
https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

---

## Component 3: Database Backups

### Backup Script
- **File:** `scripts/backup-database.sh`
- **Lines:** 120
- **Purpose:** Create daily database backups

**Usage:**
```bash
bash scripts/backup-database.sh
```

**Configuration:**
```bash
BACKUP_DIR="/backups/unilink"
RETENTION_DAYS=30
DB_HOST="localhost"
DB_PORT=5432
DB_NAME="unilink"
DB_USER="unilink_user"
DB_PASSWORD="your_password"
```

**Features:**
- ✅ PostgreSQL dump with pg_dump
- ✅ gzip compression (level 9)
- ✅ Automatic integrity verification
- ✅ Automatic old backup cleanup
- ✅ 30-day retention (configurable)
- ✅ Detailed logging
- ✅ Backup summary

**Output:**
- Backup file: `/backups/unilink/backup_YYYYMMDD_HHMMSS.sql.gz`
- Log file: `/backups/unilink/backup.log`

### Restore Script
- **File:** `scripts/restore-database.sh`
- **Lines:** 110
- **Purpose:** Restore from backup

**Usage:**
```bash
bash scripts/restore-database.sh /backups/unilink/backup_20260121_020000.sql.gz
```

**What It Does:**
1. Verifies backup file exists
2. Confirms restore operation
3. Drops existing database
4. Creates fresh database
5. Restores from backup
6. Verifies table count
7. Logs all operations

**Safety Features:**
- Interactive confirmation
- Transaction-based restore
- Table count verification
- Detailed error reporting

### Automation
```bash
# Create backup directory
sudo mkdir -p /backups/unilink
sudo chown postgres:postgres /backups/unilink

# Schedule daily backups at 2 AM
sudo crontab -e
# Add: 0 2 * * * bash /path/to/scripts/backup-database.sh

# Verify cron job
sudo crontab -l
```

### Monitoring
```bash
# View backups
ls -lh /backups/unilink/

# Check logs
tail -f /backups/unilink/backup.log

# Test restore
bash scripts/restore-database.sh /backups/unilink/backup_*.sql.gz
```

---

## Component 4: CI/CD Pipeline

### Test Workflow
- **File:** `.github/workflows/tests.yml`
- **Lines:** 140
- **Purpose:** Automated testing on every commit

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Jobs:**

1. **test-backend**
   - PostgreSQL service container
   - Install dependencies
   - Run pytest with coverage
   - Upload coverage to Codecov
   - Store test results artifact

2. **test-frontend**
   - Install Node.js dependencies
   - Lint code with ESLint
   - Type check with TypeScript
   - Build production bundle
   - Store build artifact

3. **code-quality**
   - Run Pylint linting
   - Black formatter check

4. **security-scan**
   - Bandit security analysis
   - Safety vulnerability check

**Artifacts:**
- Backend test results (JUnit XML)
- Backend coverage (Codecov)
- Frontend build (dist/)
- Security reports

### Deploy Workflow
- **File:** `.github/workflows/deploy.yml`
- **Lines:** 130
- **Purpose:** Automated production deployment

**Triggers:**
- Tag creation (v*)
- Push to main (optional)

**Jobs:**

1. **build-and-deploy**
   - Build backend Docker image
   - Build frontend Docker image
   - Push to Docker Hub
   - SSH to production server
   - Pull latest code
   - Run docker-compose up
   - Run migrations
   - Health check (30 retries)
   - GitHub notification

**Secrets Required:**
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub token
- `DEPLOY_HOST` - Production server IP/hostname
- `DEPLOY_USER` - SSH user
- `DEPLOY_KEY` - SSH private key

**Health Check:**
- Endpoint: `https://yourdomain.com/health`
- Retries: 30 times
- Interval: 10 seconds
- Total timeout: 5 minutes

### Setup

```bash
# 1. Create GitHub repository
git remote add origin https://github.com/yourusername/unilink.git
git push -u origin main

# 2. Add GitHub secrets
# Settings → Secrets and variables → Actions
# DOCKER_USERNAME, DOCKER_PASSWORD, DEPLOY_HOST, DEPLOY_USER, DEPLOY_KEY

# 3. Verify workflows
# Push code → GitHub Actions → View runs

# 4. Deploy
git tag v1.0.0
git push origin v1.0.0
```

### Workflow Files Location
```
.github/workflows/
├── tests.yml      ← Runs on every push/PR
└── deploy.yml     ← Runs on tag/main push
```

---

## Integration Points

### Sentry ↔ Backend
- Automatically initializes in `app/main.py`
- Catches all unhandled exceptions
- Filters sensitive data
- Sends to Sentry.io

### Sentry ↔ Frontend
- Initialize in `src/main.tsx`
- Catch React errors
- Track user interactions
- Send to Sentry.io

### SSL ↔ Nginx
- Certificates at `/etc/letsencrypt/live/`
- Auto-renewal via cron
- Nginx reloads on renewal
- HTTPS enforced

### Backups ↔ PostgreSQL
- Scheduled via cron
- Dumps to `/backups/unilink/`
- Auto-cleanup after 30 days
- Verified on creation

### CI/CD ↔ GitHub
- Tests run on push
- Deploy on tag
- Secrets securely stored
- Notifications on completion

---

## Command Reference

### Sentry
```bash
pip install sentry-sdk          # Backend
npm install @sentry/react       # Frontend
```

### SSL/TLS
```bash
sudo bash scripts/setup-ssl.sh yourdomain.com email@example.com
sudo certbot certificates
sudo certbot renew --dry-run
```

### Backups
```bash
bash scripts/backup-database.sh
bash scripts/restore-database.sh /path/to/backup.sql.gz
ls -lh /backups/unilink/
```

### CI/CD
```bash
git remote add origin https://github.com/username/unilink.git
git push -u origin main
git tag v1.0.0
git push origin v1.0.0
```

---

## Files Summary

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| sentry.py | Python | 80 | Backend error tracking |
| sentry.ts | TypeScript | 100 | Frontend error tracking |
| setup-ssl.sh | Bash | 100 | Certificate automation |
| nginx-ssl.conf | Nginx | 150 | HTTPS configuration |
| backup-database.sh | Bash | 120 | Database backups |
| restore-database.sh | Bash | 110 | Backup restoration |
| tests.yml | YAML | 140 | Test automation |
| deploy.yml | YAML | 130 | Deploy automation |

**Total: 930 lines of production code**

---

## Status: ✅ COMPLETE

All Phase 4 components implemented, tested, documented, and ready for production deployment.
