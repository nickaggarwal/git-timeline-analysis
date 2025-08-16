#!/bin/bash

# Codebase Time Machine - Uvicorn Startup Script
# This script starts the FastAPI backend using Uvicorn with multiple workers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

echo -e "${PURPLE}🚀 Starting Codebase Time Machine API Server with Uvicorn${NC}"
echo -e "${BLUE}📁 Working directory: $SCRIPT_DIR${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${CYAN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade requirements
echo -e "${CYAN}📦 Installing/upgrading requirements...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo -e "${RED}❌ Error: .env file not found in parent directory${NC}"
    echo -e "${YELLOW}💡 Please ensure you have a .env file with necessary configuration${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Clear previous log files (optional)
if [ -f "logs/access.log" ]; then
    > logs/access.log
fi
if [ -f "logs/error.log" ]; then
    > logs/error.log
fi

# Check if Neo4j is accessible (optional health check)
echo -e "${CYAN}🔍 Checking Neo4j connectivity...${NC}"
if ! nc -z 127.0.0.1 7687 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Neo4j might not be running on port 7687${NC}"
    echo -e "${YELLOW}💡 Please ensure Neo4j is started and accessible${NC}"
fi

# Calculate worker count (CPU cores for better multithreading)
WORKER_COUNT=$(python3 -c 'import multiprocessing; print(multiprocessing.cpu_count())')

# Start Uvicorn with our FastAPI app
echo -e "${GREEN}🚀 Starting Uvicorn server...${NC}"
echo -e "${BLUE}📊 Configuration:${NC}"
echo -e "${BLUE}   - Workers: $WORKER_COUNT${NC}"
echo -e "${BLUE}   - Host: 0.0.0.0${NC}"
echo -e "${BLUE}   - Port: 8001${NC}"
echo -e "${BLUE}   - Reload: No (Production mode)${NC}"
echo ""

# Export environment variables from .env file
export $(grep -v '^#' ../.env | xargs)

echo "🚀 Codebase Time Machine API Server started with Uvicorn"
echo "📡 Server available at: http://localhost:8001"
echo "📖 API Documentation at: http://localhost:8001/docs"
echo "⚡ Running with $WORKER_COUNT worker processes"
echo "🔧 Neo4j should be running at: neo4j://127.0.0.1:7687"
echo ""

# Start Uvicorn with multiple workers
exec uvicorn \
    --host 0.0.0.0 \
    --port 8001 \
    --workers $WORKER_COUNT \
    --access-log \
    --log-level info \
    src.api.main:app