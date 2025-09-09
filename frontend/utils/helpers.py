"""
Helper utilities for CleanSky AI frontend
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import base64

def format_aqi_value(aqi: float) -> str:
    """Format AQI value with appropriate precision"""
    if pd.isna(aqi) or aqi is None:
        return "N/A"
    return f"{aqi:.0f}"

def get_aqi_category(aqi: float) -> str:
    """Get AQI category from numeric value"""
    if pd.isna(aqi) or aqi is None:
        return "Unknown"
    
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def get_aqi_color(aqi: float) -> str:
    """Get color hex code for AQI value"""
    if pd.isna(aqi) or aqi is None:
        return "#808080"  # Gray for unknown
    
    if aqi <= 50:
        return "#00E400"  # Green
    elif aqi <= 100:
        return "#FFFF00"  # Yellow
    elif aqi <= 150:
        return "#FF7E00"  # Orange
    elif aqi <= 200:
        return "#FF0000"  # Red
    elif aqi <= 300:
        return "#8F3F97"  # Purple
    else:
        return "#7E0023"  # Maroon

def get_aqi_emoji(aqi: float) -> str:
    """Get emoji representation for AQI value"""
    if pd.isna(aqi) or aqi is None:
        return "❓"
    
    if aqi <= 50:
        return "😊"  # Good
    elif aqi <= 100:
        return "😐"  # Moderate
    elif aqi <= 150:
        return "😷"  # Unhealthy for Sensitive
    elif aqi <= 200:
        return "😨"  # Unhealthy
    elif aqi <= 300:
        return "🤢"  # Very Unhealthy
    else:
        return "☠️"  # Hazardous

def format_timestamp(timestamp: str, format_type: str = "short") -> str:
    """Format timestamp string for display"""
    try:
        if pd.isna(timestamp) or not timestamp:
            return "N/A"
        
        # Parse timestamp
        dt = pd.to_datetime(timestamp)
        
        if format_type == "short":
            return dt.strftime("%m/%d %H:%M")
        elif format_type == "long":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "date_only":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time_only":
            return dt.strftime("%H:%M")
        elif format_type == "relative":
            now = datetime.now()
            diff = now - dt.replace(tzinfo=None)
            
            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                return f"{diff.seconds//3600}h ago"
            elif diff.seconds > 60:
                return f"{diff.seconds//60}m ago"
            else:
                return "Just now"
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
            
    except Exception:
        return str(timestamp)[:16] if timestamp else "N/A"

def format_coordinates(lat: float, lon: float, precision: int = 4) -> str:
    """Format coordinates for display"""
    if pd.isna(lat) or pd.isna(lon):
        return "N/A"
    
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    
    return f"{abs(lat):.{precision}f}°{lat_dir}, {abs(lon):.{precision}f}°{lon_dir}"

def calculate_time_ago(timestamp: str) -> str:
    """Calculate human-readable time difference"""
    try:
        dt = pd.to_datetime(timestamp)
        now = datetime.now()
        
        # Make timezone-naive for comparison
        if dt.tz is not None:
            dt = dt.tz_localize(None)
        
        diff = now - dt
        
        if diff.days > 30:
            return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
            
    except Exception:
        return "Unknown"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero"""
    try:
        if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def generate_download_filename(prefix: str, extension: str = "csv") -> str:
    """Generate filename for downloads with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def create_download_link(data: str, filename: str, link_text: str = "Download") -> str:
    """Create a download link for data"""
    b64_data = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64_data}" download="{filename}">{link_text}</a>'
    return href

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude values"""
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        if not (-90 <= lat_float <= 90):
            return False
        if not (-180 <= lon_float <= 180):
            return False
        
        return True
    except (ValueError, TypeError):
        return False

def format_pollutant_name(pollutant: str) -> str:
    """Format pollutant name for display"""
    name_mapping = {
        'pm25': 'PM₂.₅',
        'pm2.5': 'PM₂.₅',
        'pm_25': 'PM₂.₅',
        'pm10': 'PM₁₀',
        'pm_10': 'PM₁₀',
        'o3': 'O₃',
        'ozone': 'O₃',
        'no2': 'NO₂',
        'so2': 'SO₂',
        'co': 'CO',
        'hcho': 'HCHO',
        'formaldehyde': 'HCHO'
    }
    
    return name_mapping.get(pollutant.lower(), pollutant.upper())

