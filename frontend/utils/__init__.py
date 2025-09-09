"""
CleanSky AI Frontend Utilities Package

This package contains utility functions and classes for the CleanSky AI frontend.
"""

from .api_client import APIClient
from .helpers import (
    format_aqi_value,
    get_aqi_category,
    get_aqi_color,
    get_aqi_emoji,
    format_timestamp,
    format_coordinates,
    calculate_time_ago,
    safe_divide,
    generate_download_filename,
    create_download_link,
    validate_coordinates,
    format_pollutant_name,
    get_pollutant_description,
    get_health_message_for_aqi,
    get_activity_recommendations,
    format_units,
    create_shareable_url,
    get_wind_direction_name,
    calculate_air_quality_trend,
    get_seasonal_context,
    is_mobile_device,
    get_user_preferences,
    save_user_preferences,
    format_number,
    get_browser_timezone,
    create_error_message
)

__all__ = [
    # API Client
    'APIClient',
    
    # Helper functions
    'format_aqi_value',
    'get_aqi_category',
    'get_aqi_color',
    'get_aqi_emoji',
    'format_timestamp',
    'format_coordinates',
    'calculate_time_ago',
    'safe_divide',
    'generate_download_filename',
    'create_download_link',
    'validate_coordinates',
    'format_pollutant_name',
    'get_pollutant_description',
    'get_health_message_for_aqi',
    'get_activity_recommendations',
    'format_units',
    'create_shareable_url',
    'get_wind_direction_name',
    'calculate_air_quality_trend',
    'get_seasonal_context',
    'is_mobile_device',
    'get_user_preferences',
    'save_user_preferences',
    'format_number',
    'get_browser_timezone',
    'create_error_message'
]
