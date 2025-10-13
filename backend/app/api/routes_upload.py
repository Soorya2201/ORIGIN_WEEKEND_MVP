"""Upload routes for file handling."""

from typing import Dict, Any
import uuid
import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.deps import get_db
from app.db.models import File as FileModel

router = APIRouter()
settings = get_settings()


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a file for lab result processing.
    
    Accepts image/* and application/pdf files up to 10MB.
    """
    # Validate file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )
    
    # Validate MIME type
    if file.content_type not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {settings.allowed_mime_types}"
        )
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Generate file metadata
        file_id = uuid.uuid4()
        sha256_hash = hashlib.sha256(content).hexdigest()
        bucket_key = f"{file_id}.{file.filename.split('.')[-1] if '.' in file.filename else 'bin'}"
        
        # Ensure bucket directory exists
        bucket_path = Path(settings.files_bucket_path)
        bucket_path.mkdir(exist_ok=True)
        
        # Save file to local storage
        file_path = bucket_path / bucket_key
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store file metadata in database
        db_file = FileModel(
            id=file_id,
            bucket_key=bucket_key,
            mime=file.content_type,
            size=file_size,
            sha256=sha256_hash,
            uploaded_by=None  # TODO: Add user authentication
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {
            "file_id": str(file_id),
            "mime": file.content_type,
            "size": file_size,
            "sha256": sha256_hash,
            "bucket_key": bucket_key
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )
