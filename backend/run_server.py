#!/usr/bin/env python3
"""
Start the Codebase Time Machine API server
"""

import sys
import os
import uvicorn

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    print("🚀 Starting Codebase Time Machine API Server")
    print("📡 Server will be available at: http://localhost:8001")
    print("📖 API Documentation at: http://localhost:8001/docs")
    print("🔧 Neo4j should be running at: neo4j://127.0.0.1:7687")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )