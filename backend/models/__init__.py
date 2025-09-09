"""
CleanSky AI Backend Models Package

This package contains all database models and business logic for CleanSky AI.
"""

from .database import (
    Base,
    DatabaseManager,
    init_db,
    get_db,
    AirQualityMeasurement,
    TempoMeasurement,
    WeatherData,
    AirQualityForecast,
    User,
    AlertLog,
    DataIngestionLog,
    ModelTrainingLog
)

from .air_quality_model import (
    AirQualityStation,
    AirQualityReading,
    AirQualityService
)

from .forecast_model import (
    ForecastModel,
    ForecastPrediction,
    ModelPerformanceLog,
    ForecastService
)

__all__ = [
    # Database core
    'Base',
    'DatabaseManager', 
    'init_db',
    'get_db',
    
    # Database models (from database.py)
    'AirQualityMeasurement',
    'TempoMeasurement',
    'WeatherData',
    'AirQualityForecast',
    'User',
    'AlertLog',
    'DataIngestionLog',
    'ModelTrainingLog',
    
    # Air Quality models (from air_quality_model.py)
    'AirQualityStation',
    'AirQualityReading',
    'AirQualityService',
    
    # Forecast models (from forecast_model.py)
    'ForecastModel',
    'ForecastPrediction',
    'ModelPerformanceLog',
    'ForecastService'
]
