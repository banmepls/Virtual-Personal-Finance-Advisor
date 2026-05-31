#!/bin/bash
set -e

# Run database initialization
echo "Initializing database..."
python -m scripts.init_db

# Start the application
echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --loop uvloop
