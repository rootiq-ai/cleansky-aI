"""
Interactive Map page for CleanSky AI
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from frontend.utils.api_client import APIClient

st.set_page_config(
    page_title="Air Quality Map - CleanSky AI",
    page_icon="🗺️",
    layout="wide"
)

def create_air_quality_map(center_lat=39.8283, center_lon=-98.5795, zoom=4):
    """Create an interactive air quality map"""
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='CartoDB positron'
    )
    
    # Add air quality monitoring stations (mock data)
    stations = generate_mock_stations()
    
    # Color mapping for AQI levels
    def get_aqi_color(aqi):
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        elif aqi <= 150:
            return 'orange'
        elif aqi <= 200:
            return 'red'
        elif aqi <= 300:
            return 'purple'
        else:
            return 'darkred'
    
    # Add markers for each station
    for station in stations:
        aqi = station['aqi']
        color = get_aqi_color(aqi)
        
        # Create popup content
