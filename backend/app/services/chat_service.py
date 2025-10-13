"""
Chat Service with Health Context
Provides AI-powered health consultations with access to user's health data
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.db.models_mvp import ChatSession, ChatMessage, HealthDataLake, HealthAssessment, UserProfile
from app.schemas.mvp import ChatRequest, ChatResponse, ChatSessionCreate
from app.insights.clients import generate_chat_response

logger = logging.getLogger(__name__)


class ChatService:
    """Service for AI-powered health chat with context"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_chat_message(self, user_id: str, chat_request: ChatRequest) -> ChatResponse:
        """
        Process a chat message with health context
        """
        logger.info(f"Processing chat message for user {user_id}")
        
        # Get or create chat session
        session = await self._get_or_create_session(user_id, chat_request.session_id)
        
        # Get health context if requested
        health_context = None
        if chat_request.include_health_context:
            health_context = await self._get_health_context(user_id)
        
        # Create user message
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=chat_request.message,
            health_context_used=health_context
        )
        self.db.add(user_message)
        self.db.commit()
        
        # Generate AI response
        ai_response = await self._generate_ai_response(
            chat_request.message, 
            health_context, 
            session.id
        )
        
        # Create AI message
        ai_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=ai_response["message"],
            health_context_used=health_context,
            tokens_used=ai_response.get("tokens_used"),
            model_used=ai_response.get("model_used")
        )
        self.db.add(ai_message)
        
        # Update session
        session.last_message_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return ChatResponse(
            message=ai_response["message"],
            session_id=session.id,
            message_id=ai_message.id,
            health_context_used=health_context,
            recommendations=ai_response.get("recommendations", []),
            follow_up_questions=ai_response.get("follow_up_questions", [])
        )
    
    async def _get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).first()
            
            if session:
                return session
        
        # Create new session
        new_session = ChatSession(
            user_id=user_id,
            session_name=f"Health Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            is_active=True
        )
        
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return new_session
    
    async def _get_health_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive health context for the user"""
        logger.info(f"Building health context for user {user_id}")
        
        # Get user profile
        user_profile = self.db.query(UserProfile).filter(UserProfile.id == user_id).first()
        
        # Get latest health assessment
        latest_assessment = self.db.query(HealthAssessment).filter(
            HealthAssessment.user_id == user_id
        ).order_by(HealthAssessment.assessment_date.desc()).first()
        
        # Get recent health data from data lake
        recent_data = self.db.query(HealthDataLake).filter(
            HealthDataLake.user_id == user_id
        ).order_by(HealthDataLake.created_at.desc()).limit(50).all()
        
        # Build context
        context = {
            "user_profile": {
                "age": self._calculate_age(user_profile.date_of_birth) if user_profile and user_profile.date_of_birth else None,
                "gender": user_profile.gender if user_profile else None,
                "height_cm": user_profile.height_cm if user_profile else None,
                "weight_kg": user_profile.weight_kg if user_profile else None
            },
            "health_assessment": self._format_health_assessment(latest_assessment) if latest_assessment else None,
            "recent_data_summary": self._summarize_recent_data(recent_data),
            "data_sources": self._get_active_data_sources(recent_data),
            "context_timestamp": datetime.utcnow().isoformat()
        }
        
        return context
    
    def _calculate_age(self, date_of_birth: datetime) -> Optional[int]:
        """Calculate age from date of birth"""
        if not date_of_birth:
            return None
        
        today = datetime.utcnow()
        age = today.year - date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
            age -= 1
        
        return age
    
    def _format_health_assessment(self, assessment: HealthAssessment) -> Dict[str, Any]:
        """Format health assessment for context"""
        if not assessment:
            return None
        
        return {
            "assessment_date": assessment.assessment_date.isoformat(),
            "scores": {
                "sleep_score": assessment.sleep_score,
                "hydration_score": assessment.hydration_score,
                "vitamin_score": assessment.vitamin_score,
                "caloric_intake_score": assessment.caloric_intake_score,
                "overall_health_score": assessment.overall_health_score
            },
            "details": {
                "sleep_details": assessment.sleep_details,
                "hydration_details": assessment.hydration_details,
                "vitamin_details": assessment.vitamin_details,
                "caloric_details": assessment.caloric_details
            },
            "confidence_score": assessment.confidence_score,
            "data_sources": assessment.data_sources
        }
    
    def _summarize_recent_data(self, recent_data: List[HealthDataLake]) -> Dict[str, Any]:
        """Summarize recent health data"""
        if not recent_data:
            return {"message": "No recent health data available"}
        
        summary = {
            "total_records": len(recent_data),
            "data_types": {},
            "recent_activities": [],
            "key_metrics": {}
        }
        
        # Count data types
        for record in recent_data:
            data_type = record.data_type
            summary["data_types"][data_type] = summary["data_types"].get(data_type, 0) + 1
        
        # Extract key metrics from recent data
        for record in recent_data[:10]:  # Look at most recent 10 records
            if record.data_type == "lab_results" and record.raw_data:
                # Handle both formats: extracted_data.labs and direct labs
                extracted_data = record.raw_data.get("extracted_data", {})
                labs = extracted_data.get("labs", []) if extracted_data else record.raw_data.get("labs", [])
                
                for lab in labs:
                    # Handle both formats: analyte_name/value_numeric and analyte/value
                    analyte = (lab.get("analyte_name", "") or lab.get("analyte", "")).lower()
                    value = lab.get("value_numeric") or lab.get("value")
                    
                    if "hemoglobin" in analyte:
                        summary["key_metrics"]["hemoglobin"] = value
                    elif "glucose" in analyte:
                        summary["key_metrics"]["glucose"] = value
                    elif "cholesterol" in analyte:
                        summary["key_metrics"]["cholesterol"] = value
                    elif "leukocyte" in analyte or "white blood" in analyte:
                        summary["key_metrics"]["white_blood_cells"] = value
                    elif "platelet" in analyte:
                        summary["key_metrics"]["platelets"] = value
                    elif "vitamin d" in analyte:
                        summary["key_metrics"]["vitamin_d"] = value
            
            elif record.data_type == "wearable" and record.processed_data:
                metrics = record.processed_data.get("metrics", {})
                if "steps" in metrics:
                    summary["key_metrics"]["average_daily_steps"] = metrics["steps"].get("average_daily_steps")
                if "sleep" in metrics:
                    summary["key_metrics"]["average_sleep_hours"] = metrics["sleep"].get("average_sleep_hours")
        
        return summary
    
    def _get_active_data_sources(self, recent_data: List[HealthDataLake]) -> List[str]:
        """Get list of active data sources"""
        sources = set()
        for record in recent_data:
            sources.add(record.data_source)
        return list(sources)
    
    async def _generate_ai_response(self, user_message: str, health_context: Optional[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Generate AI response using Gemini with health context"""
        try:
            # Prepare context for AI
            context_text = self._format_context_for_ai(health_context)
            
            # Create prompt with health context
            prompt = f"""
You are a knowledgeable and empathetic AI health assistant. You have access to the user's health data and should provide helpful, evidence-based advice while being careful not to provide medical diagnoses.

User's Health Context:
{context_text}

User's Question: {user_message}

IMPORTANT: If the user asks about lab results, blood work, or health metrics, you MUST reference the specific values from their uploaded lab data. Do not ask them to provide lab data - use what's available in their health context.

Please provide a helpful response that:
1. Addresses the user's question directly
2. References specific lab values and health data from their uploaded results
3. Provides actionable recommendations based on their actual data
4. Suggests follow-up questions
5. Reminds the user to consult healthcare professionals for medical concerns

Response format:
- Be conversational and empathetic
- Use the specific lab values to provide personalized insights
- Include specific recommendations based on their actual data
- If they have lab results, reference the specific values (e.g., "Your hemoglobin level of 15.3 g/dl is above the normal range of 11.1-14.1 g/dl")
- Suggest 2-3 follow-up questions
- Keep medical advice general and educational
"""
            
            # Use Gemini to generate response
            response = generate_chat_response(prompt)
            
            # Parse response and extract recommendations
            recommendations = self._extract_recommendations(response)
            follow_up_questions = self._extract_follow_up_questions(response)
            
            return {
                "message": response,
                "recommendations": recommendations,
                "follow_up_questions": follow_up_questions,
                "tokens_used": len(prompt.split()) + len(response.split()),  # Rough estimate
                "model_used": "gemini-pro"
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            
            # Fallback response
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Please try again, and if the issue persists, consider consulting with a healthcare professional for immediate concerns.",
                "recommendations": ["Try rephrasing your question", "Consult a healthcare professional for medical concerns"],
                "follow_up_questions": ["Is there anything specific about your health you'd like to discuss?", "Would you like me to help you understand any of your recent health data?"],
                "tokens_used": 0,
                "model_used": "fallback"
            }
    
    def _format_context_for_ai(self, health_context: Optional[Dict[str, Any]]) -> str:
        """Format health context for AI consumption"""
        if not health_context:
            return "No health data available"
        
        context_parts = []
        
        # User profile
        if health_context.get("user_profile"):
            profile = health_context["user_profile"]
            profile_text = "User Profile: "
            if profile.get("age"):
                profile_text += f"Age {profile['age']}, "
            if profile.get("gender"):
                profile_text += f"Gender: {profile['gender']}, "
            if profile.get("height_cm") and profile.get("weight_kg"):
                bmi = profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2)
                profile_text += f"BMI: {bmi:.1f}"
            context_parts.append(profile_text)
        
        # Health assessment
        if health_context.get("health_assessment"):
            assessment = health_context["health_assessment"]
            scores = assessment.get("scores", {})
            assessment_text = "Health Scores: "
            for score_name, score_value in scores.items():
                if score_value is not None:
                    assessment_text += f"{score_name.replace('_', ' ').title()}: {score_value}/100, "
            context_parts.append(assessment_text.rstrip(", "))
        
        # Recent data summary
        if health_context.get("recent_data_summary"):
            summary = health_context["recent_data_summary"]
            summary_text = f"Recent Data: {summary.get('total_records', 0)} records from {', '.join(summary.get('data_types', {}).keys())}"
            context_parts.append(summary_text)
            
            # Key metrics
            metrics = summary.get("key_metrics", {})
            if metrics:
                metrics_text = "Key Lab Results: "
                for metric_name, metric_value in metrics.items():
                    if metric_value is not None:
                        metrics_text += f"{metric_name.replace('_', ' ').title()}: {metric_value}, "
                context_parts.append(metrics_text.rstrip(", "))
        
        # Add detailed lab results if available
        if health_context.get("recent_data_summary", {}).get("data_types", {}).get("lab_results", 0) > 0:
            context_parts.append("The user has uploaded lab results that should be referenced in your response.")
        
        return "\n".join(context_parts)
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from AI response"""
        recommendations = []
        
        # Simple extraction - look for bullet points or numbered lists
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                # Clean up the line
                clean_line = line.lstrip('-•*123456789. ').strip()
                if clean_line and len(clean_line) > 10:  # Filter out very short items
                    recommendations.append(clean_line)
        
        return recommendations[:3]  # Limit to 3 recommendations
    
    def _extract_follow_up_questions(self, response: str) -> List[str]:
        """Extract follow-up questions from AI response"""
        questions = []
        
        # Look for question marks
        sentences = response.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if '?' in sentence and len(sentence) > 10:
                # Clean up the sentence
                clean_sentence = sentence.strip('?').strip()
                if clean_sentence:
                    questions.append(clean_sentence + '?')
        
        return questions[:3]  # Limit to 3 questions
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "health_context_used": message.health_context_used is not None
            }
            for message in reversed(messages)  # Return in chronological order
        ]
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.last_message_at.desc()).all()
        
        return [
            {
                "id": str(session.id),
                "session_name": session.session_name,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat(),
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None
            }
            for session in sessions
        ]