def get_pollutant_description(pollutant: str) -> str:
    """Get description for pollutant"""
    descriptions = {
        'PM2.5': 'Fine particulate matter with diameter ≤ 2.5 micrometers',
        'PM10': 'Coarse particulate matter with diameter ≤ 10 micrometers',
        'O3': 'Ground-level ozone',
        'NO2': 'Nitrogen dioxide',
        'SO2': 'Sulfur dioxide',
        'CO': 'Carbon monoxide',
        'HCHO': 'Formaldehyde'
    }
    
    formatted_name = format_pollutant_name(pollutant)
    return descriptions.get(formatted_name, f"{formatted_name} concentration")

def get_health_message_for_aqi(aqi: float) -> str:
    """Get health message for AQI value"""
    if pd.isna(aqi) or aqi is None:
        return "Air quality information unavailable"
    
    if aqi <= 50:
        return "Air quality is satisfactory and poses little or no risk."
    elif aqi <= 100:
        return "Air quality is acceptable. Unusually sensitive people should consider reducing prolonged outdoor exertion."
    elif aqi <= 150:
        return "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
    elif aqi <= 200:
        return "Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects."
    elif aqi <= 300:
        return "Health alert: The risk of health effects is increased for everyone."
    else:
        return "Health warning of emergency conditions: everyone is more likely to be affected."

def get_activity_recommendations(aqi: float) -> List[str]:
    """Get activity recommendations based on AQI"""
    if pd.isna(aqi) or aqi is None:
        return ["Monitor air quality updates"]
    
    if aqi <= 50:
        return [
            "🏃‍♂️ Great conditions for outdoor activities",
            "🚴‍♀️ Perfect for exercise and sports",
            "🌳 Enjoy outdoor recreation"
        ]
    elif aqi <= 100:
        return [
            "🚶‍♂️ Most outdoor activities are fine",
            "⚠️ Unusually sensitive people should watch for symptoms",
            "🏃‍♂️ Reduce prolonged vigorous exercise if sensitive"
        ]
    elif aqi <= 150:
        return [
            "👶 Children and elderly should limit prolonged outdoor activities",
            "🫁 People with heart/lung conditions should reduce outdoor exertion",
            "😷 Consider wearing masks during outdoor activities",
            "🏠 Take breaks indoors when possible"
        ]
    elif aqi <= 200:
        return [
            "🚨 Everyone should limit prolonged outdoor activities",
            "😷 Consider wearing N95 masks when outside",
            "🏠 Stay indoors when possible",
            "🚪 Keep windows and doors closed"
        ]
    elif aqi <= 300:
        return [
            "🚨 Avoid all outdoor activities",
            "😷 Wear N95 masks if you must go outside",
            "🏠 Stay indoors with air purifiers running",
            "🚪 Keep all windows and doors sealed"
        ]
    else:
        return [
            "🚨 Emergency conditions - stay indoors",
            "😷 N95 masks required for any outdoor exposure",
            "🏥 Seek medical attention if experiencing symptoms",
            "📞 Follow official emergency guidance"
        ]

def format_units(value: float, units: str) -> str:
    """Format measurement value with units"""
    if pd.isna(value):
        return "N/A"
    
    # Format based on value magnitude
    if abs(value) >= 1e6:
        return f"{value:.2e} {units}"
    elif abs(value) >= 1000:
        return f"{value:.0f} {units}"
    elif abs(value) >= 1:
        return f"{value:.1f} {units}"
    else:
        return f"{value:.2f} {units}"

def create_shareable_url(params: Dict[str, Any]) -> str:
    """Create a shareable URL with parameters"""
    base_url = "https://cleansky-ai.streamlit.app"
    
    if not params:
        return base_url
    
    # Convert parameters to query string
    param_strings = []
    for key, value in params.items():
        if value is not None:
            param_strings.append(f"{key}={value}")
    
    if param_strings:
        return f"{base_url}?{'&'.join(param_strings)}"
    
    return base_url

def get_wind_direction_name(degrees: float) -> str:
    """Convert wind direction degrees to compass direction"""
    if pd.isna(degrees):
        return "Variable"
    
    # Normalize to 0-360
    degrees = degrees % 360
    
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE", 
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    
    # Calculate index (16 directions)
    index = int((degrees + 11.25) / 22.5) % 16
    
    return directions[index]

