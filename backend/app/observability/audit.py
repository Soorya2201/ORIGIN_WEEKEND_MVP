"""Audit logging utilities."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def log_audit_event(
    event_type: str,
    user_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True
) -> None:
    """
    Log audit events for compliance and monitoring.
    
    Args:
        event_type: Type of event (e.g., 'file_upload', 'lab_extraction')
        user_id: User ID if available
        details: Additional event details
        success: Whether the operation was successful
    """
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": str(user_id) if user_id else None,
        "success": success,
        "details": details or {}
    }
    
    logger.info(f"AUDIT: {audit_data}")


def log_file_upload(file_id: UUID, filename: str, size: int, success: bool = True) -> None:
    """Log file upload events."""
    log_audit_event(
        event_type="file_upload",
        details={
            "file_id": str(file_id),
            "filename": filename,
            "size": size
        },
        success=success
    )


def log_lab_extraction(file_id: UUID, lab_count: int, confidence: float, success: bool = True) -> None:
    """Log lab extraction events."""
    log_audit_event(
        event_type="lab_extraction",
        details={
            "file_id": str(file_id),
            "lab_count": lab_count,
            "confidence": confidence
        },
        success=success
    )


def log_insight_generation(insight_count: int, engine: str, success: bool = True) -> None:
    """Log insight generation events."""
    log_audit_event(
        event_type="insight_generation",
        details={
            "insight_count": insight_count,
            "engine": engine
        },
        success=success
    )
