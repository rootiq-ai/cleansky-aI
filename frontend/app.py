"""
Streamlit frontend application for CleanSky AI
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from frontend.components.widgets import setup_page_config
from frontend.utils.api_client import APIClient
from config.config import get_config

# Page configuration
st.set_page_config(
    page_title="CleanSky AI",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/cleansky-ai/help',
        'Report a bug': 'https://github.com/cleansky-ai/issues',
        'About': """
        # CleanSky AI
        
        **NASA TEMPO Air Quality Monitoring System**
        
        Leveraging NASA's Tropospheric Emissions: Monitoring of Pollution (TEMPO) 
        mission to revolutionize air quality monitoring and forecasting across North America.
        
        ## Features
        - Real-time TEMPO satellite data integration
        - Ground-based air quality measurements
        - Weather data correlation
        - AI-powered air quality forecasting
        - Smart notification system
        - Interactive maps and visualizations
        
        Built with ❤️ for better air quality and public health.
        """
    }
)

def main():
    """Main application entry point"""
    
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.api_client = APIClient()
        st.session_state.user_location = None
        st.session_state.selected_location = None
    
    # Sidebar configuration
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/4CAF50/FFFFFF?text=CleanSky+AI", width=200)
        
        st.markdown("### 🌤️ CleanSky AI")
        st.markdown("**NASA TEMPO Air Quality Monitor**")
        
        st.divider()
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        # Location selector
        st.markdown("#### Current Location")
        
        # Get user's location (simplified for demo)
        col1, col2 = st.columns(2)
        with col1:
            user_lat = st.number_input(
                "Latitude", 
                value=39.8283, 
                min_value=-90.0, 
                max_value=90.0,
                step=0.0001,
                format="%.4f"
            )
        with col2:
            user_lon = st.number_input(
                "Longitude", 
                value=-98.5795, 
                min_value=-180.0, 
                max_value=180.0,
                step=0.0001,
                format="%.4f"
            )
        
        st.session_state.user_location = (user_lat, user_lon)
        
        # Quick location presets
        st.markdown("#### Quick Locations")
        location_presets = {
            "Los Angeles, CA": (34.0522, -118.2437),
            "New York, NY": (40.7128, -74.0060),
            "Chicago, IL": (41.8781, -87.6298),
            "Houston, TX": (29.7604, -95.3698),
            "Denver, CO": (39.7392, -104.9903),
            "Atlanta, GA": (33.7490, -84.3880)
        }
        
        selected_preset = st.selectbox(
            "Select a city:",
            ["Custom"] + list(location_presets.keys()),
            index=0
        )
        
        if selected_preset != "Custom":
            st.session_state.user_location = location_presets[selected_preset]
        
        st.divider()
        
        # System status
        st.markdown("### 📊 System Status")
        
        # Check API status
        try:
            status = st.session_state.api_client.get_health_status()
            if status.get('status') == 'healthy':
                st.success("🟢 API Online")
            else:
                st.error("🔴 API Offline")
        except:
            st.error("🔴 API Unavailable")
        
        # Data freshness indicators
        st.markdown("**Data Status:**")
        st.info("🛰️ TEMPO: Updated hourly")
        st.info("🏭 Ground Stations: Real-time")
        st.info("🌦️ Weather: Updated 15min")
        
        st.divider()
        
        # Settings
        st.markdown("### ⚙️ Settings")
        
        # Alert preferences
        alert_enabled = st.checkbox("Enable Alerts", value=True)
        if alert_enabled:
            alert_threshold = st.select_slider(
                "Alert Threshold (AQI)",
                options=[50, 100, 150, 200, 300],
                value=100,
                help="Get notified when AQI exceeds this value"
            )
            st.session_state.alert_threshold = alert_threshold
        
        # Display preferences
        st.markdown("#### Display Options")
        temperature_unit = st.radio("Temperature Unit", ["°C", "°F"], index=1)
        map_style = st.selectbox("Map Style", ["Light", "Dark", "Satellite"], index=0)
        
        st.session_state.temperature_unit = temperature_unit
        st.session_state.map_style = map_style.lower()
    
    # Main content area
    st.title("🌤️ CleanSky AI - Air Quality Monitor")
    st.markdown("""
    **Powered by NASA TEMPO Satellite Data**
    
    Real-time air quality monitoring and forecasting using NASA's Tropospheric Emissions: 
    Monitoring of Pollution (TEMPO) mission data integrated with ground-based measurements.
    """)
    
    # Current location display
    if st.session_state.user_location:
        lat, lon = st.session_state.user_location
        st.info(f"📍 Monitoring location: {lat:.4f}°N, {lon:.4f}°W")
    
    # Main dashboard sections
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 🎯 Current Air Quality")
        
        # Get current air quality data
        try:
            if st.session_state.user_location:
                lat, lon = st.session_state.user_location
                air_quality_data = st.session_state.api_client.get_air_quality(lat, lon)
                
                if air_quality_data and air_quality_data.get('status') == 'success':
                    current = air_quality_data.get('current_summary', {})
                    
                    # Display AQI with color coding
                    aqi = current.get('maximum_aqi', 0)
                    category = current.get('category', 'Unknown')
                    
                    # AQI color mapping
                    aqi_colors = {
                        'Good': '#00E400',
                        'Moderate': '#FFFF00', 
                        'Unhealthy for Sensitive Groups': '#FF7E00',
                        'Unhealthy': '#FF0000',
                        'Very Unhealthy': '#8F3F97',
                        'Hazardous': '#7E0023'
                    }
                    
                    color = aqi_colors.get(category, '#808080')
                    
                    st.markdown(f"""
                    <div style="
                        background-color: {color}; 
                        padding: 20px; 
                        border-radius: 10px; 
                        text-align: center;
                        color: {'white' if category in ['Unhealthy', 'Very Unhealthy', 'Hazardous'] else 'black'};
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 20px;
                    ">
                        AQI: {aqi} - {category}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Additional details
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Average AQI", f"{current.get('average_aqi', 0):.1f}")
                        st.metric("Monitoring Stations", current.get('station_count', 0))
                    
                    with col_b:
                        st.metric("Primary Pollutant", current.get('primary_pollutant', 'N/A'))
                        if current.get('last_updated'):
                            from datetime import datetime
                            last_update = datetime.fromisoformat(current['last_updated'].replace('Z', '+00:00'))
                            st.metric("Last Updated", last_update.strftime("%H:%M"))
                
                else:
                    st.warning("Unable to fetch current air quality data")
            else:
                st.info("Please set your location in the sidebar")
                
        except Exception as e:
            st.error(f"Error fetching air quality data: {str(e)}")
    
    with col2:
        st.markdown("### 🌡️ Weather")
        
        # Weather information
        try:
            if st.session_state.user_location:
                lat, lon = st.session_state.user_location
                weather_data = st.session_state.api_client.get_weather(lat, lon)
                
                if weather_data:
                    temp = weather_data.get('temperature', 0)
                    if st.session_state.temperature_unit == "°F":
                        temp = temp * 9/5 + 32
                    
                    st.metric("Temperature", f"{temp:.1f}{st.session_state.temperature_unit}")
                    st.metric("Humidity", f"{weather_data.get('humidity', 0):.0f}%")
                    st.metric("Wind Speed", f"{weather_data.get('wind_speed', 0):.1f} m/s")
                else:
                    st.info("Weather data unavailable")
        except:
            st.info("Weather data unavailable")
    
    with col3:
        st.markdown("### 🔔 Alerts")
        
        # Alert status
        if 'alert_threshold' in st.session_state:
            if 'aqi' in locals() and aqi > st.session_state.alert_threshold:
                st.error(f"⚠️ AQI Alert!\nCurrent: {aqi}\nThreshold: {st.session_state.alert_threshold}")
            else:
                st.success("✅ Air quality is within safe limits")
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
        
        if st.button("📊 View Detailed Dashboard"):
            st.switch_page("pages/Dashboard.py")
        
        if st.button("🗺️ Open Map View"):
            st.switch_page("pages/Map.py")
        
        if st.button("📈 View Forecast"):
            st.switch_page("pages/Forecast.py")
    
    # Footer information
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🛰️ Data Sources:**
        - NASA TEMPO Satellite
        - EPA Air Quality System
        - NOAA Weather Service
        """)
    
    with col2:
        st.markdown("""
        **📊 Parameters Monitored:**
        - NO₂ (Nitrogen Dioxide)
        - O₃ (Ozone)
        - PM₂.₅ (Fine Particles)
        - SO₂ (Sulfur Dioxide)
        """)
    
    with col3:
        st.markdown("""
        **🔔 Stay Informed:**
        - Real-time alerts
        - Daily forecasts
        - Health recommendations
        - Mobile notifications
        """)

if __name__ == "__main__":
    main()
