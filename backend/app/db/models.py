"""Database models for the lab backend."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Person(Base):
    """Person entity - represents a human being."""
    
    __tablename__ = "person"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True)
    name = Column(String(255), nullable=True)
    dob = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="person", uselist=False)
    lab_results = relationship("LabResult", back_populates="person")
    insights = relationship("Insight", back_populates="person")


class Patient(Base):
    """Patient entity - extends Person with medical data."""
    
    __tablename__ = "patient"
    
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id"), primary_key=True)
    sex_at_birth = Column(String(10), nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    person = relationship("Person", back_populates="patient")


class File(Base):
    """File entity - represents uploaded files."""
    
    __tablename__ = "file"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket_key = Column(String(255), unique=True, nullable=False)
    mime = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("person.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lab_results = relationship("LabResult", back_populates="file")


class LabResult(Base):
    """Lab result entity - represents individual lab measurements."""
    
    __tablename__ = "lab_result"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id"), nullable=False)
    analyte_name = Column(String(255), nullable=False)
    value_numeric = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    ref_low = Column(Float, nullable=True)
    ref_high = Column(Float, nullable=True)
    loinc_code = Column(String(20), nullable=True)
    observed_at = Column(DateTime, nullable=False)
    source = Column(String(100), nullable=False, default="gemini")
    file_id = Column(UUID(as_uuid=True), ForeignKey("file.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    person = relationship("Person", back_populates="lab_results")
    file = relationship("File", back_populates="lab_results")


class Insight(Base):
    """Insight entity - represents generated insights from lab results."""
    
    __tablename__ = "insight"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.id"), nullable=False)
    kind = Column(String(100), nullable=False)  # e.g., "rule", "llm_summary"
    title = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    engine = Column(String(100), nullable=False)  # e.g., "rule", "gemini"
    inputs = Column(JSON, nullable=True)  # JSON array of lab_result IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="active")
    
    # Relationships
    person = relationship("Person", back_populates="insights")
