#!/bin/bash
set -e

echo "UniLink Frontend Setup"
echo "====================="

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "VITE_API_URL=http://localhost:8000" > .env
fi

# Install dependencies
echo "Installing dependencies..."
npm install

echo ""
echo "Setup complete! Run 'npm run dev' to start the development server"
