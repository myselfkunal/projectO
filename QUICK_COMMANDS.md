# 🚀 Quick Commands - UniLink

Everything has been set up and verified! Use these commands to run your project.

---

## ✅ Setup Complete

- ✓ Backend virtual environment created
- ✓ All 18 Python packages installed
- ✓ All 372 Node packages installed  
- ✓ Frontend builds successfully (0 errors)
- ✓ Backend imports successfully
- ✓ All 11 routes registered
- ✓ .env files created

---

## 🏃 RUN LOCALLY (3 TERMINALS)

### Terminal 1: PostgreSQL
```bash
# Make sure PostgreSQL is running
# Windows: Start PostgreSQL service or use pgAdmin
# Linux/Mac: brew services start postgresql
```

### Terminal 2: Backend
```bash
cd c:\Users\KIIT\Desktop\projectO\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Terminal 3: Frontend
```bash
cd c:\Users\KIIT\Desktop\projectO\frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

---

## 🐳 RUN WITH DOCKER

One command to start everything:

```bash
cd c:\Users\KIIT\Desktop\projectO\docker
docker-compose up
```

Then open:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 🔧 Common Commands

### Backend Commands
```bash
cd c:\Users\KIIT\Desktop\projectO\backend
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt

# Run server
python -m uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Check imports
python -c "from app.main import app; print('OK')"
```

### Frontend Commands
```bash
cd c:\Users\KIIT\Desktop\projectO\frontend

# Install packages
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Commands
```bash
cd c:\Users\KIIT\Desktop\projectO\docker

# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Rebuild
docker-compose up --build
```

---

## 🧪 Quick Test Flow

1. **Register**: Go to `http://localhost:3000/register`
   - Email: `test@sample.kiit.ac.in`
   - Username: `testuser1`
   - Password: `Test@1234`

2. **Verify Email**: Check backend logs for verification token (if SMTP not configured)

3. **Login**: Use credentials from step 1

4. **Open 2 browsers**: 
   - Browser 1: Register `user1@sample.kiit.ac.in`
   - Browser 2: Register `user2@sample.kiit.ac.in`
   - Both click "Start a Call"
   - Should match automatically

5. **Test Features**:
   - Video/Audio call
   - Text chat
   - End call
   - Call appears in history

---

## 📝 Configuration

### Backend .env (`backend/.env`)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/unilink
SECRET_KEY=your-secret-key-change-this
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Frontend .env (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

### "Database connection refused"
```bash
# Start PostgreSQL
# Windows: Services > PostgreSQL > Start
# Or create Docker volume and use docker-compose
```

### "Port already in use"
```bash
# Change port in:
# Backend: vite.config.ts (change port: 3000 to 3001)
# Frontend: in code, update BACKEND_URL
```

### "Module not found"
```bash
# Backend
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### "Cannot find type 'NodeJS'"
```bash
# Already fixed! But if it reappears:
cd frontend
npm install --save-dev @types/node
```

---

## 📊 What's Running

| Service | Port | Status |
|---------|------|--------|
| Frontend (Vite) | 3000 | Local dev server |
| Backend (FastAPI) | 8000 | API + WebSocket |
| PostgreSQL | 5432 | Database |
| WebSocket | 8000/calls/ws | Real-time |

---

## ✨ Next Steps

1. **Test locally** (5 minutes)
2. **Configure SMTP** for real email verification (10 minutes)
3. **Deploy to Docker** (2 minutes)
4. **Deploy to AWS** (30 minutes) - Follow README.md

---

## 📖 Documentation

- **[INDEX.md](INDEX.md)** - Documentation hub
- **[STARTUP.md](STARTUP.md)** - Detailed setup guide
- **[README.md](README.md)** - Complete reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical design
- **[ENV_SETUP.md](ENV_SETUP.md)** - Configuration guide
- **[TESTING.md](TESTING.md)** - Testing procedures
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Troubleshooting
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Overview

---

## 🎯 Status: READY TO RUN ✅

All systems operational. Choose your deployment method above and start!

```
Happy coding! 🚀
```
