# 🎯 PRODUCTION SETUP CHECKLIST & QUESTIONS

## Quick Answer: Do You Need PostgreSQL?

### **YES, You Need PostgreSQL** (But we have options)

**Why?** The entire backend requires a database to:
- Store user accounts and passwords
- Store call history
- Store verification tokens
- Store blocked users list
- Store user reports

---

## ⚡ TESTING FIRST (Recommended!)

### Option 1: Use Docker PostgreSQL (EASIEST - 1 line)
**No installation needed! Docker handles everything:**

```bash
cd c:\Users\KIIT\Desktop\projectO\docker
docker-compose up
```

This starts:
- ✅ PostgreSQL (automatic)
- ✅ Backend (automatic)
- ✅ Frontend (automatic)
- ✅ All services connected

**Requirements:** Docker Desktop installed

---

### Option 2: Install PostgreSQL Locally (MANUAL)
**If you want to test with local PostgreSQL:**

**Windows:**
1. Download: https://www.postgresql.org/download/windows/
2. Install PostgreSQL 15+
3. Choose password (remember it!)
4. Port: 5432 (default)

**After Installation:**
```bash
# Add to backend/.env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/unilink

# Then run:
cd c:\Users\KIIT\Desktop\projectO\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

---

## 📋 PRODUCTION SETUP - WHAT TO EDIT & WHERE

### **LEVEL 1: Must-Edit (Before Going Live)**

#### 1️⃣ **Backend .env** (`backend/.env`)
**Location:** `c:\Users\KIIT\Desktop\projectO\backend\.env`

**What needs editing:**

| Field | Current Value | What to Replace With | Example |
|-------|---------------|----------------------|---------|
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/unilink` | Your AWS RDS URL | `postgresql://admin:StrongPass123@your-db.amazonaws.com:5432/unilink` |
| `SECRET_KEY` | `your-secret-key-change-this` | Random 32+ char string | `abcdef1234567890hijklmnop1234567890` (use random generator) |
| `SMTP_SERVER` | `smtp.gmail.com` | Your email provider | `smtp.gmail.com` (Gmail) or `smtp-mail.outlook.com` (Outlook) |
| `SMTP_USER` | `your-email@gmail.com` | Your actual email | `your.email@gmail.com` |
| `SMTP_PASSWORD` | `your-app-password` | Email app-specific password | Get from Gmail/Outlook settings |
| `EMAIL_FROM` | `your-email@gmail.com` | Same as SMTP_USER | `your.email@gmail.com` |
| `FRONTEND_URL` | `http://localhost:3000` | Your domain | `https://yourdomain.com` |
| `BACKEND_URL` | `http://localhost:8000` | Your backend URL | `https://api.yourdomain.com` |
| `ENVIRONMENT` | `development` | `production` | `production` |

**How to edit:**
```bash
# Open the file
notepad c:\Users\KIIT\Desktop\projectO\backend\.env

# Or use VS Code
code c:\Users\KIIT\Desktop\projectO\backend\.env
```

---

#### 2️⃣ **Frontend .env** (`frontend/.env`)
**Location:** `c:\Users\KIIT\Desktop\projectO\frontend\.env`

**What needs editing:**

| Field | Current Value | What to Replace With | Example |
|-------|---------------|----------------------|---------|
| `VITE_API_URL` | `http://localhost:8000` | Your backend URL | `https://api.yourdomain.com` |

**How to edit:**
```bash
notepad c:\Users\KIIT\Desktop\projectO\frontend\.env
```

---

### **LEVEL 2: Optional (Performance & Security)**

#### 3️⃣ **Backend CORS** (`app/main.py`)
**Location:** `c:\Users\KIIT\Desktop\projectO\backend\app\main.py`

**Current (Development):**
```python
allow_origins=["http://localhost:3000", "http://localhost:5173"]
```

**Change to (Production):**
```python
allow_origins=["https://yourdomain.com"]
```

