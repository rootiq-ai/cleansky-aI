# 🌤️ CleanSky AI

**NASA TEMPO Air Quality Monitoring & Forecasting System**

CleanSky AI is a comprehensive web-based application that revolutionizes air quality monitoring across North America by integrating real-time data from NASA's Tropospheric Emissions: Monitoring of Pollution (TEMPO) satellite mission with ground-based air quality measurements and weather data. Our AI-powered system provides accurate forecasts, smart notifications, and actionable insights to improve public health decisions.

## 🎯 Project Overview

The TEMPO mission represents a groundbreaking advancement in air quality monitoring, providing hourly daytime measurements of atmospheric pollutants across North America at unprecedented spatial resolution (2.1 km x 4.4 km). CleanSky AI harnesses this revolutionary capability alongside traditional ground-based monitoring networks to deliver:

- **Real-time Air Quality Monitoring**: Integration of TEMPO satellite data with EPA ground stations
- **AI-Powered Forecasting**: Machine learning models for predicting air quality up to 72 hours ahead  
- **Smart Notification System**: Proactive alerts for poor air quality conditions
- **Interactive Visualizations**: Maps, charts, and dashboards for comprehensive data exploration
- **Health Recommendations**: Personalized guidance based on current and forecasted conditions

## 🏗️ Architecture

### Frontend (Streamlit)
- **Main Dashboard**: Real-time air quality overview and current conditions
- **Interactive Maps**: Spatial visualization of air quality data across regions
- **Detailed Analytics**: Historical trends, forecasting, and comparative analysis
- **Alert Management**: User preferences and notification settings

### Backend (Flask API)
- **Data Integration**: TEMPO satellite data, EPA ground stations, weather services
- **Machine Learning**: XGBoost and TensorFlow models for air quality prediction
- **Real-time Processing**: Continuous data ingestion and processing pipeline
- **Notification Engine**: Multi-channel alert system (email, SMS, push notifications)

### Data Sources
- **NASA TEMPO**: NO₂, O₃, HCHO, SO₂ column measurements
- **EPA Air Quality System**: Ground-based PM₂.₅, PM₁₀, CO measurements
- **OpenWeather API**: Meteorological data for model inputs
- **AirNow API**: Real-time air quality observations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/cleansky-ai.git
cd cleansky-ai
```

2. **Create and activate virtual environment**
```bash
python -m venv cleansky_env
source cleansky_env/bin/activate  # On Windows: cleansky_env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the root directory:
```env
# API Keys
NASA_EARTHDATA_TOKEN=your_nasa_token_here
OPENWEATHER_API_KEY=your_openweather_key_here
EPA_API_KEY=your_epa_key_here

# Notification Services (Optional)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SENDGRID_API_KEY=your_sendgrid_key

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///cleansky.db

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

### Running the Application

1. **Start the Backend API**
```bash
cd backend
python app.py
```
The Flask API will start on `http://localhost:5000`

2. **Start the Frontend (in a new terminal)**
```bash
cd frontend
streamlit run app.py
```
The Streamlit app will open in your browser at `http://localhost:8501`

## 📊 Features

### 🎯 Real-Time Monitoring
- Live air quality index (AQI) calculations
- Multi-parameter pollutant tracking (NO₂, O₃, PM₂.₅, SO₂, CO, HCHO)
- Integration of satellite and ground-based measurements
- Weather correlation and analysis

### 🤖 AI-Powered Forecasting
- XGBoost machine learning models trained on historical data
- 1-72 hour air quality predictions with confidence intervals
- Feature engineering using meteorological and satellite data
- Continuous model retraining and improvement

### 🔔 Smart Notifications
- Customizable AQI threshold alerts
- Multi-channel delivery (email, SMS, push notifications)
- Health-sensitive group recommendations
- Proactive poor air quality warnings

### 🗺️ Interactive Visualization
- Real-time air quality maps with color-coded regions
- Time series charts showing historical trends
- Comparative analysis across multiple locations
- TEMPO satellite data overlay capabilities

### 📱 User Experience
- Responsive web design for mobile and desktop
- Location-based personalization
- Exportable data and reports
- Accessibility-compliant interface

## 🛠️ Development

### Project Structure
```
CleanSky-AI/
├── backend/               # Flask API backend
│   ├── routes/           # API endpoints
│   ├── services/         # Data services and integrations
│   ├── models/           # Database and ML models
│   └── utils/            # Utility functions
├── frontend/             # Streamlit frontend
│   ├── pages/           # Multi-page application
│   ├── components/      # Reusable UI components
│   └── utils/           # Frontend utilities
├── config/              # Configuration management
├── data/               # Data storage and caching
├── tests/              # Test suites
└── docs/               # Documentation
```

