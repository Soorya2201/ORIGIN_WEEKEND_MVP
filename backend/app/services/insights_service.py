"""Insights service for rule-based analysis and LLM summaries."""

import logging
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Insight, Person
from app.insights.rules import run_deterministic_rules
from app.insights.llm_summary import generate_clinical_summary

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for insights generation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def run_insights(self, person_id: UUID) -> Dict[str, Any]:
        """
        Run deterministic rules to generate insights.
        
        Args:
            person_id: Person ID to analyze
            
        Returns:
            Dictionary with generated insights
        """
        try:
            # Run deterministic rules
            insights = run_deterministic_rules(person_id, self.db)
            
            # Save insights to database
            db_insights = []
            for insight_data in insights:
                db_insight = Insight(
                    person_id=person_id,
                    kind="rule",
                    title=insight_data["title"],
                    detail=insight_data["detail"],
                    confidence=insight_data.get("confidence", 1.0),
                    engine="rule",
                    inputs=insight_data.get("inputs", []),
                    status="active"
                )
                self.db.add(db_insight)
                db_insights.append(db_insight)
            
            self.db.commit()
            
            # Refresh to get IDs
            for insight in db_insights:
                self.db.refresh(insight)
            
            return {
                "insights": [self._insight_to_dict(insight) for insight in db_insights],
                "engine": "rule",
                "count": len(db_insights)
            }
            
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            raise
    
    def get_insights(self, person_id: UUID) -> List[Dict[str, Any]]:
        """Get all insights for a person."""
        try:
            insights = self.db.query(Insight).filter(
                Insight.person_id == person_id,
                Insight.status == "active"
            ).order_by(Insight.created_at.desc()).all()
            
            return [self._insight_to_dict(insight) for insight in insights]
            
        except Exception as e:
            logger.error(f"Failed to retrieve insights: {e}")
            raise
    
    def generate_summary(self, person_id: UUID) -> str:
        """Generate clinical summary using LLM."""
        try:
            return generate_clinical_summary(person_id, self.db)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise
    
    def _insight_to_dict(self, insight: Insight) -> Dict[str, Any]:
        """Convert Insight to dictionary."""
        return {
            "id": str(insight.id),
            "kind": insight.kind,
            "title": insight.title,
            "detail": insight.detail,
            "confidence": insight.confidence,
            "engine": insight.engine,
            "inputs": insight.inputs,
            "created_at": insight.created_at.isoformat(),
            "status": insight.status
        }
