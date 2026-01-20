@echo off
setlocal enabledelayedexpansion

echo UniLink Backend Setup
echo ====================

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env with your configuration
)

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create database tables
echo Creating database tables...
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

echo.
echo Setup complete! Run 'python -m uvicorn app.main:app --reload' to start the server
