"""
CleanSky AI Backend Services Package

This package contains all data services and integrations for CleanSky AI.
"""

from .tempo_service import TempoService
from .weather_service import WeatherService
from .ground_station_service import GroundStationService
from .ml_service import MLService

# Import other services that will be created
try:
    from .notification_service import NotificationService
except ImportError:
    NotificationService = None

try:
    from .data_ingestion_service import DataIngestionService
except ImportError:
    DataIngestionService = None

try:
    from .alert_service import AlertService
except ImportError:
    AlertService = None

try:
    from .cache_service import CacheService
except ImportError:
    CacheService = None

try:
    from .auth_service import AuthService
except ImportError:
    AuthService = None

__all__ = [
    # Core data services
    'TempoService',
    'WeatherService', 
    'GroundStationService',
    'MLService',
    
    # Additional services (if available)
    'NotificationService',
    'DataIngestionService',
    'AlertService',
    'CacheService',
    'AuthService'
]
