"""
Flask backend application for CleanSky AI
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
import structlog

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from backend.routes.air_quality import AirQualityAPI
from backend.routes.tempo_data import TempoDataAPI
from backend.routes.weather import WeatherAPI
from backend.routes.notifications import NotificationAPI
from backend.models.database import init_db
from backend.services.ml_service import MLService
from backend.utils.helpers import setup_logging

# Setup structured logging
logger = structlog.get_logger()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Setup CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8501", "http://127.0.0.1:8501"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize database
    init_db(app)
    
    # Setup logging
    setup_logging(app.config.get('DEBUG', False))
    
    # Initialize API
    api = Api(app, prefix='/api/v1')
    
    # Register API routes
    api.add_resource(AirQualityAPI, '/air-quality', '/air-quality/<string:location>')
    api.add_resource(TempoDataAPI, '/tempo', '/tempo/<string:parameter>')
    api.add_resource(WeatherAPI, '/weather', '/weather/<string:location>')
    api.add_resource(NotificationAPI, '/notifications', '/notifications/<int:user_id>')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({
            'status': 'healthy',
            'service': 'CleanSky AI Backend',
            'version': '1.0.0'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error", error=str(error))
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    # Initialize ML service
    ml_service = MLService()
    app.ml_service = ml_service
    
    logger.info("CleanSky AI Backend initialized", config=config_name or 'default')
    
    return app

def run_app():
    """Run the Flask application"""
    app = create_app()
    
    host = app.config.get('FLASK_HOST', '0.0.0.0')
    port = int(app.config.get('FLASK_PORT', 5000))
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Starting CleanSky AI Backend on {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    run_app()
