"""
MVP Data Models for Health Dashboard
Data Lake approach with JSON storage for flexibility
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class UserProfile(Base):
    """User profile and basic information"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other, prefer_not_to_say
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_assessments = relationship("HealthAssessment", back_populates="user")
    wearable_data = relationship("WearableData", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")


class HealthAssessment(Base):
    """Overall health assessments and ratings"""
    __tablename__ = "health_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Assessment scores (0-100)
    sleep_score = Column(Float, nullable=True)  # 0-100
    hydration_score = Column(Float, nullable=True)  # 0-100
    vitamin_score = Column(Float, nullable=True)  # 0-100
    caloric_intake_score = Column(Float, nullable=True)  # 0-100
    overall_health_score = Column(Float, nullable=True)  # 0-100
    
    # Assessment details (JSON for flexibility)
    sleep_details = Column(JSON, nullable=True)  # sleep duration, quality, etc.
    hydration_details = Column(JSON, nullable=True)  # water intake, urine color, etc.
    vitamin_details = Column(JSON, nullable=True)  # vitamin levels, supplements, etc.
    caloric_details = Column(JSON, nullable=True)  # calories consumed, burned, etc.
    
    # Assessment metadata
    assessment_date = Column(DateTime, default=datetime.utcnow)
    data_sources = Column(JSON, nullable=True)  # which data sources were used
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in assessment
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="health_assessments")


class WearableData(Base):
    """Wearable device data (Apple Watch, Fitbit, etc.)"""
    __tablename__ = "wearable_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Device information
    device_type = Column(String(100), nullable=False)  # apple_watch, fitbit, garmin, etc.
    device_id = Column(String(255), nullable=False)
    device_name = Column(String(255), nullable=True)
    
    # Data sync information
    sync_status = Column(String(50), default="pending")  # pending, syncing, completed, failed
    last_sync_at = Column(DateTime, nullable=True)
    sync_frequency_hours = Column(Integer, default=24)  # how often to sync
    
    # Raw wearable data (JSON for flexibility)
    raw_data = Column(JSON, nullable=True)  # raw API response from wearable
    processed_data = Column(JSON, nullable=True)  # processed/cleaned data
    
    # Data types available
    data_types = Column(JSON, nullable=True)  # ["steps", "heart_rate", "sleep", "calories", etc.]
    
    # Authentication/connection info (encrypted)
    connection_config = Column(JSON, nullable=True)  # OAuth tokens, API keys, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="wearable_data")


class ChatSession(Base):
    """Chat sessions with the AI doctor"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Session information
    session_name = Column(String(255), nullable=True)  # user-defined name
    is_active = Column(Boolean, default=True)
    
    # Health context for this session
    health_context = Column(JSON, nullable=True)  # relevant health data for context
    
    # Session metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserProfile", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Individual chat messages"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Message metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    tokens_used = Column(Integer, nullable=True)  # for cost tracking
    model_used = Column(String(100), nullable=True)  # which AI model was used
    
    # Health context used for this message
    health_context_used = Column(JSON, nullable=True)  # which health data was referenced
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class DataSyncLog(Base):
    """Log of data synchronization activities"""
    __tablename__ = "data_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Sync information
    sync_type = Column(String(50), nullable=False)  # wearable, lab_results, manual_entry
    source = Column(String(100), nullable=False)  # apple_watch, lab_corp, manual, etc.
    
    # Sync status and results
    status = Column(String(50), nullable=False)  # started, completed, failed, partial
    records_processed = Column(Integer, default=0)
    records_successful = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Sync metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Data summary
    data_summary = Column(JSON, nullable=True)  # summary of what was synced


class HealthDataLake(Base):
    """Central data lake for all health information (JSON storage)"""
    __tablename__ = "health_data_lake"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Data categorization
    data_type = Column(String(100), nullable=False)  # lab_results, wearable, manual_entry, etc.
    data_source = Column(String(100), nullable=False)  # lab_corp, apple_watch, user_input, etc.
    
    # Data content
    raw_data = Column(JSON, nullable=False)  # original data
    processed_data = Column(JSON, nullable=True)  # cleaned/processed data
    data_metadata = Column(JSON, nullable=True)  # timestamps, confidence, etc.
    
    # Data lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # for temporary data
    
    # Data quality
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in data quality
    validation_status = Column(String(50), default="pending")  # pending, validated, failed
    
    # Search and indexing
    tags = Column(JSON, nullable=True)  # for easy searching/filtering
    search_vector = Column(Text, nullable=True)  # for full-text search
