"""
Bhopal Crime & Safety Intelligence Dashboard
Folium Map Rendering Engine
Builds interactive Folium maps supporting Marker Clusters, Heatmaps, and Police Layers.
Uses high-reliability public basemaps (ESRI Street Map & Carto Voyager) to avoid access restrictions.
"""

import folium
from folium.plugins import MarkerCluster, HeatMap, Fullscreen
import pandas as pd
from data_generator import POLICE_STATIONS, SAFE_CORRIDORS

# Visual color mapping for crime categories
CATEGORY_PALETTE = {
    "Property Crime & Theft": {
        "hex": "#FF7A00",
        "badge": "rgba(255, 122, 0, 0.15)",
        "border": "#FF7A00"
    },
    "Assault & Physical Offenses": {
        "hex": "#E63946",
        "badge": "rgba(230, 57, 70, 0.15)",
        "border": "#E63946"
    },
    "Public Harassment / Women's Safety": {
        "hex": "#9333EA",
        "badge": "rgba(147, 51, 234, 0.15)",
        "border": "#9333EA"
    },
    "Vandalism / Petty Mischief": {
        "hex": "#EAB308",
        "badge": "rgba(234, 179, 8, 0.15)",
        "border": "#EAB308"
    }
}


def build_bhopal_map(
    filtered_df: pd.DataFrame,
    view_mode: str = "Marker Cluster",
    show_police_stations: bool = True,
    show_safe_corridors: bool = True,
    selected_neighborhood: str = "All Bhopal Sectors"
) -> folium.Map:
    """
    Constructs a customized Folium map for Bhopal crime analysis.
    Uses reliable tile servers (ESRI & Carto Voyager) that do not block browser requests.
    Supports Marker Cluster View and Kernel Density Heatmap View.
    """
    # Calculate map center
    if not filtered_df.empty and selected_neighborhood != "All Bhopal Sectors":
        center_lat = float(filtered_df["latitude"].mean())
        center_lon = float(filtered_df["longitude"].mean())
        zoom_level = 14
    else:
        center_lat = 23.2500
        center_lon = 77.4170
        zoom_level = 12

    # Initialize Base Folium Map with ESRI World Street Map (unrestricted, high detail)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, METI, TomTom",
        name="ESRI Street Map (Detailed)",
        control_scale=True,
        prefer_canvas=True
    )

    # 1. OpenStreetMap Tile Layer (100% Free, Unrestricted, No API key)
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="OpenStreetMap (Standard)",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        control=True
    ).add_to(m)

    # 2. ESRI Satellite Imagery
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite Imagery (ESRI)",
        attr="Tiles &copy; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP",
        control=True
    ).add_to(m)

    # 3. Minimal Light Gray Canvas
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        name="Minimal Light Gray (ESRI)",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        control=True
    ).add_to(m)

    # 4. ESRI Topographic
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        name="Topographic Map (ESRI)",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap",
        control=True
    ).add_to(m)

    # --- Mode 1: Marker Cluster View ---
    if view_mode == "Marker Cluster":
        mc_group = folium.FeatureGroup(name="Crime Incident Markers", show=True)
        cluster = MarkerCluster(
            name="Incidents Cluster",
            options={
                "maxClusterRadius": 45,
                "spiderfyOnMaxZoom": True,
                "showCoverageOnHover": False,
                "zoomToBoundsOnClick": True
            }
        ).add_to(mc_group)

        for _, row in filtered_df.iterrows():
            cat = row.get("crime_category", "Other")
            palette = CATEGORY_PALETTE.get(cat, {"hex": "#3B82F6", "badge": "rgba(59,130,246,0.15)", "border": "#3B82F6"})
            color = palette["hex"]
            
            # Severity color badge
            sev = int(row.get("severity_score", 3))
            sev_color = "#10B981" if sev <= 2 else "#F59E0B" if sev == 3 else "#EF4444"
            
            # Distance info if present
            dist_str = ""
            if "nearest_station" in row and pd.notna(row["nearest_station"]):
                dist_str = f"""
                <div style="margin-top:6px; font-size:11px; color:#334155; background:#F8FAFC; padding:4px 8px; border-radius:4px; border:1px solid #E2E8F0;">
                    🛡️ <b>Nearest Thana:</b> {row['nearest_station']} ({row.get('distance_to_station_km', 'N/A')} km)
                </div>
                """

            popup_html = f"""
            <div style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; width:260px; font-size:12px; color:#0F172A; line-height:1.45;">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #E2E8F0; padding-bottom:6px; margin-bottom:8px;">
                    <span style="font-weight:700; color:#0F172A; font-size:13px;">{row['incident_id']}</span>
                    <span style="background:{palette['badge']}; color:{palette['hex']}; font-weight:700; font-size:10px; padding:2px 6px; border-radius:10px; border:1px solid {palette['border']};">
                        {cat}
                    </span>
                </div>
                <div style="margin-bottom:4px;"><b>📍 Sector:</b> {row['neighborhood']}</div>
                <div style="margin-bottom:4px;"><b>⚠️ Detail:</b> {row.get('crime_subtype', 'Reported Incident')}</div>
                <div style="margin-bottom:4px;"><b>🕒 Time:</b> {row['time_of_day']} ({row['date']})</div>
                <div style="margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                    <b>Severity:</b>
                    <span style="background:{sev_color}; color:#fff; font-weight:bold; padding:1px 7px; border-radius:4px; font-size:11px;">
                        Level {sev}/5
                    </span>
                    <span style="color:#64748B; font-size:11px;">({row.get('status', 'Registered')})</span>
                </div>
                {dist_str}
            </div>
            """

            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=7,
                color="#FFFFFF",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.90,
                tooltip=f"<b>{row['incident_id']}</b>: {cat} ({row['neighborhood']})",
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(cluster)

        mc_group.add_to(m)

    # --- Mode 2: Kernel Density Heatmap View ---
    elif view_mode == "Kernel Density Heatmap":
        heat_data = []
        for _, row in filtered_df.iterrows():
            weight = float(row.get("severity_score", 3)) / 5.0
            heat_data.append([row["latitude"], row["longitude"], weight])

        if heat_data:
            HeatMap(
                data=heat_data,
                name="Crime Density Heatmap",
                min_opacity=0.40,
                radius=26,
                blur=22,
                max_zoom=14,
                gradient={
                    0.2: "#38bdf8",
                    0.4: "#22c55e",
                    0.6: "#eab308",
                    0.8: "#f97316",
                    1.0: "#dc2626"
                }
            ).add_to(m)

    # --- Police Station Overlay Layer ---
    if show_police_stations:
        ps_group = folium.FeatureGroup(name="Bhopal Police Stations & Thanas", show=True)
        for ps in POLICE_STATIONS:
            is_special = "Mahila" in ps["name"]
            pin_color = "darkpurple" if is_special else "blue"
            icon_symbol = "star" if is_special else "flag"

            ps_popup = f"""
            <div style="font-family:'Segoe UI',Roboto,Helvetica,sans-serif; width:230px; font-size:12px; color:#0F172A;">
                <div style="font-weight:700; color:#1E3A8A; font-size:13px; margin-bottom:4px;">
                    🛡️ {ps['name']}
                </div>
                <div style="color:#475569; margin-bottom:3px;"><b>Jurisdiction:</b> {ps['jurisdiction']}</div>
                <div style="color:#047857; margin-bottom:3px;"><b>📞 Desk:</b> {ps['phone']}</div>
                <div style="background:#EFF6FF; padding:4px 6px; border-radius:4px; font-size:10px; color:#1D4ED8; margin-top:4px; border:1px solid #BFDBFE;">
                    ⚡ Emergency Response Hub • Dial 112
                </div>
            </div>
            """

            folium.Marker(
                location=[ps["lat"], ps["lon"]],
                popup=folium.Popup(ps_popup, max_width=260),
                tooltip=f"Police Station: {ps['name']}",
                icon=folium.Icon(color=pin_color, icon=icon_symbol)
            ).add_to(ps_group)

        ps_group.add_to(m)

    # --- Safe Well-Lit Corridors Layer ---
    if show_safe_corridors:
        corridor_group = folium.FeatureGroup(name="Smart City Well-Lit Safe Corridors", show=True)
        for corridor in SAFE_CORRIDORS:
            folium.PolyLine(
                locations=corridor["coords"],
                color="#0284C7",
                weight=5,
                opacity=0.85,
                dash_array="6, 8",
                tooltip=f"Safe Corridor: {corridor['name']} ({corridor['status']})"
            ).add_to(corridor_group)

        corridor_group.add_to(m)

    # Add Fullscreen and LayerControl
    Fullscreen(position="topright").add_to(m)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)

    return m
