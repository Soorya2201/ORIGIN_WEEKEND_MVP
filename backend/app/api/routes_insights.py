"""Insights routes for rule-based analysis and LLM summaries."""

from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.deps import get_db
from app.db.models import Insight, Person
from app.insights.rules import run_deterministic_rules
from app.insights.llm_summary import generate_clinical_summary
from app.schemas.insights import InsightResponse, InsightRunResponse

router = APIRouter()
settings = get_settings()


@router.post("/run")
async def run_insights(
    db: Session = Depends(get_db)
) -> InsightRunResponse:
    """
    Run deterministic rules on lab results to generate insights.
    
    Returns:
        Generated insights from rule-based analysis
    """
    try:
        # Get demo person (for demo purposes)
        demo_person = db.query(Person).first()
        if not demo_person:
            raise HTTPException(status_code=404, detail="No patient data found")
        
        # Run deterministic rules
        insights = run_deterministic_rules(demo_person.id, db)
        
        # Save insights to database
        db_insights = []
        for insight_data in insights:
            db_insight = Insight(
                person_id=demo_person.id,
                kind="rule",
                title=insight_data["title"],
                detail=insight_data["detail"],
                confidence=insight_data.get("confidence", 1.0),
                engine="rule",
                inputs=insight_data.get("inputs", []),
                status="active"
            )
            db.add(db_insight)
            db_insights.append(db_insight)
        
        db.commit()
        
        # Refresh to get IDs
        for insight in db_insights:
            db.refresh(insight)
        
        return InsightRunResponse(
            insights=[InsightResponse.from_orm(insight) for insight in db_insights],
            engine="rule",
            count=len(db_insights)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Insight generation failed: {str(e)}"
        )


@router.get("/")
async def get_insights(
    db: Session = Depends(get_db)
) -> List[InsightResponse]:
    """
    Get all insights for the current patient.
    
    Returns:
        List of insights
    """
    try:
        # Get demo person (for demo purposes)
        demo_person = db.query(Person).first()
        if not demo_person:
            return []
        
        insights = db.query(Insight).filter(
            Insight.person_id == demo_person.id,
            Insight.status == "active"
        ).order_by(Insight.created_at.desc()).all()
        
        return [InsightResponse.from_orm(insight) for insight in insights]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve insights: {str(e)}"
        )


@router.post("/summaries/clinician")
async def generate_summary(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate a clinical summary using LLM.
    
    Returns:
        Clinical summary in markdown format
    """
    try:
        # Get demo person (for demo purposes)
        demo_person = db.query(Person).first()
        if not demo_person:
            raise HTTPException(status_code=404, detail="No patient data found")
        
        # Generate summary
        summary = generate_clinical_summary(demo_person.id, db)
        
        return {
            "summary": summary,
            "engine": "gemini",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )
