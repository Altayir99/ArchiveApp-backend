import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, workspaces, documents, search
from app.routers import import_router
from app.workers.drive_worker import start_scheduler, shutdown_scheduler

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle using modern FastAPI pattern."""
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="DocuAgent AI API",
    version="1.0.0",
    description="Backend API fuer DocuAgent AI - KI-Dokumentenassistent",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(import_router.router)


@app.get("/health", tags=["default"])
async def health_check():
    return {"status": "ok"}
