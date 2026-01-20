#!/bin/bash

# UniLink Quick Start Script
# This script sets up and runs the entire project locally

set -e

echo "======================================"
echo "UniLink - Quick Start Setup"
echo "======================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. For Docker Compose setup only."; }

echo "✓ Python: $(python3 --version)"
echo "✓ Node: $(node --version)"
echo "✓ npm: $(npm --version)"
echo ""

# Setup Backend
echo "======================================"
echo "Setting up Backend..."
echo "======================================"
cd backend

if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠ Please edit backend/.env with your PostgreSQL credentials and SMTP settings"
fi

# Create virtual environment
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✓ Python dependencies installed"

cd ..

# Setup Frontend
echo ""
echo "======================================"
echo "Setting up Frontend..."
echo "======================================"
cd frontend

if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "VITE_API_URL=http://localhost:8000" > .env
fi

if [ ! -d node_modules ]; then
    echo "Installing npm dependencies..."
    npm install --silent
    echo "✓ npm dependencies installed"
else
    echo "✓ npm dependencies already installed"
fi

cd ..

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the project:"
echo ""
echo "Option 1: Using Docker Compose (Recommended)"
echo "  cd docker"
echo "  docker-compose up"
echo ""
echo "Option 2: Local Development"
echo "  Terminal 1 (Backend):"
echo "    cd backend"
echo "    source venv/bin/activate  # On Windows: venv\Scripts\activate"
echo "    python -m uvicorn app.main:app --reload"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "Access:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
