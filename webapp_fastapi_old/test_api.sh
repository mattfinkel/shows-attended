#!/bin/bash

echo "Testing API..."

# Activate venv and start server in background
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test API
echo "Fetching stats..."
curl -s http://localhost:8000/api/stats/summary

# Kill server
kill $SERVER_PID

echo ""
echo "✓ Test complete"
