#!/bin/bash
export PYTHONPATH=/home/ysd2484/vela2
export MAX_PROFILES=50000

echo "Starting Backend API..."
export MAX_PROFILES=20000
/home/ysd2484/miniconda3/envs/vela313/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
