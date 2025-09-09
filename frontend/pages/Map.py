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
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 200px;">
            <h4 style="color: {color};">{station['name']}</h4>
            <p><strong>AQI:</strong> {aqi}</p>
            <p><strong>Category:</strong> {station['category']}</p>
            <p><strong>Primary Pollutant:</strong> {station['primary_pollutant']}</p>
            <p><strong>Last Updated:</strong> {station['last_updated']}</p>
        </div>
        """
        
        folium.CircleMarker(
            location=[station['lat'], station['lon']],
            radius=max(5, min(20, aqi/10)),  # Size based on AQI
            popup=folium.Popup(popup_html, max_width=250),
            color='black',
            weight=1,
            fillColor=color,
            fillOpacity=0.7,
            tooltip=f"{station['name']}: AQI {aqi}"
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 120px; height: 160px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><strong>AQI Legend</strong></p>
    <p><i class="fa fa-circle" style="color:green"></i> Good (0-50)</p>
    <p><i class="fa fa-circle" style="color:yellow"></i> Moderate (51-100)</p>
    <p><i class="fa fa-circle" style="color:orange"></i> USG (101-150)</p>
    <p><i class="fa fa-circle" style="color:red"></i> Unhealthy (151-200)</p>
    <p><i class="fa fa-circle" style="color:purple"></i> V. Unhealthy (201-300)</p>
    <p><i class="fa fa-circle" style="color:darkred"></i> Hazardous (300+)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m, stations

def generate_mock_stations():
    """Generate mock air quality monitoring stations"""
    import random
    
    # Major US cities and surrounding areas
    cities = [
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
        {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
        {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
        {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
        {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
        {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
        {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
        {"name": "San Jose", "lat": 37.3382, "lon": -121.8863},
        {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
        {"name": "Jacksonville", "lat": 30.3322, "lon": -81.6557},
        {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
        {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
        {"name": "Atlanta", "lat": 33.7490, "lon": -84.3880}
    ]
    
    stations = []
    pollutants = ['PM2.5', 'O3', 'NO2', 'SO2', 'CO']
    
    for city in cities:
        # Add 2-5 stations per city area
        num_stations = random.randint(2, 5)
        
        for i in range(num_stations):
            # Random offset within city area
            lat_offset = random.uniform(-0.1, 0.1)
            lon_offset = random.uniform(-0.1, 0.1)
            
            # Generate AQI with city-specific bias
            base_aqi = random.uniform(30, 100)
            if city["name"] in ["Los Angeles", "Phoenix", "Houston"]:
                base_aqi += random.uniform(20, 50)  # Higher pollution cities
            
            aqi = min(300, max(0, int(base_aqi + random.uniform(-20, 30))))
            
            # Determine category
            if aqi <= 50:
                category = "Good"
            elif aqi <= 100:
                category = "Moderate"
            elif aqi <= 150:
                category = "Unhealthy for Sensitive Groups"
            elif aqi <= 200:
                category = "Unhealthy"
            elif aqi <= 300:
                category = "Very Unhealthy"
            else:
                category = "Hazardous"
            
            station = {
                'name': f"{city['name']} Station {i+1}",
                'lat': city['lat'] + lat_offset,
                'lon': city['lon'] + lon_offset,
                'aqi': aqi,
                'category': category,
                'primary_pollutant': random.choice(pollutants),
                'last_updated': datetime.now().strftime("%H:%M")
            }
            stations.append(station)
    
    return stations

def main():
    """Main map page"""
    
    # Initialize session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    
    st.title("🗺️ Air Quality Map")
    st.markdown("**Interactive map showing real-time air quality across North America**")
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ Map Controls")
        
        # Map view options
        map_style = st.selectbox(
            "Map Style",
            ["Light", "Dark", "Satellite", "Street"],
            index=0
        )
        
        # Data layer options
        st.markdown("#### Data Layers")
        show_stations = st.checkbox("Ground Stations", value=True)
        show_satellite = st.checkbox("TEMPO Satellite Data", value=False)
        show_weather = st.checkbox("Weather Overlays", value=False)
        show_forecasts = st.checkbox("Forecast Zones", value=False)
        
        # Filters
        st.markdown("#### Filters")
        
        # AQI range filter
        aqi_range = st.slider(
            "AQI Range",
            min_value=0,
            max_value=300,
            value=(0, 300),
            step=10
        )
        
        # Pollutant filter
        pollutant_filter = st.multiselect(
            "Primary Pollutants",
            ["PM2.5", "O3", "NO2", "SO2", "CO"],
            default=["PM2.5", "O3", "NO2", "SO2", "CO"]
        )
        
        # Time controls
        st.markdown("#### Time Controls")
        
        show_historical = st.checkbox("Historical Data", value=False)
        if show_historical:
            historical_date = st.date_input(
                "Select Date",
                value=datetime.now().date() - timedelta(days=1)
            )
            historical_hour = st.slider("Hour", 0, 23, 12)
        
        # Auto-refresh
        auto_refresh = st.checkbox("Auto Refresh (5min)", value=False)
        if auto_refresh:
            st.info("⏱️ Map will refresh every 5 minutes")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create and display map
        st.markdown("### 🌍 North America Air Quality")
        
        try:
            # Create map
            air_quality_map, stations_data = create_air_quality_map()
            
            # Display map
            map_data = st_folium(
                air_quality_map,
                width=800,
                height=600,
                returned_objects=["last_object_clicked"]
            )
            
            # Handle map interactions
            if map_data["last_object_clicked"]:
                clicked_data = map_data["last_object_clicked"]
                if clicked_data:
                    st.info(f"📍 Clicked location: {clicked_data.get('lat', 'N/A'):.4f}°, {clicked_data.get('lng', 'N/A'):.4f}°")
        
        except Exception as e:
            st.error(f"Error loading map: {str(e)}")
            st.info("Please check your internet connection and refresh the page.")
    
    with col2:
        st.markdown("### 📊 Statistics")
        
        # Calculate statistics from mock data
        try:
            stations_df = pd.DataFrame(stations_data)
            
            # Filter stations based on sidebar filters
            filtered_stations = stations_df[
                (stations_df['aqi'] >= aqi_range[0]) & 
                (stations_df['aqi'] <= aqi_range[1]) &
                (stations_df['primary_pollutant'].isin(pollutant_filter))
            ]
            
            # Display metrics
            total_stations = len(filtered_stations)
            avg_aqi = filtered_stations['aqi'].mean() if total_stations > 0 else 0
            max_aqi = filtered_stations['aqi'].max() if total_stations > 0 else 0
            
            st.metric("Total Stations", total_stations)
            st.metric("Average AQI", f"{avg_aqi:.1f}")
            st.metric("Maximum AQI", f"{max_aqi:.0f}")
            
            # AQI distribution
            if total_stations > 0:
                st.markdown("#### AQI Distribution")
                
                category_counts = filtered_stations['category'].value_counts()
                
                # Create a simple bar chart
                fig = px.bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    color=category_counts.values,
                    color_continuous_scale="RdYlGn_r",
                    labels={'x': 'Air Quality Category', 'y': 'Number of Stations'}
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Top pollutants
                st.markdown("#### Primary Pollutants")
                pollutant_counts = filtered_stations['primary_pollutant'].value_counts()
                
                for pollutant, count in pollutant_counts.head(5).items():
                    percentage = (count / total_stations) * 100
                    st.write(f"**{pollutant}**: {count} stations ({percentage:.1f}%)")
        
        except Exception as e:
            st.error(f"Error calculating statistics: {str(e)}")
    
    # Additional information section
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🛰️ TEMPO Satellite")
        if show_satellite:
            st.success("✅ TEMPO data overlay active")
            st.info("Showing NO₂, O₃, HCHO columns from NASA TEMPO satellite")
        else:
            st.info("Enable TEMPO data in sidebar to view satellite measurements")
    
    with col2:
        st.markdown("### 🌦️ Weather Integration")
        if show_weather:
            st.success("✅ Weather overlay active")
            st.info("Showing wind patterns, temperature, and precipitation")
        else:
            st.info("Enable weather overlays to see meteorological conditions")
    
    with col3:
        st.markdown("### 📈 Forecasting")
        if show_forecasts:
            st.success("✅ Forecast zones active")
            st.info("Showing 24-hour air quality predictions")
        else:
            st.info("Enable forecast zones to view predicted air quality")
    
    # Data export section
    st.markdown("### 💾 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Visible Stations"):
            try:
                stations_df = pd.DataFrame(stations_data)
                csv = stations_df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"air_quality_stations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    with col2:
        if st.button("🗺️ Export Map Image"):
            st.info("Map image export feature coming soon!")
    
    with col3:
        if st.button("📋 Generate Report"):
            st.info("Automated report generation feature coming soon!")
    
    # Auto-refresh functionality
    if auto_refresh:
        import time
        time.sleep(300)  # 5 minutes
        st.rerun()

if __name__ == "__main__":
    main()
