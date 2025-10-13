"""
Health Assessment Engine for MVP Dashboard
Generates health scores and ratings based on available data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from app.db.models_mvp import HealthAssessment, HealthDataLake, UserProfile
from app.schemas.mvp import HealthAssessmentCreate, HealthAssessmentUpdate

logger = logging.getLogger(__name__)


class HealthAssessmentEngine:
    """Engine for calculating health assessments and scores"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_health_assessment(self, user_id: str) -> HealthAssessmentCreate:
        """
        Calculate comprehensive health assessment for a user
        """
        logger.info(f"Calculating health assessment for user {user_id}")
        
        # Get user's recent health data
        health_data = self._get_user_health_data(user_id)
        
        # Calculate individual scores
        sleep_score, sleep_details = self._calculate_sleep_score(health_data)
        hydration_score, hydration_details = self._calculate_hydration_score(health_data)
        vitamin_score, vitamin_details = self._calculate_vitamin_score(health_data)
        caloric_score, caloric_details = self._calculate_caloric_score(health_data)
        
        # Calculate overall health score
        overall_score = self._calculate_overall_score(
            sleep_score, hydration_score, vitamin_score, caloric_score
        )
        
        # Determine data sources used
        data_sources = self._get_data_sources(health_data)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(health_data, data_sources)
        
        return HealthAssessmentCreate(
            user_id=user_id,
            sleep_score=sleep_score,
            hydration_score=hydration_score,
            vitamin_score=vitamin_score,
            caloric_intake_score=caloric_score,
            overall_health_score=overall_score,
            sleep_details=sleep_details,
            hydration_details=hydration_details,
            vitamin_details=vitamin_details,
            caloric_details=caloric_details,
            data_sources=data_sources,
            confidence_score=confidence_score
        )
    
    def _get_user_health_data(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get user's health data from the data lake"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        data_lake_records = self.db.query(HealthDataLake).filter(
            HealthDataLake.user_id == user_id,
            HealthDataLake.created_at >= cutoff_date
        ).all()
        
        health_data = {
            'wearable_data': [],
            'lab_results': [],
            'manual_entries': [],
            'sleep_data': [],
            'hydration_data': [],
            'nutrition_data': [],
            'activity_data': []
        }
        
        for record in data_lake_records:
            if record.data_type == 'wearable':
                health_data['wearable_data'].append(record.raw_data)
            elif record.data_type == 'lab_results':
                health_data['lab_results'].append(record.raw_data)
            elif record.data_type == 'manual_entry':
                health_data['manual_entries'].append(record.raw_data)
            
            # Categorize by content
            if 'sleep' in record.raw_data.get('data_types', []):
                health_data['sleep_data'].append(record.raw_data)
            if 'hydration' in record.raw_data.get('data_types', []):
                health_data['hydration_data'].append(record.raw_data)
            if 'nutrition' in record.raw_data.get('data_types', []):
                health_data['nutrition_data'].append(record.raw_data)
            if 'activity' in record.raw_data.get('data_types', []):
                health_data['activity_data'].append(record.raw_data)
        
        return health_data
    
    def _calculate_sleep_score(self, health_data: Dict[str, Any]) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculate sleep quality score (0-100)"""
        sleep_data = health_data.get('sleep_data', [])
        wearable_data = health_data.get('wearable_data', [])
        
        if not sleep_data and not wearable_data:
            return None, {'message': 'No sleep data available'}
        
        # Extract sleep metrics
        total_sleep_hours = []
        sleep_efficiency = []
        deep_sleep_percentage = []
        rem_sleep_percentage = []
        
        for data in sleep_data + wearable_data:
            if 'sleep' in data:
                sleep_info = data['sleep']
                if 'duration_hours' in sleep_info:
                    total_sleep_hours.append(sleep_info['duration_hours'])
                if 'efficiency' in sleep_info:
                    sleep_efficiency.append(sleep_info['efficiency'])
                if 'deep_sleep_percentage' in sleep_info:
                    deep_sleep_percentage.append(sleep_info['deep_sleep_percentage'])
                if 'rem_sleep_percentage' in sleep_info:
                    rem_sleep_percentage.append(sleep_info['rem_sleep_percentage'])
        
        if not total_sleep_hours:
            return None, {'message': 'Insufficient sleep data'}
        
        # Calculate average metrics
        avg_sleep_hours = sum(total_sleep_hours) / len(total_sleep_hours)
        avg_efficiency = sum(sleep_efficiency) / len(sleep_efficiency) if sleep_efficiency else 85
        avg_deep_sleep = sum(deep_sleep_percentage) / len(deep_sleep_percentage) if deep_sleep_percentage else 20
        avg_rem_sleep = sum(rem_sleep_percentage) / len(rem_sleep_percentage) if rem_sleep_percentage else 20
        
        # Calculate score based on sleep recommendations
        # Optimal: 7-9 hours, >85% efficiency, 15-20% deep sleep, 20-25% REM
        duration_score = min(100, max(0, 100 - abs(avg_sleep_hours - 8) * 12.5))  # 8 hours optimal
        efficiency_score = min(100, avg_efficiency)
        deep_sleep_score = min(100, max(0, 100 - abs(avg_deep_sleep - 17.5) * 4))  # 17.5% optimal
        rem_sleep_score = min(100, max(0, 100 - abs(avg_rem_sleep - 22.5) * 4))  # 22.5% optimal
        
        # Weighted average
        sleep_score = (duration_score * 0.4 + efficiency_score * 0.3 + 
                      deep_sleep_score * 0.15 + rem_sleep_score * 0.15)
        
        details = {
            'average_sleep_hours': round(avg_sleep_hours, 1),
            'average_efficiency': round(avg_efficiency, 1),
            'average_deep_sleep_percentage': round(avg_deep_sleep, 1),
            'average_rem_sleep_percentage': round(avg_rem_sleep, 1),
            'data_points': len(total_sleep_hours),
            'recommendations': self._get_sleep_recommendations(avg_sleep_hours, avg_efficiency)
        }
        
        return round(sleep_score, 1), details
    
    def _calculate_hydration_score(self, health_data: Dict[str, Any]) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculate hydration score (0-100)"""
        hydration_data = health_data.get('hydration_data', [])
        wearable_data = health_data.get('wearable_data', [])
        
        if not hydration_data and not wearable_data:
            return None, {'message': 'No hydration data available'}
        
        # Extract hydration metrics
        water_intake_ml = []
        urine_color_scores = []
        activity_levels = []
        
        for data in hydration_data + wearable_data:
            if 'hydration' in data:
                hydration_info = data['hydration']
                if 'water_intake_ml' in hydration_info:
                    water_intake_ml.append(hydration_info['water_intake_ml'])
                if 'urine_color_score' in hydration_info:
                    urine_color_scores.append(hydration_info['urine_color_score'])
            if 'activity' in data:
                activity_info = data['activity']
                if 'intensity' in activity_info:
                    activity_levels.append(activity_info['intensity'])
        
        if not water_intake_ml:
            return None, {'message': 'Insufficient hydration data'}
        
        # Calculate average daily water intake
        avg_water_intake = sum(water_intake_ml) / len(water_intake_ml)
        
        # Calculate score based on recommendations (2.7L for men, 2.2L for women)
        # Using 2.5L as average recommendation
        optimal_intake = 2500  # ml
        intake_score = min(100, (avg_water_intake / optimal_intake) * 100)
        
        # Factor in urine color if available
        if urine_color_scores:
            avg_urine_score = sum(urine_color_scores) / len(urine_color_scores)
            # Urine color score: 1-3 is good (light), 4-6 is concerning (dark)
            urine_score = max(0, 100 - (avg_urine_score - 2) * 25)
            hydration_score = (intake_score * 0.7 + urine_score * 0.3)
        else:
            hydration_score = intake_score
        
        details = {
            'average_daily_water_intake_ml': round(avg_water_intake, 0),
            'average_daily_water_intake_liters': round(avg_water_intake / 1000, 1),
            'data_points': len(water_intake_ml),
            'recommendations': self._get_hydration_recommendations(avg_water_intake)
        }
        
        return round(hydration_score, 1), details
    
    def _calculate_vitamin_score(self, health_data: Dict[str, Any]) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculate vitamin/nutrition score (0-100)"""
        lab_results = health_data.get('lab_results', [])
        nutrition_data = health_data.get('nutrition_data', [])
        
        if not lab_results and not nutrition_data:
            return None, {'message': 'No vitamin/nutrition data available'}
        
        # Extract vitamin levels from lab results
        vitamin_levels = {}
        nutrition_scores = []
        
        for lab in lab_results:
            if 'labs' in lab:
                for lab_result in lab['labs']:
                    analyte = lab_result.get('analyte', '').lower()
                    value = lab_result.get('value')
                    
                    # Key vitamins and minerals
                    if 'vitamin d' in analyte or '25-hydroxy' in analyte:
                        vitamin_levels['vitamin_d'] = value
                    elif 'vitamin b12' in analyte or 'b12' in analyte:
                        vitamin_levels['vitamin_b12'] = value
                    elif 'folate' in analyte or 'folic acid' in analyte:
                        vitamin_levels['folate'] = value
                    elif 'iron' in analyte and 'ferritin' not in analyte:
                        vitamin_levels['iron'] = value
                    elif 'ferritin' in analyte:
                        vitamin_levels['ferritin'] = value
        
        # Calculate nutrition scores from food data
        for nutrition in nutrition_data:
            if 'nutrition_score' in nutrition:
                nutrition_scores.append(nutrition['nutrition_score'])
        
        if not vitamin_levels and not nutrition_scores:
            return None, {'message': 'Insufficient vitamin/nutrition data'}
        
        # Calculate vitamin score based on optimal ranges
        vitamin_scores = []
        vitamin_details = {}
        
        # Vitamin D (optimal: 30-100 ng/mL)
        if 'vitamin_d' in vitamin_levels:
            vit_d = vitamin_levels['vitamin_d']
            if 30 <= vit_d <= 100:
                vitamin_scores.append(100)
            elif vit_d < 30:
                vitamin_scores.append(max(0, vit_d / 30 * 100))
            else:
                vitamin_scores.append(max(0, 100 - (vit_d - 100) * 2))
            vitamin_details['vitamin_d_ng_ml'] = vit_d
        
        # Vitamin B12 (optimal: 200-900 pg/mL)
        if 'vitamin_b12' in vitamin_levels:
            vit_b12 = vitamin_levels['vitamin_b12']
            if 200 <= vit_b12 <= 900:
                vitamin_scores.append(100)
            elif vit_b12 < 200:
                vitamin_scores.append(max(0, vit_b12 / 200 * 100))
            else:
                vitamin_scores.append(max(0, 100 - (vit_b12 - 900) * 0.1))
            vitamin_details['vitamin_b12_pg_ml'] = vit_b12
        
        # Ferritin (optimal: 15-150 ng/mL for women, 30-300 ng/mL for men)
        if 'ferritin' in vitamin_levels:
            ferritin = vitamin_levels['ferritin']
            # Using average optimal range
            if 22.5 <= ferritin <= 225:
                vitamin_scores.append(100)
            elif ferritin < 22.5:
                vitamin_scores.append(max(0, ferritin / 22.5 * 100))
            else:
                vitamin_scores.append(max(0, 100 - (ferritin - 225) * 0.2))
            vitamin_details['ferritin_ng_ml'] = ferritin
        
        # Calculate overall vitamin score
        if vitamin_scores:
            vitamin_score = sum(vitamin_scores) / len(vitamin_scores)
        else:
            vitamin_score = 50  # Default if no lab data
        
        # Factor in nutrition scores if available
        if nutrition_scores:
            avg_nutrition_score = sum(nutrition_scores) / len(nutrition_scores)
            vitamin_score = (vitamin_score * 0.6 + avg_nutrition_score * 0.4)
        
        details = {
            'vitamin_levels': vitamin_details,
            'nutrition_scores': nutrition_scores,
            'data_points': len(vitamin_levels) + len(nutrition_scores),
            'recommendations': self._get_vitamin_recommendations(vitamin_levels)
        }
        
        return round(vitamin_score, 1), details
    
    def _calculate_caloric_score(self, health_data: Dict[str, Any]) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculate caloric intake/balance score (0-100)"""
        nutrition_data = health_data.get('nutrition_data', [])
        activity_data = health_data.get('activity_data', [])
        wearable_data = health_data.get('wearable_data', [])
        
        if not nutrition_data and not activity_data and not wearable_data:
            return None, {'message': 'No caloric data available'}
        
        # Extract caloric data
        calories_consumed = []
        calories_burned = []
        bmr_estimates = []
        
        for data in nutrition_data:
            if 'calories_consumed' in data:
                calories_consumed.append(data['calories_consumed'])
        
        for data in activity_data + wearable_data:
            if 'calories_burned' in data:
                calories_burned.append(data['calories_burned'])
            if 'bmr' in data:
                bmr_estimates.append(data['bmr'])
        
        if not calories_consumed:
            return None, {'message': 'Insufficient caloric intake data'}
        
        # Calculate averages
        avg_calories_consumed = sum(calories_consumed) / len(calories_consumed)
        avg_calories_burned = sum(calories_burned) / len(calories_burned) if calories_burned else 2000
        avg_bmr = sum(bmr_estimates) / len(bmr_estimates) if bmr_estimates else 1800
        
        # Calculate caloric balance
        total_daily_expenditure = avg_bmr + (avg_calories_burned - avg_bmr)
        caloric_balance = avg_calories_consumed - total_daily_expenditure
        
        # Calculate score based on caloric balance
        # Optimal: slight deficit for weight loss, maintenance for weight maintenance
        if -200 <= caloric_balance <= 200:  # Maintenance range
            caloric_score = 100
        elif -500 <= caloric_balance < -200:  # Moderate deficit
            caloric_score = 90
        elif 200 < caloric_balance <= 500:  # Moderate surplus
            caloric_score = 80
        else:  # Extreme deficit or surplus
            caloric_score = max(0, 100 - abs(caloric_balance) * 0.1)
        
        details = {
            'average_calories_consumed': round(avg_calories_consumed, 0),
            'average_calories_burned': round(avg_calories_burned, 0),
            'estimated_bmr': round(avg_bmr, 0),
            'caloric_balance': round(caloric_balance, 0),
            'data_points': len(calories_consumed),
            'recommendations': self._get_caloric_recommendations(caloric_balance, avg_calories_consumed)
        }
        
        return round(caloric_score, 1), details
    
    def _calculate_overall_score(self, sleep: Optional[float], hydration: Optional[float], 
                               vitamin: Optional[float], caloric: Optional[float]) -> Optional[float]:
        """Calculate overall health score from individual scores"""
        scores = [s for s in [sleep, hydration, vitamin, caloric] if s is not None]
        
        if not scores:
            return None
        
        # Weighted average (sleep is most important)
        weights = [0.3, 0.25, 0.25, 0.2]  # sleep, hydration, vitamin, caloric
        weighted_sum = 0
        total_weight = 0
        
        for i, score in enumerate([sleep, hydration, vitamin, caloric]):
            if score is not None:
                weighted_sum += score * weights[i]
                total_weight += weights[i]
        
        return round(weighted_sum / total_weight, 1) if total_weight > 0 else None
    
    def _get_data_sources(self, health_data: Dict[str, Any]) -> List[str]:
        """Get list of data sources used in assessment"""
        sources = []
        
        if health_data.get('wearable_data'):
            sources.append('wearable_devices')
        if health_data.get('lab_results'):
            sources.append('lab_results')
        if health_data.get('manual_entries'):
            sources.append('manual_entries')
        
        return sources
    
    def _calculate_confidence_score(self, health_data: Dict[str, Any], data_sources: List[str]) -> float:
        """Calculate confidence score based on data quality and quantity"""
        confidence = 0.0
        
        # Base confidence from data sources
        if 'wearable_devices' in data_sources:
            confidence += 0.4
        if 'lab_results' in data_sources:
            confidence += 0.4
        if 'manual_entries' in data_sources:
            confidence += 0.2
        
        # Boost confidence based on data quantity
        total_data_points = sum(len(data) for data in health_data.values())
        if total_data_points > 50:
            confidence += 0.2
        elif total_data_points > 20:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _get_sleep_recommendations(self, avg_hours: float, avg_efficiency: float) -> List[str]:
        """Get sleep recommendations based on metrics"""
        recommendations = []
        
        if avg_hours < 7:
            recommendations.append("Try to get 7-9 hours of sleep per night")
        elif avg_hours > 9:
            recommendations.append("Consider if you're getting too much sleep")
        
        if avg_efficiency < 85:
            recommendations.append("Improve sleep efficiency by reducing screen time before bed")
        
        return recommendations
    
    def _get_hydration_recommendations(self, avg_intake_ml: float) -> List[str]:
        """Get hydration recommendations based on intake"""
        recommendations = []
        
        if avg_intake_ml < 2000:
            recommendations.append("Increase daily water intake to at least 2-2.5 liters")
        elif avg_intake_ml > 4000:
            recommendations.append("Consider if you're drinking too much water")
        
        return recommendations
    
    def _get_vitamin_recommendations(self, vitamin_levels: Dict[str, float]) -> List[str]:
        """Get vitamin recommendations based on levels"""
        recommendations = []
        
        if 'vitamin_d' in vitamin_levels and vitamin_levels['vitamin_d'] < 30:
            recommendations.append("Consider vitamin D supplementation")
        
        if 'vitamin_b12' in vitamin_levels and vitamin_levels['vitamin_b12'] < 200:
            recommendations.append("Consider vitamin B12 supplementation")
        
        if 'ferritin' in vitamin_levels and vitamin_levels['ferritin'] < 15:
            recommendations.append("Consider iron supplementation")
        
        return recommendations
    
    def _get_caloric_recommendations(self, caloric_balance: float, avg_intake: float) -> List[str]:
        """Get caloric recommendations based on balance"""
        recommendations = []
        
        if caloric_balance < -500:
            recommendations.append("Consider increasing caloric intake to avoid excessive deficit")
        elif caloric_balance > 500:
            recommendations.append("Consider reducing caloric intake or increasing activity")
        
        return recommendations
