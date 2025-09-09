"""
Database models for CleanSky AI
"""
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()

Base = declarative_base()

class AirQualityMeasurement(Base):
    """Air quality measurement from ground stations"""
    __tablename__ = 'air_quality_measurements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # AQI and pollutant data
    aqi = Column(Float, nullable=True)
    primary_pollutant = Column(String(20), nullable=True)
    
    # Individual pollutant measurements
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    ozone = Column(Float, nullable=True)
    no2 = Column(Float, nullable=True)
    so2 = Column(Float, nullable=True)
    co = Column(Float, nullable=True)
    
    # Metadata
    data_source = Column(String(50), nullable=False)
    quality_flag = Column(String(20), default='good')
    raw_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AirQualityMeasurement(station={self.station_id}, aqi={self.aqi}, timestamp={self.timestamp})>"

class TempoMeasurement(Base):
    """TEMPO satellite measurements"""
    __tablename__ = 'tempo_measurements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Measurement data
    parameter = Column(String(20), nullable=False, index=True)
    value = Column(Float, nullable=False)
    units = Column(String(50), nullable=False)
    
    # Quality and processing info
    quality_flag = Column(String(20), default='good')
    cloud_fraction = Column(Float, nullable=True)
    solar_zenith_angle = Column(Float, nullable=True)
    
    # Metadata
    pixel_corner_lats = Column(JSON, nullable=True)
    pixel_corner_lons = Column(JSON, nullable=True)
    processing_level = Column(String(10), default='L2')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TempoMeasurement(parameter={self.parameter}, value={self.value}, timestamp={self.timestamp})>"

class WeatherData(Base):
    """Weather observations and forecasts"""
    __tablename__ = 'weather_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Weather parameters
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    visibility = Column(Float, nullable=True)
    cloudiness = Column(Float, nullable=True)
    
    # Weather conditions
    conditions = Column(String(100), nullable=True)
    description = Column(String(200), nullable=True)
    
    # Data source and type
    data_source = Column(String(50), nullable=False)
    data_type = Column(String(20), nullable=False)  # 'observation' or 'forecast'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<WeatherData(temp={self.temperature}, conditions={self.conditions}, timestamp={self.timestamp})>"

class AirQualityForecast(Base):
    """Air quality forecast predictions"""
    __tablename__ = 'air_quality_forecasts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_timestamp = Column(DateTime, nullable=False, index=True)
    target_timestamp = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Forecast data
    predicted_aqi = Column(Float, nullable=False)
    predicted_primary_pollutant = Column(String(20), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Model information
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)
    input_features = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AirQualityForecast(aqi={self.predicted_aqi}, target={self.target_timestamp})>"

class User(Base):
    """User accounts and preferences"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Location preferences
    home_latitude = Column(Float, nullable=True)
    home_longitude = Column(Float, nullable=True)
    
    # Notification preferences
    email_alerts = Column(Boolean, default=True)
    sms_alerts = Column(Boolean, default=False)
    push_alerts = Column(Boolean, default=True)
    alert_threshold = Column(Integer, default=100)
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

class AlertLog(Base):
    """Log of sent alerts and notifications"""
    __tablename__ = 'alert_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    
    # Location context
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)
    
    # Trigger data
    aqi_value = Column(Float, nullable=True)
    primary_pollutant = Column(String(20), nullable=True)
    
    # Delivery information
    channels = Column(JSON, nullable=False)  # ['email', 'sms', 'push']
    delivery_status = Column(JSON, nullable=False)  # {channel: status}
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<AlertLog(type={self.alert_type}, severity={self.severity}, user={self.user_id})>"

class DataIngestionLog(Base):
    """Log of data ingestion operations"""
    __tablename__ = 'data_ingestion_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Operation details
    data_source = Column(String(50), nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)  # 'fetch', 'process', 'store'
    status = Column(String(20), nullable=False, index=True)  # 'success', 'error', 'partial'
    
    # Metrics
    records_processed = Column(Integer, default=0)
    records_success = Column(Integer, default=0)
    records_error = Column(Integer, default=0)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DataIngestionLog(source={self.data_source}, status={self.status})>"

class ModelTrainingLog(Base):
    """Log of model training operations"""
    __tablename__ = 'model_training_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Model details
    model_type = Column(String(50), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Training metrics
    training_samples = Column(Integer, nullable=False)
    validation_samples = Column(Integer, nullable=False)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    r2_score = Column(Float, nullable=True)
    
    # Training configuration
    hyperparameters = Column(JSON, nullable=True)
    features = Column(JSON, nullable=True)
    
    # Status and timing
    status = Column(String(20), nullable=False)  # 'training', 'completed', 'failed'
    training_time_seconds = Column(Float, nullable=True)
    
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelTrainingLog(type={self.model_type}, rmse={self.rmse})>"

# Database initialization and session management
class DatabaseManager:
    """Database manager for CleanSky AI"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///cleansky.db')
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Database initialized: {database_url}")
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")

# Global database manager instance
db_manager = None

def init_db(app=None):
    """Initialize database for Flask app"""
    global db_manager
    
    database_url = None
    if app:
        database_url = app.config.get('DATABASE_URL')
    
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    
    return db_manager

def get_db():
    """Get database session (for dependency injection)"""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    session = db_manager.get_session()
    try:
        yield session
    finally:
        db_manager.close_session(session)
