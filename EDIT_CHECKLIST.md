# 📋 PRODUCTION CHECKLIST - WHAT TO EDIT & WHERE

## ⚠️ IMPORTANT: Don't Edit Yet!

**DO NOT fill these before testing locally!**
1. Test first with current values (Docker will work as-is)
2. Verify everything works (15-20 minutes)
3. Then fill production values
4. Then deploy to AWS

---

## 🎯 ITEMS TO EDIT (For Production Deployment)

### **LEVEL 1: MUST EDIT (Before Deployment)**

#### **1. Backend Database Connection**

**File:** `c:\Users\KIIT\Desktop\projectO\backend\.env`

**Current:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/unilink
```

**Replace with:** Your AWS RDS connection string

**How to get:**
1. Create AWS RDS PostgreSQL instance
2. Copy connection string from AWS console
3. Paste here

**Example:**
```env
DATABASE_URL=postgresql://admin:MyStrongPass123@mydb.c9akciq32.us-east-1.rds.amazonaws.com:5432/unilink
```

---

#### **2. Backend Secret Key (Security)**

**File:** `c:\Users\KIIT\Desktop\projectO\backend\.env`

**Current:**
```env
SECRET_KEY=your-secret-key-change-this
```

**Replace with:** Generate secure 32+ character string

**How to generate:**
```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Online
https://generate-secret.vercel.app/

# Option 3: Simple random
abcd1234efgh5678ijkl9012mnop3456
```

**Example:**
```env
SECRET_KEY=6J_kL9mN-pQ2rSt4uVwX5yZa-bcDeFgHi
```

---

#### **3. Backend Email (SMTP) Settings**

**File:** `c:\Users\KIIT\Desktop\projectO\backend\.env`

**Current:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
```

**Replace with:** Your actual email credentials

**How to setup Gmail:**
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Google generates 16-character password
4. Copy the password (without spaces)

**Example:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=contact@unilink.com
SMTP_PASSWORD=abcd efgh ijkl mnop
EMAIL_FROM=contact@unilink.com
```

---

#### **4. Frontend API URL**

**File:** `c:\Users\KIIT\Desktop\projectO\frontend\.env`

**Current:**
```env
VITE_API_URL=http://localhost:8000
```

**Replace with:** Your production backend URL

**Example (AWS EC2):**
```env
VITE_API_URL=https://api.yourdomain.com
```

---

#### **5. Backend Domain URLs**

**File:** `c:\Users\KIIT\Desktop\projectO\backend\.env`

**Current:**
```env
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

**Replace with:** Your production domains

**Example:**
```env
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

---

#### **6. Environment Mode**

**File:** `c:\Users\KIIT\Desktop\projectO\backend\.env`

**Current:**
```env
ENVIRONMENT=development
```

**Change to:**
```env
ENVIRONMENT=production
```

---

### **LEVEL 2: OPTIONAL (Performance & Security)**

#### **7. Backend CORS (Cross-Origin)**

**File:** `c:\Users\KIIT\Desktop\projectO\backend\app\main.py`

**Find this line (approximately line 16-20):**
```python
allow_origins=["http://localhost:3000", "http://localhost:5173"],
```

**Change to:**
```python
allow_origins=["https://yourdomain.com"],
```

**Example:**
```python
allow_origins=["https://unilink.example.com"],
```

---

#### **8. WebRTC TURN Servers (Optional)**

**File:** `c:\Users\KIIT\Desktop\projectO\frontend\src\utils\webrtc.ts`

**Current:** Uses only STUN (free, works for most)

**Optional:** Add TURN servers for firewall bypass

**Location:** Line 8-15

**Current:**
```typescript
const STUN_SERVERS = [
  'stun.l.google.com:19302',
  'stun1.l.google.com:19302',
]
const TURN_SERVERS = [] // Empty for now
```

---

### **LEVEL 3: AWS SETUP (Advanced)**

#### **9. AWS RDS Database**

**Steps:**
1. Create RDS PostgreSQL instance (15+)
2. Get connection string
3. Add to `backend/.env` DATABASE_URL (see #1 above)
4. Run migrations: `alembic upgrade head`

---

#### **10. AWS EC2 Backend Server**

**Steps:**
1. Launch EC2 instance (Ubuntu 22.04)
2. SSH into server
3. Clone/upload project
4. Install Python, create venv
5. Fill `.env` values
6. Install Gunicorn + Nginx
7. Start backend service

**Command (on EC2):**
```bash
cd /var/www/unilink
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

