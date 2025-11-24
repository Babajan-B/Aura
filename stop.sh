#!/bin/bash

# AI Learning Coach - Stop Script
# Stops both Backend and Frontend servers

echo "🛑 Stopping AI Learning Coach..."
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Stop backend (port 8000)
echo -e "${RED}Stopping Backend (port 8000)...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend stopped${NC}"
else
    echo "   No backend process found"
fi

# Stop frontend (ports 3000-3003)
echo -e "${RED}Stopping Frontend (ports 3000-3003)...${NC}"
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
lsof -ti:3002 | xargs kill -9 2>/dev/null
lsof -ti:3003 | xargs kill -9 2>/dev/null
echo -e "${GREEN}✅ Frontend stopped${NC}"

# Clean up log files
rm -f /tmp/backend.log /tmp/frontend.log

echo ""
echo "=================================="
echo -e "${GREEN}✅ All servers stopped!${NC}"
echo "=================================="
