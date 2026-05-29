# DocuAgent AI Backend

FastAPI Backend fuer DocuAgent AI.

## Stack
- Python 3.12 / FastAPI
- PostgreSQL 16
- SQLAlchemy (async) + Alembic
- JWT Auth (bcrypt + python-jose)
- Docker + Docker Compose

## Server: VPS 91.134.133.206 (Shared with Facturo)

| | Facturo | DocuAgent |
|---|---------|-----------|
| Pfad | ~/apps/invoice-app | ~/apps/docuagent-backend |
| API Port | 8080 | 8001 |
| DB Container | postgres | docuagent-db |
| API Container | spring-app | docuagent-api |
| Docker Network | default | docuagent-network |
| Nginx | api.facturo.it.com | /docuagent/* on IP |

## Deploy

```bash
ssh ubuntu@91.134.133.206
cd ~/apps/docuagent-backend
cp .env.example .env  # edit secrets
chmod +x deploy.sh && ./deploy.sh
```

## Local Dev

```bash
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
docker compose -p docuagent up -d docuagent-db
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

## Swagger: http://91.134.133.206:8001/docs
