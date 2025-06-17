"""Unit tests for date calculation utilities."""

from datetime import datetime, timedelta

import pytest

from libs.date_tools import (
    calculate_date_from_delta,
    get_weekday_delta,
    DATE_CALCULATION_FUNCTIONS,
    FUNCTION_REGISTRY
)


@pytest.mark.unit
def test_calculate_date_from_delta_basic():
    """Test basic date calculation with days delta."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(current_dt, days_delta=5)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-01-20"
    assert result["calculated_datetime"] == "2024-01-20T10:00:00"
    assert result["day_of_week"] == "Saturday"
    assert result["is_future"] is True
    assert result["days_from_now"] == 5


@pytest.mark.unit
def test_calculate_date_from_delta_negative_days():
    """Test date calculation with negative days (past dates)."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(current_dt, days_delta=-3)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-01-12"
    assert result["is_future"] is False
    assert result["days_from_now"] == -3


@pytest.mark.unit
def test_calculate_date_from_delta_weeks():
    """Test date calculation with weeks delta."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(current_dt, weeks_delta=2)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-01-29"
    assert result["days_from_now"] == 14


@pytest.mark.unit
def test_calculate_date_from_delta_months():
    """Test date calculation with months delta."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(current_dt, months_delta=1)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-02-14"  # 30 days later
    assert result["days_from_now"] == 30


@pytest.mark.unit
def test_calculate_date_from_delta_hours_minutes():
    """Test date calculation with hours and minutes delta."""
    current_dt = "2024-01-15T10:30:00"
    
    result = calculate_date_from_delta(current_dt, hours_delta=5, minutes_delta=30)
    
    assert result["success"] is True
    assert result["calculated_datetime"] == "2024-01-15T16:00:00"
    assert result["calculated_time"] == "16:00"


@pytest.mark.unit
def test_calculate_date_from_delta_combined():
    """Test date calculation with multiple deltas combined."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(
        current_dt,
        days_delta=1,
        weeks_delta=1,
        hours_delta=2
    )
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-01-23"  # 1 + 7 = 8 days later
    assert result["calculated_time"] == "12:00"  # 2 hours later
    assert result["days_from_now"] == 8


@pytest.mark.unit
def test_calculate_date_from_delta_timezone_handling():
    """Test date calculation with timezone in datetime string."""
    current_dt = "2024-01-15T10:00:00Z"
    
    result = calculate_date_from_delta(current_dt, days_delta=1)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-01-16"


@pytest.mark.unit
def test_calculate_date_from_delta_invalid_datetime():
    """Test date calculation with invalid datetime string."""
    current_dt = "invalid-datetime"
    
    result = calculate_date_from_delta(current_dt, days_delta=1)
    
    assert result["success"] is False
    assert "error" in result
    assert "Failed to calculate date" in result["error"]


@pytest.mark.unit
def test_get_weekday_delta_next_occurrence():
    """Test getting delta to next occurrence of a weekday."""
    # Monday, January 15, 2024
    current_dt = "2024-01-15T10:00:00"
    
    # Next Thursday (4 days ahead)
    result = get_weekday_delta(current_dt, "Thursday", next_occurrence=True)
    
    assert result["success"] is True
    assert result["days_delta"] == 3  # Monday to Thursday = 3 days
    assert result["target_weekday"] == "Thursday"
    assert result["current_weekday"] == "Monday"


@pytest.mark.unit
def test_get_weekday_delta_same_weekday():
    """Test getting delta when target is same as current weekday."""
    # Monday, January 15, 2024
    current_dt = "2024-01-15T10:00:00"
    
    # Next Monday (7 days ahead since it's currently Monday)
    result = get_weekday_delta(current_dt, "Monday", next_occurrence=True)
    
    assert result["success"] is True
    assert result["days_delta"] == 7


@pytest.mark.unit
def test_get_weekday_delta_this_week():
    """Test getting delta to this week's occurrence of a weekday."""
    # Monday, January 15, 2024
    current_dt = "2024-01-15T10:00:00"
    
    # This Friday (4 days ahead)
    result = get_weekday_delta(current_dt, "Friday", next_occurrence=False)
    
    assert result["success"] is True
    assert result["days_delta"] == 4


@pytest.mark.unit
def test_get_weekday_delta_this_week_past_day():
    """Test getting delta to this week's occurrence of a past weekday."""
    # Friday, January 19, 2024
    current_dt = "2024-01-19T10:00:00"
    
    # This Monday (negative delta)
    result = get_weekday_delta(current_dt, "Monday", next_occurrence=False)
    
    assert result["success"] is True
    assert result["days_delta"] == -4  # Friday to Monday = -4 days


@pytest.mark.unit
def test_get_weekday_delta_case_insensitive():
    """Test that weekday names are case insensitive."""
    current_dt = "2024-01-15T10:00:00"
    
    result = get_weekday_delta(current_dt, "THURSDAY", next_occurrence=True)
    
    assert result["success"] is True
    assert result["days_delta"] == 3