**How to edit:**
- Open file in VS Code
- Find: `allow_origins=`
- Replace localhost URLs with your production domain

---

#### 4️⃣ **Backend Rate Limiting** (OPTIONAL - Advanced)
**Location:** `c:\Users\KIIT\Desktop\projectO\backend\app\main.py`

**Current:** No rate limiting
**Recommendation:** Add in production (prevents abuse)

---

#### 5️⃣ **Frontend Build** (Optional - CDN)
**Location:** `c:\Users\KIIT\Desktop\projectO\frontend\vite.config.ts`

**For production:** Configure CDN if hosting assets on S3/CloudFront

---

### **LEVEL 3: AWS Deployment (If Going to AWS)**

#### 6️⃣ **AWS RDS Database**
```
Steps:
1. Create RDS PostgreSQL 15+ instance
2. Copy connection string
3. Add to backend/.env as DATABASE_URL
4. Run migrations: alembic upgrade head
```

#### 7️⃣ **AWS EC2 Backend**
```
Steps:
1. Create EC2 instance (Ubuntu 22.04)
2. Copy files to server
3. Install Python, create venv
4. Set environment variables
5. Run with Gunicorn + Nginx
```

#### 8️⃣ **AWS S3 Frontend**
```
Steps:
1. Build: npm run build
2. Upload dist/ to S3
3. CloudFront distribution
4. Route53 DNS
```

---

## 🚀 HOW TO TEST WITHOUT PRODUCTION VALUES

### **YES! You Can Test with Development Values!**

For testing purposes, you can use:
- `localhost:8000` as backend
- `localhost:3000` as frontend
- Local or Docker PostgreSQL
- Gmail SMTP (free tier)
- Any SECRET_KEY

**Just run:**
```bash
cd docker
docker-compose up
# Then open http://localhost:3000
```

**This will work perfectly for testing!**

---

## 📝 PRODUCTION CHECKLIST

### **Before Deploying to Production:**

```
☐ Backend .env - All values filled correctly
☐ Frontend .env - VITE_API_URL set to production URL
☐ Database - PostgreSQL/RDS created and accessible
☐ SMTP - Email credentials working
☐ SECRET_KEY - Generated and secure
☐ CORS origins - Updated for your domain
☐ Frontend build - Run: npm run build
☐ Backend tested - Verified imports and routes
☐ Email tested - Send test verification email
☐ WebRTC tested - Make test call with 2 accounts
☐ SSL certificate - HTTPS configured
☐ Environment - Set ENVIRONMENT=production
```

---

## 🔐 SECURING SECRET_KEY

### **Generate a Secure Secret Key:**

**Option 1: Python (Recommended)**
```bash
cd c:\Users\KIIT\Desktop\projectO\backend
.\venv\Scripts\python.exe
>>> import secrets
>>> secrets.token_urlsafe(32)
# Copy the output to backend/.env SECRET_KEY
```

**Option 2: Online Generator**
- Visit: https://generate-secret.vercel.app/
- Copy 32+ character string

---

## 📧 GMAIL SMTP SETUP (For Email Verification)

### **Enable Gmail App Password:**

