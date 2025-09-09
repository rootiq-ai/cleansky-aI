"""
Air Quality API routes for CleanSky AI
"""
from flask import request, current_app
from flask_restful import Resource
import structlog
from datetime import datetime, timedelta
import json

from backend.services.ground_station_service import GroundStationService
from backend.services.ml_service import MLService
from backend.utils.validators import validate_coordinates, validate_date_range
from backend.utils.data_processor import AQICalculator

logger = structlog.get_logger()

class AirQualityAPI(Resource):
    """Air Quality data API endpoints"""
    
    def __init__(self):
        self.ground_service = GroundStationService()
        self.ml_service = MLService()
        self.aqi_calculator = AQICalculator()
    
    def get(self, location=None):
        """Get current air quality data"""
        try:
            # Parse query parameters
            lat = request.args.get('lat', type=float)
            lon = request.args.get('lon', type=float)
            radius = request.args.get('radius', 25, type=int)  # km
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Validate coordinates if provided
            if lat is not None and lon is not None:
                if not validate_coordinates(lat, lon):
                    return {'error': 'Invalid coordinates'}, 400
                location = f"{lat},{lon}"
            
            # Validate date range
            if start_date or end_date:
                if not validate_date_range(start_date, end_date):
                    return {'error': 'Invalid date range'}, 400
            
            # Default to last 24 hours if no date range specified
            if not start_date:
                start_date = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            if not end_date:
                end_date = datetime.utcnow().isoformat()
            
            logger.info(f"Fetching air quality data for location: {location}")
            
            # Get ground station data
            ground_data = self.ground_service.get_air_quality_data(
                location=location,
                radius=radius,
                start_date=start_date,
                end_date=end_date
            )
            
            if not ground_data:
                return {
                    'error': 'No air quality data available for specified location and time range'
                }, 404
            
            # Calculate AQI values
            processed_data = []
            for station_data in ground_data:
                aqi_data = self.aqi_calculator.calculate_aqi(station_data)
                processed_data.append(aqi_data)
            
            # Get current conditions summary
            current_summary = self._get_current_summary(processed_data)
            
            return {
                'status': 'success',
                'location': location,
                'timestamp': datetime.utcnow().isoformat(),
                'current_summary': current_summary,
                'stations': processed_data,
                'metadata': {
                    'total_stations': len(processed_data),
                    'radius_km': radius,
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching air quality data: {str(e)}")
            return {'error': 'Failed to fetch air quality data'}, 500
    
    def post(self):
        """Get air quality forecast"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            lat = data.get('lat')
            lon = data.get('lon')
            forecast_hours = data.get('forecast_hours', 24)
            
            if not validate_coordinates(lat, lon):
                return {'error': 'Invalid coordinates'}, 400
            
            if not (1 <= forecast_hours <= 72):
                return {'error': 'Forecast hours must be between 1 and 72'}, 400
            
            logger.info(f"Generating air quality forecast for {lat}, {lon}")
            
            # Get historical data for ML model
            historical_data = self.ground_service.get_historical_data(
                lat=lat,
                lon=lon,
                days_back=7
            )
            
            # Generate forecast using ML model
            forecast_data = self.ml_service.predict_air_quality(
                lat=lat,
                lon=lon,
                forecast_hours=forecast_hours,
                historical_data=historical_data
            )
            
            # Calculate health recommendations
            recommendations = self._get_health_recommendations(forecast_data)
            
            return {
                'status': 'success',
                'location': f"{lat},{lon}",
                'forecast_generated': datetime.utcnow().isoformat(),
                'forecast_hours': forecast_hours,
                'forecast': forecast_data,
                'health_recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating air quality forecast: {str(e)}")
            return {'error': 'Failed to generate forecast'}, 500
    
    def _get_current_summary(self, station_data):
        """Calculate current air quality summary"""
        if not station_data:
            return None
        
        # Get the most recent data point
        latest_data = max(station_data, key=lambda x: x.get('timestamp', ''))
        
        # Calculate overall AQI
        aqi_values = [data.get('aqi', 0) for data in station_data if data.get('aqi')]
        if not aqi_values:
            return None
        
        avg_aqi = sum(aqi_values) / len(aqi_values)
        max_aqi = max(aqi_values)
        
        # Determine air quality category
        category = self.aqi_calculator.get_aqi_category(max_aqi)
        
        return {
            'average_aqi': round(avg_aqi, 1),
            'maximum_aqi': max_aqi,
            'category': category,
            'primary_pollutant': latest_data.get('primary_pollutant'),
            'last_updated': latest_data.get('timestamp'),
            'station_count': len(station_data)
        }
    
    def _get_health_recommendations(self, forecast_data):
        """Generate health recommendations based on forecast"""
        recommendations = []
        
        max_aqi_forecast = max([point.get('aqi', 0) for point in forecast_data])
        
        if max_aqi_forecast > 150:
            recommendations.extend([
                "Avoid outdoor activities, especially strenuous exercise",
                "Keep windows closed and use air purifiers indoors",
                "Consider wearing N95 masks when going outside",
                "People with heart/lung conditions should stay indoors"
            ])
        elif max_aqi_forecast > 100:
            recommendations.extend([
                "Limit prolonged outdoor activities",
                "Sensitive individuals should reduce outdoor exercise",
                "Consider rescheduling outdoor events",
                "Monitor symptoms if you have respiratory conditions"
            ])
        elif max_aqi_forecast > 50:
            recommendations.extend([
                "Air quality is moderate - most people can enjoy outdoor activities",
                "Unusually sensitive people may experience minor symptoms",
                "Consider reducing prolonged vigorous exercise"
            ])
        else:
            recommendations.append("Air quality is good - enjoy outdoor activities!")
        
        return recommendations