### API Endpoints

**Air Quality**
- `GET /api/v1/air-quality?lat={lat}&lon={lon}` - Current air quality data
- `POST /api/v1/air-quality` - Air quality forecast request

**TEMPO Data** 
- `GET /api/v1/tempo?lat={lat}&lon={lon}&parameter={param}` - Satellite data
- `POST /api/v1/tempo` - Batch satellite data processing

**Weather**
- `GET /api/v1/weather?lat={lat}&lon={lon}` - Current weather conditions

**Notifications**
- `POST /api/v1/notifications` - Send notification
- `GET /api/v1/notifications/{user_id}` - Get notification history

### Running Tests
```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_backend/
pytest tests/test_services/

# Run with coverage
pytest --cov=backend --cov=frontend
```

### Code Style
```bash
# Format code
black backend/ frontend/

# Lint code
flake8 backend/ frontend/
```

## 🔧 Configuration

### Data Sources Setup

**NASA Earthdata Account**
1. Register at https://urs.earthdata.nasa.gov/
2. Generate an access token
3. Add to `.env` as `NASA_EARTHDATA_TOKEN`

**EPA API Access**
1. Request API key at https://aqs.epa.gov/aqsweb/documents/data_api.html
2. Add to `.env` as `EPA_API_KEY`

**OpenWeather API**
1. Sign up at https://openweathermap.org/api
2. Get free API key
3. Add to `.env` as `OPENWEATHER_API_KEY`

### ML Model Configuration

Models can be configured in `config/settings.yaml`:

```yaml
ml_models:
  forecast:
    algorithm: "XGBoost"
    features:
      - "temperature"
      - "humidity" 
      - "wind_speed"
      - "no2_column"
      - "o3_column"
    hyperparameters:
      n_estimators: 100
      max_depth: 6
      learning_rate: 0.1
```

## 🚀 Deployment

### Local Deployment
The application runs locally with the quick start instructions above.

### Production Deployment

**Using Gunicorn (Backend)**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 backend.app:create_app()
```

**Using Streamlit Cloud (Frontend)**
1. Push code to GitHub repository
2. Connect repository to Streamlit Cloud
3. Configure environment variables in Streamlit Cloud dashboard
4. Deploy with automatic HTTPS and custom domain support

**Environment Variables for Production**
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/database
REDIS_URL=redis://redis-host:6379/0
```

## 📈 Performance & Scalability

### Caching Strategy
- Redis for real-time data caching (15-30 minute TTL)
- File-based caching for processed datasets
- Database query optimization with indexes

### Horizontal Scaling
- Stateless API design enables multiple backend instances
- Load balancing with nginx or cloud load balancers
- Database connection pooling for concurrent requests

### Data Processing
- Asynchronous data ingestion with Celery
- Batch processing for historical data analysis
- Efficient spatial indexing for geographic queries

## 🤝 Contributing

We welcome contributions from the community! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Ensure cross-browser compatibility for frontend changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NASA Goddard Space Flight Center** for the TEMPO mission and data access
- **EPA** for providing comprehensive ground-based air quality monitoring data
- **NOAA** for meteorological data integration
- **Open source community** for the excellent tools and libraries that make this project possible

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/cleansky-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/cleansky-ai/discussions)
- **Email**: support@cleansky-ai.org

## 🔮 Roadmap

### Phase 1 (Current)
- ✅ Basic TEMPO data integration
- ✅ Ground station data fusion
- ✅ Real-time AQI calculations
- ✅ Interactive web interface

### Phase 2 (Next 3 months)
- 🔄 Advanced ML forecasting models
- 🔄 Mobile application development
- 🔄 Enhanced notification system
- 🔄 Multi-language support

### Phase 3 (6 months)
- 📋 Health impact modeling
- 📋 Policy recommendation engine
- 📋 Climate change correlation analysis
- 📋 Integration with smart city platforms

### Phase 4 (12 months)
- 📋 Global expansion beyond North America
- 📋 Real-time satellite image processing
- 📋 Advanced AI/deep learning models
- 📋 Open data API for researchers

---

**Built with ❤️ for cleaner air and healthier communities**

*CleanSky AI - Powered by NASA TEMPO Satellite Technology*
