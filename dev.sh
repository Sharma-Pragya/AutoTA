#!/bin/bash
# dev.sh — starts backend and frontend for development

echo "🚀 Starting AutoTA Development Servers"
echo "======================================="
echo ""
echo "Starting backend on :8000..."
echo "Starting frontend on :5173..."
echo ""
echo "✅ Servers will start in separate processes"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Test with: http://localhost:5173/?sid=UID123456789"
echo ""
echo "Press Ctrl+C in each terminal to stop"
echo "======================================="
echo ""

# Start backend
uvicorn autota.web.app:app --reload --port 8000 &

# Wait a moment
sleep 2

# Start frontend
(cd frontend && npm run dev) &

# Wait for both
wait
