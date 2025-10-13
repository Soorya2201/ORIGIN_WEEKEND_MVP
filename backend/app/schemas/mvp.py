"""
Pydantic schemas for MVP Health Dashboard
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID


# User Profile Schemas
class UserProfileBase(BaseModel):
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    date_of_birth: Optional[datetime] = Field(None, description="User date of birth")
    gender: Optional[str] = Field(None, description="User gender")
    height_cm: Optional[float] = Field(None, description="User height in centimeters")
    weight_kg: Optional[float] = Field(None, description="User weight in kilograms")


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None


class UserProfile(UserProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Health Assessment Schemas
class HealthAssessmentBase(BaseModel):
    sleep_score: Optional[float] = Field(None, ge=0, le=100, description="Sleep quality score (0-100)")
    hydration_score: Optional[float] = Field(None, ge=0, le=100, description="Hydration score (0-100)")
    vitamin_score: Optional[float] = Field(None, ge=0, le=100, description="Vitamin levels score (0-100)")
    caloric_intake_score: Optional[float] = Field(None, ge=0, le=100, description="Caloric intake score (0-100)")
    overall_health_score: Optional[float] = Field(None, ge=0, le=100, description="Overall health score (0-100)")
    
    sleep_details: Optional[Dict[str, Any]] = Field(None, description="Detailed sleep information")
    hydration_details: Optional[Dict[str, Any]] = Field(None, description="Detailed hydration information")
    vitamin_details: Optional[Dict[str, Any]] = Field(None, description="Detailed vitamin information")
    caloric_details: Optional[Dict[str, Any]] = Field(None, description="Detailed caloric information")
    
    data_sources: Optional[List[str]] = Field(None, description="Data sources used for assessment")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence in assessment (0-1)")


class HealthAssessmentCreate(HealthAssessmentBase):
    user_id: UUID


class HealthAssessmentUpdate(BaseModel):
    sleep_score: Optional[float] = Field(None, ge=0, le=100)
    hydration_score: Optional[float] = Field(None, ge=0, le=100)
    vitamin_score: Optional[float] = Field(None, ge=0, le=100)
    caloric_intake_score: Optional[float] = Field(None, ge=0, le=100)
    overall_health_score: Optional[float] = Field(None, ge=0, le=100)
    
    sleep_details: Optional[Dict[str, Any]] = None
    hydration_details: Optional[Dict[str, Any]] = None
    vitamin_details: Optional[Dict[str, Any]] = None
    caloric_details: Optional[Dict[str, Any]] = None
    
    data_sources: Optional[List[str]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)


class HealthAssessment(HealthAssessmentBase):
    id: UUID
    user_id: UUID
    assessment_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Wearable Data Schemas
class WearableDataBase(BaseModel):
    device_type: str = Field(..., description="Type of wearable device")
    device_id: str = Field(..., description="Unique device identifier")
    device_name: Optional[str] = Field(None, description="User-friendly device name")
    sync_frequency_hours: int = Field(24, description="Sync frequency in hours")
    data_types: Optional[List[str]] = Field(None, description="Available data types")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="Device connection configuration")


class WearableDataCreate(WearableDataBase):
    user_id: UUID


class WearableDataUpdate(BaseModel):
    device_name: Optional[str] = None
    sync_frequency_hours: Optional[int] = None
    data_types: Optional[List[str]] = None
    connection_config: Optional[Dict[str, Any]] = None


class WearableData(WearableDataBase):
    id: UUID
    user_id: UUID
    sync_status: str
    last_sync_at: Optional[datetime]
    raw_data: Optional[Dict[str, Any]]
    processed_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Chat Session Schemas
class ChatSessionBase(BaseModel):
    session_name: Optional[str] = Field(None, description="User-defined session name")
    health_context: Optional[Dict[str, Any]] = Field(None, description="Health context for the session")


class ChatSessionCreate(ChatSessionBase):
    user_id: UUID


class ChatSessionUpdate(BaseModel):
    session_name: Optional[str] = None
    is_active: Optional[bool] = None
    health_context: Optional[Dict[str, Any]] = None


class ChatSession(ChatSessionBase):
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Chat Message Schemas
class ChatMessageBase(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    health_context_used: Optional[Dict[str, Any]] = Field(None, description="Health context used for this message")


class ChatMessageCreate(ChatMessageBase):
    session_id: UUID


class ChatMessage(ChatMessageBase):
    id: UUID
    session_id: UUID
    timestamp: datetime
    tokens_used: Optional[int]
    model_used: Optional[str]
    
    class Config:
        from_attributes = True


# Data Sync Log Schemas
class DataSyncLogBase(BaseModel):
    sync_type: str = Field(..., description="Type of sync: wearable, lab_results, manual_entry")
    source: str = Field(..., description="Data source: apple_watch, lab_corp, manual, etc.")
    status: str = Field(..., description="Sync status: started, completed, failed, partial")
    records_processed: int = Field(0, description="Total records processed")
    records_successful: int = Field(0, description="Successfully processed records")
    records_failed: int = Field(0, description="Failed records")
    error_message: Optional[str] = Field(None, description="Error message if sync failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    data_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of synced data")


class DataSyncLogCreate(DataSyncLogBase):
    user_id: UUID


class DataSyncLog(DataSyncLogBase):
    id: UUID
    user_id: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    class Config:
        from_attributes = True


# Health Data Lake Schemas
class HealthDataLakeBase(BaseModel):
    data_type: str = Field(..., description="Type of health data")
    data_source: str = Field(..., description="Source of the data")
    raw_data: Dict[str, Any] = Field(..., description="Raw health data")
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Processed health data")
    data_metadata: Optional[Dict[str, Any]] = Field(None, description="Data metadata")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Data confidence score")
    validation_status: str = Field("pending", description="Data validation status")
    tags: Optional[List[str]] = Field(None, description="Data tags for searching")


class HealthDataLakeCreate(HealthDataLakeBase):
    user_id: UUID


class HealthDataLakeUpdate(BaseModel):
    processed_data: Optional[Dict[str, Any]] = None
    data_metadata: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    validation_status: Optional[str] = None
    tags: Optional[List[str]] = None


class HealthDataLake(HealthDataLakeBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Dashboard Response Schemas
class DashboardHealthMetrics(BaseModel):
    """Health metrics for dashboard display"""
    sleep_score: Optional[float] = Field(None, ge=0, le=100)
    hydration_score: Optional[float] = Field(None, ge=0, le=100)
    vitamin_score: Optional[float] = Field(None, ge=0, le=100)
    caloric_intake_score: Optional[float] = Field(None, ge=0, le=100)
    overall_health_score: Optional[float] = Field(None, ge=0, le=100)
    
    # Trend information
    sleep_trend: Optional[str] = Field(None, description="improving, declining, stable")
    hydration_trend: Optional[str] = Field(None, description="improving, declining, stable")
    vitamin_trend: Optional[str] = Field(None, description="improving, declining, stable")
    caloric_trend: Optional[str] = Field(None, description="improving, declining, stable")
    
    # Data freshness
    last_updated: Optional[datetime] = Field(None, description="When data was last updated")
    data_sources: Optional[List[str]] = Field(None, description="Active data sources")


class DashboardResponse(BaseModel):
    """Complete dashboard response"""
    user_profile: UserProfile
    health_metrics: DashboardHealthMetrics
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


# Wearable Sync Schemas
class WearableSyncRequest(BaseModel):
    """Request to sync wearable data"""
    device_type: str = Field(..., description="Type of wearable device")
    device_id: str = Field(..., description="Device identifier")
    sync_all_data: bool = Field(True, description="Whether to sync all available data")
    data_types: Optional[List[str]] = Field(None, description="Specific data types to sync")


class WearableSyncResponse(BaseModel):
    """Response from wearable sync"""
    sync_id: UUID
    status: str
    records_processed: int
    records_successful: int
    records_failed: int
    sync_duration_seconds: float
    error_message: Optional[str] = None


# Chat Schemas
class ChatRequest(BaseModel):
    """Chat request with health context"""
    message: str = Field(..., description="User message")
    session_id: Optional[UUID] = Field(None, description="Existing session ID")
    include_health_context: bool = Field(True, description="Whether to include health context")


class ChatResponse(BaseModel):
    """Chat response from AI doctor"""
    message: str = Field(..., description="AI response message")
    session_id: UUID = Field(..., description="Session ID")
    message_id: UUID = Field(..., description="Message ID")
    health_context_used: Optional[Dict[str, Any]] = Field(None, description="Health context used")
    recommendations: Optional[List[str]] = Field(None, description="Health recommendations")
    follow_up_questions: Optional[List[str]] = Field(None, description="Suggested follow-up questions")