@pytest.mark.unit
def test_get_weekday_delta_invalid_weekday():
    """Test getting delta with invalid weekday name."""
    current_dt = "2024-01-15T10:00:00"
    
    result = get_weekday_delta(current_dt, "InvalidDay", next_occurrence=True)
    
    assert result["success"] is False
    assert "error" in result
    assert "Invalid weekday" in result["error"]


@pytest.mark.unit
def test_get_weekday_delta_invalid_datetime():
    """Test getting weekday delta with invalid datetime."""
    current_dt = "invalid-datetime"
    
    result = get_weekday_delta(current_dt, "Monday", next_occurrence=True)
    
    assert result["success"] is False
    assert "error" in result
    assert "Failed to calculate weekday delta" in result["error"]


@pytest.mark.unit
def test_date_calculation_functions_structure():
    """Test that DATE_CALCULATION_FUNCTIONS has correct structure."""
    assert isinstance(DATE_CALCULATION_FUNCTIONS, list)
    assert len(DATE_CALCULATION_FUNCTIONS) == 2
    
    # Check first function (calculate_date_from_delta)
    func1 = DATE_CALCULATION_FUNCTIONS[0]
    assert func1["name"] == "calculate_date_from_delta"
    assert "description" in func1
    assert "parameters" in func1
    assert func1["parameters"]["type"] == "object"
    assert "current_datetime" in func1["parameters"]["properties"]
    assert "current_datetime" in func1["parameters"]["required"]
    
    # Check second function (get_weekday_delta)
    func2 = DATE_CALCULATION_FUNCTIONS[1]
    assert func2["name"] == "get_weekday_delta"
    assert "description" in func2
    assert "parameters" in func2
    assert "current_datetime" in func2["parameters"]["properties"]
    assert "target_weekday" in func2["parameters"]["properties"]


@pytest.mark.unit
def test_function_registry():
    """Test that FUNCTION_REGISTRY contains all expected functions."""
    assert isinstance(FUNCTION_REGISTRY, dict)
    assert len(FUNCTION_REGISTRY) == 2
    
    assert "calculate_date_from_delta" in FUNCTION_REGISTRY
    assert "get_weekday_delta" in FUNCTION_REGISTRY
    
    # Test that functions are callable
    assert callable(FUNCTION_REGISTRY["calculate_date_from_delta"])
    assert callable(FUNCTION_REGISTRY["get_weekday_delta"])


@pytest.mark.unit
def test_function_registry_execution():
    """Test that functions in registry can be executed."""
    current_dt = "2024-01-15T10:00:00"
    
    # Test calculate_date_from_delta through registry
    func1 = FUNCTION_REGISTRY["calculate_date_from_delta"]
    result1 = func1(current_dt, days_delta=1)
    assert result1["success"] is True
    assert result1["calculated_date"] == "2024-01-16"
    
    # Test get_weekday_delta through registry
    func2 = FUNCTION_REGISTRY["get_weekday_delta"]
    result2 = func2(current_dt, "Friday", True)
    assert result2["success"] is True
    assert result2["days_delta"] == 4


@pytest.mark.unit
def test_formatted_date_output():
    """Test that formatted date output is correct."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(current_dt, days_delta=5)
    
    assert result["success"] is True
    assert result["formatted_date"] == "January 20, 2024"


@pytest.mark.unit
def test_edge_case_end_of_month():
    """Test date calculation at end of month."""
    # January 31, 2024
    current_dt = "2024-01-31T10:00:00"
    
    result = calculate_date_from_delta(current_dt, days_delta=1)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-02-01"
    assert result["day_of_week"] == "Thursday"


@pytest.mark.unit
def test_edge_case_leap_year():
    """Test date calculation in leap year."""
    # February 28, 2024 (leap year)
    current_dt = "2024-02-28T10:00:00"
    
    result = calculate_date_from_delta(current_dt, days_delta=1)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-02-29"  # Leap day


@pytest.mark.unit
def test_edge_case_year_boundary():
    """Test date calculation across year boundary."""
    # December 31, 2023
    current_dt = "2023-12-31T23:59:59"
    
    result = calculate_date_from_delta(current_dt, minutes_delta=1)
    
    assert result["success"] is True
    assert result["calculated_date"] == "2024-01-01"
    assert result["calculated_time"] == "00:00"


@pytest.mark.unit
def test_large_deltas():
    """Test calculation with large time deltas."""
    current_dt = "2024-01-15T10:00:00"
    
    result = calculate_date_from_delta(
        current_dt,
        days_delta=365,
        hours_delta=24,
        minutes_delta=60
    )
    
    assert result["success"] is True
    # 365 days + 1 day (24 hours) + 1 hour (60 minutes) = 366 days and 1 hour
    assert result["calculated_date"] == "2025-01-15"
    assert result["calculated_time"] == "11:00"
