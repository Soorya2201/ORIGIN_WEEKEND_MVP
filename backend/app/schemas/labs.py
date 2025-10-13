"""Pydantic schemas for lab results."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class LabResultResponse(BaseModel):
    """Lab result response schema."""
    
    id: UUID
    analyte_name: str
    value_numeric: Optional[float] = None
    unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    loinc_code: Optional[str] = None
    observed_at: datetime
    source: str
    file_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LabIngestResponse(BaseModel):
    """Lab ingestion response schema."""
    
    labs: List[LabResultResponse]
    provenance: Dict[str, Any] = Field(
        description="Information about the extraction process"
    )
