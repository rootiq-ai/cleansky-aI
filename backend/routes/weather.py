"""
Weather API routes for CleanSky AI
"""
from flask import request, current_app
from flask_restful import Resource
import structlog
from datetime import datetime, timedelta

from backend.services.weather_service import WeatherService
from backend.utils.validators import validate_coordinates

logger = structlog.get_logger()

class WeatherAPI(Resource):
    """Weather data API endpoints"""
    
    def __init__(self):
        self.weather_service = WeatherService()
    
    def get(self, location=None):
        """Get current weather data"""
        try:
            # Parse query parameters
            lat = request.args.get('lat', type=float)
            lon = request.args.get('lon', type=float)
            include_forecast = request.args.get('forecast', 'false').lower() == 'true'
            units = request.args.get('units', 'metric')  # metric, imperial, standard
            
            # Validate coordinates
            if lat is None or lon is None:
                return {'error': 'Latitude and longitude are required'}, 400
            
            if not validate_coordinates(lat, lon):
                return {'error': 'Invalid coordinates'}, 400
            
            logger.info(f"Fetching weather data for {lat}, {lon}")
            
            # Get current weather
            current_weather = self.weather_service.get_current_weather(lat, lon, units)
            
            if not current_weather:
                return {'error': 'Unable to fetch weather data'}, 404
            
            response_data = {
                'status': 'success',
                'location': f"{lat},{lon}",
                'timestamp': datetime.utcnow().isoformat(),
                'data': current_weather
            }
            
            # Add forecast if requested
            if include_forecast:
                forecast_data = self.weather_service.get_forecast(lat, lon, units)
                if forecast_data:
                    response_data['forecast'] = forecast_data
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return {'error': 'Failed to fetch weather data'}, 500
    
    def post(self):
        """Get weather data for multiple locations"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            locations = data.get('locations', [])
            include_forecast = data.get('include_forecast', False)
            units = data.get('units', 'metric')
            
            if not locations:
                return {'error': 'No locations specified'}, 400
            
            # Validate all locations
            for i, loc in enumerate(locations):
                if not validate_coordinates(loc.get('lat'), loc.get('lon')):
                    return {'error': f'Invalid coordinates for location {i+1}'}, 400
            
            logger.info(f"Fetching weather data for {len(locations)} locations")
            
            results = []
            for location in locations:
                try:
                    lat, lon = location['lat'], location['lon']
                    
                    # Get current weather
                    current_weather = self.weather_service.get_current_weather(lat, lon, units)
                    
                    location_result = {
                        'location': location,
                        'status': 'success',
                        'data': current_weather
                    }
                    
                    # Add forecast if requested
                    if include_forecast:
                        forecast = self.weather_service.get_forecast(lat, lon, units)
                        if forecast:
                            location_result['forecast'] = forecast
                    
                    results.append(location_result)
                    
                except Exception as e:
                    logger.error(f"Error processing location {location}: {str(e)}")
                    results.append({
                        'location': location,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Generate summary
            successful = sum(1 for r in results if r['status'] == 'success')
            summary = {
                'total_locations': len(locations),
                'successful': successful,
                'failed': len(locations) - successful
            }
            
            return {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'summary': summary,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing batch weather request: {str(e)}")
            return {'error': 'Failed to process batch request'}, 500
