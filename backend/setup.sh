#!/bin/bash
set -e

echo "UniLink Backend Setup"
echo "===================="

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env with your configuration"
fi

# Create virtual environment
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create database if it doesn't exist
echo "Checking PostgreSQL connection..."
python -c "from app.core.database import engine; engine.connect().close()" && echo "Database connection OK" || echo "Warning: Could not connect to database"

# Create tables
echo "Creating database tables..."
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

echo ""
echo "Setup complete! Run 'python -m uvicorn app.main:app --reload' to start the server"
