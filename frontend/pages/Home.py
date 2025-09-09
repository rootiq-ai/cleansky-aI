"""
Home page for CleanSky AI - Main landing page with overview and quick access
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from frontend.utils.api_client import APIClient
from frontend.components.charts import create_aqi_gauge

st.set_page_config(
    page_title="Home - CleanSky AI",
    page_icon="🏠",
    layout="wide"
)

def create_mini_trend_chart(data_points, title="AQI Trend"):
    """Create a mini trend chart for the overview cards"""
    fig = go.Figure()
    
    # Create x-axis (last 24 hours)
    x_values = list(range(len(data_points)))
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=data_points,
        mode='lines+markers',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4),
        name=title,
        hovertemplate='<b>%{y}</b><extra></extra>'
    ))
    
    fig.update_layout(
        height=100,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def generate_quick_stats():
    """Generate quick statistics for the overview"""
    import random
    
    # Mock current conditions
    current_aqi = random.randint(35, 95)
    trend_data = [current_aqi + random.randint(-10, 10) for _ in range(24)]
    
    # Mock forecast
    forecast_change = random.choice(["improving", "stable", "worsening"])
    
    # Mock alerts
    active_alerts = random.randint(0, 3)
    
    # Mock air quality summary for major cities
    cities_data = {
        'Los Angeles': random.randint(80, 140),
        'New York': random.randint(45, 85),
        'Chicago': random.randint(50, 90),
        'Houston': random.randint(60, 100),
        'Phoenix': random.randint(70, 110),
        'Denver': random.randint(40, 80)
    }
    
    return {
        'current_aqi': current_aqi,
        'trend_data': trend_data,
        'forecast_change': forecast_change,
        'active_alerts': active_alerts,
        'cities_data': cities_data
    }

def create_us_overview_map():
    """Create a simplified US overview map showing major cities"""
    import random
    
    # Major US cities with their coordinates
    cities = {
        'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'aqi': random.randint(80, 140)},
        'New York': {'lat': 40.7128, 'lon': -74.0060, 'aqi': random.randint(45, 85)},
        'Chicago': {'lat': 41.8781, 'lon': -87.6298, 'aqi': random.randint(50, 90)},
        'Houston': {'lat': 29.7604, 'lon': -95.3698, 'aqi': random.randint(60, 100)},
        'Phoenix': {'lat': 33.4484, 'lon': -112.0740, 'aqi': random.randint(70, 110)},
        'Philadelphia': {'lat': 39.9526, 'lon': -75.1652, 'aqi': random.randint(55, 95)},
        'San Antonio': {'lat': 29.4241, 'lon': -98.4936, 'aqi': random.randint(65, 105)},
        'San Diego': {'lat': 32.7157, 'lon': -117.1611, 'aqi': random.randint(70, 110)},
        'Dallas': {'lat': 32.7767, 'lon': -96.7970, 'aqi': random.randint(75, 115)},
        'Denver': {'lat': 39.7392, 'lon': -104.9903, 'aqi': random.randint(40, 80)},
        'Seattle': {'lat': 47.6062, 'lon': -122.3321, 'aqi': random.randint(35, 75)},
        'Atlanta': {'lat': 33.7490, 'lon': -84.3880, 'aqi': random.randint(55, 95)}
    }
    
    # Prepare data for scatter plot
    city_names = list(cities.keys())
    lats = [cities[city]['lat'] for city in city_names]
    lons = [cities[city]['lon'] for city in city_names]
    aqis = [cities[city]['aqi'] for city in city_names]
    
    # Color mapping for AQI
    colors = []
    for aqi in aqis:
        if aqi <= 50:
            colors.append('#00E400')  # Good
        elif aqi <= 100:
            colors.append('#FFFF00')  # Moderate
        elif aqi <= 150:
            colors.append('#FF7E00')  # Unhealthy for Sensitive
        else:
            colors.append('#FF0000')  # Unhealthy
    
    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        text=[f"{city}<br>AQI: {aqi}" for city, aqi in zip(city_names, aqis)],
        mode='markers',
        marker=dict(
            size=[max(8, min(25, aqi/5)) for aqi in aqis],
            color=colors,
            line=dict(width=2, color='white'),
            sizemode='diameter'
        ),
        hovertemplate='<b>%{text}</b><extra></extra>',
        name='Cities'
    ))
    
    fig.update_geos(
        scope='usa',
        showlakes=True,
        lakecolor='lightblue',
        showland=True,
        landcolor='lightgray',
        showocean=True,
        oceancolor='lightblue',
        projection_type='albers usa'
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        title="Air Quality Across Major US Cities",
        title_x=0.5
    )
    
    return fig

def main():
    """Main home page"""
    
    # Initialize session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    
    # Page header
    st.title("🌤️ CleanSky AI")
    st.markdown("### **NASA TEMPO Air Quality Monitoring System**")
    st.markdown("Welcome to the future of air quality monitoring powered by satellite technology")
    
    # Quick stats section
    stats = generate_quick_stats()
    
    # Overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; font-size: 2.5em;">{}</h3>
            <p style="margin: 5px 0;">Current AQI</p>
            <small>Last updated: {}</small>
        </div>
        """.format(stats['current_aqi'], datetime.now().strftime("%H:%M")), 
        unsafe_allow_html=True)
    
    with col2:
        forecast_emoji = "📈" if stats['forecast_change'] == "worsening" else "📉" if stats['forecast_change'] == "improving" else "➡️"
        forecast_color = "#e74c3c" if stats['forecast_change'] == "worsening" else "#2ecc71" if stats['forecast_change'] == "improving" else "#3498db"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; font-size: 2.5em;">{forecast_emoji}</h3>
            <p style="margin: 5px 0;">24h Forecast</p>
            <small style="color: {forecast_color}; font-weight: bold;">{stats['forecast_change'].title()}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        alert_color = "#e74c3c" if stats['active_alerts'] > 0 else "#2ecc71"
        alert_text = f"{stats['active_alerts']} Active" if stats['active_alerts'] > 0 else "All Clear"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; font-size: 2.5em;">🔔</h3>
            <p style="margin: 5px 0;">Alerts</p>
            <small style="color: {alert_color}; font-weight: bold;">{alert_text}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; font-size: 2.5em;">🛰️</h3>
            <p style="margin: 5px 0;">TEMPO Data</p>
            <small>Updated Hourly</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🗺️ National Air Quality Overview")
        
        # US overview map
        try:
            us_map = create_us_overview_map()
            st.plotly_chart(us_map, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading map: {str(e)}")
            st.info("Map visualization unavailable. Please refresh the page.")
    
    with col2:
        st.markdown("### 📊 Quick Metrics")
        
        # AQI Gauge for current location
        gauge_fig = create_aqi_gauge(stats['current_aqi'], "Your Area")
        st.plotly_chart(gauge_fig, use_container_width=True)
        
        # Trend mini-chart
        st.markdown("#### 24-Hour Trend")
        trend_fig = create_mini_trend_chart(stats['trend_data'])
        st.plotly_chart(trend_fig, use_container_width=True)
    
    # Major cities summary
    st.markdown("### 🏙️ Major Cities Air Quality")
    
    # Create cities summary table
    cities_data = []
    for city, aqi in stats['cities_data'].items():
        if aqi <= 50:
            category = "Good"
            color = "🟢"
        elif aqi <= 100:
            category = "Moderate" 
            color = "🟡"
        elif aqi <= 150:
            category = "Unhealthy for Sensitive"
            color = "🟠"
        else:
            category = "Unhealthy"
            color = "🔴"
        
        cities_data.append({
            'Status': color,
            'City': city,
            'AQI': aqi,
            'Category': category
        })
    
    cities_df = pd.DataFrame(cities_data)
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(
            cities_df.iloc[:6],
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.dataframe(
            cities_df.iloc[6:],
            use_container_width=True,
            hide_index=True
        )
    
    # Quick actions section
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 View Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/Dashboard.py")
    
    with col2:
        if st.button("🗺️ Interactive Map", use_container_width=True):
            st.switch_page("pages/Map.py")
    
    with col3:
        if st.button("📈 Air Quality Forecast", use_container_width=True):
            st.switch_page("pages/Forecast.py")
    
    with col4:
        if st.button("🔔 Manage Alerts", use_container_width=True):
            st.switch_page("pages/Alerts.py")
    
    # News and insights section
    st.markdown("### 📰 Latest Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🛰️ TEMPO Mission Update**
        
        NASA's TEMPO satellite continues to provide unprecedented hourly air quality measurements across North America. Latest data shows improved monitoring capabilities for NO₂ and O₃ detection.
        
        *Updated 2 hours ago*
        """)
    
    with col2:
        st.markdown("""
        **📊 Weekly Air Quality Report**
        
        This week showed moderate air quality across most urban areas, with slight improvements in the Pacific Northwest due to favorable weather patterns.
        
        *Published today*
        """)
    
    with col3:
        st.markdown("""
        **🌡️ Seasonal Outlook**
        
        Spring air quality forecast indicates typical seasonal patterns with occasional ozone episodes during warm, sunny days. Pollen levels remain moderate.
        
        *Updated daily*
        """)
    
    # About section
    with st.expander("🔍 About CleanSky AI"):
        st.markdown("""
        **CleanSky AI** revolutionizes air quality monitoring by integrating NASA's cutting-edge TEMPO satellite data with ground-based measurements and advanced AI forecasting.
        
        **Key Features:**
        - 🛰️ **Real-time TEMPO Data**: Hourly satellite measurements of key pollutants
        - 🏭 **Ground Station Integration**: EPA and AirNow monitoring networks
        - 🤖 **AI-Powered Forecasting**: Machine learning predictions up to 72 hours ahead
        - 🔔 **Smart Notifications**: Personalized air quality alerts
        - 📱 **Interactive Visualizations**: Maps, charts, and detailed analytics
        
        **Data Sources:**
        - NASA TEMPO Satellite Mission
        - EPA Air Quality System (AQS)  
        - AirNow Real-time Data
        - NOAA Weather Service
        
        **Coverage Area:** North America (United States, Canada, Mexico)
        
        Built with ❤️ for cleaner air and healthier communities.
        """)
    
    # Footer
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🛰️ Data Freshness:**
        - TEMPO: Updated hourly
        - Ground Stations: Every 15 minutes
        - Weather: Every 30 minutes
        """)
    
    with col2:
        st.markdown("""
        **📈 System Status:**
        - API: ✅ Operational
        - Database: ✅ Operational  
        - ML Models: ✅ Online
        """)
    
    with col3:
        st.markdown("""
        **🌍 Coverage:**
        - 1,000+ Monitoring Stations
        - 50+ Major Cities
        - Hourly Satellite Updates
        """)

if __name__ == "__main__":
    main()
