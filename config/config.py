"""
Configuration management for CleanSky AI
"""
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'cleansky-ai-secret-key-2024')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///cleansky.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # API Keys
    NASA_EARTHDATA_TOKEN = os.getenv('NASA_EARTHDATA_TOKEN')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    EPA_API_KEY = os.getenv('EPA_API_KEY')
    
    # TEMPO satellite data settings
    TEMPO_DATA_URL = 'https://disc.gsfc.nasa.gov/datasets/TEMPO_NO2_L3'
    TEMPO_UPDATE_INTERVAL = 3600  # 1 hour in seconds
    
    # Ground station data sources
    EPA_AQS_URL = 'https://aqs.epa.gov/data/api'
    AIRNOW_API_URL = 'https://www.airnowapi.org/aq'
    
    # Weather data
    WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5'
    
    # ML Model settings
    MODEL_UPDATE_FREQUENCY = 24  # hours
    PREDICTION_HORIZON = 72  # hours
    
    # Notification settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    
    # Alert thresholds (AQI values)
    AQI_THRESHOLDS = {
        'moderate': 51,
        'unhealthy_sensitive': 101,
        'unhealthy': 151,
        'very_unhealthy': 201,
        'hazardous': 301
    }
    
    # Geographical bounds (North America)
    GEOGRAPHICAL_BOUNDS = {
        'north': 70.0,
        'south': 15.0,
        'east': -50.0,
        'west': -170.0
    }
    
    # Data processing settings
    DATA_CACHE_DURATION = 1800  # 30 minutes
    MAX_CONCURRENT_REQUESTS = 10
    REQUEST_TIMEOUT = 30
    
    # Streamlit settings
    STREAMLIT_SERVER_PORT = 8501
    STREAMLIT_SERVER_ADDRESS = '0.0.0.0'
    
    # Flask API settings
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Use more secure settings for production
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/cleansky')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis-server:6379/0')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def load_yaml_config():
    """Load additional configuration from YAML file"""
    config_path = Path(__file__).parent / 'settings.yaml'
    if config_path.exists():
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    return {}

def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    return config[config_name]
