"""Date calculation utilities for AI function calling."""

from datetime import datetime, timedelta
from typing import Dict, Any


def calculate_date_from_delta(
    current_datetime: str,
    days_delta: int = 0,
    weeks_delta: int = 0,
    months_delta: int = 0,
    hours_delta: int = 0,
    minutes_delta: int = 0
) -> Dict[str, Any]:
    """
    Calculate a new date by adding deltas to the current datetime.
    
    This function is designed to be called by AI when parsing natural language dates.
    The AI will determine the appropriate deltas based on expressions like:
    - "next Thursday" -> AI calculates days_delta to next Thursday
    - "in 3 weeks" -> AI sets weeks_delta=3
    - "tomorrow at 2pm" -> AI sets days_delta=1, hours_delta to reach 2pm
    
    Args:
        current_datetime: Current datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
        days_delta: Number of days to add (can be negative)
        weeks_delta: Number of weeks to add (can be negative)
        months_delta: Number of months to add (can be negative, approximated as 30 days)
        hours_delta: Number of hours to add (can be negative)
        minutes_delta: Number of minutes to add (can be negative)
        
    Returns:
        Dictionary with calculated date information
    """
    try:
        # Parse the current datetime
        current_dt = datetime.fromisoformat(current_datetime.replace('Z', '+00:00'))
        
        # Calculate the new datetime
        new_dt = current_dt + timedelta(
            days=days_delta + (weeks_delta * 7) + (months_delta * 30),
            hours=hours_delta,
            minutes=minutes_delta
        )
        
        return {
            "success": True,
            "calculated_date": new_dt.strftime("%Y-%m-%d"),
            "calculated_datetime": new_dt.isoformat(),
            "calculated_time": new_dt.strftime("%H:%M"),
            "day_of_week": new_dt.strftime("%A"),
            "formatted_date": new_dt.strftime("%B %d, %Y"),
            "is_future": new_dt > current_dt,
            "days_from_now": (new_dt - current_dt).days
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to calculate date: {str(e)}"
        }


def get_weekday_delta(current_datetime: str, target_weekday: str, next_occurrence: bool = True) -> Dict[str, Any]:
    """
    Calculate the delta to reach a specific weekday.
    
    This function helps AI calculate how many days to add to reach a specific weekday.
    
    Args:
        current_datetime: Current datetime in ISO format
        target_weekday: Target weekday name (e.g., "Monday", "Tuesday")
        next_occurrence: If True, get next occurrence; if False, get this week's occurrence
        
    Returns:
        Dictionary with delta information
    """
    try:
        current_dt = datetime.fromisoformat(current_datetime.replace('Z', '+00:00'))
        
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday_lower = target_weekday.lower()
        if target_weekday_lower not in weekdays:
            return {
                "success": False,
                "error": f"Invalid weekday: {target_weekday}"
            }
        
        target_weekday_num = weekdays[target_weekday_lower]
        current_weekday_num = current_dt.weekday()
        
        days_ahead = target_weekday_num - current_weekday_num
        
        if next_occurrence and days_ahead <= 0:
            days_ahead += 7
        
        return {
            "success": True,
            "days_delta": days_ahead,
            "target_weekday": target_weekday,
            "current_weekday": current_dt.strftime("%A")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to calculate weekday delta: {str(e)}"
        }


# Function definitions for OpenAI function calling
DATE_CALCULATION_FUNCTIONS = [
    {
        "name": "calculate_date_from_delta",
        "description": "Calculate a new date by adding time deltas to the current datetime. Use this when you need to determine a specific date from relative expressions like 'next Thursday', 'in 3 weeks', 'tomorrow', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "current_datetime": {
                    "type": "string",
                    "description": "Current datetime in ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                "days_delta": {
                    "type": "integer",
                    "description": "Number of days to add (can be negative for past dates)",
                    "default": 0
                },
                "weeks_delta": {
                    "type": "integer", 
                    "description": "Number of weeks to add (can be negative)",
                    "default": 0
                },
                "months_delta": {
                    "type": "integer",
                    "description": "Number of months to add (can be negative, approximated as 30 days)",
                    "default": 0
                },
                "hours_delta": {
                    "type": "integer",
                    "description": "Number of hours to add (can be negative)",
                    "default": 0
                },
                "minutes_delta": {
                    "type": "integer",
                    "description": "Number of minutes to add (can be negative)",
                    "default": 0
                }
            },
            "required": ["current_datetime"]
        }
    },
    {
        "name": "get_weekday_delta",
        "description": "Calculate how many days to add to reach a specific weekday. Use this to help calculate dates like 'next Monday', 'this Friday', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "current_datetime": {
                    "type": "string",
                    "description": "Current datetime in ISO format"
                },
                "target_weekday": {
                    "type": "string",
                    "description": "Target weekday name (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday)"
                },
                "next_occurrence": {
                    "type": "boolean",
                    "description": "If true, get next occurrence of the weekday; if false, get this week's occurrence",
                    "default": True
                }
            },
            "required": ["current_datetime", "target_weekday"]
        }
    }
]


# Registry of available functions for function calling
FUNCTION_REGISTRY = {
    "calculate_date_from_delta": calculate_date_from_delta,
    "get_weekday_delta": get_weekday_delta
}
