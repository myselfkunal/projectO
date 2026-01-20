@echo off
setlocal enabledelayedexpansion

echo UniLink Frontend Setup
echo =====================

if not exist .env (
    echo VITE_API_URL=http://localhost:8000 > .env
)

echo Installing dependencies...
npm install

echo.
echo Setup complete! Run 'npm run dev' to start the development server
