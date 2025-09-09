"""
Map components and utilities for CleanSky AI
"""
import folium
from folium import plugins
import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

def create_base_map(
    center_lat: float = 39.8283,
    center_lon: float = -98.5795,
    zoom: int = 4,
    style: str = "light"
) -> folium.Map:
    """
    Create a base map with specified center and style
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude  
        zoom: Initial zoom level
        style: Map style ('light', 'dark', 'satellite', 'street')
        
    Returns:
        Folium map object
    """
    # Map tile styles
    tile_styles = {
        'light': 'CartoDB positron',
        'dark': 'CartoDB dark_matter',
        'satellite': 'Esri WorldImagery',
        'street': 'OpenStreetMap'
    }
    
    tiles = tile_styles.get(style, 'CartoDB positron')
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=tiles,
        prefer_canvas=True
    )
    
    # Add scale
    folium.plugins.MeasureControl(
        primary_length_unit='kilometers',
        secondary_length_unit='miles'
    ).add_to(m)
    
    return m

def add_air_quality_stations(
    map_obj: folium.Map,
    stations_data: List[Dict[str, Any]],
    show_values: bool = True,
    cluster_markers: bool = False
) -> folium.Map:
    """
    Add air quality monitoring stations to map
    
    Args:
        map_obj: Folium map object
        stations_data: List of station data dictionaries
        show_values: Whether to show AQI values on markers
        cluster_markers: Whether to cluster nearby markers
        
    Returns:
        Updated folium map object
    """
    def get_aqi_color(aqi: float) -> str:
        """Get color based on AQI value"""
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
    
    def get_aqi_category(aqi: float) -> str:
        """Get AQI category name"""
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Moderate'
        elif aqi <= 150:
            return 'Unhealthy for Sensitive Groups'
        elif aqi <= 200:
            return 'Unhealthy'
        elif aqi <= 300:
            return 'Very Unhealthy'
        else:
            return 'Hazardous'
    
    # Create marker cluster if requested
    if cluster_markers:
        marker_cluster = plugins.MarkerCluster(
            name="Air Quality Stations",
            control=True
        ).add_to(map_obj)
        parent_obj = marker_cluster
    else:
        parent_obj = map_obj
    
    # Add station markers
    for station in stations_data:
        aqi = station.get('aqi', 0)
        lat = station.get('lat', 0)
        lon = station.get('lon', 0)
        name = station.get('name', 'Unknown Station')
        
        color = get_aqi_color(aqi)
        category = get_aqi_category(aqi)
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="color: {color}; margin-bottom: 10px;">{name}</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 4px; font-weight: bold;">AQI:</td>
                    <td style="padding: 4px; color: {color}; font-weight: bold;">{aqi:.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 4px; font-weight: bold;">Category:</td>
                    <td style="padding: 4px;">{category}</td>
                </tr>
                <tr>
                    <td style="padding: 4px; font-weight: bold;">Primary Pollutant:</td>
                    <td style="padding: 4px;">{station.get('primary_pollutant', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 4px; font-weight: bold;">Location:</td>
                    <td style="padding: 4px;">{lat:.4f}°, {lon:.4f}°</td>
                </tr>
                <tr>
                    <td style="padding: 4px; font-weight: bold;">Last Updated:</td>
                    <td style="padding: 4px;">{station.get('last_updated', 'Unknown')}</td>
                </tr>
            </table>
        </div>
        """
        
        # Create marker
        if show_values:
            # Circle marker with AQI value
            folium.CircleMarker(
                location=[lat, lon],
                radius=max(8, min(25, aqi/8)),
                popup=folium.Popup(popup_html, max_width=300),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.8,
                tooltip=f"{name}: AQI {aqi:.0f}"
            ).add_to(parent_obj)
            
            # Add text label for AQI value
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    html=f'<div style="color: white; font-weight: bold; text-shadow: 1px 1px 2px black; font-size: 12px;">{aqi:.0f}</div>',
                    icon_size=(30, 20),
                    icon_anchor=(15, 10)
                )
            ).add_to(parent_obj)
        else:
            # Simple circle marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                popup=folium.Popup(popup_html, max_width=300),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{name}: AQI {aqi:.0f}"
            ).add_to(parent_obj)
    
    return map_obj

def add_tempo_overlay(
    map_obj: folium.Map,
    tempo_data: List[Dict[str, Any]],
    parameter: str = 'NO2',
    opacity: float = 0.6
) -> folium.Map:
    """
    Add TEMPO satellite data overlay to map
    
    Args:
        map_obj: Folium map object
        tempo_data: TEMPO satellite data
        parameter: Parameter to display (NO2, O3, etc.)
        opacity: Overlay opacity (0-1)
        
    Returns:
        Updated folium map object
    """
    if not tempo_data:
        return map_obj
    
    # Filter data for the specified parameter
    param_data = [d for d in tempo_data if d.get('parameter') == parameter]
    
    if not param_data:
        return map_obj
    
    # Create color mapping based on parameter values
    values = [d.get('value', 0) for d in param_data]
    if not values:
        return map_obj
    
    min_val, max_val = min(values), max(values)
    
    # Add data points as colored circles
    for data_point in param_data:
        lat = data_point.get('lat', 0)
        lon = data_point.get('lon', 0)
        value = data_point.get('value', 0)
        
        # Normalize value for color mapping (0-1)
        normalized_value = (value - min_val) / (max_val - min_val) if max_val != min_val else 0
        
        # Color mapping: blue (low) to red (high)
        red = int(255 * normalized_value)
        blue = int(255 * (1 - normalized_value))
        color = f"#{red:02x}00{blue:02x}"
        
        # Create circle marker for TEMPO data
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            popup=f"""
            <div style="font-family: Arial, sans-serif;">
                <h5>TEMPO {parameter}</h5>
                <p><strong>Value:</strong> {value:.2e}</p>
                <p><strong>Units:</strong> {data_point.get('units', 'N/A')}</p>
                <p><strong>Location:</strong> {lat:.4f}°, {lon:.4f}°</p>
                <p><strong>Time:</strong> {data_point.get('timestamp', 'N/A')}</p>
            </div>
            """,
            color=color,
            weight=0,
            fillColor=color,
            fillOpacity=opacity,
            tooltip=f"TEMPO {parameter}: {value:.2e}"
        ).add_to(map_obj)
    
    return map_obj

def add_heatmap_layer(
    map_obj: folium.Map,
    data_points: List[Tuple[float, float, float]],
    name: str = "Air Quality Heatmap",
    radius: int = 25,
    blur: int = 15,
    gradient: Optional[Dict] = None
) -> folium.Map:
    """
    Add heatmap layer to map
    
    Args:
        map_obj: Folium map object
        data_points: List of (lat, lon, intensity) tuples
        name: Layer name
        radius: Heatmap radius
        blur: Blur amount
        gradient: Custom color gradient
        
    Returns:
        Updated folium map object
    """
    if not data_points:
        return map_obj
    
    # Default gradient (blue to red)
    if gradient is None:
        gradient = {
            0.0: 'blue',
            0.3: 'cyan', 
            0.5: 'lime',
            0.7: 'yellow',
            1.0: 'red'
        }
    
    # Create heatmap
    heat_map = plugins.HeatMap(
        data_points,
        name=name,
        radius=radius,
        blur=blur,
        gradient=gradient,
        control=True
    )
    
    heat_map.add_to(map_obj)
    
    return map_obj

def add_wind_overlay(
    map_obj: folium.Map,
    wind_data: List[Dict[str, Any]],
    arrow_scale: float = 0.1
) -> folium.Map:
    """
    Add wind direction and speed overlay
    
    Args:
        map_obj: Folium map object
        wind_data: Wind data with lat, lon, speed, direction
        arrow_scale: Scale factor for arrows
        
    Returns:
        Updated folium map object
    """
    for wind_point in wind_data:
        lat = wind_point.get('lat', 0)
        lon = wind_point.get('lon', 0)
        speed = wind_point.get('wind_speed', 0)
        direction = wind_point.get('wind_direction', 0)
        
        # Calculate arrow end point
        import math
        
        # Convert direction to radians (meteorological convention: 0° = North)
        direction_rad = math.radians(direction - 90)  # Adjust for mathematical convention
        
        # Arrow length based on wind speed
        arrow_length = speed * arrow_scale
        
        end_lat = lat + arrow_length * math.cos(direction_rad)
        end_lon = lon + arrow_length * math.sin(direction_rad)
        
        # Color based on wind speed
        if speed < 5:
            color = 'green'
        elif speed < 10:
            color = 'yellow'
        elif speed < 15:
            color = 'orange'
        else:
            color = 'red'
        
        # Add arrow
        folium.PolyLine(
            locations=[[lat, lon], [end_lat, end_lon]],
            color=color,
            weight=3,
            opacity=0.8,
            popup=f"Wind: {speed:.1f} m/s, {direction:.0f}°"
        ).add_to(map_obj)
        
        # Add arrowhead (simplified)
        folium.CircleMarker(
            location=[end_lat, end_lon],
            radius=3,
            color=color,
            fill=True,
            fillOpacity=0.8
        ).add_to(map_obj)
    
    return map_obj

def add_map_legend(
    map_obj: folium.Map,
    legend_data: Dict[str, str],
    title: str = "Legend",
    position: str = "bottomright"
) -> folium.Map:
    """
    Add custom legend to map
    
    Args:
        map_obj: Folium map object
        legend_data: Dictionary of label: color pairs
        title: Legend title
        position: Legend position
        
    Returns:
        Updated folium map object
    """
    # Create legend HTML
    legend_html = f"""
    <div style="
        position: fixed;
        {position.replace('bottom', 'bottom: 50px').replace('top', 'top: 50px').replace('left', 'left: 50px').replace('right', 'right: 50px')};
        width: 150px;
        background-color: white;
        border: 2px solid grey;
        z-index: 9999;
        font-size: 14px;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.3);
    ">
        <h4 style="margin: 0 0 10px 0; text-align: center;">{title}</h4>
    """
    
    for label, color in legend_data.items():
        legend_html += f"""
        <p style="margin: 5px 0;">
            <span style="
                display: inline-block;
                width: 15px;
                height: 15px;
                background-color: {color};
                margin-right: 8px;
                border: 1px solid black;
            "></span>
            {label}
        </p>
        """
    
    legend_html += "</div>"
    
    map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    return map_obj

def add_layer_control(map_obj: folium.Map) -> folium.Map:
    """Add layer control to map"""
    folium.LayerControl(
        position='topright',
        collapsed=False
    ).add_to(map_obj)
    
    return map_obj

def add_fullscreen_control(map_obj: folium.Map) -> folium.Map:
    """Add fullscreen control to map"""
    plugins.Fullscreen(
        position='topleft',
        title='Expand map',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(map_obj)
    
    return map_obj

def add_draw_control(map_obj: folium.Map) -> folium.Map:
    """Add drawing tools to map"""
    draw = plugins.Draw(
        export=True,
        position='topleft'
    )
    draw.add_to(map_obj)
    
    return map_obj

def create_choropleth_map(
    map_obj: folium.Map,
    geojson_data: str,
    data: pd.DataFrame,
    columns: List[str],
    key_on: str = "feature.id",
    fill_color: str = "YlOrRd",
    nan_fill_color: str = "white",
    legend_name: str = "Air Quality Index"
) -> folium.Map:
    """
    Create choropleth map for regional air quality data
    
    Args:
        map_obj: Folium map object
        geojson_data: GeoJSON data for regions
        data: DataFrame with regional data
        columns: [region_id, value] columns
        key_on: GeoJSON key to match with data
        fill_color: Color scheme
        nan_fill_color: Color for missing data
        legend_name: Legend title
        
    Returns:
        Updated folium map object
    """
    folium.Choropleth(
        geo_data=geojson_data,
        name=legend_name,
        data=data,
        columns=columns,
        key_on=key_on,
        fill_color=fill_color,
        fill_opacity=0.7,
        line_opacity=0.2,
        nan_fill_color=nan_fill_color,
        legend_name=legend_name,
        control=True
    ).add_to(map_obj)
    
    return map_obj

def export_map(
    map_obj: folium.Map,
    filename: str = "cleansky_map.html",
    include_data: bool = True
) -> str:
    """
    Export map to HTML file
    
    Args:
        map_obj: Folium map object
        filename: Output filename
        include_data: Whether to include data in export
        
    Returns:
        Path to exported file
    """
    try:
        map_obj.save(filename)
        return filename
    except Exception as e:
        st.error(f"Failed to export map: {str(e)}")
        return None

def get_map_bounds(locations: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Calculate map bounds for list of locations
    
    Args:
        locations: List of (lat, lon) tuples
        
    Returns:
        Dictionary with north, south, east, west bounds
    """
    if not locations:
        return {'north': 50, 'south': 30, 'east': -70, 'west': -120}
    
    lats = [loc[0] for loc in locations]
    lons = [loc[1] for loc in locations]
    
    return {
        'north': max(lats),
        'south': min(lats),
        'east': max(lons),
        'west': min(lons)
    }

def fit_map_to_bounds(
    map_obj: folium.Map,
    bounds: Dict[str, float],
    padding: float = 0.1
) -> folium.Map:
    """
    Fit map view to specified bounds
    
    Args:
        map_obj: Folium map object
        bounds: Dictionary with north, south, east, west bounds
        padding: Padding factor for bounds
        
    Returns:
        Updated folium map object
    """
    # Add padding
    lat_padding = (bounds['north'] - bounds['south']) * padding
    lon_padding = (bounds['east'] - bounds['west']) * padding
    
    southwest = [bounds['south'] - lat_padding, bounds['west'] - lon_padding]
    northeast = [bounds['north'] + lat_padding, bounds['east'] + lon_padding]
    
    map_obj.fit_bounds([southwest, northeast])
    
    return map_obj