def calculate_air_quality_trend(data: List[float], window: int = 3) -> str:
    """Calculate trend in air quality data"""
    if not data or len(data) < window:
        return "Insufficient data"
    
    # Use moving average to smooth data
    if len(data) >= window * 2:
        recent_avg = np.mean(data[-window:])
        previous_avg = np.mean(data[-(window*2):-window])
        
        change = recent_avg - previous_avg
        change_percent = abs(change / previous_avg * 100) if previous_avg != 0 else 0
        
        if change_percent < 5:  # Less than 5% change
            return "Stable"
        elif change > 0:
            return "Worsening"
        else:
            return "Improving"
    
    # Simple comparison of first and last values
    if data[-1] > data[0]:
        return "Worsening"
    elif data[-1] < data[0]:
        return "Improving"
    else:
        return "Stable"

def get_seasonal_context(date: datetime = None) -> Dict[str, Any]:
    """Get seasonal context for air quality interpretation"""
    if date is None:
        date = datetime.now()
    
    month = date.month
    
    # Define seasons (Northern Hemisphere)
    if month in [12, 1, 2]:
        season = "Winter"
        context = {
            "season": season,
            "typical_issues": ["Heating emissions", "Inversion layers", "Reduced ventilation"],
            "common_pollutants": ["PM2.5", "CO", "NO2"],
            "recommendations": ["Monitor indoor air quality", "Ensure proper ventilation"]
        }
    elif month in [3, 4, 5]:
        season = "Spring"
        context = {
            "season": season,
            "typical_issues": ["Pollen", "Dust storms", "Temperature fluctuations"],
            "common_pollutants": ["PM10", "O3"],
            "recommendations": ["Be aware of allergens", "Monitor ozone levels"]
        }
    elif month in [6, 7, 8]:
        season = "Summer"
        context = {
            "season": season,
            "typical_issues": ["Photochemical smog", "Wildfires", "Heat inversions"],
            "common_pollutants": ["O3", "PM2.5"],
            "recommendations": ["Avoid midday outdoor activities", "Stay hydrated"]
        }
    else:  # Fall
        season = "Fall"
        context = {
            "season": season,
            "typical_issues": ["Leaf burning", "Increased heating", "Weather changes"],
            "common_pollutants": ["PM2.5", "CO"],
            "recommendations": ["Prepare for heating season", "Monitor weather patterns"]
        }
    
    return context

def is_mobile_device() -> bool:
    """Detect if user is on mobile device (simplified)"""
    # This is a basic detection - in a real app you'd use JavaScript
    # For now, assume desktop
    return False

def get_user_preferences() -> Dict[str, Any]:
    """Get user preferences from session state"""
    default_prefs = {
        'temperature_unit': '°F',
        'distance_unit': 'miles',
        'time_format': '12h',
        'theme': 'light',
        'alert_threshold': 100,
        'notifications_enabled': True
    }
    
    # Get from session state or use defaults
    prefs = {}
    for key, default in default_prefs.items():
        prefs[key] = st.session_state.get(f"pref_{key}", default)
    
    return prefs

def save_user_preferences(preferences: Dict[str, Any]):
    """Save user preferences to session state"""
    for key, value in preferences.items():
        st.session_state[f"pref_{key}"] = value

def format_number(value: float, precision: int = 1) -> str:
    """Format number with appropriate precision and thousands separator"""
    if pd.isna(value):
        return "N/A"
    
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:.{precision}f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.{precision}f}K"
    else:
        return f"{value:.{precision}f}"

def get_browser_timezone() -> str:
    """Get browser timezone (simplified - would use JavaScript in real app)"""
    # For now, return a default timezone
    return "America/New_York"

def create_error_message(error: Exception, context: str = "") -> str:
    """Create user-friendly error message"""
    error_messages = {
        "ConnectionError": "Unable to connect to data services. Please check your internet connection.",
        "TimeoutError": "Request timed out. Please try again later.",
        "ValueError": "Invalid data received. Please refresh and try again.",
        "KeyError": "Missing required data. Please contact support if this persists."
    }
    
    error_type = type(error).__name__
    user_message = error_messages.get(error_type, "An unexpected error occurred.")
    
    if context:
        user_message = f"{context}: {user_message}"
    
    return user_message
