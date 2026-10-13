#!/bin/sh
set -e

echo "Applying database migrations via Alembic..."
alembic upgrade head

echo "Seeding skills..."
python seed.py

echo "Launching FastAPI application server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}