1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Google generates 16-char password
4. Add to `backend/.env`:
   ```env
   SMTP_USER=your.email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

---

## 🐳 TESTING WITHOUT POSTGRES INSTALLED

### **Using Docker (Recommended!)**

```bash
# No PostgreSQL installation needed!
cd docker
docker-compose up
```

**Includes:**
- PostgreSQL 15 (Docker)
- Backend (Docker)
- Frontend (Dev server)
- All connected automatically

**Check if Docker is installed:**
```bash
docker --version
docker-compose --version
```

**If not installed:**
- Download Docker Desktop: https://www.docker.com/products/docker-desktop

---

## ⚠️ IMPORTANT: DON'T FILL PRODUCTION VALUES YET

### **Why Not?**

1. You need actual AWS account for database
2. You need domain name
3. You need SMTP credentials
4. You need SSL certificate

### **When to Fill:**

1. ✅ After testing with Docker (2-3 hours)
2. ✅ After you have production domain
3. ✅ After you setup AWS account (if using AWS)
4. ✅ After you setup email account

---

## 🎯 STEP-BY-STEP TESTING

### **Step 1: Start Services (5 minutes)**
```bash
cd docker
docker-compose up
```
Wait for "Uvicorn running on"

### **Step 2: Register (1 minute)**
- Open: http://localhost:3000
- Click "Register"
- Email: `test@sample.kiit.ac.in`
- Password: `Test@1234`
- Click "Register"

### **Step 3: Verify Email (2 minutes)**
- Check backend logs for verification token
- Or configure SMTP (see Gmail setup above)
- Paste token and set password

### **Step 4: Login (1 minute)**
- Use email and password
- Click "Login"

### **Step 5: Test Call (3 minutes)**
- Open 2 browser windows
- Register 2 different users
- Both click "Start a Call"
- Should match automatically
- Video/audio should work
- Chat should work

### **Step 6: After Verification**
- Now fill production values
- Deploy to AWS
- Update DNS

---

## 📍 FILE LOCATIONS QUICK REFERENCE

| What | Where | Edit How |
|-----|-------|----------|
| Backend config | `backend/.env` | Text editor |
| Frontend config | `frontend/.env` | Text editor |
| Backend CORS | `backend/app/main.py` | VS Code |
| Database connection | `backend/.env` | Text editor |
| Email settings | `backend/.env` | Text editor |
| API URL | `frontend/.env` | Text editor |
| Frontend domain | `frontend/.env` | Text editor |

---

## ✅ STATUS

```
✓ ESLint config created (.eslintrc.cjs)
✓ TypeScript errors: FIXED
✓ Tailwind: WORKING
✓ React: WORKING
✓ Frontend builds: SUCCESS
✓ Backend imports: SUCCESS
✓ All red lines: REMOVED
✓ Ready to test: YES
✓ PostgreSQL required: YES (can use Docker)
```

---

## 🚀 NEXT ACTIONS

### **Choose One:**

**Option A: Test Now (Recommended)**
```bash
cd docker
docker-compose up
# Then open http://localhost:3000
```

**Option B: Install PostgreSQL**
1. Download from postgresql.org
2. Install locally
3. Update backend/.env DATABASE_URL
4. Run backend/frontend separately

**Option C: Go Straight to Production**
1. Setup AWS RDS
2. Fill all .env values
3. Deploy to EC2
4. Setup CloudFront + Route53

---

## ❓ QUESTIONS?

- **"Can I test before filling production values?"** → YES! Use Docker
- **"Do I need PostgreSQL installed?"** → NO! Docker has it
- **"How long to test?"** → 15-20 minutes total
- **"When to deploy to AWS?"** → After testing works locally

---

**Recommendation: Start with Docker (Option A) - Easiest & Fastest! 🚀**

---

## Phase 4: Production Infrastructure ✅ COMPLETE

### 1. Error Tracking (Sentry)

**Files Created:**
- `backend/app/core/sentry.py` - Backend error tracking
- `frontend/src/utils/sentry.ts` - Frontend error tracking

**Setup:**
```bash
# Backend
pip install sentry-sdk

# Frontend
npm install @sentry/react
```

**Configuration (.env):**
```
SENTRY_DSN=https://[key]@sentry.io/[project-id]
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=production
```

**Features:**
- ✅ Real-time error monitoring
- ✅ Performance tracking
- ✅ Sensitive data filtering
- ✅ Breadcrumbs for debugging

---

### 2. SSL/TLS Certificates (Let's Encrypt)

**Files Created:**
- `scripts/setup-ssl.sh` - Automated certificate setup
- `docker/nginx-ssl.conf` - Secure Nginx configuration

**Setup:**
```bash
# For testing (staging)
sudo bash scripts/setup-ssl.sh unilink.example.com admin@email.com --staging

