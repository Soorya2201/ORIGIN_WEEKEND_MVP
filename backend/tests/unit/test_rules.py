"""Tests for deterministic rules engine."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock

from app.insights.rules import (
    run_deterministic_rules,
    _check_ldl_cholesterol,
    _check_hba1c,
    _check_tsh,
    _check_ferritin,
    _check_trends
)
from app.db.models import LabResult


def create_mock_lab(analyte_name, value, unit, observed_at=None, lab_id=None):
    """Helper to create mock lab result."""
    if observed_at is None:
        observed_at = datetime.utcnow()
    if lab_id is None:
        lab_id = uuid4()
    
    lab = Mock(spec=LabResult)
    lab.id = lab_id
    lab.analyte_name = analyte_name
    lab.value_numeric = value
    lab.unit = unit
    lab.observed_at = observed_at
    lab.ref_low = None
    lab.ref_high = None
    return lab


def test_check_ldl_cholesterol_elevated():
    """Test LDL cholesterol elevated level detection."""
    labs = [create_mock_lab("LDL Cholesterol", 172, "mg/dL")]
    
    insights = _check_ldl_cholesterol(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "High LDL Cholesterol"
    assert "172 mg/dL" in insights[0]["detail"]
    assert insights[0]["confidence"] == 1.0


def test_check_ldl_cholesterol_very_high():
    """Test LDL cholesterol very high level detection."""
    labs = [create_mock_lab("LDL Cholesterol", 195, "mg/dL")]
    
    insights = _check_ldl_cholesterol(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Very High LDL Cholesterol"
    assert "195 mg/dL" in insights[0]["detail"]


def test_check_ldl_cholesterol_borderline():
    """Test LDL cholesterol borderline high detection."""
    labs = [create_mock_lab("LDL Cholesterol", 145, "mg/dL")]
    
    insights = _check_ldl_cholesterol(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Borderline High LDL Cholesterol"


def test_check_ldl_cholesterol_normal():
    """Test LDL cholesterol normal level (no insight)."""
    labs = [create_mock_lab("LDL Cholesterol", 120, "mg/dL")]
    
    insights = _check_ldl_cholesterol(labs)
    
    assert len(insights) == 0


def test_check_ldl_cholesterol_wrong_unit():
    """Test LDL cholesterol with wrong unit (no insight)."""
    labs = [create_mock_lab("LDL Cholesterol", 172, "mmol/L")]
    
    insights = _check_ldl_cholesterol(labs)
    
    assert len(insights) == 0


def test_check_hba1c_diabetes():
    """Test HbA1c diabetes level detection."""
    labs = [create_mock_lab("HbA1c", 7.2, "%")]
    
    insights = _check_hba1c(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Diabetes Risk - High HbA1c"
    assert "7.2%" in insights[0]["detail"]
    assert "≥6.5%" in insights[0]["detail"]


def test_check_hba1c_prediabetes():
    """Test HbA1c prediabetes level detection."""
    labs = [create_mock_lab("HbA1c", 6.0, "%")]
    
    insights = _check_hba1c(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Prediabetes Risk"
    assert "6.0%" in insights[0]["detail"]
    assert "5.7-6.4%" in insights[0]["detail"]


def test_check_hba1c_normal():
    """Test HbA1c normal level (no insight)."""
    labs = [create_mock_lab("HbA1c", 5.5, "%")]
    
    insights = _check_hba1c(labs)
    
    assert len(insights) == 0


def test_check_tsh_hypothyroidism():
    """Test TSH hypothyroidism detection."""
    labs = [create_mock_lab("TSH", 5.2, "mIU/L")]
    
    insights = _check_tsh(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Possible Hypothyroidism"
    assert "5.2 mIU/L" in insights[0]["detail"]
    assert ">4.0 mIU/L" in insights[0]["detail"]


def test_check_tsh_hyperthyroidism():
    """Test TSH hyperthyroidism detection."""
    labs = [create_mock_lab("TSH", 0.2, "mIU/L")]
    
    insights = _check_tsh(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Possible Hyperthyroidism"
    assert "0.2 mIU/L" in insights[0]["detail"]
    assert "<0.4 mIU/L" in insights[0]["detail"]


def test_check_tsh_normal():
    """Test TSH normal level (no insight)."""
    labs = [create_mock_lab("TSH", 2.5, "mIU/L")]
    
    insights = _check_tsh(labs)
    
    assert len(insights) == 0


def test_check_ferritin_low():
    """Test ferritin low level detection."""
    labs = [create_mock_lab("Ferritin", 25, "ng/mL")]
    
    insights = _check_ferritin(labs)
    
    assert len(insights) == 1
    assert insights[0]["title"] == "Low Iron Stores"
    assert "25 ng/mL" in insights[0]["detail"]
    assert "<30 ng/mL" in insights[0]["detail"]


def test_check_ferritin_normal():
    """Test ferritin normal level (no insight)."""
    labs = [create_mock_lab("Ferritin", 45, "ng/mL")]
    
    insights = _check_ferritin(labs)
    
    assert len(insights) == 0


def test_check_trends_increase():
    """Test trend detection for increasing values."""
    now = datetime.utcnow()
    past = now - timedelta(days=30)
    
    # Labs should be sorted by date desc (most recent first)
    labs = [
        create_mock_lab("LDL Cholesterol", 190, "mg/dL", now, uuid4()),  # Latest
        create_mock_lab("LDL Cholesterol", 150, "mg/dL", past, uuid4())  # Previous
    ]
    
    insights = _check_trends({"LDL Cholesterol": labs})
    
    assert len(insights) == 1
    assert "Significant Trend" in insights[0]["title"]
    assert "increased" in insights[0]["detail"]
    assert "26.7%" in insights[0]["detail"]


def test_check_trends_decrease():
    """Test trend detection for decreasing values."""
    now = datetime.utcnow()
    past = now - timedelta(days=30)
    
    # Labs should be sorted by date desc (most recent first)
    labs = [
        create_mock_lab("LDL Cholesterol", 110, "mg/dL", now, uuid4()),  # Latest
        create_mock_lab("LDL Cholesterol", 150, "mg/dL", past, uuid4())  # Previous
    ]
    
    insights = _check_trends({"LDL Cholesterol": labs})
    
    assert len(insights) == 1
    assert "decreased" in insights[0]["detail"]
    assert "26.7%" in insights[0]["detail"]


def test_check_trends_insufficient_change():
    """Test trend detection with insufficient change."""
    now = datetime.utcnow()
    past = now - timedelta(days=30)
    
    labs = [
        create_mock_lab("LDL Cholesterol", 155, "mg/dL", now, uuid4()),
        create_mock_lab("LDL Cholesterol", 150, "mg/dL", past, uuid4())
    ]
    
    insights = _check_trends({"LDL Cholesterol": labs})
    
    assert len(insights) == 0  # Only 3.3% change


def test_check_trends_too_old():
    """Test trend detection with values too far apart."""
    now = datetime.utcnow()
    past = now - timedelta(days=150)  # More than 120 days
    
    labs = [
        create_mock_lab("LDL Cholesterol", 180, "mg/dL", now, uuid4()),
        create_mock_lab("LDL Cholesterol", 150, "mg/dL", past, uuid4())
    ]
    
    insights = _check_trends({"LDL Cholesterol": labs})
    
    assert len(insights) == 0  # Too old


def test_check_trends_different_units():
    """Test trend detection with different units."""
    now = datetime.utcnow()
    past = now - timedelta(days=30)
    
    labs = [
        create_mock_lab("LDL Cholesterol", 180, "mg/dL", now, uuid4()),
        create_mock_lab("LDL Cholesterol", 150, "mmol/L", past, uuid4())
    ]
    
    insights = _check_trends({"LDL Cholesterol": labs})
    
    assert len(insights) == 0  # Different units


def test_check_trends_insufficient_data():
    """Test trend detection with insufficient data."""
    labs = [create_mock_lab("LDL Cholesterol", 150, "mg/dL")]
    
    insights = _check_trends({"LDL Cholesterol": labs})
    
    assert len(insights) == 0  # Need at least 2 values


def test_run_deterministic_rules_no_labs():
    """Test running rules with no lab data."""
    person_id = uuid4()
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    
    insights = run_deterministic_rules(person_id, mock_db)
    
    assert len(insights) == 0


def test_run_deterministic_rules_multiple_analytes():
    """Test running rules with multiple analytes."""
    person_id = uuid4()
    
    # Create mock labs for different analytes
    ldl_lab = create_mock_lab("LDL Cholesterol", 172, "mg/dL")
    hba1c_lab = create_mock_lab("HbA1c", 6.2, "%")
    tsh_lab = create_mock_lab("TSH", 0.2, "mIU/L")
    
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        ldl_lab, hba1c_lab, tsh_lab
    ]
    
    insights = run_deterministic_rules(person_id, mock_db)
    
    # Should generate insights for all three analytes
    assert len(insights) == 3
    
    titles = [insight["title"] for insight in insights]
    assert "High LDL Cholesterol" in titles
    assert "Prediabetes Risk" in titles
    assert "Possible Hyperthyroidism" in titles


def test_run_deterministic_rules_error_handling():
    """Test error handling in rules engine."""
    person_id = uuid4()
    mock_db = Mock()
    mock_db.query.side_effect = Exception("Database error")
    
    insights = run_deterministic_rules(person_id, mock_db)
    
    assert len(insights) == 0  # Should return empty list on error
