# Deployment Checklist - UniLink Phase 4

## Pre-Deployment ✅

- [x] Git history cleaned (no .env files)
- [x] Phase 4 infrastructure files created (8 files)
- [x] All tests passing (26 E2E tests)
- [x] Frontend build successful
- [x] Documentation complete

**Git Status:**
```
Last commit: eb8a8ba - Phase 4: Complete production infrastructure setup
Branch: main
Ahead of origin/main: 1 commit
```

---

## Step 1: GitHub Repository Setup

### 1.1 Create GitHub Repository
```bash
# Go to github.com and create new repo "unilink"
# Clone pattern: https://github.com/yourusername/unilink.git
```

### 1.2 Add Remote and Push
```bash
git remote add origin https://github.com/yourusername/unilink.git
git push -u origin main

# Verify
git remote -v
# origin  https://github.com/yourusername/unilink.git (fetch)
# origin  https://github.com/yourusername/unilink.git (push)
```

**Status:** ⏳ Awaiting GitHub setup

---

## Step 2: GitHub Actions Secrets

Go to: **GitHub → Settings → Secrets and variables → Actions**

### Required Secrets

#### For CI/CD Testing (tests.yml)
- `CODECOV_TOKEN` - [Get from codecov.io](https://codecov.io)
  
#### For Production Deployment (deploy.yml)
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub access token ([Create](https://hub.docker.com/settings/security))
- `DEPLOY_HOST` - Production server IP (e.g., `192.168.1.100`)
- `DEPLOY_USER` - SSH user (e.g., `ubuntu`)
- `DEPLOY_KEY` - SSH private key (full content of ~/.ssh/id_rsa)

### Add Secrets Script
```bash
# Instructions for adding each secret:
# 1. Go to GitHub repo → Settings → Secrets and variables → Actions
# 2. Click "New repository secret"
# 3. Name: DOCKER_USERNAME
# 4. Value: your_docker_hub_username
# 5. Click "Add secret"
# Repeat for each secret above
```

**Status:** ⏳ Awaiting secret configuration

---

## Step 3: Sentry Setup

### 3.1 Create Sentry Project
1. Go to [sentry.io](https://sentry.io)
2. Create free account
3. Create new project → Select "Django"
4. Copy the DSN (format: `https://key@sentry.io/project_id`)

### 3.2 Set Sentry DSN
```bash
# Create .env.production in project root
echo "SENTRY_DSN=https://your_key@sentry.io/your_project_id" >> .env.production
echo "SENTRY_ENVIRONMENT=production" >> .env.production

# Or manually edit:
# SENTRY_DSN=https://your_key@sentry.io/your_project_id
# SENTRY_ENVIRONMENT=production
```

### 3.3 Verify Integration
```bash
# Backend - automatic on startup
# Frontend - automatic on startup
# Check Sentry dashboard for events
```

**Status:** ⏳ Awaiting Sentry setup

---

## Step 4: SSL/TLS Certificate Setup

### 4.1 Prerequisites
```bash
# On production server:
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Verify
certbot --version
```

### 4.2 Run SSL Setup Script
```bash
# Staging (TEST FIRST)
sudo bash scripts/setup-ssl.sh yourdomain.com admin@email.com --staging

# If successful, upgrade to production
sudo bash scripts/setup-ssl.sh yourdomain.com admin@email.com

# Verify certificate
sudo certbot certificates
```

### 4.3 Verify HTTPS
```bash
curl -I https://yourdomain.com
# Should return 200 OK with SSL certificate

# Test SSL strength
# https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

**Status:** ⏳ Awaiting certificate setup

---

## Step 5: Database Backup Setup

### 5.1 Create Backup Directory
```bash
sudo mkdir -p /backups/unilink
sudo chown postgres:postgres /backups/unilink
chmod 700 /backups/unilink
```

### 5.2 Test Backup Script
```bash
bash scripts/backup-database.sh

# Verify backup created
ls -lh /backups/unilink/
```

### 5.3 Schedule Daily Backups
```bash
# Create cron job as root
sudo crontab -e

# Add this line (backup daily at 2 AM):
0 2 * * * cd /path/to/projectO && bash scripts/backup-database.sh

# Verify
sudo crontab -l
```

### 5.4 Test Restore
```bash
# Create test backup first
bash scripts/backup-database.sh

# Test restore (CAUTION: uses current database)
bash scripts/restore-database.sh /backups/unilink/backup_*.sql.gz
```

**Status:** ⏳ Awaiting backup setup

---

## Step 6: Docker Build & Push

### 6.1 Build Images Locally
```bash
docker-compose build

# Verify builds
docker images | grep unilink
```

### 6.2 Push to Docker Hub
```bash
# Tag images
docker tag projectO-backend:latest yourusername/unilink-backend:latest
docker tag projectO-frontend:latest yourusername/unilink-frontend:latest

# Login to Docker Hub
docker login

# Push images
docker push yourusername/unilink-backend:latest
docker push yourusername/unilink-frontend:latest

# Verify on Docker Hub
# https://hub.docker.com/r/yourusername/unilink-backend
```

**Status:** ⏳ Awaiting Docker Hub push

---

## Step 7: Production Deployment

### 7.1 Create Deployment Tag
```bash
# Create version tag
git tag v1.0.0 -m "Release 1.0.0: Phase 4 complete with production infrastructure"

# Push tag (triggers deployment)
git push origin v1.0.0

# Verify on GitHub
# https://github.com/yourusername/unilink/tags
```

### 7.2 Monitor Deployment
```bash
# Watch GitHub Actions
# https://github.com/yourusername/unilink/actions

# Check logs:
# 1. Click on the deployment workflow
# 2. Expand "build-and-deploy" job
# 3. Review SSH output and health checks
```

### 7.3 Verify Production
```bash
# Test endpoints
curl -I https://yourdomain.com                    # Frontend
curl https://yourdomain.com/api/health           # Health check
curl https://yourdomain.com/api/users/register   # API endpoint

# Check Sentry dashboard
# https://sentry.io/organizations/yourorg/issues/

# View logs
ssh user@yourdomain.com
docker logs container_name
```

**Status:** ⏳ Awaiting deployment

---

## Step 8: Post-Deployment Verification

### 8.1 Check Application
- [ ] Frontend loads at https://yourdomain.com
- [ ] Login page responsive
- [ ] API endpoints responding
- [ ] WebSocket connection works

### 8.2 Check Infrastructure
- [ ] SSL certificate valid
- [ ] Sentry receiving errors
- [ ] Database backups running daily
- [ ] Health checks passing

### 8.3 Check Monitoring
- [ ] GitHub Actions passing
- [ ] CI/CD workflow successful
- [ ] No error alerts in Sentry
- [ ] Backup logs clean

### 8.4 Security Verification
```bash
# Test HTTPS only
curl -I http://yourdomain.com
# Should redirect to HTTPS

# Check SSL grade
# https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
# Target: A+ grade

# Test security headers
curl -I https://yourdomain.com | grep -i "strict-transport"
# Should show: strict-transport-security: max-age=31536000
```

**Status:** ⏳ Awaiting verification

---

## Summary

| Step | Task | Status | Completed |
|------|------|--------|-----------|
| 1 | GitHub Repository | ⏳ | - |
| 2 | GitHub Secrets | ⏳ | - |
| 3 | Sentry Setup | ⏳ | - |
| 4 | SSL/TLS Certificates | ⏳ | - |
| 5 | Database Backups | ⏳ | - |
| 6 | Docker Build & Push | ⏳ | - |
| 7 | Production Deployment | ⏳ | - |
| 8 | Post-Deployment Verify | ⏳ | - |

---

## Quick Reference

### Important Files
- **CI/CD Workflows:** `.github/workflows/` (tests.yml, deploy.yml)
- **SSL Setup:** `scripts/setup-ssl.sh`
- **Backups:** `scripts/backup-database.sh`, `scripts/restore-database.sh`
- **Config:** `backend/app/core/config.py`, `.env.production`
- **Nginx:** `docker/nginx-ssl.conf`

### Important URLs
- **GitHub:** https://github.com/yourusername/unilink
- **Docker Hub:** https://hub.docker.com/r/yourusername
- **Sentry:** https://sentry.io/organizations/yourorg
- **Production:** https://yourdomain.com

### Important Secrets
- Docker Hub credentials
- SSH key to production server
- Sentry DSN
- Domain name

---

**Ready to deploy!** 🚀

Start with Step 1: GitHub Repository Setup