# For production (valid)
sudo bash scripts/setup-ssl.sh unilink.example.com admin@email.com
```

**Features:**
- ✅ Automated certificate renewal
- ✅ HTTPS redirect (HTTP → HTTPS)
- ✅ Security headers (HSTS, CSP)
- ✅ TLSv1.2 + TLSv1.3 only

---

### 3. Database Backups

**Files Created:**
- `scripts/backup-database.sh` - Daily backup script
- `scripts/restore-database.sh` - Restore from backup

**Setup:**
```bash
# Create backup directory
sudo mkdir -p /backups/unilink

# Schedule cron job
sudo crontab -e
# Add: 0 2 * * * /path/to/scripts/backup-database.sh
```

**Features:**
- ✅ Automated daily backups
- ✅ 30-day retention
- ✅ Compression (gzip)
- ✅ Point-in-time recovery
- ✅ Integrity verification

**Commands:**
```bash
# Manual backup
bash scripts/backup-database.sh

# View backups
ls -lh /backups/unilink/

# Restore
bash scripts/restore-database.sh /backups/unilink/backup_*.sql.gz
```

---

### 4. CI/CD Pipeline (GitHub Actions)

**Files Created:**
- `.github/workflows/tests.yml` - Test automation
- `.github/workflows/deploy.yml` - Production deployment

**Workflows:**

**Tests Workflow:**
- Run backend tests (pytest)
- Run frontend tests (npm build)
- Code quality checks (pylint, black)
- Security scans (bandit, safety)
- Upload coverage to Codecov

**Deploy Workflow:**
- Triggered on push to `main` or tag creation
- Build Docker images
- Push to Docker Hub
- Deploy to production
- Run health checks

**Setup:**
1. Push repository to GitHub
2. Add secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY`
3. Push code → Tests run automatically
4. Tag: `git tag v1.0.0 && git push origin v1.0.0` → Deploys to production

---

## Production Infrastructure Summary

| Component | Status | Files |
|-----------|--------|-------|
| Error Tracking | ✅ Complete | sentry.py, sentry.ts |
| SSL/TLS | ✅ Complete | setup-ssl.sh, nginx-ssl.conf |
| Backups | ✅ Complete | backup-database.sh, restore-database.sh |
| CI/CD | ✅ Complete | tests.yml, deploy.yml |

---

## Deployment Steps

### 1. Configure Environment
```bash
# Copy .env.example to .env
cp backend/.env.example backend/.env

# Edit with production values
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=production
DEBUG=false
```

### 2. Setup SSL Certificate
```bash
sudo bash scripts/setup-ssl.sh yourdomain.com your@email.com
```

### 3. Setup Database Backups
```bash
sudo mkdir -p /backups/unilink
sudo bash scripts/backup-database.sh
sudo crontab -e  # Add backup cron job
```

### 4. Connect GitHub Repository
```bash
git remote add origin https://github.com/yourusername/unilink.git
git push -u origin main
```

### 5. Add GitHub Secrets
- DOCKER_USERNAME
- DOCKER_PASSWORD
- DEPLOY_HOST
- DEPLOY_USER
- DEPLOY_KEY

### 6. Deploy
```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions will automatically deploy
```

---

## Monitoring & Maintenance

### Check Services
```bash
# Sentry errors
https://sentry.io/organizations/your-org/

# SSL certificate
sudo certbot certificates

# Backups
ls -lh /backups/unilink/

# Deployment logs
https://github.com/yourusername/unilink/actions
```

### Health Checks
```bash
# Website
curl -I https://yourdomain.com

# API
curl -I https://yourdomain.com/api/health

# Database backup test
psql postgresql://user@host/db -c "SELECT COUNT(*) FROM users;"
```

---

**Phase 4 Complete: All production infrastructure ready! 🚀**
