"""LLM-based clinical summary generation."""

import logging
from typing import Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import LabResult, Insight, Person
from app.insights.clients import summarize_clinician
from app.ingest.redactor import redact_lab_data

logger = logging.getLogger(__name__)


def generate_clinical_summary(person_id: UUID, db: Session) -> str:
    """
    Generate a clinical summary using LLM.
    
    Args:
        person_id: Person ID to summarize
        db: Database session
        
    Returns:
        Clinical summary in markdown format
    """
    try:
        # Get person data
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise ValueError("Person not found")
        
        # Get recent lab results
        labs = db.query(LabResult).filter(
            LabResult.person_id == person_id
        ).order_by(desc(LabResult.observed_at)).limit(50).all()
        
        # Get recent insights
        insights = db.query(Insight).filter(
            Insight.person_id == person_id,
            Insight.status == "active"
        ).order_by(desc(Insight.created_at)).limit(20).all()
        
        # Prepare deidentified data
        deidentified_data = _prepare_deidentified_data(person, labs, insights)
        
        # Generate summary using LLM
        summary = summarize_clinician(deidentified_data)
        
        logger.info("Clinical summary generated successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate clinical summary: {e}")
        raise


def _prepare_deidentified_data(
    person: Person,
    labs: list,
    insights: list
) -> Dict[str, Any]:
    """Prepare deidentified data for LLM processing."""
    
    # Convert labs to dict format
    lab_data = []
    for lab in labs:
        lab_dict = {
            "analyte": lab.analyte_name,
            "value": lab.value_numeric,
            "unit": lab.unit,
            "observed_at": lab.observed_at.isoformat(),
            "ref_low": lab.ref_low,
            "ref_high": lab.ref_high,
            "loinc_code": lab.loinc_code
        }
        lab_data.append(lab_dict)
    
    # Convert insights to dict format
    insight_data = []
    for insight in insights:
        insight_dict = {
            "title": insight.title,
            "detail": insight.detail,
            "confidence": insight.confidence,
            "engine": insight.engine,
            "created_at": insight.created_at.isoformat()
        }
        insight_data.append(insight_dict)
    
    # Create deidentified summary
    deidentified = {
        "patient_info": {
            "age_group": _get_age_group(person.dob) if person.dob else "unknown",
            "sex": "not_specified"  # Don't include actual sex for privacy
        },
        "lab_results": lab_data,
        "insights": insight_data,
        "summary_metadata": {
            "total_labs": len(lab_data),
            "total_insights": len(insight_data),
            "date_range": _get_date_range(lab_data) if lab_data else None
        }
    }
    
    # Apply additional redaction
    return redact_lab_data(deidentified)


def _get_age_group(dob) -> str:
    """Get age group without revealing exact age."""
    if not dob:
        return "unknown"
    
    from datetime import datetime
    today = datetime.now().date()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    if age < 18:
        return "pediatric"
    elif age < 30:
        return "young_adult"
    elif age < 50:
        return "adult"
    elif age < 65:
        return "middle_aged"
    else:
        return "senior"


def _get_date_range(lab_data: list) -> Dict[str, str]:
    """Get date range of lab results."""
    if not lab_data:
        return None
    
    dates = [lab["observed_at"] for lab in lab_data if lab.get("observed_at")]
    if not dates:
        return None
    
    return {
        "earliest": min(dates),
        "latest": max(dates)
    }