---

#### **11. AWS S3 Frontend Hosting**

**Steps:**
1. Build frontend: `npm run build`
2. Create S3 bucket
3. Upload `dist/` folder contents
4. Enable static website hosting
5. Setup CloudFront CDN

---

#### **12. AWS Route53 DNS**

**Steps:**
1. Register domain (or use existing)
2. Create Route53 hosted zone
3. Add A records pointing to:
   - CloudFront (frontend)
   - EC2/ALB (backend)

---

## 📍 QUICK REFERENCE TABLE

| Item | File | Current | Should Be | Status |
|------|------|---------|-----------|--------|
| Database | backend/.env | localhost | AWS RDS | ⏳ Later |
| Secret Key | backend/.env | generic | Random 32+ char | ⏳ Later |
| SMTP Server | backend/.env | gmail.com | Your email provider | ⏳ Later |
| SMTP User | backend/.env | placeholder | Your email | ⏳ Later |
| SMTP Password | backend/.env | placeholder | App password | ⏳ Later |
| Frontend URL | frontend/.env | localhost:3000 | Your domain | ⏳ Later |
| Backend URL | backend/.env | localhost:8000 | Your domain | ⏳ Later |
| CORS Origins | main.py | localhost | Your domain | ⏳ Later |
| Environment | backend/.env | development | production | ⏳ Later |

---

## 🔐 SECURITY NOTES

### **DO NOT:**
- ❌ Commit .env files to Git
- ❌ Share SECRET_KEY with anyone
- ❌ Use weak passwords
- ❌ Expose database credentials in code
- ❌ Use development values in production

### **DO:**
- ✅ Use AWS Secrets Manager (advanced)
- ✅ Use environment variables
- ✅ Generate strong SECRET_KEY
- ✅ Use app-specific passwords (Gmail)
- ✅ Enable HTTPS/SSL
- ✅ Setup firewall rules

---

## 🚀 DEPLOYMENT ORDER

### **Step 1: Test Locally (NOW)**
```bash
cd docker
docker-compose up
# Test everything works
```

### **Step 2: Setup AWS (After Testing)**
- Create RDS instance
- Create EC2 instance
- Create S3 bucket
- Register domain

### **Step 3: Fill Production Values (After AWS Setup)**
- Database URL
- Secret key
- SMTP credentials
- Domain URLs

### **Step 4: Deploy Code (Final)**
- Upload to EC2
- Deploy frontend to S3
- Configure DNS

### **Step 5: Verify Production (Sanity Check)**
- Test registration
- Test login
- Test call
- Check logs

---

## ❓ ANSWERS

### **Q: When should I fill these values?**
> A: AFTER you test locally and verify everything works!

### **Q: Can I test without filling?**
> A: YES! Everything works as-is for testing!

### **Q: What if I fill wrong values?**
> A: App won't start. Just fix and restart.

### **Q: Do I need all of these?**
> A: Level 1 is required. Level 2-3 are optional.

### **Q: Can I deploy with localhost values?**
> A: NO! Must change for production deployment.

### **Q: Where do I get these values?**
> A: See specific instructions for each above.

---

## 📝 BEFORE DEPLOYMENT CHECKLIST

```
☐ All Level 1 items filled
☐ .env files secured (not in Git)
☐ Database tested and working
☐ Email verified working
☐ SECRET_KEY generated (32+ chars)
☐ CORS updated for your domain
☐ Frontend URL configured
☐ Backend URL configured
☐ ENVIRONMENT set to production
☐ SSL certificate obtained
☐ DNS records configured
☐ Docker tested locally
☐ All tests pass
☐ Documentation read
☐ Backup created
```

---

## 🎯 SUMMARY

**DO NOT EDIT NOW:** All values work for testing

**EDIT LATER:** When ready for production (see instructions above)

**RECOMMENDATION:** Test first → Edit later → Deploy

---

**Status: ✅ READY TO TEST**

**Next: Run `docker-compose up` and test! 🚀**
