"""Pydantic schemas for insights."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class InsightResponse(BaseModel):
    """Insight response schema."""
    
    id: UUID
    kind: str
    title: str
    detail: Optional[str] = None
    confidence: Optional[float] = None
    engine: str
    inputs: Optional[Dict[str, Any]] = None
    created_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class InsightRunResponse(BaseModel):
    """Insight run response schema."""
    
    insights: List[InsightResponse]
    engine: str
    count: int
