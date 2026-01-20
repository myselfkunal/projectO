@echo off
REM UniLink Quick Start Script for Windows

echo.
echo ======================================
echo UniLink - Quick Start Setup
echo ======================================
echo.

REM Check prerequisites
echo Checking prerequisites...
python --version >nul 2>&1 || (echo Python is required but not installed. && exit /b 1)
node --version >nul 2>&1 || (echo Node.js is required but not installed. && exit /b 1)

echo OK: Python installed
echo OK: Node.js installed
echo.

REM Setup Backend
echo ======================================
echo Setting up Backend...
echo ======================================
cd backend

if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo WARNING: Please edit backend\.env with your configuration
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo OK: Virtual environment activated

echo Installing Python dependencies...
pip install -q -r requirements.txt
echo OK: Python dependencies installed

cd ..

REM Setup Frontend
echo.
echo ======================================
echo Setting up Frontend...
echo ======================================
cd frontend

if not exist .env (
    echo Creating .env file...
    (
        echo VITE_API_URL=http://localhost:8000
    ) > .env
)

if not exist node_modules (
    echo Installing npm dependencies...
    call npm install --silent
    echo OK: npm dependencies installed
) else (
    echo OK: npm dependencies already installed
)

cd ..

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo To start the project:
echo.
echo Option 1: Using Docker Compose
echo   cd docker
echo   docker-compose up
echo.
echo Option 2: Local Development
echo   Terminal 1 ^(Backend^):
echo     cd backend
echo     venv\Scripts\activate
echo     python -m uvicorn app.main:app --reload
echo.
echo   Terminal 2 ^(Frontend^):
echo     cd frontend
echo     npm run dev
echo.
echo Access:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
