#!/bin/bash

# Codebase Time Machine - System Startup Script

echo "🕰️  Starting Codebase Time Machine System"
echo "=========================================="

# Check if Neo4j is running
echo "🔍 Checking Neo4j connection..."
if ! curl -f -s neo4j://127.0.0.1:7687 > /dev/null 2>&1; then
    echo "❌ Neo4j is not running at neo4j://127.0.0.1:7687"
    echo "💡 Please start Neo4j and try again"
    echo "   Example: docker run -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest"
    exit 1
fi

echo "✅ Neo4j connection OK"

# Start backend with Gunicorn
echo "🚀 Starting FastAPI backend server with Gunicorn..."
cd backend
./start_gunicorn.sh &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check backend health
if curl -f -s http://localhost:8001/health > /dev/null; then
    echo "✅ Backend server is running at http://localhost:8001"
else
    echo "❌ Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting Next.js frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 10

echo ""
echo "🎉 System started successfully!"
echo "================================"
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Backend:  http://localhost:8001"
echo "📖 API Docs: http://localhost:8001/docs"
echo "🗃️  Neo4j:    http://localhost:7474"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait