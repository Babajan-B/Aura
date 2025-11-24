#!/bin/bash

# AI Learning Coach - Start Script
# Runs both Backend and Frontend servers

echo "🚀 Starting AI Learning Coach..."
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kill any existing processes on ports 8000 and 3000-3003
echo "🔄 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
lsof -ti:3002 | xargs kill -9 2>/dev/null
lsof -ti:3003 | xargs kill -9 2>/dev/null
sleep 2

# Get the base directory
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start Backend
echo ""
echo -e "${BLUE}📡 Starting Backend API...${NC}"
cd "$BASE_DIR/backend"
/Users/jaan/miniconda3/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo "   Waiting for backend to initialize..."
sleep 5

# Start Frontend
echo ""
echo -e "${BLUE}🎨 Starting Frontend...${NC}"
cd "$BASE_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to be ready
echo "   Waiting for frontend to initialize..."
sleep 5

# Show status
echo ""
echo "=================================="
echo -e "${GREEN}🎉 AI Learning Coach is RUNNING!${NC}"
echo "=================================="
echo ""
echo -e "${YELLOW}📱 Frontend:${NC}  http://localhost:3002"
echo -e "${YELLOW}⚡ Backend:${NC}   http://localhost:8000"
echo -e "${YELLOW}📚 API Docs:${NC}  http://localhost:8000/docs"
echo ""
echo "=================================="
echo ""
echo -e "${BLUE}Process IDs:${NC}"
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo "  Backend:  tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo ""
echo -e "${YELLOW}🛑 To stop all servers:${NC}"
echo "  ./stop.sh"
echo "  or: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=================================="
echo ""
echo "Press Ctrl+C to stop watching logs..."
echo ""

# Follow logs
tail -f /tmp/backend.log /tmp/frontend.log
