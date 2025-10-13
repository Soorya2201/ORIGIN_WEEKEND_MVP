"""Admin routes for health checks and environment verification."""

import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.deps import get_db
from app.insights.clients import ensure_live

router = APIRouter()
settings = get_settings()


@router.get("/healthz")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "message": "Lab Backend is running"}


@router.get("/envcheck")
async def env_check():
    """Check essential environment variables."""
    # Check settings instead of environment variables directly
    missing_vars = []
    present_vars = []
    
    # Check GEMINI_API_KEY
    if not settings.gemini_api_key or settings.gemini_api_key == "<YOUR_KEY_HERE>":
        missing_vars.append("GEMINI_API_KEY")
    else:
        present_vars.append("GEMINI_API_KEY")
    
    # Check DATABASE_URL
    if not settings.database_url:
        missing_vars.append("DATABASE_URL")
    else:
        present_vars.append("DATABASE_URL")
    
    # Check REDIS_URL
    if not settings.redis_url:
        missing_vars.append("REDIS_URL")
    else:
        present_vars.append("REDIS_URL")
    
    # Check FILES_BUCKET_PATH
    if not settings.files_bucket_path:
        missing_vars.append("FILES_BUCKET_PATH")
    else:
        present_vars.append("FILES_BUCKET_PATH")
    
    if missing_vars:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Missing or invalid environment variables",
                "missing": missing_vars,
                "present": present_vars
            }
        )
    
    return {
        "status": "ok",
        "message": "All required environment variables are present",
        "present": present_vars
    }


@router.get("/gemini_check")
async def gemini_check():
    """Check Gemini API connectivity."""
    if settings.offline_mode:
        return {
            "live": False,
            "offline": True,
            "message": "Running in offline mode"
        }
    
    try:
        ensure_live()
        return {
            "live": True,
            "offline": False,
            "message": "Gemini API is accessible"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "live": False,
                "offline": False,
                "error": str(e),
                "message": "Gemini API check failed"
            }
        )
