from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, workspaces, documents, search

settings = get_settings()

app = FastAPI(
    title="DocuAgent AI API",
    version="1.0.0",
    description="Backend API fuer DocuAgent AI - KI-Dokumentenassistent",
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


@app.get("/health", tags=["default"])
async def health_check():
    return {"status": "ok"}
