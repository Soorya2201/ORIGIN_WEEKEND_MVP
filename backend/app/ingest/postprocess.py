"""Post-processing utilities for lab results."""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import LabResult

logger = logging.getLogger(__name__)


def normalize_and_dedupe_labs(
    labs: List[Dict[str, Any]],
    person_id: UUID,
    file_id: UUID,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Normalize lab results and deduplicate against existing data.
    
    Args:
        labs: Raw lab results from extraction
        person_id: Person ID for the labs
        file_id: File ID for provenance
        db: Database session
        
    Returns:
        Processed and deduplicated lab results
    """
    processed_labs = []
    
    for lab in labs:
        try:
            # Normalize the lab data
            normalized_lab = _normalize_lab_data(lab)
            
            # Check for duplicates
            if not _is_duplicate(normalized_lab, person_id, db):
                processed_labs.append(normalized_lab)
            else:
                logger.info(f"Skipping duplicate lab: {normalized_lab['analyte']}")
                
        except Exception as e:
            logger.error(f"Failed to process lab {lab}: {e}")
            continue
    
    return processed_labs


def _normalize_lab_data(lab: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize individual lab data."""
    # Normalize analyte name
    analyte = lab.get("analyte", "").strip()
    analyte = _normalize_analyte_name(analyte)
    
    # Normalize value
    value = lab.get("value")
    if value is not None:
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = None
    
    # Normalize unit
    unit = lab.get("unit", "").strip() if lab.get("unit") else None
    
    # Normalize date
    observed_at = lab.get("observed_at")
    if observed_at:
        try:
            if isinstance(observed_at, str):
                # Try to parse ISO date
                observed_at = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
            elif isinstance(observed_at, date):
                observed_at = datetime.combine(observed_at, datetime.min.time())
        except (ValueError, TypeError):
            # Fallback to current date
            observed_at = datetime.utcnow()
    else:
        observed_at = datetime.utcnow()
    
    # Normalize reference ranges
    ref_low = lab.get("ref_low")
    ref_high = lab.get("ref_high")
    
    if ref_low is not None:
        try:
            ref_low = float(ref_low)
        except (ValueError, TypeError):
            ref_low = None
    
    if ref_high is not None:
        try:
            ref_high = float(ref_high)
        except (ValueError, TypeError):
            ref_high = None
    
    return {
        "analyte": analyte,
        "value": value,
        "unit": unit,
        "observed_at": observed_at.isoformat(),
        "loinc_code": lab.get("loinc_code"),
        "ref_low": ref_low,
        "ref_high": ref_high
    }


def _normalize_analyte_name(analyte: str) -> str:
    """Normalize analyte names to standard forms."""
    analyte = analyte.upper().strip()
    
    # Common normalizations
    normalizations = {
        "LDL-C": "LDL Cholesterol",
        "LDL CHOLESTEROL": "LDL Cholesterol",
        "HDL-C": "HDL Cholesterol", 
        "HDL CHOLESTEROL": "HDL Cholesterol",
        "TOTAL CHOLESTEROL": "Total Cholesterol",
        "CHOLESTEROL, TOTAL": "Total Cholesterol",
        "TRIGLYCERIDES": "Triglycerides",
        "HBA1C": "HbA1c",
        "A1C": "HbA1c",
        "HEMOGLOBIN A1C": "HbA1c",
        "TSH": "TSH",
        "THYROID STIMULATING HORMONE": "TSH",
        "FERRITIN": "Ferritin",
        "GLUCOSE": "Glucose",
        "CREATININE": "Creatinine",
        "BUN": "BUN",
        "BLOOD UREA NITROGEN": "BUN"
    }
    
    return normalizations.get(analyte, analyte.title())


def _is_duplicate(
    lab: Dict[str, Any],
    person_id: UUID,
    db: Session
) -> bool:
    """Check if a lab result is a duplicate of existing data."""
    try:
        # Look for existing lab with same analyte, person, and similar timestamp
        existing = db.query(LabResult).filter(
            and_(
                LabResult.person_id == person_id,
                LabResult.analyte_name == lab["analyte"],
                LabResult.value_numeric == lab["value"],
                LabResult.unit == lab["unit"]
            )
        ).first()
        
        return existing is not None
        
    except Exception as e:
        logger.error(f"Error checking for duplicates: {e}")
        return False
