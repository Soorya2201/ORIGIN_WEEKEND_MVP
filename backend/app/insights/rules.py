"""Deterministic rules engine for lab result analysis."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.db.models import LabResult

logger = logging.getLogger(__name__)


def run_deterministic_rules(person_id: UUID, db: Session) -> List[Dict[str, Any]]:
    """
    Run deterministic rules on lab results to generate insights.
    
    Args:
        person_id: Person ID to analyze
        db: Database session
        
    Returns:
        List of generated insights
    """
    insights = []
    
    try:
        # Get all lab results for the person
        labs = db.query(LabResult).filter(
            LabResult.person_id == person_id
        ).order_by(desc(LabResult.observed_at)).all()
        
        if not labs:
            logger.info("No lab results found for person")
            return insights
        
        # Group labs by analyte
        labs_by_analyte = {}
        for lab in labs:
            if lab.analyte_name not in labs_by_analyte:
                labs_by_analyte[lab.analyte_name] = []
            labs_by_analyte[lab.analyte_name].append(lab)
        
        # Run specific rule sets
        insights.extend(_check_ldl_cholesterol(labs_by_analyte.get("LDL Cholesterol", [])))
        insights.extend(_check_hba1c(labs_by_analyte.get("HbA1c", [])))
        insights.extend(_check_tsh(labs_by_analyte.get("TSH", [])))
        insights.extend(_check_ferritin(labs_by_analyte.get("Ferritin", [])))
        insights.extend(_check_trends(labs_by_analyte))
        
        logger.info(f"Generated {len(insights)} insights from rules")
        return insights
        
    except Exception as e:
        logger.error(f"Error running deterministic rules: {e}")
        return []


def _check_ldl_cholesterol(labs: List[LabResult]) -> List[Dict[str, Any]]:
    """Check LDL cholesterol levels against guidelines."""
    insights = []
    
    if not labs:
        return insights
    
    latest_lab = labs[0]  # Already sorted by date desc
    
    if latest_lab.value_numeric is None or latest_lab.unit != "mg/dL":
        return insights
    
    value = latest_lab.value_numeric
    lab_id = str(latest_lab.id)
    
    if value >= 190:
        insights.append({
            "title": "Very High LDL Cholesterol",
            "detail": f"LDL cholesterol is {value} mg/dL, which is very high (≥190 mg/dL). This significantly increases cardiovascular risk and requires immediate attention.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    elif value >= 160:
        insights.append({
            "title": "High LDL Cholesterol", 
            "detail": f"LDL cholesterol is {value} mg/dL, which is high (160-189 mg/dL). Consider lifestyle modifications and potential medication.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    elif value >= 130:
        insights.append({
            "title": "Borderline High LDL Cholesterol",
            "detail": f"LDL cholesterol is {value} mg/dL, which is borderline high (130-159 mg/dL). Monitor and consider lifestyle changes.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    
    return insights


def _check_hba1c(labs: List[LabResult]) -> List[Dict[str, Any]]:
    """Check HbA1c levels for diabetes risk."""
    insights = []
    
    if not labs:
        return insights
    
    latest_lab = labs[0]
    
    if latest_lab.value_numeric is None or latest_lab.unit != "%":
        return insights
    
    value = latest_lab.value_numeric
    lab_id = str(latest_lab.id)
    
    if value >= 6.5:
        insights.append({
            "title": "Diabetes Risk - High HbA1c",
            "detail": f"HbA1c is {value}%, indicating diabetes (≥6.5%). Immediate medical attention and diabetes management required.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    elif value >= 5.7:
        insights.append({
            "title": "Prediabetes Risk",
            "detail": f"HbA1c is {value}%, indicating prediabetes (5.7-6.4%). Lifestyle modifications and monitoring recommended.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    
    return insights


def _check_tsh(labs: List[LabResult]) -> List[Dict[str, Any]]:
    """Check TSH levels for thyroid function."""
    insights = []
    
    if not labs:
        return insights
    
    latest_lab = labs[0]
    
    if latest_lab.value_numeric is None or latest_lab.unit not in ["mIU/L", "mU/L"]:
        return insights
    
    value = latest_lab.value_numeric
    lab_id = str(latest_lab.id)
    
    if value > 4.0:
        insights.append({
            "title": "Possible Hypothyroidism",
            "detail": f"TSH is {value} mIU/L, which is elevated (>4.0 mIU/L). This may indicate hypothyroidism and requires evaluation.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    elif value < 0.4:
        insights.append({
            "title": "Possible Hyperthyroidism",
            "detail": f"TSH is {value} mIU/L, which is low (<0.4 mIU/L). This may indicate hyperthyroidism and requires evaluation.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    
    return insights


def _check_ferritin(labs: List[LabResult]) -> List[Dict[str, Any]]:
    """Check ferritin levels for iron stores."""
    insights = []
    
    if not labs:
        return insights
    
    latest_lab = labs[0]
    
    if latest_lab.value_numeric is None or latest_lab.unit != "ng/mL":
        return insights
    
    value = latest_lab.value_numeric
    lab_id = str(latest_lab.id)
    
    if value < 30:
        insights.append({
            "title": "Low Iron Stores",
            "detail": f"Ferritin is {value} ng/mL, indicating low iron stores (<30 ng/mL). Consider iron supplementation and evaluation for iron deficiency.",
            "confidence": 1.0,
            "inputs": [lab_id]
        })
    
    return insights


def _check_trends(labs_by_analyte: Dict[str, List[LabResult]]) -> List[Dict[str, Any]]:
    """Check for significant trends in lab values."""
    insights = []
    
    for analyte, labs in labs_by_analyte.items():
        if len(labs) < 2:
            continue
        
        # Get the two most recent values
        latest = labs[0]
        previous = labs[1]
        
        if (latest.value_numeric is None or 
            previous.value_numeric is None or
            latest.unit != previous.unit):
            continue
        
        # Check if values are within 120 days
        time_diff = latest.observed_at - previous.observed_at
        if time_diff > timedelta(days=120):
            continue
        
        # Calculate percentage change
        if previous.value_numeric == 0:
            continue
        
        percent_change = abs((latest.value_numeric - previous.value_numeric) / previous.value_numeric * 100)
        
        if percent_change > 20:
            direction = "increased" if latest.value_numeric > previous.value_numeric else "decreased"
            insights.append({
                "title": f"Significant Trend in {analyte}",
                "detail": f"{analyte} has {direction} by {percent_change:.1f}% from {previous.value_numeric} to {latest.value_numeric} {latest.unit} over {time_diff.days} days.",
                "confidence": 0.9,
                "inputs": [str(latest.id), str(previous.id)]
            })
    
    return insights
