#!/bin/bash

# Shows Attended - Startup Script

echo "🎸 Shows Attended - Starting Server"
echo "=================================="

# Check if database exists
if [ ! -f "database/shows.db" ]; then
    echo "⚠️  Database not found. Please run: python3 database/init_db.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv

    # Activate and install dependencies
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
else
    # Activate existing venv
    source venv/bin/activate
fi

# Start the server
echo ""
echo "✓ Server starting at http://localhost:8000"
echo "✓ Open http://localhost:8000/app in your browser"
echo ""

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
