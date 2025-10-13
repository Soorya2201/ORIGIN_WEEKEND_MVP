"""
MVP API Routes for Health Dashboard
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.mvp import (
    UserProfile, UserProfileCreate, UserProfileUpdate,
    HealthAssessment, HealthAssessmentCreate,
    DashboardResponse, DashboardHealthMetrics,
    WearableData, WearableDataCreate, WearableDataUpdate,
    WearableSyncRequest, WearableSyncResponse,
    ChatRequest, ChatResponse,
    ChatSession, ChatSessionCreate,
    HealthDataLake, HealthDataLakeCreate
)
from app.services.health_assessment import HealthAssessmentEngine
from app.services.wearable_sync import WearableSyncService
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()


# User Profile Endpoints
@router.post("/users/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    user_profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile"""
    try:
        from app.db.models_mvp import UserProfile as UserProfileModel
        
        # Check if user already exists
        existing_user = db.query(UserProfileModel).filter(
            UserProfileModel.email == user_profile.email
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        db_user = UserProfileModel(**user_profile.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created user profile for {user_profile.email}")
        return db_user
        
    except Exception as e:
        logger.error(f"Error creating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile"
        )


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user profile by ID"""
    from app.db.models_mvp import UserProfile as UserProfileModel
    
    user = db.query(UserProfileModel).filter(UserProfileModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_id: str,
    user_update: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile"""
    from app.db.models_mvp import UserProfile as UserProfileModel
    
    user = db.query(UserProfileModel).filter(UserProfileModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Updated user profile for {user_id}")
    return user


# Dashboard Endpoints
@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
async def get_dashboard(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data for a user"""
    try:
        from app.db.models_mvp import UserProfile as UserProfileModel, HealthAssessment as HealthAssessmentModel
        
        # Get user profile
        user = db.query(UserProfileModel).filter(UserProfileModel.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get latest health assessment
        latest_assessment = db.query(HealthAssessmentModel).filter(
            HealthAssessmentModel.user_id == user_id
        ).order_by(HealthAssessmentModel.assessment_date.desc()).first()
        
        # Build health metrics
        health_metrics = DashboardHealthMetrics(
            sleep_score=latest_assessment.sleep_score if latest_assessment else None,
            hydration_score=latest_assessment.hydration_score if latest_assessment else None,
            vitamin_score=latest_assessment.vitamin_score if latest_assessment else None,
            caloric_intake_score=latest_assessment.caloric_intake_score if latest_assessment else None,
            overall_health_score=latest_assessment.overall_health_score if latest_assessment else None,
            last_updated=latest_assessment.updated_at if latest_assessment else None,
            data_sources=latest_assessment.data_sources if latest_assessment else []
        )
        
        # Get recent activities (mock data for now)
        recent_activities = [
            {"type": "lab_upload", "description": "Lab results uploaded", "timestamp": "2024-01-15T10:00:00Z"},
            {"type": "wearable_sync", "description": "Apple Watch data synced", "timestamp": "2024-01-15T09:30:00Z"},
            {"type": "chat_session", "description": "Health consultation completed", "timestamp": "2024-01-14T16:45:00Z"}
        ]
        
        # Generate recommendations (mock for now)
        recommendations = []
        if latest_assessment:
            if latest_assessment.sleep_score and latest_assessment.sleep_score < 70:
                recommendations.append("Consider improving your sleep quality")
            if latest_assessment.hydration_score and latest_assessment.hydration_score < 70:
                recommendations.append("Increase your daily water intake")
            if latest_assessment.vitamin_score and latest_assessment.vitamin_score < 70:
                recommendations.append("Consider vitamin supplementation")
        
        # Generate alerts (mock for now)
        alerts = []
        if latest_assessment and latest_assessment.overall_health_score and latest_assessment.overall_health_score < 60:
            alerts.append({
                "type": "warning",
                "message": "Overall health score is below recommended levels",
                "priority": "medium"
            })
        
        return DashboardResponse(
            user_profile=user,
            health_metrics=health_metrics,
            recent_activities=recent_activities,
            recommendations=recommendations,
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data"
        )


# Health Assessment Endpoints
@router.post("/health-assessments/", response_model=HealthAssessment, status_code=status.HTTP_201_CREATED)
async def create_health_assessment(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Calculate and create a new health assessment"""
    try:
        # Use health assessment engine
        assessment_engine = HealthAssessmentEngine(db)
        assessment_data = assessment_engine.calculate_health_assessment(user_id)
        
        # Create assessment record
        from app.db.models_mvp import HealthAssessment as HealthAssessmentModel
        db_assessment = HealthAssessmentModel(**assessment_data.dict())
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)
        
        logger.info(f"Created health assessment for user {user_id}")
        return db_assessment
        
    except Exception as e:
        logger.error(f"Error creating health assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health assessment"
        )


@router.get("/health-assessments/{user_id}", response_model=List[HealthAssessment])
async def get_health_assessments(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get health assessments for a user"""
    from app.db.models_mvp import HealthAssessment as HealthAssessmentModel
    
    assessments = db.query(HealthAssessmentModel).filter(
        HealthAssessmentModel.user_id == user_id
    ).order_by(HealthAssessmentModel.assessment_date.desc()).limit(limit).all()
    
    return assessments


# Wearable Data Endpoints
@router.post("/wearables/", response_model=WearableData, status_code=status.HTTP_201_CREATED)
async def create_wearable_device(
    wearable_data: WearableDataCreate,
    db: Session = Depends(get_db)
):
    """Register a new wearable device"""
    try:
        from app.db.models_mvp import WearableData as WearableDataModel
        
        # Check if device already exists
        existing_device = db.query(WearableDataModel).filter(
            WearableDataModel.user_id == wearable_data.user_id,
            WearableDataModel.device_type == wearable_data.device_type,
            WearableDataModel.device_id == wearable_data.device_id
        ).first()
        
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device already registered"
            )
        
        # Create new device
        db_device = WearableDataModel(**wearable_data.dict())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        logger.info(f"Registered wearable device {wearable_data.device_type} for user {wearable_data.user_id}")
        return db_device
        
    except Exception as e:
        logger.error(f"Error creating wearable device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register wearable device"
        )


@router.get("/wearables/{user_id}", response_model=List[WearableData])
async def get_wearable_devices(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all wearable devices for a user"""
    from app.db.models_mvp import WearableData as WearableDataModel
    
    devices = db.query(WearableDataModel).filter(
        WearableDataModel.user_id == user_id
    ).all()
    
    return devices


@router.post("/wearables/sync", response_model=WearableSyncResponse)
async def sync_wearable_data(
    user_id: str,
    sync_request: WearableSyncRequest,
    db: Session = Depends(get_db)
):
    """Sync data from a wearable device"""
    try:
        sync_service = WearableSyncService(db)
        result = await sync_service.sync_wearable_data(user_id, sync_request)
        
        logger.info(f"Wearable sync completed for user {user_id}, device {sync_request.device_type}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing wearable data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync wearable data"
        )


@router.get("/wearables/{user_id}/sync-status")
async def get_sync_status(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get sync status for all user's wearable devices"""
    try:
        sync_service = WearableSyncService(db)
        status_list = sync_service.get_sync_status(user_id)
        
        return {"devices": status_list}
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync status"
        )


# Chat Endpoints
@router.post("/chat/message", response_model=ChatResponse)
async def send_chat_message(
    user_id: str,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message to the AI health assistant"""
    try:
        chat_service = ChatService(db)
        response = await chat_service.process_chat_message(user_id, chat_request)
        
        logger.info(f"Chat message processed for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )


@router.get("/chat/sessions/{user_id}", response_model=List[ChatSession])
async def get_chat_sessions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all chat sessions for a user"""
    try:
        chat_service = ChatService(db)
        sessions = chat_service.get_user_sessions(user_id)
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat sessions"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get chat history for a session"""
    try:
        chat_service = ChatService(db)
        history = chat_service.get_chat_history(session_id, limit)
        
        return {"messages": history}
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat history"
        )


# Data Lake Endpoints
@router.post("/data-lake/", response_model=HealthDataLake, status_code=status.HTTP_201_CREATED)
async def store_health_data(
    health_data: HealthDataLakeCreate,
    db: Session = Depends(get_db)
):
    """Store health data in the data lake"""
    try:
        from app.db.models_mvp import HealthDataLake as HealthDataLakeModel
        
        # Create data lake entry
        db_entry = HealthDataLakeModel(**health_data.dict())
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        
        logger.info(f"Stored health data in data lake for user {health_data.user_id}")
        return db_entry
        
    except Exception as e:
        logger.error(f"Error storing health data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store health data"
        )


@router.get("/data-lake/{user_id}")
async def get_health_data(
    user_id: str,
    data_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get health data from the data lake"""
    try:
        from app.db.models_mvp import HealthDataLake as HealthDataLakeModel
        
        query = db.query(HealthDataLakeModel).filter(
            HealthDataLakeModel.user_id == user_id
        )
        
        if data_type:
            query = query.filter(HealthDataLakeModel.data_type == data_type)
        
        data_entries = query.order_by(
            HealthDataLakeModel.created_at.desc()
        ).limit(limit).all()
        
        return {
            "entries": data_entries,
            "total_count": len(data_entries),
            "data_types": list(set(entry.data_type for entry in data_entries))
        }
        
    except Exception as e:
        logger.error(f"Error getting health data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health data"
        )
