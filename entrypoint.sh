
set -e

echo "--- STARTING DEPLOYMENT UPGRADE CYCLE ---"


echo "Applying database migrations via Alembic..."
alembic upgrade head

echo "Launching FastAPI application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000