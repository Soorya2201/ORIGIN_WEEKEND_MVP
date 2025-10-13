"""
Data Processing Pipeline for MVP
Processes and normalizes health data from various sources
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.db.models_mvp import HealthDataLake, UserProfile
from app.schemas.mvp import HealthDataLakeCreate

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    """Pipeline for processing and normalizing health data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_lab_results(self, user_id: str, lab_data: Dict[str, Any]) -> HealthDataLakeCreate:
        """
        Process lab results and store in data lake
        """
        logger.info(f"Processing lab results for user {user_id}")
        
        # Extract and normalize lab data
        processed_labs = self._normalize_lab_results(lab_data)
        
        # Calculate confidence score
        confidence_score = self._calculate_lab_confidence(processed_labs)
        
        # Generate tags for searchability
        tags = self._generate_lab_tags(processed_labs)
        
        # Create data lake entry
        data_lake_entry = HealthDataLakeCreate(
            user_id=user_id,
            data_type="lab_results",
            data_source=lab_data.get("source", "unknown"),
            raw_data=lab_data,
            processed_data=processed_labs,
            data_metadata={
                "processing_timestamp": datetime.utcnow().isoformat(),
                "total_labs": len(processed_labs.get("labs", [])),
                "processing_version": "1.0"
            },
            confidence_score=confidence_score,
            validation_status="validated",
            tags=tags
        )
        
        return data_lake_entry
    
    async def process_wearable_data(self, user_id: str, wearable_data: Dict[str, Any]) -> HealthDataLakeCreate:
        """
        Process wearable data and store in data lake
        """
        logger.info(f"Processing wearable data for user {user_id}")
        
        # Extract and normalize wearable data
        processed_data = self._normalize_wearable_data(wearable_data)
        
        # Calculate confidence score
        confidence_score = self._calculate_wearable_confidence(processed_data)
        
        # Generate tags
        tags = self._generate_wearable_tags(processed_data)
        
        # Create data lake entry
        data_lake_entry = HealthDataLakeCreate(
            user_id=user_id,
            data_type="wearable",
            data_source=wearable_data.get("device_type", "unknown"),
            raw_data=wearable_data,
            processed_data=processed_data,
            data_metadata={
                "processing_timestamp": datetime.utcnow().isoformat(),
                "device_id": wearable_data.get("device_id"),
                "sync_timestamp": wearable_data.get("sync_timestamp"),
                "processing_version": "1.0"
            },
            confidence_score=confidence_score,
            validation_status="validated",
            tags=tags
        )
        
        return data_lake_entry
    
    async def process_manual_entry(self, user_id: str, manual_data: Dict[str, Any]) -> HealthDataLakeCreate:
        """
        Process manually entered health data
        """
        logger.info(f"Processing manual entry for user {user_id}")
        
        # Validate and normalize manual data
        processed_data = self._normalize_manual_data(manual_data)
        
        # Calculate confidence score (lower for manual entries)
        confidence_score = 0.7  # Manual entries have lower confidence
        
        # Generate tags
        tags = self._generate_manual_tags(processed_data)
        
        # Create data lake entry
        data_lake_entry = HealthDataLakeCreate(
            user_id=user_id,
            data_type="manual_entry",
            data_source="user_input",
            raw_data=manual_data,
            processed_data=processed_data,
            data_metadata={
                "processing_timestamp": datetime.utcnow().isoformat(),
                "entry_type": manual_data.get("entry_type", "general"),
                "processing_version": "1.0"
            },
            confidence_score=confidence_score,
            validation_status="validated",
            tags=tags
        )
        
        return data_lake_entry
    
    def _normalize_lab_results(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize lab results data"""
        normalized = {
            "labs": [],
            "metadata": {
                "collection_date": None,
                "lab_name": None,
                "total_tests": 0
            }
        }
        
        # Extract lab results
        labs = lab_data.get("labs", [])
        for lab in labs:
            normalized_lab = {
                "analyte": self._normalize_analyte_name(lab.get("analyte", "")),
                "value": self._normalize_lab_value(lab.get("value")),
                "unit": self._normalize_unit(lab.get("unit", "")),
                "reference_range": {
                    "low": lab.get("ref_low"),
                    "high": lab.get("ref_high")
                },
                "status": self._determine_lab_status(lab),
                "collection_date": lab.get("observed_at"),
                "loinc_code": lab.get("loinc_code")
            }
            normalized["labs"].append(normalized_lab)
        
        # Extract metadata
        normalized["metadata"]["collection_date"] = lab_data.get("collection_date")
        normalized["metadata"]["lab_name"] = lab_data.get("lab_name", "Unknown")
        normalized["metadata"]["total_tests"] = len(normalized["labs"])
        
        return normalized
    
    def _normalize_wearable_data(self, wearable_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize wearable data"""
        normalized = {
            "device_info": wearable_data.get("device_info", {}),
            "metrics": {},
            "data_types": []
        }
        
        # Process different types of wearable data
        data = wearable_data.get("data", {})
        
        # Process steps data
        if "steps" in data:
            steps_data = data["steps"]
            if steps_data:
                total_steps = sum(day.get("steps", 0) for day in steps_data)
                avg_steps = total_steps / len(steps_data)
                normalized["metrics"]["steps"] = {
                    "total_steps": total_steps,
                    "average_daily_steps": avg_steps,
                    "days_tracked": len(steps_data),
                    "latest_daily_steps": steps_data[-1].get("steps", 0) if steps_data else 0
                }
                normalized["data_types"].append("steps")
        
        # Process heart rate data
        if "heart_rate" in data:
            hr_data = data["heart_rate"]
            if hr_data:
                bpm_values = [reading.get("bpm", 0) for reading in hr_data if reading.get("bpm")]
                if bpm_values:
                    avg_hr = sum(bpm_values) / len(bpm_values)
                    min_hr = min(bpm_values)
                    max_hr = max(bpm_values)
                    normalized["metrics"]["heart_rate"] = {
                        "average_bpm": avg_hr,
                        "min_bpm": min_hr,
                        "max_bpm": max_hr,
                        "readings_count": len(bpm_values)
                    }
                    normalized["data_types"].append("heart_rate")
        
        # Process sleep data
        if "sleep" in data:
            sleep_data = data["sleep"]
            if sleep_data:
                sleep_hours = [day.get("duration_hours", 0) for day in sleep_data]
                efficiency_scores = [day.get("efficiency", 0) for day in sleep_data]
                
                if sleep_hours:
                    avg_sleep_hours = sum(sleep_hours) / len(sleep_hours)
                    avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
                    
                    normalized["metrics"]["sleep"] = {
                        "average_sleep_hours": avg_sleep_hours,
                        "average_efficiency": avg_efficiency,
                        "days_tracked": len(sleep_data),
                        "latest_sleep_hours": sleep_hours[-1] if sleep_hours else 0
                    }
                    normalized["data_types"].append("sleep")
        
        # Process calories data
        if "calories" in data:
            calories_data = data["calories"]
            if calories_data:
                active_calories = [day.get("active_calories", 0) for day in calories_data]
                total_calories = [day.get("total_calories", 0) for day in calories_data]
                
                if active_calories and total_calories:
                    avg_active_calories = sum(active_calories) / len(active_calories)
                    avg_total_calories = sum(total_calories) / len(total_calories)
                    
                    normalized["metrics"]["calories"] = {
                        "average_active_calories": avg_active_calories,
                        "average_total_calories": avg_total_calories,
                        "days_tracked": len(calories_data)
                    }
                    normalized["data_types"].append("calories")
        
        return normalized
    
    def _normalize_manual_data(self, manual_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize manually entered data"""
        normalized = {
            "entry_type": manual_data.get("entry_type", "general"),
            "data": {},
            "timestamp": manual_data.get("timestamp", datetime.utcnow().isoformat())
        }
        
        # Process different types of manual entries
        entry_type = manual_data.get("entry_type", "general")
        
        if entry_type == "symptoms":
            normalized["data"] = {
                "symptoms": manual_data.get("symptoms", []),
                "severity": manual_data.get("severity"),
                "duration": manual_data.get("duration"),
                "notes": manual_data.get("notes", "")
            }
        elif entry_type == "medications":
            normalized["data"] = {
                "medications": manual_data.get("medications", []),
                "dosages": manual_data.get("dosages", []),
                "frequency": manual_data.get("frequency", []),
                "notes": manual_data.get("notes", "")
            }
        elif entry_type == "vitals":
            normalized["data"] = {
                "blood_pressure": manual_data.get("blood_pressure"),
                "heart_rate": manual_data.get("heart_rate"),
                "temperature": manual_data.get("temperature"),
                "weight": manual_data.get("weight"),
                "notes": manual_data.get("notes", "")
            }
        else:
            # General entry
            normalized["data"] = manual_data.get("data", {})
        
        return normalized
    
    def _normalize_analyte_name(self, analyte: str) -> str:
        """Normalize analyte names to standard format"""
        analyte_lower = analyte.lower().strip()
        
        # Common normalizations
        normalizations = {
            "ldl-c": "LDL Cholesterol",
            "ldl cholesterol": "LDL Cholesterol",
            "hdl-c": "HDL Cholesterol",
            "hdl cholesterol": "HDL Cholesterol",
            "total cholesterol": "Total Cholesterol",
            "hba1c": "HbA1c",
            "hemoglobin a1c": "HbA1c",
            "glucose": "Glucose",
            "fasting glucose": "Glucose",
            "tsh": "TSH",
            "thyroid stimulating hormone": "TSH",
            "ferritin": "Ferritin",
            "vitamin d": "Vitamin D",
            "25-hydroxyvitamin d": "Vitamin D",
            "b12": "Vitamin B12",
            "vitamin b12": "Vitamin B12"
        }
        
        return normalizations.get(analyte_lower, analyte.title())
    
    def _normalize_lab_value(self, value: Any) -> Optional[float]:
        """Normalize lab values to float"""
        if value is None:
            return None
        
        try:
            # Handle string values
            if isinstance(value, str):
                # Remove common prefixes/suffixes
                value = value.replace("<", "").replace(">", "").replace("=", "").strip()
                return float(value)
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def _normalize_unit(self, unit: str) -> str:
        """Normalize units to standard format"""
        unit_lower = unit.lower().strip()
        
        # Common unit normalizations
        normalizations = {
            "mg/dl": "mg/dL",
            "mg/dl": "mg/dL",
            "mmol/l": "mmol/L",
            "ng/ml": "ng/mL",
            "pg/ml": "pg/mL",
            "iu/ml": "IU/mL",
            "mcg/dl": "mcg/dL",
            "ug/dl": "mcg/dL"
        }
        
        return normalizations.get(unit_lower, unit)
    
    def _determine_lab_status(self, lab: Dict[str, Any]) -> str:
        """Determine if lab result is normal, high, or low"""
        value = self._normalize_lab_value(lab.get("value"))
        ref_low = lab.get("ref_low")
        ref_high = lab.get("ref_high")
        
        if value is None or ref_low is None or ref_high is None:
            return "unknown"
        
        if value < ref_low:
            return "low"
        elif value > ref_high:
            return "high"
        else:
            return "normal"
    
    def _calculate_lab_confidence(self, processed_labs: Dict[str, Any]) -> float:
        """Calculate confidence score for lab results"""
        labs = processed_labs.get("labs", [])
        if not labs:
            return 0.0
        
        confidence = 0.8  # Base confidence for lab results
        
        # Boost confidence for complete data
        complete_labs = sum(1 for lab in labs if lab.get("value") is not None and lab.get("unit"))
        if complete_labs == len(labs):
            confidence += 0.1
        
        # Boost confidence for reference ranges
        labs_with_refs = sum(1 for lab in labs if lab.get("reference_range", {}).get("low") is not None)
        if labs_with_refs > 0:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_wearable_confidence(self, processed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for wearable data"""
        confidence = 0.9  # High confidence for wearable data
        
        # Check data completeness
        metrics = processed_data.get("metrics", {})
        data_types = processed_data.get("data_types", [])
        
        if len(data_types) >= 3:  # Multiple data types
            confidence += 0.05
        
        if "sleep" in metrics and metrics["sleep"].get("days_tracked", 0) >= 7:
            confidence += 0.05  # Good sleep tracking
        
        return min(1.0, confidence)
    
    def _generate_lab_tags(self, processed_labs: Dict[str, Any]) -> List[str]:
        """Generate tags for lab results"""
        tags = ["lab_results", "medical"]
        
        labs = processed_labs.get("labs", [])
        for lab in labs:
            analyte = lab.get("analyte", "").lower()
            
            if "cholesterol" in analyte:
                tags.append("cardiovascular")
            elif "glucose" in analyte or "hba1c" in analyte:
                tags.append("diabetes")
            elif "thyroid" in analyte or "tsh" in analyte:
                tags.append("thyroid")
            elif "vitamin" in analyte:
                tags.append("nutrition")
            elif "iron" in analyte or "ferritin" in analyte:
                tags.append("anemia")
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_wearable_tags(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate tags for wearable data"""
        tags = ["wearable", "fitness"]
        
        data_types = processed_data.get("data_types", [])
        for data_type in data_types:
            if data_type == "steps":
                tags.append("activity")
            elif data_type == "heart_rate":
                tags.append("cardiovascular")
            elif data_type == "sleep":
                tags.append("sleep")
            elif data_type == "calories":
                tags.append("nutrition")
        
        return list(set(tags))
    
    def _generate_manual_tags(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate tags for manual entries"""
        tags = ["manual_entry", "user_input"]
        
        entry_type = processed_data.get("entry_type", "general")
        if entry_type == "symptoms":
            tags.append("symptoms")
        elif entry_type == "medications":
            tags.append("medications")
        elif entry_type == "vitals":
            tags.append("vitals")
        
        return list(set(tags))
