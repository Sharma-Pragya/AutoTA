#!/bin/bash
# Start backend server only

echo "🚀 Starting Backend Server"
uvicorn autota.web.app:app --reload --port 8000
