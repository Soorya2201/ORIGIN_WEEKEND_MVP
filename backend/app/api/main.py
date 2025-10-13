"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_admin import router as admin_router
from app.api.routes_upload import router as upload_router
from app.api.routes_labs import router as labs_router
from app.api.routes_insights import router as insights_router
from app.api.routes_mvp import router as mvp_router
from app.config.settings import get_settings

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Lab Backend API",
    description="FastAPI backend for lab result processing with Gemini multimodal extraction",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(labs_router, prefix="/labs", tags=["labs"])
app.include_router(insights_router, prefix="/insights", tags=["insights"])
app.include_router(mvp_router, prefix="/mvp", tags=["mvp"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Lab Backend API",
        "version": "0.1.0",
        "docs": "/docs"
    }
