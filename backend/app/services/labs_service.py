"""Lab results service for orchestrating media extraction and database operations."""

import logging
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import File as FileModel, LabResult, Person
from app.ingest.gemini_extract import extract_labs_from_media
from app.ingest.postprocess import normalize_and_dedupe_labs
from app.ingest.redactor import redact_lab_data

logger = logging.getLogger(__name__)


class LabsService:
    """Service for lab result operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def ingest_from_media(self, file_id: UUID) -> Dict[str, Any]:
        """
        Extract lab results from media file and store in database.
        
        Args:
            file_id: UUID of the uploaded file
            
        Returns:
            Dictionary with extracted labs and provenance information
        """
        try:
            # Get file from database
            db_file = self.db.query(FileModel).filter(FileModel.id == file_id).first()
            if not db_file:
                raise ValueError("File not found")
            
            # Read file content
            from app.files.bucket import LocalBucket
            bucket = LocalBucket()
            file_content = bucket.get_file(db_file.bucket_key)
            if not file_content:
                raise ValueError("File not found on disk")
            
            # Extract labs using Gemini
            extracted_data = extract_labs_from_media(file_content, db_file.mime)
            
            # Redact PII from extracted data
            redacted_data = redact_lab_data(extracted_data)
            
            # Get or create demo person (for demo purposes)
            demo_person = self._get_or_create_demo_person()
            
            # Process and normalize labs
            processed_labs = normalize_and_dedupe_labs(
                redacted_data["labs"],
                person_id=demo_person.id,
                file_id=db_file.id,
                db=self.db
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
                    observed_at=lab_data["observed_at"],
                    source="gemini",
                    file_id=db_file.id
                )
                self.db.add(db_lab)
                db_labs.append(db_lab)
            
            self.db.commit()
            
            # Refresh to get IDs
            for lab in db_labs:
                self.db.refresh(lab)
            
            return {
                "labs": [self._lab_to_dict(lab) for lab in db_labs],
                "provenance": {
                    "engine": "gemini",
                    "confidence": redacted_data.get("confidence", 0.8),
                    "file_id": str(db_file.id),
                    "notes": redacted_data.get("notes", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Lab ingestion failed: {e}")
            raise
    
    def get_latest_labs(self, person_id: UUID) -> List[Dict[str, Any]]:
        """Get latest lab results for a person."""
        # This would be implemented to get the most recent value per analyte
        # For now, return empty list
        return []
    
    def _get_or_create_demo_person(self) -> Person:
        """Get or create demo person for testing."""
        demo_person = self.db.query(Person).first()
        if not demo_person:
            demo_person = Person(
                email="demo@example.com",
                name="Demo Patient"
            )
            self.db.add(demo_person)
            self.db.commit()
            self.db.refresh(demo_person)
        return demo_person
    
    def _lab_to_dict(self, lab: LabResult) -> Dict[str, Any]:
        """Convert LabResult to dictionary."""
        return {
            "id": str(lab.id),
            "analyte_name": lab.analyte_name,
            "value_numeric": lab.value_numeric,
            "unit": lab.unit,
            "ref_low": lab.ref_low,
            "ref_high": lab.ref_high,
            "loinc_code": lab.loinc_code,
            "observed_at": lab.observed_at.isoformat(),
            "source": lab.source,
            "file_id": str(lab.file_id) if lab.file_id else None,
            "created_at": lab.created_at.isoformat()
        }
