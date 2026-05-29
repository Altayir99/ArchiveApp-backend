#!/bin/bash
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================="
echo "  DocuAgent AI - Deployment"
echo "  Facturo wird NICHT beruehrt"
echo "========================================="

if [ ! -f "app/main.py" ]; then
    echo "FEHLER: app/main.py nicht gefunden."
    exit 1
fi

echo "Pulling latest changes..."
git pull

echo "Stopping DocuAgent services ONLY..."
docker compose -p docuagent down

echo "Building DocuAgent..."
docker compose -p docuagent build

echo "Starting DocuAgent services..."
docker compose -p docuagent up -d

echo "Waiting for database..."
sleep 5

echo "Running migrations..."
docker compose -p docuagent exec docuagent-api alembic upgrade head

echo "DocuAgent deployed successfully!"
echo "API: http://91.134.133.206:8001/health"
echo "Swagger: http://91.134.133.206:8001/docs"
