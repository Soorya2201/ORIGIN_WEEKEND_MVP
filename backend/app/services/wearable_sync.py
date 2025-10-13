"""
Wearable Data Sync Service
Handles syncing data from various wearable devices
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.db.models_mvp import WearableData, DataSyncLog, HealthDataLake, UserProfile
from app.schemas.mvp import WearableDataCreate, WearableSyncRequest, WearableSyncResponse

logger = logging.getLogger(__name__)


class WearableSyncService:
    """Service for syncing wearable device data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_wearable_data(self, user_id: str, sync_request: WearableSyncRequest) -> WearableSyncResponse:
        """
        Sync data from a wearable device
        """
        logger.info(f"Starting wearable sync for user {user_id}, device {sync_request.device_type}")
        
        # Create sync log entry
        sync_log = DataSyncLog(
            user_id=user_id,
            sync_type="wearable",
            source=sync_request.device_type,
            status="started",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            # Get or create wearable device record
            wearable_device = self._get_or_create_wearable_device(user_id, sync_request)
            
            # Update sync status
            wearable_device.sync_status = "syncing"
            self.db.commit()
            
            # Sync data based on device type
            if sync_request.device_type == "apple_watch":
                sync_result = await self._sync_apple_watch_data(wearable_device, sync_request)
            elif sync_request.device_type == "fitbit":
                sync_result = await self._sync_fitbit_data(wearable_device, sync_request)
            elif sync_request.device_type == "garmin":
                sync_result = await self._sync_garmin_data(wearable_device, sync_request)
            else:
                raise ValueError(f"Unsupported device type: {sync_request.device_type}")
            
            # Update device with sync results
            wearable_device.sync_status = "completed"
            wearable_device.last_sync_at = datetime.utcnow()
            wearable_device.raw_data = sync_result.get('raw_data')
            wearable_device.processed_data = sync_result.get('processed_data')
            wearable_device.data_types = sync_result.get('data_types', [])
            
            # Store data in health data lake
            await self._store_in_data_lake(user_id, sync_request.device_type, sync_result)
            
            # Update sync log
            sync_log.status = "completed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            sync_log.records_processed = sync_result.get('records_processed', 0)
            sync_log.records_successful = sync_result.get('records_successful', 0)
            sync_log.records_failed = sync_result.get('records_failed', 0)
            sync_log.data_summary = sync_result.get('data_summary', {})
            
            self.db.commit()
            
            return WearableSyncResponse(
                sync_id=sync_log.id,
                status="completed",
                records_processed=sync_log.records_processed,
                records_successful=sync_log.records_successful,
                records_failed=sync_log.records_failed,
                sync_duration_seconds=sync_log.duration_seconds
            )
            
        except Exception as e:
            logger.error(f"Wearable sync failed: {str(e)}")
            
            # Update sync log with error
            sync_log.status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
            sync_log.error_message = str(e)
            sync_log.error_details = {"exception_type": type(e).__name__}
            
            # Update device status
            if 'wearable_device' in locals():
                wearable_device.sync_status = "failed"
            
            self.db.commit()
            
            return WearableSyncResponse(
                sync_id=sync_log.id,
                status="failed",
                records_processed=0,
                records_successful=0,
                records_failed=0,
                sync_duration_seconds=sync_log.duration_seconds,
                error_message=str(e)
            )
    
    def _get_or_create_wearable_device(self, user_id: str, sync_request: WearableSyncRequest) -> WearableData:
        """Get existing wearable device or create new one"""
        existing_device = self.db.query(WearableData).filter(
            WearableData.user_id == user_id,
            WearableData.device_type == sync_request.device_type,
            WearableData.device_id == sync_request.device_id
        ).first()
        
        if existing_device:
            return existing_device
        
        # Create new device
        new_device = WearableData(
            user_id=user_id,
            device_type=sync_request.device_type,
            device_id=sync_request.device_id,
            device_name=f"{sync_request.device_type.title()} Device",
            sync_frequency_hours=24
        )
        
        self.db.add(new_device)
        self.db.commit()
        self.db.refresh(new_device)
        
        return new_device
    
    async def _sync_apple_watch_data(self, device: WearableData, sync_request: WearableSyncRequest) -> Dict[str, Any]:
        """Sync data from Apple Watch (mock implementation)"""
        logger.info(f"Syncing Apple Watch data for device {device.device_id}")
        
        # Mock Apple Watch data sync
        # In a real implementation, this would use HealthKit API or Apple Health app data
        
        await asyncio.sleep(1)  # Simulate API call
        
        # Mock data structure
        raw_data = {
            "device_info": {
                "device_type": "apple_watch",
                "device_id": device.device_id,
                "model": "Apple Watch Series 9",
                "os_version": "10.0"
            },
            "sync_timestamp": datetime.utcnow().isoformat(),
            "data": {
                "steps": [
                    {"date": "2024-01-15", "steps": 8500, "distance_km": 6.2},
                    {"date": "2024-01-14", "steps": 9200, "distance_km": 6.8},
                    {"date": "2024-01-13", "steps": 7800, "distance_km": 5.9}
                ],
                "heart_rate": [
                    {"timestamp": "2024-01-15T10:00:00Z", "bpm": 72, "zone": "resting"},
                    {"timestamp": "2024-01-15T10:05:00Z", "bpm": 75, "zone": "resting"},
                    {"timestamp": "2024-01-15T10:10:00Z", "bpm": 78, "zone": "resting"}
                ],
                "sleep": [
                    {
                        "date": "2024-01-15",
                        "bedtime": "2024-01-15T23:00:00Z",
                        "wake_time": "2024-01-16T07:00:00Z",
                        "duration_hours": 8.0,
                        "efficiency": 87.5,
                        "deep_sleep_percentage": 18.2,
                        "rem_sleep_percentage": 22.1,
                        "light_sleep_percentage": 59.7
                    }
                ],
                "calories": [
                    {"date": "2024-01-15", "active_calories": 450, "resting_calories": 1800, "total_calories": 2250},
                    {"date": "2024-01-14", "active_calories": 520, "resting_calories": 1780, "total_calories": 2300}
                ],
                "workouts": [
                    {
                        "date": "2024-01-15",
                        "type": "running",
                        "duration_minutes": 30,
                        "calories_burned": 280,
                        "average_heart_rate": 145
                    }
                ]
            }
        }
        
        # Process the data
        processed_data = self._process_apple_watch_data(raw_data)
        
        return {
            "raw_data": raw_data,
            "processed_data": processed_data,
            "data_types": ["steps", "heart_rate", "sleep", "calories", "workouts"],
            "records_processed": 10,
            "records_successful": 10,
            "records_failed": 0,
            "data_summary": {
                "days_of_data": 3,
                "total_steps": 25500,
                "average_sleep_hours": 8.0,
                "total_workouts": 1
            }
        }
    
    async def _sync_fitbit_data(self, device: WearableData, sync_request: WearableSyncRequest) -> Dict[str, Any]:
        """Sync data from Fitbit (mock implementation)"""
        logger.info(f"Syncing Fitbit data for device {device.device_id}")
        
        await asyncio.sleep(1)  # Simulate API call
        
        # Mock Fitbit data structure
        raw_data = {
            "device_info": {
                "device_type": "fitbit",
                "device_id": device.device_id,
                "model": "Fitbit Charge 5",
                "firmware_version": "1.0.0"
            },
            "sync_timestamp": datetime.utcnow().isoformat(),
            "data": {
                "steps": [
                    {"date": "2024-01-15", "steps": 8200, "distance_km": 6.1},
                    {"date": "2024-01-14", "steps": 9500, "distance_km": 7.0}
                ],
                "heart_rate": [
                    {"timestamp": "2024-01-15T10:00:00Z", "bpm": 70, "zone": "fat_burn"},
                    {"timestamp": "2024-01-15T10:05:00Z", "bpm": 73, "zone": "fat_burn"}
                ],
                "sleep": [
                    {
                        "date": "2024-01-15",
                        "bedtime": "2024-01-15T22:30:00Z",
                        "wake_time": "2024-01-16T06:30:00Z",
                        "duration_hours": 8.0,
                        "efficiency": 85.0,
                        "deep_sleep_percentage": 20.0,
                        "rem_sleep_percentage": 25.0,
                        "light_sleep_percentage": 55.0
                    }
                ],
                "calories": [
                    {"date": "2024-01-15", "active_calories": 420, "resting_calories": 1750, "total_calories": 2170}
                ]
            }
        }
        
        processed_data = self._process_fitbit_data(raw_data)
        
        return {
            "raw_data": raw_data,
            "processed_data": processed_data,
            "data_types": ["steps", "heart_rate", "sleep", "calories"],
            "records_processed": 8,
            "records_successful": 8,
            "records_failed": 0,
            "data_summary": {
                "days_of_data": 2,
                "total_steps": 17700,
                "average_sleep_hours": 8.0,
                "total_workouts": 0
            }
        }
    
    async def _sync_garmin_data(self, device: WearableData, sync_request: WearableSyncRequest) -> Dict[str, Any]:
        """Sync data from Garmin (mock implementation)"""
        logger.info(f"Syncing Garmin data for device {device.device_id}")
        
        await asyncio.sleep(1)  # Simulate API call
        
        # Mock Garmin data structure
        raw_data = {
            "device_info": {
                "device_type": "garmin",
                "device_id": device.device_id,
                "model": "Garmin Venu 3",
                "firmware_version": "8.0.0"
            },
            "sync_timestamp": datetime.utcnow().isoformat(),
            "data": {
                "steps": [
                    {"date": "2024-01-15", "steps": 8800, "distance_km": 6.5}
                ],
                "heart_rate": [
                    {"timestamp": "2024-01-15T10:00:00Z", "bpm": 68, "zone": "aerobic"},
                    {"timestamp": "2024-01-15T10:05:00Z", "bpm": 71, "zone": "aerobic"}
                ],
                "sleep": [
                    {
                        "date": "2024-01-15",
                        "bedtime": "2024-01-15T23:15:00Z",
                        "wake_time": "2024-01-16T07:15:00Z",
                        "duration_hours": 8.0,
                        "efficiency": 90.0,
                        "deep_sleep_percentage": 22.0,
                        "rem_sleep_percentage": 20.0,
                        "light_sleep_percentage": 58.0
                    }
                ],
                "activities": [
                    {
                        "date": "2024-01-15",
                        "type": "cycling",
                        "duration_minutes": 45,
                        "calories_burned": 350,
                        "average_heart_rate": 140,
                        "distance_km": 15.2
                    }
                ]
            }
        }
        
        processed_data = self._process_garmin_data(raw_data)
        
        return {
            "raw_data": raw_data,
            "processed_data": processed_data,
            "data_types": ["steps", "heart_rate", "sleep", "activities"],
            "records_processed": 6,
            "records_successful": 6,
            "records_failed": 0,
            "data_summary": {
                "days_of_data": 1,
                "total_steps": 8800,
                "average_sleep_hours": 8.0,
                "total_activities": 1
            }
        }
    
    def _process_apple_watch_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize Apple Watch data"""
        processed = {
            "device_type": "apple_watch",
            "sync_timestamp": raw_data["sync_timestamp"],
            "metrics": {}
        }
        
        data = raw_data.get("data", {})
        
        # Process steps data
        if "steps" in data:
            steps_data = data["steps"]
            total_steps = sum(day["steps"] for day in steps_data)
            avg_steps = total_steps / len(steps_data) if steps_data else 0
            processed["metrics"]["steps"] = {
                "total_steps": total_steps,
                "average_daily_steps": avg_steps,
                "days_tracked": len(steps_data)
            }
        
        # Process sleep data
        if "sleep" in data:
            sleep_data = data["sleep"]
            if sleep_data:
                avg_sleep_hours = sum(day["duration_hours"] for day in sleep_data) / len(sleep_data)
                avg_efficiency = sum(day["efficiency"] for day in sleep_data) / len(sleep_data)
                processed["metrics"]["sleep"] = {
                    "average_sleep_hours": avg_sleep_hours,
                    "average_efficiency": avg_efficiency,
                    "days_tracked": len(sleep_data)
                }
        
        # Process heart rate data
        if "heart_rate" in data:
            hr_data = data["heart_rate"]
            if hr_data:
                avg_hr = sum(reading["bpm"] for reading in hr_data) / len(hr_data)
                processed["metrics"]["heart_rate"] = {
                    "average_bpm": avg_hr,
                    "readings_count": len(hr_data)
                }
        
        return processed
    
    def _process_fitbit_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize Fitbit data"""
        processed = {
            "device_type": "fitbit",
            "sync_timestamp": raw_data["sync_timestamp"],
            "metrics": {}
        }
        
        data = raw_data.get("data", {})
        
        # Process steps data
        if "steps" in data:
            steps_data = data["steps"]
            total_steps = sum(day["steps"] for day in steps_data)
            avg_steps = total_steps / len(steps_data) if steps_data else 0
            processed["metrics"]["steps"] = {
                "total_steps": total_steps,
                "average_daily_steps": avg_steps,
                "days_tracked": len(steps_data)
            }
        
        # Process sleep data
        if "sleep" in data:
            sleep_data = data["sleep"]
            if sleep_data:
                avg_sleep_hours = sum(day["duration_hours"] for day in sleep_data) / len(sleep_data)
                avg_efficiency = sum(day["efficiency"] for day in sleep_data) / len(sleep_data)
                processed["metrics"]["sleep"] = {
                    "average_sleep_hours": avg_sleep_hours,
                    "average_efficiency": avg_efficiency,
                    "days_tracked": len(sleep_data)
                }
        
        return processed
    
    def _process_garmin_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize Garmin data"""
        processed = {
            "device_type": "garmin",
            "sync_timestamp": raw_data["sync_timestamp"],
            "metrics": {}
        }
        
        data = raw_data.get("data", {})
        
        # Process steps data
        if "steps" in data:
            steps_data = data["steps"]
            total_steps = sum(day["steps"] for day in steps_data)
            avg_steps = total_steps / len(steps_data) if steps_data else 0
            processed["metrics"]["steps"] = {
                "total_steps": total_steps,
                "average_daily_steps": avg_steps,
                "days_tracked": len(steps_data)
            }
        
        # Process activities data
        if "activities" in data:
            activities_data = data["activities"]
            total_activities = len(activities_data)
            total_calories_burned = sum(activity["calories_burned"] for activity in activities_data)
            processed["metrics"]["activities"] = {
                "total_activities": total_activities,
                "total_calories_burned": total_calories_burned,
                "days_tracked": len(set(activity["date"] for activity in activities_data))
            }
        
        return processed
    
    async def _store_in_data_lake(self, user_id: str, device_type: str, sync_result: Dict[str, Any]):
        """Store synced data in the health data lake"""
        data_lake_entry = HealthDataLake(
            user_id=user_id,
            data_type="wearable",
            data_source=device_type,
            raw_data=sync_result["raw_data"],
            processed_data=sync_result["processed_data"],
            data_metadata={
                "sync_timestamp": datetime.utcnow().isoformat(),
                "records_processed": sync_result.get("records_processed", 0),
                "records_successful": sync_result.get("records_successful", 0),
                "records_failed": sync_result.get("records_failed", 0)
            },
            confidence_score=0.9,  # High confidence for wearable data
            validation_status="validated",
            tags=["wearable", device_type, "automated_sync"]
        )
        
        self.db.add(data_lake_entry)
        self.db.commit()
        
        logger.info(f"Stored {device_type} data in health data lake for user {user_id}")
    
    def get_sync_status(self, user_id: str) -> List[Dict[str, Any]]:
        """Get sync status for all user's wearable devices"""
        devices = self.db.query(WearableData).filter(WearableData.user_id == user_id).all()
        
        status_list = []
        for device in devices:
            status_list.append({
                "device_id": device.device_id,
                "device_type": device.device_type,
                "device_name": device.device_name,
                "sync_status": device.sync_status,
                "last_sync_at": device.last_sync_at,
                "data_types": device.data_types,
                "sync_frequency_hours": device.sync_frequency_hours
            })
        
        return status_list
