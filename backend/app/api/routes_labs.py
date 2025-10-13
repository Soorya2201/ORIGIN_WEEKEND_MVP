"""Lab result routes for ingestion and retrieval."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config.settings import get_settings
from app.db.deps import get_db
from app.db.models import File as FileModel, LabResult, Person
from app.ingest.gemini_extract import extract_labs_from_media
from app.ingest.postprocess import normalize_and_dedupe_labs
from app.schemas.labs import LabResultResponse, LabIngestResponse

router = APIRouter()
settings = get_settings()


@router.post("/ingest_from_media")
async def ingest_from_media(
    file_id: str,
    db: Session = Depends(get_db)
) -> LabIngestResponse:
    """
    Extract lab results from uploaded media file using Gemini multimodal.
    
    Args:
        file_id: UUID of the uploaded file
        
    Returns:
        Extracted and processed lab results
    """
    try:
        # Get file from database
        db_file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        file_path = Path(settings.files_bucket_path) / db_file.bucket_key
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Extract labs using Gemini
        extracted_data = extract_labs_from_media(file_content, db_file.mime)
        
        # Get or create demo person (for demo purposes)
        demo_person = db.query(Person).first()
        if not demo_person:
            demo_person = Person(
                id=uuid.uuid4(),
                email="demo@example.com",
                name="Demo Patient"
            )
            db.add(demo_person)
            db.commit()
            db.refresh(demo_person)
        
        # Process and normalize labs
        processed_labs = normalize_and_dedupe_labs(
            extracted_data["labs"],
            person_id=demo_person.id,
            file_id=db_file.id,
            db=db
        )
        
        # Save to database
        db_labs = []
        for lab_data in processed_labs:
            db_lab = LabResult(
                person_id=demo_person.id,
                analyte_name=lab_data["analyte"],
                value_numeric=lab_data["value"],
                unit=lab_data["unit"],
                ref_low=lab_data.get("ref_low"),
                ref_high=lab_data.get("ref_high"),
                loinc_code=lab_data.get("loinc_code"),
                observed_at=datetime.fromisoformat(lab_data["observed_at"]),
                source="gemini",
                file_id=db_file.id
            )
            db.add(db_lab)
            db_labs.append(db_lab)
        
        db.commit()
        
        # Refresh to get IDs
        for lab in db_labs:
            db.refresh(lab)
        
        return LabIngestResponse(
            labs=[LabResultResponse.from_orm(lab) for lab in db_labs],
            provenance={
                "engine": "gemini",
                "confidence": extracted_data.get("confidence", 0.8),
                "file_id": str(db_file.id),
                "notes": extracted_data.get("notes", "")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lab ingestion failed: {str(e)}"
        )


@router.get("/")
async def get_labs(
    latest: bool = Query(True, description="Return only latest values per analyte"),
    db: Session = Depends(get_db)
) -> List[LabResultResponse]:
    """
    Get lab results.
    
    Args:
        latest: If True, return only the most recent value per analyte
        
    Returns:
        List of lab results
    """
    try:
        if latest:
            # Get latest value per analyte
            subquery = db.query(
                LabResult.analyte_name,
                LabResult.person_id,
                db.func.max(LabResult.observed_at).label('max_date')
            ).group_by(
                LabResult.analyte_name,
                LabResult.person_id
            ).subquery()
            
            labs = db.query(LabResult).join(
                subquery,
                (LabResult.analyte_name == subquery.c.analyte_name) &
                (LabResult.person_id == subquery.c.person_id) &
                (LabResult.observed_at == subquery.c.max_date)
            ).order_by(desc(LabResult.observed_at)).all()
        else:
            # Get all labs
            labs = db.query(LabResult).order_by(desc(LabResult.observed_at)).all()
        
        return [LabResultResponse.from_orm(lab) for lab in labs]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve labs: {str(e)}"
        )
