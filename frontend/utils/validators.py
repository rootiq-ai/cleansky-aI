"""
Validation utilities for CleanSky AI backend
"""
import re
from datetime import datetime
from typing import Optional, Tuple
import structlog

logger = structlog.get_logger()

def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude coordinates
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        bool: True if coordinates are valid, False otherwise
    """
    try:
        if lat is None or lon is None:
            return False
            
        # Check if values are within valid ranges
        if not (-90.0 <= lat <= 90.0):
            return False
            
        if not (-180.0 <= lon <= 180.0):
            return False
            
        return True
        
    except (TypeError, ValueError):
        return False

def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> bool:
    """
    Validate date range strings
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        
    Returns:
        bool: True if date range is valid, False otherwise
    """
    try:
        if not start_date or not end_date:
            return True  # Allow None values
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Check if start is before end
        if start_dt >= end_dt:
            return False
            
        # Check if dates are not too far in the past or future
        now = datetime.utcnow()
        max_past = 365  # days
        max_future = 30  # days
        
        if (now - start_dt).days > max_past:
            return False
            
        if (end_dt - now).days > max_future:
            return False
            
        return True
        
    except (ValueError, TypeError, AttributeError):
        return False

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address string
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    try:
        if not email or not isinstance(email, str):
            return False
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
            
        # Additional checks
        if len(email) > 254:  # RFC 5321 limit
            return False
            
        if '..' in email:  # Consecutive dots not allowed
            return False
            
        return True
        
    except (TypeError, AttributeError):
        return False

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number string
        
    Returns:
        bool: True if phone is valid, False otherwise
    """
    try:
        if not phone or not isinstance(phone, str):
            return False
        
        # Remove common separators
        cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        
        # Check if only digits remain
        if not cleaned_phone.isdigit():
            return False
        
        # Check length (7-15 digits is reasonable for international numbers)
        if not (7 <= len(cleaned_phone) <= 15):
            return False
            
        return True
        
    except (TypeError, AttributeError):
        return False

def validate_aqi_value(aqi: float) -> bool:
    """
    Validate Air Quality Index value
    
    Args:
        aqi: AQI value
        
    Returns:
        bool: True if AQI is valid, False otherwise
    """
    try:
        if aqi is None:
            return False
            
        # AQI should be between 0 and 500
        if not (0 <= aqi <= 500):
            return False
            
        return True
        
    except (TypeError, ValueError):
        return False

def validate_forecast_hours(hours: int) -> bool:
    """
    Validate forecast hours parameter
    
    Args:
        hours: Number of hours for forecast
        
    Returns:
        bool: True if hours is valid, False otherwise
    """
    try:
        if hours is None:
            return False
            
        # Allow 1-72 hours forecast
        if not (1 <= hours <= 72):
            return False
            
        return True
        
    except (TypeError, ValueError):
        return False

def validate_parameter_list(parameters: list, allowed_parameters: list) -> bool:
    """
    Validate list of parameters against allowed values
    
    Args:
        parameters: List of parameters to validate
        allowed_parameters: List of allowed parameter values
        
    Returns:
        bool: True if all parameters are valid, False otherwise
    """
    try:
        if not parameters or not isinstance(parameters, list):
            return False
            
        if not allowed_parameters or not isinstance(allowed_parameters, list):
            return False
        
        # Check if all parameters are in allowed list
        for param in parameters:
            if param not in allowed_parameters:
                return False
                
        return True
        
    except (TypeError, AttributeError):
        return False

def validate_radius(radius: int) -> bool:
    """
    Validate search radius parameter
    
    Args:
        radius: Search radius in kilometers
        
    Returns:
        bool: True if radius is valid, False otherwise
    """
    try:
        if radius is None:
            return False
            
        # Allow radius between 1 and 500 km
        if not (1 <= radius <= 500):
            return False
            
        return True
        
    except (TypeError, ValueError):
        return False

def validate_user_id(user_id: int) -> bool:
    """
    Validate user ID
    
    Args:
        user_id: User identifier
        
    Returns:
        bool: True if user_id is valid, False otherwise
    """
    try:
        if user_id is None:
            return False
            
        # User ID should be positive integer
        if not isinstance(user_id, int) or user_id <= 0:
            return False
            
        return True
        
    except (TypeError, ValueError):
        return False

def sanitize_string_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent injection attacks
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
    """
    try:
        if not input_str or not isinstance(input_str, str):
            return ""
            
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        # Remove potentially dangerous characters for basic protection
        dangerous_chars = ['<', '>', '"', "'", '&', '\r', '\n']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
            
        return sanitized.strip()
        
    except (TypeError, AttributeError):
        return ""

def validate_notification_channels(channels: list) -> bool:
    """
    Validate notification channels list
    
    Args:
        channels: List of notification channels
        
    Returns:
        bool: True if all channels are valid, False otherwise
    """
    try:
        if not channels or not isinstance(channels, list):
            return False
            
        allowed_channels = ['email', 'sms', 'push']
        
        for channel in channels:
            if channel not in allowed_channels:
                return False
                
        return True
        
    except (TypeError, AttributeError):
        return False

def validate_aqi_threshold(threshold: int) -> bool:
    """
    Validate AQI threshold for alerts
    
    Args:
        threshold: AQI threshold value
        
    Returns:
        bool: True if threshold is valid, False otherwise
    """
    try:
        if threshold is None:
            return False
            
        # Common AQI thresholds: 50, 100, 150, 200, 300
        valid_thresholds = [25, 50, 75, 100, 125, 150, 175, 200, 250, 300]
        
        return threshold in valid_thresholds
        
    except (TypeError, ValueError):
        return False

def validate_time_range(time_range: str) -> bool:
    """
    Validate time range parameter
    
    Args:
        time_range: Time range string
        
    Returns:
        bool: True if time range is valid, False otherwise
    """
    try:
        if not time_range or not isinstance(time_range, str):
            return False
            
        valid_ranges = [
            'last_hour', 'last_6_hours', 'last_24_hours', 
            'last_3_days', 'last_week', 'last_month'
        ]
        
        return time_range.lower() in valid_ranges
        
    except (TypeError, AttributeError):
        return False

def validate_json_payload(payload: dict, required_fields: list) -> Tuple[bool, list]:
    """
    Validate JSON payload contains required fields
    
    Args:
        payload: JSON payload dictionary
        required_fields: List of required field names
        
    Returns:
        Tuple[bool, list]: (is_valid, missing_fields)
    """
    try:
        if not payload or not isinstance(payload, dict):
            return False, required_fields
            
        if not required_fields or not isinstance(required_fields, list):
            return True, []
        
        missing_fields = []
        
        for field in required_fields:
            if field not in payload or payload[field] is None:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
        
    except (TypeError, AttributeError):
        return False, required_fields
