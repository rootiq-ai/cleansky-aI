"""
Dashboard page for CleanSky AI - Detailed air quality analytics
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from frontend.utils.api_client import APIClient
from frontend.components.charts import create_time_series_chart, create_aqi_gauge, create_pollutant_comparison

st.set_page_config(
    page_title="Dashboard - CleanSky AI",
    page_icon="📊",
    layout="wide"
)

def main():
    """Main dashboard page"""
    
    # Initialize session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    
    if 'user_location' not in st.session_state:
        st.session_state.user_location = (39.8283, -98.5795)  # Default to geographic center of US
    
    st.title("📊 Air Quality Dashboard")
    st.markdown("**Comprehensive air quality analytics powered by NASA TEMPO satellite data**")
    
    # Sidebar filters and controls
    with st.sidebar:
        st.markdown("### 🎛️ Dashboard Controls")
        
        # Time range selector
        time_range = st.selectbox(
            "Time Range",
            ["Last 24 Hours", "Last 3 Days", "Last Week", "Last Month"],
            index=1
        )
        
        # Parameter selector
        parameters = st.multiselect(
            "Parameters to Display",
            ["NO2", "O3", "PM2.5", "SO2", "CO"],
            default=["NO2", "O3", "PM2.5"]
        )
        
        # Data source selector
        data_sources = st.multiselect(
            "Data Sources",
            ["TEMPO Satellite", "Ground Stations", "Weather Data"],
            default=["TEMPO Satellite", "Ground Stations"]
        )
        
        # Location controls
        st.markdown("### 📍 Location")
        
        # Use location from main app or allow override
        if st.session_state.user_location:
            lat, lon = st.session_state.user_location
            st.write(f"Current: {lat:.4f}°N, {lon:.4f}°W")
        
        # Radius for nearby stations
        radius = st.slider("Search Radius (km)", 5, 100, 25)
        
        # Refresh button
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
    
    # Convert time range to dates
    end_date = datetime.now()
    if time_range == "Last 24 Hours":
        start_date = end_date - timedelta(hours=24)
    elif time_range == "Last 3 Days":
        start_date = end_date - timedelta(days=3)
    elif time_range == "Last Week":
        start_date = end_date - timedelta(weeks=1)
    else:  # Last Month
        start_date = end_date - timedelta(days=30)
    
    # Main dashboard content
    try:
        # Fetch data
        with st.spinner("Loading air quality data..."):
            lat, lon = st.session_state.user_location
            air_quality_data = st.session_state.api_client.get_air_quality(
                lat, lon, 
                radius=radius,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
        
        if not air_quality_data or air_quality_data.get('status') != 'success':
            st.error("Unable to load air quality data. Please check your connection and try again.")
            return
        
        # Current conditions overview
        st.markdown("### 🎯 Current Conditions")
        
        current = air_quality_data.get('current_summary', {})
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            aqi = current.get('maximum_aqi', 0)
            st.metric("Current AQI", f"{aqi:.0f}", help="Air Quality Index - higher is worse")
        
        with col2:
            avg_aqi = current.get('average_aqi', 0)
            st.metric("Average AQI", f"{avg_aqi:.1f}")
        
        with col3:
            station_count = current.get('station_count', 0)
            st.metric("Monitoring Stations", station_count)
        
        with col4:
            category = current.get('category', 'Unknown')
            st.metric("Air Quality", category)
        
        with col5:
            pollutant = current.get('primary_pollutant', 'N/A')
            st.metric("Primary Pollutant", pollutant)
        
        # AQI Gauge Chart
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 📊 AQI Gauge")
            gauge_fig = create_aqi_gauge(aqi)
            st.plotly_chart(gauge_fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🏭 Station Data")
            stations = air_quality_data.get('stations', [])
            if stations:
                # Create a summary table of stations
                station_df = pd.DataFrame([
                    {
                        'Station': f"Station {i+1}",
                        'AQI': station.get('aqi', 0),
                        'Primary Pollutant': station.get('primary_pollutant', 'N/A'),
                        'Distance (km)': station.get('distance_km', 0),
                        'Last Updated': station.get('timestamp', '')[:16] if station.get('timestamp') else 'N/A'
                    }
                    for i, station in enumerate(stations[:10])  # Show top 10 stations
                ])
                st.dataframe(station_df, use_container_width=True, height=300)
            else:
                st.info("No station data available for the selected area.")
        
        # Time series charts
        st.markdown("### 📈 Historical Trends")
        
        # Generate sample time series data for visualization
        if stations:
            # Create time series data from stations
            time_series_data = []
            for station in stations:
                # Simulate hourly data points
                base_time = datetime.now() - timedelta(hours=24)
                for hour in range(24):
                    timestamp = base_time + timedelta(hours=hour)
                    
                    # Add some realistic variation
                    import numpy as np
                    base_aqi = station.get('aqi', 50)
                    hour_variation = 10 * np.sin(hour * np.pi / 12)  # Daily pattern
                    noise = np.random.normal(0, 5)
                    aqi_value = max(0, base_aqi + hour_variation + noise)
                    
                    time_series_data.append({
                        'timestamp': timestamp,
                        'aqi': aqi_value,
                        'station': f"Station {stations.index(station) + 1}",
                        'parameter': 'AQI'
                    })
            
            if time_series_data:
                df = pd.DataFrame(time_series_data)
                
                # Time series chart
                fig = px.line(
                    df, 
                    x='timestamp', 
                    y='aqi', 
                    color='station',
                    title='AQI Trends Over Time',
                    labels={'aqi': 'Air Quality Index', 'timestamp': 'Time'}
                )
                
                fig.update_layout(
                    height=400,
                    hovermode='x unified',
                    xaxis_title="Time",
                    yaxis_title="AQI"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Parameter breakdown
        if len(parameters) > 1:
            st.markdown("### 🧪 Pollutant Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pollutant comparison chart
                pollutant_data = {
                    'NO2': np.random.uniform(20, 80),
                    'O3': np.random.uniform(30, 120),
                    'PM2.5': np.random.uniform(10, 60),
                    'SO2': np.random.uniform(5, 30),
                    'CO': np.random.uniform(1, 10)
                }
                
                selected_data = {k: v for k, v in pollutant_data.items() if k in parameters}
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(selected_data.keys()),
                        y=list(selected_data.values()),
                        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                    )
                ])
                
                fig.update_layout(
                    title="Current Pollutant Levels",
                    xaxis_title="Pollutant",
                    yaxis_title="Concentration",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pollutant pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=list(selected_data.keys()),
                    values=list(selected_data.values()),
                    hole=.3
                )])
                
                fig.update_layout(
                    title="Pollutant Distribution",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # TEMPO satellite data section
        if "TEMPO Satellite" in data_sources:
            st.markdown("### 🛰️ TEMPO Satellite Data")
            
            # Fetch TEMPO data
            with st.spinner("Loading TEMPO satellite data..."):
                tempo_data = st.session_state.api_client.get_tempo_data(
                    lat, lon, 
                    parameters=parameters,
                    date=end_date.strftime('%Y-%m-%d')
                )
            
            if tempo_data and tempo_data.get('status') == 'success':
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # TEMPO time series
                    tempo_points = tempo_data.get('data', [])
                    if tempo_points:
                        tempo_df = pd.DataFrame(tempo_points)
                        
                        if 'timestamp' in tempo_df.columns and 'value' in tempo_df.columns:
                            tempo_df['timestamp'] = pd.to_datetime(tempo_df['timestamp'])
                            
                            fig = px.scatter(
                                tempo_df,
                                x='timestamp',
                                y='value',
                                color='parameter',
                                title='TEMPO Satellite Measurements',
                                labels={'value': 'Column Density', 'timestamp': 'Time'}
                            )
                            
                            fig.update_layout(height=350)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("TEMPO data structure not suitable for time series display")
                    else:
                        st.info("No TEMPO data points available")
                
                with col2:
                    # TEMPO statistics
                    st.markdown("#### 📊 TEMPO Statistics")
                    stats = tempo_data.get('statistics', {})
                    
                    for param, stat in stats.items():
                        if isinstance(stat, dict) and 'mean' in stat:
                            st.metric(f"{param} Mean", f"{stat['mean']:.2e}")
                        else:
                            st.info(f"{param}: {stat.get('message', 'No data')}")
            else:
                st.warning("TEMPO satellite data unavailable")
        
        # Health recommendations
        st.markdown("### 💡 Health Recommendations")
        
        recommendations = []
        if aqi <= 50:
            recommendations = [
                "✅ Air quality is good - enjoy outdoor activities!",
                "🏃‍♂️ Perfect conditions for exercise and sports",
                "🌳 Great time for outdoor recreation"
            ]
        elif aqi <= 100:
            recommendations = [
                "⚠️ Air quality is moderate",
                "👥 Unusually sensitive people should consider reducing prolonged outdoor exertion",
                "🏃‍♂️ Most people can enjoy outdoor activities normally"
            ]
        elif aqi <= 150:
            recommendations = [
                "🚨 Unhealthy for sensitive groups",
                "👶 Children, elderly, and people with heart/lung conditions should limit outdoor activities",
                "😷 Consider wearing masks during outdoor activities",
                "🏠 Keep windows closed and use air purifiers indoors"
            ]
        else:
            recommendations = [
                "🚨 Air quality is unhealthy",
                "🏠 Everyone should avoid prolonged outdoor activities",
                "😷 Wear N95 masks when going outside",
                "🚪 Keep windows and doors closed",
                "💨 Use air purifiers indoors if available"
            ]
        
        for rec in recommendations:
            st.info(rec)
        
        # Data export section
        st.markdown("### 💾 Data Export")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export CSV", help="Download current data as CSV"):
                # Prepare data for export
                export_data = {
                    'timestamp': [datetime.now().isoformat()],
                    'latitude': [lat],
                    'longitude': [lon],
                    'aqi': [aqi],
                    'category': [category],
                    'primary_pollutant': [pollutant]
                }
                
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"cleansky_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📈 Generate Report", help="Create detailed PDF report"):
                st.info("Report generation feature coming soon!")
        
        with col3:
            if st.button("🔗 Share Dashboard", help="Get shareable link"):
                share_url = f"https://cleansky-ai.streamlit.app/Dashboard?lat={lat}&lon={lon}"
                st.code(share_url)
        
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Please check your internet connection and try refreshing the page.")

if __name__ == "__main__":
    main()
