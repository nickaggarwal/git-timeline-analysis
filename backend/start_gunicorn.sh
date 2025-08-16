#!/bin/bash

# Codebase Time Machine - Gunicorn Startup Script
# This script starts the FastAPI backend using Gunicorn for better performance

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

echo -e "${PURPLE}🚀 Starting Codebase Time Machine API Server with Gunicorn${NC}"
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
# This is a simple check - you might want to enhance it
if ! nc -z 127.0.0.1 7687 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Neo4j might not be running on port 7687${NC}"
    echo -e "${YELLOW}💡 Please ensure Neo4j is started and accessible${NC}"
fi

# Start Gunicorn with our FastAPI app
echo -e "${GREEN}🚀 Starting Gunicorn server...${NC}"
echo -e "${BLUE}📊 Configuration:${NC}"
echo -e "${BLUE}   - Workers: $(python3 -c 'import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)')${NC}"
echo -e "${BLUE}   - Worker class: uvicorn.workers.UvicornWorker${NC}"
echo -e "${BLUE}   - Bind: 0.0.0.0:8001${NC}"
echo ""

# Export environment variables from .env file
export $(grep -v '^#' ../.env | xargs)

# Start Gunicorn
exec gunicorn \
    --config gunicorn.conf.py \
    src.api.main:app