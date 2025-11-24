#!/bin/bash

# Simple Manual Startup Commands
# If start.sh has issues, use these commands directly

echo "🚀 Starting AI Learning Coach - Manual Mode"
echo "=========================================="

# Get absolute path
BASE_DIR="/Users/jaan/Desktop/Ai-Coach"

# Kill existing processes
echo "🔄 Cleaning up..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
lsof -ti:3002 | xargs kill -9 2>/dev/null
sleep 2

# Start Backend
echo ""
echo "📡 Starting Backend..."
cd "$BASE_DIR/backend"
/Users/jaan/miniconda3/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
sleep 5

# Start Frontend
echo ""
echo "🎨 Starting Frontend..."
cd "$BASE_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
sleep 5

echo ""
echo "=========================================="
echo "✅ RUNNING!"
echo "=========================================="
echo ""
echo "📱 Frontend:  http://localhost:3000"
echo "⚡ Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "PIDs: Backend=$BACKEND_PID Frontend=$FRONTEND_PID"
echo ""
echo "📋 Logs:"
echo "  Backend:  tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 To stop: ./stop.sh or kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop watching logs..."
echo ""

# Follow logs
tail -f /tmp/backend.log /tmp/frontend.log
