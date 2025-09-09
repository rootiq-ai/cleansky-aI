"""
Air Quality data models and business logic for CleanSky AI
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import structlog
import pandas as pd
import numpy as np

from backend.models.database import Base
from backend.utils.data_processor import AQICalculator

logger = structlog.get_logger()

class AirQualityStation(Base):
    """Model for air quality monitoring stations"""
    __tablename__ = 'air_quality_stations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation = Column(Float, nullable=True)
    
    # Administrative info
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(50), default='US')
    zip_code = Column(String(20), nullable=True)
    
    # Station metadata
    data_source = Column(String(50), nullable=False)  # 'EPA', 'AirNow', etc.
    station_type = Column(String(50), nullable=True)  # 'urban', 'suburban', 'rural'
    monitor_types = Column(JSON, nullable=True)  # List of monitored pollutants
    
    # Status
    is_active = Column(Boolean, default=True)
    last_data_time = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for geographic queries
    __table_args__ = (
        Index('idx_station_location', 'latitude', 'longitude'),
        Index('idx_station_source_active', 'data_source', 'is_active'),
    )
    
    def __repr__(self):
        return f"<AirQualityStation(id={self.station_id}, name={self.name})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert station to dictionary"""
        return {
            'station_id': self.station_id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'elevation': self.elevation,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'data_source': self.data_source,
            'station_type': self.station_type,
            'monitor_types': self.monitor_types,
            'is_active': self.is_active,
            'last_data_time': self.last_data_time.isoformat() if self.last_data_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AirQualityReading(Base):
    """Model for individual air quality readings"""
    __tablename__ = 'air_quality_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Station reference
    station_id = Column(String(100), nullable=False, index=True)
    
    # Time and location
    timestamp = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Air Quality Index
    aqi = Column(Float, nullable=True, index=True)
    aqi_category = Column(String(50), nullable=True)
    primary_pollutant = Column(String(20), nullable=True)
    
    # Individual pollutant concentrations
    pm25_concentration = Column(Float, nullable=True)
    pm25_aqi = Column(Float, nullable=True)
    
    pm10_concentration = Column(Float, nullable=True)
    pm10_aqi = Column(Float, nullable=True)
    
    ozone_concentration = Column(Float, nullable=True)
    ozone_aqi = Column(Float, nullable=True)
    
    no2_concentration = Column(Float, nullable=True)
    no2_aqi = Column(Float, nullable=True)
    
    so2_concentration = Column(Float, nullable=True)
    so2_aqi = Column(Float, nullable=True)
    
    co_concentration = Column(Float, nullable=True)
    co_aqi = Column(Float, nullable=True)
    
    # Data quality and metadata
    data_source = Column(String(50), nullable=False)
    quality_flag = Column(String(20), default='valid')
    measurement_method = Column(String(100), nullable=True)
    
    # Raw data storage
    raw_data = Column(JSON, nullable=True)
    
    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_reading_station_time', 'station_id', 'timestamp'),
        Index('idx_reading_location_time', 'latitude', 'longitude', 'timestamp'),
        Index('idx_reading_aqi_time', 'aqi', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AirQualityReading(station={self.station_id}, aqi={self.aqi}, time={self.timestamp})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reading to dictionary"""
        return {
            'station_id': self.station_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'aqi': self.aqi,
            'aqi_category': self.aqi_category,
            'primary_pollutant': self.primary_pollutant,
            'pollutants': {
                'PM2.5': {
                    'concentration': self.pm25_concentration,
                    'aqi': self.pm25_aqi
                },
                'PM10': {
                    'concentration': self.pm10_concentration,
                    'aqi': self.pm10_aqi
                },
                'O3': {
                    'concentration': self.ozone_concentration,
                    'aqi': self.ozone_aqi
                },
                'NO2': {
                    'concentration': self.no2_concentration,
                    'aqi': self.no2_aqi
                },
                'SO2': {
                    'concentration': self.so2_concentration,
                    'aqi': self.so2_aqi
                },
                'CO': {
                    'concentration': self.co_concentration,
                    'aqi': self.co_aqi
                }
            },
            'data_source': self.data_source,
            'quality_flag': self.quality_flag,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class AirQualityService:
    """Business logic service for air quality data"""
    
    def __init__(self):
        self.aqi_calculator = AQICalculator()
    
    def get_stations_near_location(
        self,
        session: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 25,
        limit: int = 10
    ) -> List[AirQualityStation]:
        """Get air quality stations near a location"""
        try:
            # Simple distance calculation using lat/lon bounds
            # For more accurate results, would use spatial database functions
            lat_delta = radius_km / 111.0  # Approximate km per degree latitude
            lon_delta = radius_km / (111.0 * abs(np.cos(np.radians(latitude))))
            
            stations = session.query(AirQualityStation).filter(
                AirQualityStation.is_active == True,
                AirQualityStation.latitude.between(
                    latitude - lat_delta, latitude + lat_delta
                ),
                AirQualityStation.longitude.between(
                    longitude - lon_delta, longitude + lon_delta
                )
            ).limit(limit).all()
            
            # Calculate actual distances and sort
            stations_with_distance = []
            for station in stations:
                distance = self._calculate_distance(
                    latitude, longitude,
                    station.latitude, station.longitude
                )
                if distance <= radius_km:
                    stations_with_distance.append((station, distance))
            
            # Sort by distance
            stations_with_distance.sort(key=lambda x: x[1])
            
            return [station for station, distance in stations_with_distance]
            
        except Exception as e:
            logger.error(f"Error getting stations near location: {str(e)}")
            return []
    
    def get_latest_readings_for_stations(
        self,
        session: Session,
        station_ids: List[str],
        hours_back: int = 24
    ) -> Dict[str, AirQualityReading]:
        """Get latest readings for multiple stations"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Get latest reading for each station
            latest_readings = {}
            
            for station_id in station_ids:
                reading = session.query(AirQualityReading).filter(
                    AirQualityReading.station_id == station_id,
                    AirQualityReading.timestamp >= cutoff_time,
                    AirQualityReading.quality_flag == 'valid'
                ).order_by(
                    AirQualityReading.timestamp.desc()
                ).first()
                
                if reading:
                    latest_readings[station_id] = reading
            
            return latest_readings
            
        except Exception as e:
            logger.error(f"Error getting latest readings: {str(e)}")
            return {}
    
    def get_historical_data(
        self,
        session: Session,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        radius_km: float = 25
    ) -> pd.DataFrame:
        """Get historical air quality data for a location"""
        try:
            # Get nearby stations
            stations = self.get_stations_near_location(
                session, latitude, longitude, radius_km
            )
            
            if not stations:
                return pd.DataFrame()
            
            station_ids = [s.station_id for s in stations]
            
            # Get readings for time period
            readings = session.query(AirQualityReading).filter(
                AirQualityReading.station_id.in_(station_ids),
                AirQualityReading.timestamp.between(start_date, end_date),
                AirQualityReading.quality_flag == 'valid'
            ).order_by(AirQualityReading.timestamp).all()
            
            # Convert to DataFrame
            data = []
            for reading in readings:
                data.append({
                    'timestamp': reading.timestamp,
                    'station_id': reading.station_id,
                    'latitude': reading.latitude,
                    'longitude': reading.longitude,
                    'aqi': reading.aqi,
                    'aqi_category': reading.aqi_category,
                    'primary_pollutant': reading.primary_pollutant,
                    'pm25': reading.pm25_concentration,
                    'pm10': reading.pm10_concentration,
                    'ozone': reading.ozone_concentration,
                    'no2': reading.no2_concentration,
                    'so2': reading.so2_concentration,
                    'co': reading.co_concentration
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return pd.DataFrame()
    
    def calculate_area_summary(
        self,
        session: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 25
    ) -> Dict[str, Any]:
        """Calculate summary statistics for an area"""
        try:
            # Get recent readings from nearby stations
            stations = self.get_stations_near_location(
                session, latitude, longitude, radius_km
            )
            
            if not stations:
                return {}
            
            station_ids = [s.station_id for s in stations]
            latest_readings = self.get_latest_readings_for_stations(
                session, station_ids
            )
            
            if not latest_readings:
                return {}
            
            # Calculate summary statistics
            aqi_values = [r.aqi for r in latest_readings.values() if r.aqi is not None]
            
            if not aqi_values:
                return {}
            
            # Find primary pollutant across all stations
            pollutant_counts = {}
            for reading in latest_readings.values():
                if reading.primary_pollutant:
                    pollutant_counts[reading.primary_pollutant] = \
                        pollutant_counts.get(reading.primary_pollutant, 0) + 1
            
            primary_pollutant = max(pollutant_counts.items(), 
                                  key=lambda x: x[1])[0] if pollutant_counts else None
            
            summary = {
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius_km
                },
                'current_aqi': {
                    'average': np.mean(aqi_values),
                    'maximum': max(aqi_values),
                    'minimum': min(aqi_values),
                    'median': np.median(aqi_values)
                },
                'primary_pollutant': primary_pollutant,
                'station_count': len(latest_readings),
                'data_timestamp': max(r.timestamp for r in latest_readings.values()).isoformat(),
                'aqi_category': self._get_aqi_category(max(aqi_values))
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating area summary: {str(e)}")
            return {}
    
    def store_reading(
        self,
        session: Session,
        reading_data: Dict[str, Any]
    ) -> AirQualityReading:
        """Store a new air quality reading"""
        try:
            # Calculate AQI if not provided
            if not reading_data.get('aqi'):
                aqi_data = self.aqi_calculator.calculate_aqi(reading_data)
                reading_data.update(aqi_data)
            
            # Create reading object
            reading = AirQualityReading(
                station_id=reading_data.get('station_id'),
                timestamp=reading_data.get('timestamp', datetime.utcnow()),
                latitude=reading_data.get('latitude'),
                longitude=reading_data.get('longitude'),
                aqi=reading_data.get('aqi'),
                aqi_category=reading_data.get('aqi_category'),
                primary_pollutant=reading_data.get('primary_pollutant'),
                pm25_concentration=reading_data.get('pm25_concentration'),
                pm25_aqi=reading_data.get('pm25_aqi'),
                pm10_concentration=reading_data.get('pm10_concentration'),
                pm10_aqi=reading_data.get('pm10_aqi'),
                ozone_concentration=reading_data.get('ozone_concentration'),
                ozone_aqi=reading_data.get('ozone_aqi'),
                no2_concentration=reading_data.get('no2_concentration'),
                no2_aqi=reading_data.get('no2_aqi'),
                so2_concentration=reading_data.get('so2_concentration'),
                so2_aqi=reading_data.get('so2_aqi'),
                co_concentration=reading_data.get('co_concentration'),
                co_aqi=reading_data.get('co_aqi'),
                data_source=reading_data.get('data_source', 'unknown'),
                quality_flag=reading_data.get('quality_flag', 'valid'),
                raw_data=reading_data.get('raw_data')
            )
            
            session.add(reading)
            session.commit()
            
            logger.info(f"Stored air quality reading for station {reading.station_id}")
            return reading
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing air quality reading: {str(e)}")
            raise
    
    def create_or_update_station(
        self,
        session: Session,
        station_data: Dict[str, Any]
    ) -> AirQualityStation:
        """Create or update an air quality station"""
        try:
            station_id = station_data.get('station_id')
            
            # Check if station exists
            station = session.query(AirQualityStation).filter(
                AirQualityStation.station_id == station_id
            ).first()
            
            if station:
                # Update existing station
                for key, value in station_data.items():
                    if hasattr(station, key) and key != 'id':
                        setattr(station, key, value)
                station.updated_at = datetime.utcnow()
            else:
                # Create new station
                station = AirQualityStation(**station_data)
            
            session.add(station)
            session.commit()
            
            logger.info(f"{'Updated' if station else 'Created'} station {station_id}")
            return station
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating station: {str(e)}")
            raise
    
    def get_data_quality_report(
        self,
        session: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate data quality report"""
        try:
            # Count total readings
            total_readings = session.query(AirQualityReading).filter(
                AirQualityReading.timestamp.between(start_date, end_date)
            ).count()
            
            # Count by quality flag
            quality_counts = session.query(
                AirQualityReading.quality_flag,
                session.query(AirQualityReading).filter(
                    AirQualityReading.timestamp.between(start_date, end_date),
                    AirQualityReading.quality_flag == AirQualityReading.quality_flag
                ).count().label('count')
            ).group_by(AirQualityReading.quality_flag).all()
            
            # Count by data source
            source_counts = session.query(
                AirQualityReading.data_source,
                session.query(AirQualityReading).filter(
                    AirQualityReading.timestamp.between(start_date, end_date),
                    AirQualityReading.data_source == AirQualityReading.data_source
                ).count().label('count')
            ).group_by(AirQualityReading.data_source).all()
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_readings': total_readings,
                'quality_breakdown': {qf: count for qf, count in quality_counts},
                'source_breakdown': {src: count for src, count in source_counts},
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating data quality report: {str(e)}")
            return {}
    
    def _calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers"""
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in kilometers
        r = 6371
        
        return c * r
    
    def _get_aqi_category(self, aqi: float) -> str:
        """Get AQI category name"""
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
