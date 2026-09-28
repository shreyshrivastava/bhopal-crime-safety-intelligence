"""
Bhopal Safety Intelligence Portal
Material Active (M3 Adaptive) UI Engine
Renders the complete Material You / Material Design 3 Adaptive UI with live data connections,
embedded interactive Leaflet map, and responsive cross-platform layout.
"""

import json
import pandas as pd
from data_generator import POLICE_STATIONS, SAFE_CORRIDORS, NEIGHBORHOOD_CONFIG


def generate_material_active_html(
    df: pd.DataFrame,
    risk_df: pd.DataFrame
) -> str:
    """
    Constructs the complete, self-contained HTML/CSS/JS document implementing
    the Bhopal Safety Intelligence portal, with connected dataset,
    embedded Leaflet geospatial engine, and fully working search, analyze, and navigation.
    """
    total_incidents = len(df)
    
    if total_incidents > 0:
        peak_category = df["crime_category"].mode()[0]
        peak_cat_count = int((df["crime_category"] == peak_category).sum())
        peak_cat_pct = round((peak_cat_count / total_incidents) * 100, 1)

        peak_zone = df["neighborhood"].mode()[0]
        peak_zone_count = int((df["neighborhood"] == peak_zone).sum())
        
        avg_severity = round(df["severity_score"].mean(), 2)
        high_sev_count = int((df["severity_score"] >= 4).sum())
        high_sev_pct = round((high_sev_count / total_incidents) * 100, 1)
        
        night_count = int((df["time_of_day"] == "Nighttime/Post-10 PM").sum())
        night_pct = round((night_count / total_incidents) * 100, 1)
        day_count = total_incidents - night_count
    else:
        peak_category = "No Data"
        peak_cat_count = 0
        peak_cat_pct = 0.0
        peak_zone = "N/A"
        peak_zone_count = 0
        avg_severity = 0.0
        high_sev_count = 0
        high_sev_pct = 0.0
        night_count = 0
        night_pct = 0.0
        day_count = 0

    # Sector distribution data
    sector_counts = df["neighborhood"].value_counts()
    max_sector_val = sector_counts.max() if not sector_counts.empty else 1
    sector_bars_html = ""
    for nh, count in sector_counts.items():
        pct = round((count / max_sector_val) * 100, 1)
        sector_bars_html += f"""
        <div class="flex items-center gap-3 text-[11px] group cursor-pointer hover:bg-white/5 p-1 rounded-lg transition-all" onclick="filterByZone('{nh}')">
            <span class="w-36 text-right truncate text-on-surface-variant font-medium group-hover:text-primary transition-colors">{nh}</span>
            <div class="flex-1 bg-surface-container h-5 rounded-full overflow-hidden p-0.5 border border-white/5">
                <div class="bg-gradient-to-r from-purple-600 to-fuchsia-500 h-full rounded-full flex items-center justify-end pr-2 text-white font-mono font-bold text-[10px] shadow-sm transition-all duration-500" style="width: {pct}%;">{count}</div>
            </div>
        </div>
        """

    # Severity distribution data
    sev_counts = df["severity_score"].value_counts().to_dict()
    max_sev = max(sev_counts.values()) if sev_counts else 1
    
    # Offense modalities data
    modality_counts = df["crime_subtype"].value_counts().head(5)
    max_mod = modality_counts.max() if not modality_counts.empty else 1
    modalities_html = ""
    for mod, count in modality_counts.items():
        pct = round((count / max_mod) * 100, 1)
        modalities_html += f"""
        <div class="flex items-center gap-3 text-[11px]">
            <span class="w-48 text-right truncate text-on-surface-variant font-medium">{mod}</span>
            <div class="flex-1 bg-surface-container h-5 rounded-full overflow-hidden p-0.5 border border-white/5">
                <div class="bg-gradient-to-r from-sky-500 to-blue-600 h-full rounded-full flex items-center justify-end pr-2 text-white font-mono font-bold text-[10px]" style="width: {pct}%;">{count}</div>
            </div>
        </div>
        """

    # Prepare JSON serializable records for client-side Leaflet and reactivity
    records = []
    for _, row in df.iterrows():
        records.append({
            "id": row.get("incident_id", ""),
            "lat": float(row.get("latitude", 23.25)),
            "lon": float(row.get("longitude", 77.41)),
            "neighborhood": row.get("neighborhood", ""),
            "category": row.get("crime_category", ""),
            "subtype": row.get("crime_subtype", ""),
            "time_of_day": row.get("time_of_day", ""),
            "date": str(row.get("date", "")),
            "severity": int(row.get("severity_score", 3)),
            "status": row.get("status", "Registered"),
            "nearest_ps": str(row.get("nearest_station", "Bhopal PS")),
            "dist_km": float(row.get("distance_to_station_km", 0.0))
        })
    crime_json = json.dumps(records)
    ps_json = json.dumps(POLICE_STATIONS)
    corridors_json = json.dumps(SAFE_CORRIDORS)

    # Sector table rows for Tab 2
    sector_table_rows = ""
    if not risk_df.empty:
        for _, r in risk_df.iterrows():
            badge_bg = "bg-emerald-950/50 text-emerald-300 border-emerald-500/30" if "Safe" in r["Risk Level"] else \
                       "bg-amber-950/50 text-amber-300 border-amber-500/30" if "Moderate" in r["Risk Level"] else \
                       "bg-rose-950/50 text-rose-300 border-rose-500/30"
            sector_table_rows += f"""
            <tr class="border-b border-white/5 hover:bg-white/5 transition-colors text-[12px]">
                <td class="py-2.5 px-3 font-semibold text-on-surface">{r['Neighborhood']}</td>
                <td class="py-2.5 px-3 font-mono">{r['Incidents']}</td>
                <td class="py-2.5 px-3 font-mono">{r['Avg Severity']} / 5.0</td>
                <td class="py-2.5 px-3 font-mono">{r['Nighttime Ratio (%)']}%</td>
                <td class="py-2.5 px-3 text-on-surface-variant">{r['Dominant Crime']}</td>
                <td class="py-2.5 px-3 font-mono font-bold text-primary">{r['Risk Score']}</td>
                <td class="py-2.5 px-3"><span class="px-2.5 py-0.5 rounded-full border text-[10px] font-bold {badge_bg}">{r['Risk Level']}</span></td>
            </tr>
            """

    # Severity heights
    l2_count = sev_counts.get(2, 0)
    l3_count = sev_counts.get(3, 0)
    l4_count = sev_counts.get(4, 0)
    l5_count = sev_counts.get(5, 0)
    
    l2_pct = round((l2_count / max_sev) * 100, 1)
    l3_pct = round((l3_count / max_sev) * 100, 1)
    l4_pct = round((l4_count / max_sev) * 100, 1)
    l5_pct = round((l5_count / max_sev) * 100, 1)

    html_template = f"""<!DOCTYPE html>
<html class="dark" lang="en" style="width: 100%; min-height: 100%;">
<head>
<meta charset="utf-8">
<meta content="width=device-width, initial-scale=1.0" name="viewport">
<meta content="web_dashboard" name="shell-type">
<title>Bhopal Safety Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Roboto+Flex:wght@100..900&amp;display=swap" rel="stylesheet">

<!-- Leaflet CSS & Plugins -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />

<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
tailwind.config = {{
  darkMode: "class",
  theme: {{
    extend: {{
      colors: {{
        "tertiary-fixed-dim": "#4edea3",
        "primary-fixed": "#c4e7ff",
        "on-secondary-container": "#d6e5ff",
        "error": "#ffb4ab",
        "surface-container-highest": "#31353e",
        "on-tertiary-container": "#004e34",
        "secondary-fixed": "#d4e3ff",
        "secondary": "#a4c9ff",
        "on-secondary-fixed": "#001c39",
        "tertiary-fixed": "#6ffbbe",
        "on-error-container": "#ffdad6",
        "tertiary-container": "#30c88f",
        "on-primary-fixed": "#001e2c",
        "on-secondary-fixed-variant": "#004883",
        "surface-tint": "#7bd0ff",
        "secondary-fixed-dim": "#a4c9ff",
        "error-container": "#93000a",
        "on-tertiary-fixed-variant": "#005236",
        "primary-container": "#38bdf8",
        "surface-container-low": "#141822",
        "primary": "#8ed5ff",
        "on-background": "#dfe2ee",
        "surface-variant": "#282d38",
        "secondary-container": "#0267b8",
        "on-primary": "#00354a",
        "outline-variant": "#3e484f",
        "surface-container": "#1a1f2b",
        "on-tertiary-fixed": "#002113",
        "on-surface-variant": "#bdc8d1",
        "surface-container-lowest": "#0b0f17",
        "surface-bright": "#353942",
        "outline": "#87929a",
        "inverse-primary": "#00668a",
        "on-secondary": "#00315d",
        "surface-dim": "#0f131c",
        "inverse-surface": "#dfe2ee",
        "on-primary-container": "#004965",
        "on-tertiary": "#003824",
        "surface": "#0d111a",
        "primary-fixed-dim": "#7bd0ff",
        "background": "#0b0f17",
        "on-primary-fixed-variant": "#004c69",
        "on-error": "#690005",
        "on-surface": "#dfe2ee",
        "surface-container-high": "#222735",
        "inverse-on-surface": "#2c3039",
        "tertiary": "#56e5a9"
      }},
      borderRadius: {{
        "DEFAULT": "0.5rem",
        "lg": "1rem",
        "xl": "1.25rem",
        "2xl": "1.75rem",
        "3xl": "2.25rem",
        "squircle": "28px",
        "full": "9999px"
      }},
      boxShadow: {{
        "m3-1": "0 1px 3px 1px rgba(0, 0, 0, 0.15), 0 1px 2px 0 rgba(0, 0, 0, 0.3)",
        "m3-2": "0 2px 6px 2px rgba(0, 0, 0, 0.15), 0 1px 2px 0 rgba(0, 0, 0, 0.3)",
        "m3-glow": "0 12px 36px -8px rgba(56, 189, 248, 0.2)",
        "m3-pill": "0 4px 20px -2px rgba(0, 0, 0, 0.4), inset 0 1px 1px 0 rgba(255, 255, 255, 0.08)",
        "m3-card": "0 10px 30px -10px rgba(56, 189, 248, 0.08), 0 4px 18px rgba(0, 0, 0, 0.35)",
        "m3-error-glow": "0 8px 24px -4px rgba(239, 68, 68, 0.35)"
      }},
      fontFamily: {{
        "roboto": ["Roboto Flex", "sans-serif"]
      }}
    }}
  }}
}}
</script>
<style>
@layer base {{
  html, body {{
    margin: 0;
    padding: 0;
    background-color: #0b0f17;
    color: #dfe2ee;
    font-family: 'Roboto Flex', sans-serif;
  }}
}}
::-webkit-scrollbar {{
  width: 6px;
  height: 6px;
}}
::-webkit-scrollbar-track {{
  background: transparent;
}}
::-webkit-scrollbar-thumb {{
  background: #31353e;
  border-radius: 9999px;
}}
.fluid-transition {{
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

/* Custom Leaflet Map Container inside M3 frame */
#leaflet-map {{
  width: 100%;
  height: 100%;
  background: #070b12;
  border-radius: 24px;
}}
.leaflet-popup-content-wrapper {{
  background: #141822 !important;
  color: #dfe2ee !important;
  border-radius: 18px !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
}}
.leaflet-popup-tip {{
  background: #141822 !important;
}}
.marker-cluster-small, .marker-cluster-medium, .marker-cluster-large {{
  background-color: rgba(56, 189, 248, 0.3) !important;
}}
.marker-cluster-small div, .marker-cluster-medium div, .marker-cluster-large div {{
  background-color: rgba(14, 165, 233, 0.85) !important;
  color: #ffffff !important;
  font-weight: 800 !important;
  font-family: 'Roboto Flex', monospace !important;
}}
</style>
</head>
<body class="bg-[#0b0f17] text-on-surface antialiased selection:bg-primary selection:text-on-primary min-h-screen relative font-roboto">

<!-- Main Dashboard Container -->
<div class="px-4 md:px-8 pt-5 pb-32 min-h-screen flex flex-col gap-5">

<!-- Top Operational Bar -->
<header class="w-full bg-surface-container-low/85 backdrop-blur-2xl rounded-full px-5 py-2.5 border border-white/10 shadow-m3-card flex items-center justify-between gap-4 sticky top-4 z-40">
  <!-- Left: Brand + Search with Sector Jump -->
  <div class="flex items-center gap-3 flex-1 max-w-2xl">
    <div class="flex items-center gap-2.5 shrink-0 pr-3 border-r border-white/10 cursor-pointer" onclick="resetAllFilters()">
      <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-primary-container to-secondary-container p-1.5 flex items-center justify-center shadow-m3-glow shrink-0">
        <span class="material-symbols-outlined text-[18px] text-white">shield</span>
      </div>
      <div class="hidden sm:flex flex-col min-w-0">
        <span class="text-[13px] font-bold text-primary tracking-tight leading-tight truncate">Bhopal Safety Intelligence</span>
        <span class="text-[8.5px] text-on-surface-variant font-medium tracking-wider uppercase truncate">Civic Safety Portal</span>
      </div>
    </div>

    <!-- Connected Global Search Input -->
    <div class="relative w-full flex items-center">
      <div class="absolute left-3.5 top-1/2 -translate-y-1/2 flex items-center pointer-events-none text-primary">
        <span class="material-symbols-outlined text-[19px]">search</span>
      </div>
      <input id="global-search-input" oninput="handleSearch(this.value)" onkeydown="if(event.key==='Enter') executeSearch(this.value)" class="w-full bg-surface-container-lowest/80 text-on-surface placeholder:text-outline/70 pl-10 pr-9 py-2 rounded-full text-[13px] border border-white/5 focus:border-primary/60 focus:bg-surface-container-high focus:outline-none focus:ring-2 focus:ring-primary/20 fluid-transition" placeholder="Search Ward 1-85, Sector (e.g. MP Nagar, TT Nagar, Shahpura, Arera)..." type="text">
      <button id="search-clear-btn" onclick="clearSearch()" class="hidden absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface text-[16px] cursor-pointer" title="Clear Search">
        <span class="material-symbols-outlined text-[16px]">close</span>
      </button>
    </div>

    <!-- Quick Ward Jump Select -->
    <select id="quick-ward-select" onchange="filterByZone(this.value)" class="hidden xl:flex items-center gap-1.5 bg-surface-container-high/80 px-3 py-1.5 rounded-full text-on-surface-variant text-[11px] font-medium border border-white/10 cursor-pointer hover:bg-surface-bright fluid-transition focus:outline-none">
      <option value="ALL">All Wards</option>
      <option value="MP Nagar">MP Nagar</option>
      <option value="TT Nagar / New Market">TT Nagar</option>
      <option value="Old Bhopal / Ibrahimganj">Old Bhopal</option>
      <option value="Shahpura">Shahpura</option>
      <option value="Arera Colony">Arera Colony</option>
      <option value="Kolar Road">Kolar Road</option>
      <option value="Bittan Market">Bittan Market</option>
      <option value="Ayodhya Bypass">Ayodhya Bypass</option>
      <option value="Hoshangabad Road">Hoshangabad Rd</option>
    </select>
  </div>

  <!-- Right: Incident Records Badge, SOS Action, Theme Toggle -->
  <div class="flex items-center gap-2.5">
    <div class="hidden md:flex items-center gap-2 bg-surface-container-lowest/80 px-3.5 py-1.5 rounded-full border border-white/10 shadow-sm">
      <span class="material-symbols-outlined text-primary text-[15px]">folder_open</span>
      <span class="text-[11px] font-mono text-on-surface font-semibold">520 Incident Records</span>
    </div>
    <a class="flex items-center gap-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-4 py-1.5 rounded-full text-[12px] font-bold shadow-m3-error-glow fluid-transition hover:scale-105 active:scale-95 border border-red-400/40" href="tel:112">
      <span class="material-symbols-outlined text-[16px]">emergency</span>
      <span>Dial 112 SOS</span>
    </a>
    <button class="flex items-center justify-center w-9 h-9 rounded-full bg-surface-container-high/80 hover:bg-surface-bright text-on-surface-variant hover:text-on-surface border border-white/10 fluid-transition cursor-pointer" id="theme-toggle-btn" onclick="toggleTheme()" title="Toggle Dark / Light Mode" type="button">
      <span class="material-symbols-outlined text-amber-400 text-[18px]">light_mode</span>
    </button>
  </div>
</header>

<!-- Incident Registry Overview Ribbon -->
<div class="flex flex-wrap items-center justify-between gap-2 bg-surface-container-low/70 px-4 py-2 rounded-2xl border border-white/5 text-[11px]">
  <div class="flex items-center gap-2">
    <span class="material-symbols-outlined text-primary text-[15px]">shield</span>
    <span class="font-bold text-on-surface uppercase tracking-wider">Bhopal Incident Registry</span>
    <span class="text-on-surface-variant">•</span>
    <span class="font-mono text-on-surface-variant">85-Ward Historical Analysis (90-Day Records)</span>
  </div>
  <div class="flex items-center gap-2">
    <span class="font-mono text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">GRID: 23.2599° N, 77.4126° E</span>
    <span class="font-mono font-bold text-on-surface-variant bg-surface-container-high px-2 py-0.5 rounded-full uppercase" id="ribbon-active-zone">Zone: {peak_zone}</span>
  </div>
</div>

<!-- 4 Fluid Metric Overview Cards -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  <!-- Card 1: Filtered Incidents -->
  <div class="bg-surface-container-low/80 backdrop-blur-xl rounded-[28px] p-5 border border-white/5 shadow-m3-card relative overflow-hidden group hover:border-primary/30 fluid-transition flex flex-col justify-between">
    <div class="absolute -right-8 -top-8 w-32 h-32 bg-primary/10 rounded-full blur-2xl pointer-events-none group-hover:bg-primary/20 fluid-transition"></div>
    <div class="flex items-start justify-between relative z-10">
      <div class="flex flex-col min-w-0">
        <span class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider font-mono">Filtered Incidents</span>
        <div class="flex items-baseline gap-2 mt-1">
          <span class="text-3xl font-extrabold text-on-surface tracking-tight font-mono" id="metric-total-count">{total_incidents}</span>
          <span class="text-xs text-primary font-bold bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">Selected</span>
        </div>
      </div>
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary-container to-secondary-container text-white flex items-center justify-center shadow-m3-glow shrink-0">
        <span class="material-symbols-outlined text-[24px]">filter_list</span>
      </div>
    </div>
    <div class="mt-4 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-on-surface-variant relative z-10">
      <span class="truncate">Out of {total_incidents} recorded in 90-day window</span>
    </div>
  </div>

  <!-- Card 2: Dominant Crime Type -->
  <div class="bg-surface-container-low/80 backdrop-blur-xl rounded-[28px] p-5 border border-white/5 shadow-m3-card relative overflow-hidden group hover:border-primary/30 fluid-transition flex flex-col justify-between">
    <div class="absolute -right-8 -top-8 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-purple-500/20 fluid-transition"></div>
    <div class="flex items-start justify-between relative z-10">
      <div class="flex flex-col min-w-0 pr-1">
        <span class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider font-mono">Dominant Crime Type</span>
        <div class="mt-1">
          <span class="text-[15px] font-bold text-purple-300 leading-tight block truncate" id="metric-top-crime">{peak_category}</span>
        </div>
      </div>
      <div class="w-12 h-12 rounded-2xl bg-surface-container-high border border-purple-500/20 text-purple-300 flex items-center justify-center shadow-m3-1 shrink-0">
        <span class="material-symbols-outlined text-[24px]">shield_person</span>
      </div>
    </div>
    <div class="mt-4 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-on-surface-variant relative z-10">
      <span class="truncate" id="metric-top-crime-sub">{peak_cat_pct}% of selection ({peak_cat_count} cases)</span>
      <span class="px-2 py-0.5 rounded-full bg-purple-950/60 text-purple-300 font-mono text-[10px] font-bold shrink-0">{peak_cat_pct}%</span>
    </div>
  </div>

  <!-- Card 3: Highest-Risk Sector -->
  <div class="bg-surface-container-low/80 backdrop-blur-xl rounded-[28px] p-5 border border-white/5 shadow-m3-card relative overflow-hidden group hover:border-error/30 fluid-transition flex flex-col justify-between">
    <div class="absolute -right-8 -top-8 w-32 h-32 bg-error/10 rounded-full blur-2xl pointer-events-none group-hover:bg-error/20 fluid-transition"></div>
    <div class="flex items-start justify-between relative z-10">
      <div class="flex flex-col min-w-0 pr-1">
        <span class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider font-mono">Highest-Risk Sector</span>
        <div class="mt-1 flex items-baseline gap-2">
          <span class="text-[16px] font-bold text-error leading-tight truncate" id="metric-top-sector">{peak_zone}</span>
        </div>
      </div>
      <div class="w-12 h-12 rounded-2xl bg-surface-container-high border border-error/20 text-error flex items-center justify-center shadow-m3-error-glow shrink-0">
        <span class="material-symbols-outlined text-[24px]">warning</span>
      </div>
    </div>
    <div class="mt-4 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-on-surface-variant relative z-10">
      <span class="truncate" id="metric-top-sector-sub">{peak_zone_count} reported events</span>
      <span class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface font-mono text-[10px] font-bold shrink-0">Sector Focus</span>
    </div>
  </div>

  <!-- Card 4: Average Severity -->
  <div class="bg-surface-container-low/80 backdrop-blur-xl rounded-[28px] p-5 border border-white/5 shadow-m3-card relative overflow-hidden group hover:border-amber-500/30 fluid-transition flex flex-col justify-between">
    <div class="absolute -right-8 -top-8 w-32 h-32 bg-amber-400/10 rounded-full blur-2xl pointer-events-none group-hover:bg-amber-400/20 fluid-transition"></div>
    <div class="flex items-start justify-between relative z-10">
      <div class="flex flex-col min-w-0">
        <span class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider font-mono">Average Severity</span>
        <div class="flex items-baseline gap-2 mt-1">
          <span class="text-3xl font-extrabold text-amber-300 tracking-tight font-mono" id="metric-avg-sev">{avg_severity}</span>
          <span class="text-base text-on-surface-variant font-mono">/ 5.0</span>
        </div>
      </div>
      <div class="w-12 h-12 rounded-2xl bg-surface-container-high border border-amber-500/30 text-amber-400 flex items-center justify-center shadow-m3-1 shrink-0">
        <span class="material-symbols-outlined text-[24px]">speed</span>
      </div>
    </div>
    <div class="mt-4 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-on-surface-variant relative z-10">
      <span class="truncate">Moderate Risk ({high_sev_pct}% rated High/Critical)</span>
    </div>
  </div>
</div>

<!-- Main Operational Grid: Geospatial Layer & Incident Filter Controls alongside Interactive Map -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
  <!-- LEFT OPERATIONAL STACK (5 cols on lg) -->
  <div class="lg:col-span-5 flex flex-col gap-4">
    <!-- 1. Geospatial Layer Controls Card -->
    <div class="bg-surface-container-low/90 backdrop-blur-2xl rounded-[28px] p-4.5 border border-white/10 shadow-m3-card flex flex-col gap-3">
      <div class="flex items-center justify-between pb-2 border-b border-white/5">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[20px]">layers</span>
          <span class="text-[13px] font-bold text-on-surface uppercase tracking-wide">Geospatial Layer Controls</span>
        </div>
        <span class="text-[10px] font-mono text-on-surface-variant bg-surface-container-high px-2 py-0.5 rounded-full font-medium">GIS LAYERS</span>
      </div>

      <!-- Visualization Mode toggle: Marker Cluster vs Kernel Density -->
      <div class="flex flex-col gap-1.5">
        <span class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider font-mono">Visualization Mode</span>
        <div class="grid grid-cols-2 gap-1.5 p-1 bg-surface-container-lowest/80 rounded-full border border-white/5 text-[11px]">
          <button class="py-1 px-2.5 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition text-[11px] flex items-center justify-center gap-1.5 cursor-pointer" id="viz-cluster-btn" onclick="setVizMode('cluster')" type="button">
            <span class="w-1.5 h-1.5 rounded-full bg-on-primary-container"></span>Marker Cluster
          </button>
          <button class="py-1 px-2.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high text-center fluid-transition text-[11px] cursor-pointer" id="viz-density-btn" onclick="setVizMode('density')" type="button">
            Kernel Density
          </button>
        </div>
      </div>

      <!-- Active Overlays checkboxes -->
      <div class="flex flex-col gap-2 pt-1">
        <span class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider font-mono">Active Overlays</span>
        <label class="flex items-center justify-between p-2 px-3 rounded-2xl bg-surface-container-lowest/80 border border-white/5 hover:bg-surface-container-high cursor-pointer fluid-transition">
          <div class="flex items-center gap-2.5 text-[12px]">
            <input checked id="overlay-police-chk" onchange="togglePoliceLayer(this.checked)" class="accent-primary rounded cursor-pointer w-4 h-4 bg-surface-container" type="checkbox">
            <span class="text-on-surface font-medium leading-tight">Police Stations &amp; Helplines</span>
          </div>
          <span class="font-mono text-[10px] text-primary font-bold bg-primary/10 px-2 py-0.5 rounded-full">10 PS</span>
        </label>
        <label class="flex items-center justify-between p-2 px-3 rounded-2xl bg-surface-container-lowest/80 border border-white/5 hover:bg-surface-container-high cursor-pointer fluid-transition">
          <div class="flex items-center gap-2.5 text-[12px]">
            <input checked id="overlay-corridors-chk" onchange="toggleCorridorsLayer(this.checked)" class="accent-emerald-400 rounded cursor-pointer w-4 h-4 bg-surface-container" type="checkbox">
            <span class="text-on-surface font-medium leading-tight">Civic Safe Corridors</span>
          </div>
          <span class="font-mono text-[10px] text-tertiary font-bold bg-tertiary/10 px-2 py-0.5 rounded-full">3 Nodes</span>
        </label>
      </div>

      <!-- Attribution -->
      <div class="pt-2 border-t border-white/5 flex flex-col gap-0.5 text-[10px] text-on-surface-variant font-mono">
        <span class="leading-relaxed text-outline">Bhopal Smart City Development &amp; Civic Safety Geospatial Intelligence Hub.</span>
      </div>
    </div>

    <!-- 2. Incident Filter Controls Card -->
    <div class="bg-surface-container-low/90 backdrop-blur-2xl rounded-[28px] p-4.5 border border-white/10 shadow-m3-card flex flex-col gap-3">
      <div class="flex items-center justify-between pb-2 border-b border-white/5">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-secondary text-[20px]">tune</span>
          <span class="text-[13px] font-bold text-on-surface uppercase tracking-wide">Incident Filter Controls</span>
        </div>
        <span class="text-[10px] font-mono text-on-surface-variant bg-surface-container-high px-2 py-0.5 rounded-full font-medium">FILTERS</span>
      </div>

      <!-- Incident Category Selector -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider flex items-center justify-between font-mono">
          <span>Incident Category</span>
          <span class="text-[9px] text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20" id="cat-badge-label">All Categories</span>
        </label>
        <select id="cat-filter-select" onchange="filterByCategory(this.value)" class="w-full bg-surface-container-lowest/90 text-on-surface text-[12px] p-2.5 rounded-2xl border border-white/10 focus:border-primary focus:outline-none cursor-pointer">
          <option value="ALL">All 4 Crime Categories</option>
          <option value="Property Crime & Theft">Property Crime &amp; Theft</option>
          <option value="Assault & Physical Offenses">Assault &amp; Physical Offenses</option>
          <option value="Public Harassment / Women's Safety">Public Harassment / Women's Safety</option>
          <option value="Vandalism / Petty Mischief">Vandalism / Petty Mischief</option>
        </select>
      </div>

      <!-- Time of Day -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-on-surface-variant font-bold uppercase tracking-wider font-mono flex items-center gap-1">
            <span class="material-symbols-outlined text-primary text-[14px]">schedule</span> Time of Day
          </span>
          <span class="text-[10px] text-secondary font-bold font-mono" id="time-filter-label">All Day</span>
        </div>
        <div class="grid grid-cols-3 gap-1 p-0.5 bg-surface-container-lowest/80 rounded-full border border-white/5 text-[11px]">
          <button id="time-btn-all" onclick="setTimeFilter('ALL')" class="py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition cursor-pointer" type="button">All</button>
          <button id="time-btn-night" onclick="setTimeFilter('Nighttime/Post-10 PM')" class="py-1 rounded-full text-on-surface-variant hover:text-on-surface text-center fluid-transition cursor-pointer" type="button">Night</button>
          <button id="time-btn-day" onclick="setTimeFilter('Daytime')" class="py-1 rounded-full text-on-surface-variant hover:text-on-surface text-center fluid-transition cursor-pointer" type="button">Day</button>
        </div>
      </div>

      <!-- Bhopal Zone / Ward selector & Date Range -->
      <div class="grid grid-cols-2 gap-2">
        <div class="flex flex-col gap-1">
          <label class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider font-mono flex items-center gap-1">
            <span class="material-symbols-outlined text-primary text-[13px]">location_city</span> Zone / Sector
          </label>
          <select id="zone-filter-select" onchange="filterByZone(this.value)" class="w-full bg-surface-container-lowest/90 text-on-surface text-[11px] px-3 py-2 rounded-xl border border-white/10 focus:border-primary focus:outline-none cursor-pointer">
            <option value="ALL">All Bhopal Sectors</option>
            <option value="MP Nagar">MP Nagar</option>
            <option value="TT Nagar / New Market">TT Nagar / New Market</option>
            <option value="Old Bhopal / Ibrahimganj">Old Bhopal / Ibrahimganj</option>
            <option value="Arera Colony">Arera Colony</option>
            <option value="Shahpura">Shahpura</option>
            <option value="Kolar Road">Kolar Road</option>
            <option value="Bittan Market">Bittan Market</option>
            <option value="Ayodhya Bypass">Ayodhya Bypass</option>
            <option value="Hoshangabad Road">Hoshangabad Road</option>
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider font-mono flex items-center gap-1">
            <span class="material-symbols-outlined text-primary text-[13px]">calendar_month</span> Date Range
          </label>
          <div class="bg-surface-container-lowest/90 px-2.5 py-2 rounded-xl border border-white/10 flex items-center justify-between text-[11px] text-on-surface font-mono">
            <span>Last 90 Days</span>
            <span class="text-[9px] text-primary font-bold">90D</span>
          </div>
        </div>
      </div>

      <!-- Severity Score Range -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-on-surface-variant font-bold uppercase tracking-wider font-mono">Min Severity Threshold</span>
          <span class="font-mono text-primary font-bold bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20" id="sev-slider-val">Lv 1+ (All)</span>
        </div>
        <input id="sev-slider" oninput="setSeverityThreshold(this.value)" class="accent-primary w-full h-1.5 bg-surface-container-highest rounded-full cursor-pointer" max="5" min="1" step="1" type="range" value="1">
      </div>

      <!-- Reset and Analyze action buttons -->
      <div class="pt-1 flex items-center gap-2">
        <button id="reset-filters-btn" onclick="resetAllFilters()" class="w-1/3 py-2 px-3 rounded-full bg-surface-container-high text-on-surface-variant hover:text-on-surface font-bold text-[12px] fluid-transition text-center border border-white/5 cursor-pointer" type="button">Reset</button>
        <button id="analyze-filters-btn" onclick="applyFiltersAndAnalyze()" class="w-2/3 py-2 px-4 rounded-full bg-gradient-to-r from-primary-container to-sky-500 text-on-primary-container font-bold text-[12px] shadow-m3-glow fluid-transition hover:brightness-110 flex items-center justify-center gap-1.5 cursor-pointer" type="button">
          <span class="material-symbols-outlined text-[16px]">insights</span>
          <span id="apply-btn-label">Analyze Filters</span>
        </button>
      </div>
    </div>

    <!-- 3. Threat Layer Quick Toggles -->
    <div class="bg-surface-container-low/90 backdrop-blur-2xl rounded-[28px] p-4.5 border border-white/10 shadow-m3-card flex flex-col gap-3">
      <div class="flex items-center justify-between pb-2 border-b border-white/5">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-tertiary text-[20px]">radar</span>
          <span class="text-[13px] font-bold text-on-surface uppercase tracking-wide">Threat Layer Quick Toggles</span>
        </div>
        <span class="text-[10px] font-mono text-on-surface-variant bg-surface-container-high px-2 py-0.5 rounded-full font-medium">CATEGORIES</span>
      </div>

      <div class="flex flex-wrap gap-1.5">
        <span onclick="filterByCategory('Property Crime & Theft')" class="px-2.5 py-1 rounded-full bg-surface-container-high text-on-surface text-[11px] font-medium flex items-center gap-1.5 border border-white/5 cursor-pointer hover:bg-white/10">
          <span class="w-2 h-2 rounded-full bg-amber-500"></span> Property &amp; Theft
        </span>
        <span onclick="filterByCategory('Assault & Physical Offenses')" class="px-2.5 py-1 rounded-full bg-error-container/70 text-on-error-container text-[11px] font-bold flex items-center gap-1.5 border border-error/30 cursor-pointer hover:bg-error-container">
          <span class="w-2 h-2 rounded-full bg-error"></span> Assault &amp; Physical
        </span>
        <span onclick="filterByCategory('Public Harassment / Women\'s Safety')" class="px-2.5 py-1 rounded-full bg-purple-950/70 text-purple-300 text-[11px] font-bold flex items-center gap-1.5 border border-purple-500/30 cursor-pointer hover:bg-purple-900">
          <span class="w-2 h-2 rounded-full bg-purple-400"></span> Women's Safety
        </span>
        <span onclick="filterByCategory('Vandalism / Petty Mischief')" class="px-2.5 py-1 rounded-full bg-surface-container-high text-on-surface text-[11px] font-medium flex items-center gap-1.5 border border-white/5 cursor-pointer hover:bg-white/10">
          <span class="w-2 h-2 rounded-full bg-yellow-400"></span> Vandalism
        </span>
      </div>

      <!-- Thana Jurisdiction Lookup Box -->
      <div class="bg-surface-container-lowest/80 p-3 rounded-2xl border border-white/5 flex flex-col gap-2">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-on-surface font-semibold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px] text-primary">local_police</span>
            Jurisdiction: TT Nagar, MP Nagar, Shahpura, Habibganj
          </span>
        </div>
        <div class="flex items-center justify-between text-[10px] text-on-surface-variant font-mono">
          <span>10 Police Thanas Mapped</span>
          <span class="text-primary font-bold">Emergency Dispatch • 112</span>
        </div>
      </div>
    </div>
  </div>

  <!-- RIGHT COLUMN (7 cols on lg): Embedded Interactive Leaflet Geospatial Engine -->
  <div class="lg:col-span-7 flex flex-col gap-4">
    <div class="bg-surface-container-low/90 backdrop-blur-2xl rounded-[32px] p-3.5 border border-white/10 shadow-m3-card flex flex-col overflow-hidden">
      <!-- Cartographic Header Controls -->
      <div class="px-3 pt-2 pb-3 flex flex-col gap-2.5 border-b border-white/5">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[14px] font-bold text-on-surface flex items-center gap-1.5">
              <span class="material-symbols-outlined text-primary text-[20px]">map</span>
              Interactive Geospatial Incident &amp; Safety Map
            </span>
            <span class="px-2.5 py-0.5 rounded-full bg-primary/10 border border-primary/25 text-primary text-[11px] font-mono flex items-center gap-1" id="map-mode-indicator">
              <span class="w-1.5 h-1.5 rounded-full bg-primary"></span>
              Mode: 📍 Marker Cluster
            </span>
          </div>

          <!-- Quick Action Buttons -->
          <div class="flex items-center gap-1.5">
            <button onclick="centerBhopal()" class="w-8 h-8 rounded-full bg-surface-container-high/80 hover:bg-surface-bright flex items-center justify-center text-on-surface-variant hover:text-on-surface border border-white/5 fluid-transition cursor-pointer" title="Center on Bhopal" type="button">
              <span class="material-symbols-outlined text-[17px]">my_location</span>
            </button>
            <button onclick="toggleMapFullscreen()" class="w-8 h-8 rounded-full bg-surface-container-high/80 hover:bg-surface-bright flex items-center justify-center text-on-surface-variant hover:text-on-surface border border-white/5 fluid-transition cursor-pointer" title="Full Screen Map" type="button">
              <span class="material-symbols-outlined text-[17px]">fullscreen</span>
            </button>
          </div>
        </div>

        <!-- Filter Pills & Symbology -->
        <div class="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px]">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-outline font-bold uppercase tracking-wider text-[10px]">Legend:</span>
            <span class="px-2.5 py-1 rounded-full bg-surface-container-lowest/80 border border-white/5 text-on-surface flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-amber-500"></span> Property
            </span>
            <span class="px-2.5 py-1 rounded-full bg-surface-container-lowest/80 border border-white/5 text-on-surface flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-rose-500"></span> Assault
            </span>
            <span class="px-2.5 py-1 rounded-full bg-surface-container-lowest/80 border border-white/5 text-on-surface flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-purple-500"></span> Women Safety
            </span>
            <span class="px-2.5 py-1 rounded-full bg-surface-container-lowest/80 border border-white/5 text-on-surface flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-yellow-400"></span> Vandalism
            </span>
            <span class="px-2.5 py-1 rounded-full bg-surface-container-lowest/80 border border-white/5 text-on-surface flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-sky-400"></span> Thana
            </span>
          </div>

          <!-- Layer Toggle Buttons -->
          <div class="flex items-center gap-1 bg-surface-container-lowest/80 p-0.5 rounded-full border border-white/5">
            <button id="toggle-layer-cluster" onclick="setVizMode('cluster')" class="map-layer-toggle active px-3 py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-[11px] shadow-m3-glow fluid-transition flex items-center gap-1 cursor-pointer" type="button">
              <span class="material-symbols-outlined text-[13px]">layers</span> Clusters
            </button>
            <button id="toggle-layer-density" onclick="setVizMode('density')" class="map-layer-toggle px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-[11px] font-medium fluid-transition cursor-pointer" type="button">
              Heatmap
            </button>
          </div>
        </div>
      </div>

      <!-- Real Interactive Leaflet Map Viewport Frame -->
      <div id="map-frame-container" class="relative w-full h-[540px] bg-[#070b12] rounded-[24px] overflow-hidden select-none border border-white/5 shadow-inner mt-2">
        <div id="leaflet-map"></div>
      </div>

      <!-- Bottom Map Ribbon -->
      <div class="px-4 py-2.5 flex flex-wrap items-center justify-between text-on-surface-variant text-[11px] gap-2 border-t border-white/5 mt-2">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="material-symbols-outlined text-primary text-[15px]">pin_drop</span>
          <span class="text-on-surface font-semibold">
            <span id="telemetry-node-count">{total_incidents}</span> Geo-tagged recorded incidents
          </span>
          <span>•</span>
          <span class="font-mono text-primary">Bhopal EPSG:4326 WGS84</span>
        </div>
        <div class="flex items-center gap-1.5 font-mono text-on-surface">
          <span class="text-on-surface-variant">Nearest Thana Radius:</span>
          <span class="text-tertiary font-bold">1.2 km avg</span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Bottom Civic Analytics & Material Active Visualization Suite -->
<section id="analytics-section" class="bg-surface-container-low/90 backdrop-blur-2xl rounded-[36px] p-6 border border-white/10 shadow-m3-card flex flex-col gap-5 mt-3">
  <!-- Tab Navigation Segment Pill -->
  <div class="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-4">
    <div class="flex flex-wrap items-center gap-1.5 bg-surface-container-lowest/80 p-1 rounded-full border border-white/5 text-[12px]">
      <button id="tab-btn-analytics" onclick="switchTab('analytics')" class="px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container font-bold shadow-m3-glow fluid-transition cursor-pointer" type="button">
        Risk Analytics &amp; Trends
      </button>
      <button id="tab-btn-sectors" onclick="switchTab('sectors')" class="px-4 py-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high fluid-transition cursor-pointer" type="button">
        Sector Safety &amp; Proximity
      </button>
      <button id="tab-btn-records" onclick="switchTab('records')" class="px-4 py-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high fluid-transition cursor-pointer" type="button">
        Filtered Records Explorer
      </button>
    </div>
  </div>

  <!-- TAB PANE 1: ANALYTICS & TRENDS -->
  <div id="tab-pane-analytics" class="flex flex-col gap-5">
    <div>
      <h2 class="text-xl font-extrabold text-on-surface tracking-tight">Multidimensional Crime Patterns Across Bhopal Sectors</h2>
      <p class="text-xs text-on-surface-variant mt-0.5">Statistical crime &amp; safety analytics synthesized from recorded civic incident registers.</p>
    </div>

    <!-- 4 Fluid Material 3 Analytical Cards -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <!-- Chart 1: Crime Category Prevalence by Bhopal Sector -->
      <div class="bg-surface-container-lowest/80 rounded-[28px] p-5 border border-white/5 flex flex-col justify-between shadow-m3-1">
        <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h3 class="text-[13px] font-bold text-on-surface">Crime Frequency by Sector</h3>
          <div class="flex items-center gap-1.5 text-[11px] text-purple-300 font-medium bg-purple-950/50 px-2.5 py-0.5 rounded-full border border-purple-500/20">
            <span class="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
            <span>Bhopal Metro Zones</span>
          </div>
        </div>
        <div class="flex flex-col gap-2 pt-1" id="sector-bar-container">
          {sector_bars_html}
        </div>
        <div class="text-center text-outline text-[11px] font-mono mt-3 pt-2 border-t border-white/5">Reported Incidents per Sector</div>
      </div>

      <!-- Chart 2: Daytime vs. Nighttime Distribution -->
      <div class="bg-surface-container-lowest/80 rounded-[28px] p-5 border border-white/5 flex flex-col justify-between shadow-m3-1">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-[13px] font-bold text-on-surface">Daytime vs. Nighttime Chrono Bias</h3>
          <span class="text-[10px] bg-secondary-container/40 text-secondary border border-secondary/30 px-2.5 py-0.5 rounded-full font-mono font-bold">24H CYCLE</span>
        </div>
        <div class="flex flex-col items-center justify-center my-auto py-3">
          <div class="relative w-60 h-60 flex items-center justify-center">
            <!-- Concentric Soft Depth Rings -->
            <svg class="w-60 h-60 -rotate-90" viewBox="0 0 100 100">
              <defs>
                <linearGradient id="chronoGradient" x1="0%" x2="100%" y1="0%" y2="100%">
                  <stop offset="0%" stop-color="#38bdf8"></stop>
                  <stop offset="50%" stop-color="#6366f1"></stop>
                  <stop offset="100%" stop-color="#a855f7"></stop>
                </linearGradient>
              </defs>
              <circle cx="50" cy="50" fill="none" r="38" stroke="#161c28" stroke-width="14"></circle>
              <circle cx="50" cy="50" fill="none" r="38" stroke="url(#chronoGradient)" stroke-dasharray="238.76" stroke-dashoffset="{round(238.76 * (1 - (night_pct / 100)), 2)}" stroke-linecap="round" stroke-width="14" style="filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.5));"></circle>
            </svg>
            <!-- Center Badge -->
            <div class="absolute flex flex-col items-center justify-center text-center px-4 py-3 bg-surface-container-high/90 backdrop-blur-md rounded-[24px] border border-white/10 shadow-2xl pointer-events-none">
              <span class="material-symbols-outlined text-primary text-[20px] mb-0.5">bedtime</span>
              <span class="text-[11px] text-white font-bold leading-tight">Nighttime Shift</span>
              <span class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-300 font-mono">{night_pct}%</span>
              <span class="text-[9px] text-tertiary font-mono">{night_count} / {total_incidents} Calls</span>
            </div>
          </div>
        </div>
        <div class="flex items-center justify-center gap-3 pt-2 border-t border-white/5 text-[11px] text-on-surface-variant">
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Nighttime ({night_pct}%)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-sky-400"></span> Daytime ({round(100 - night_pct, 1)}%)</span>
        </div>
      </div>

      <!-- Chart 3: Incidents by Severity Level -->
      <div class="bg-surface-container-lowest/80 rounded-[28px] p-5 border border-white/5 flex flex-col justify-between shadow-m3-1">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-[13px] font-bold text-on-surface">Incidents by Severity Level (1 to 5)</h3>
          <span class="text-[10px] font-mono text-on-surface-variant bg-surface-container px-2 py-0.5 rounded-full">N = {total_incidents} INCIDENTS</span>
        </div>
        <div class="flex items-end gap-5 h-56 pt-4 px-3">
          <!-- Level 2 -->
          <div class="flex flex-col items-center gap-2 flex-1 h-full justify-end group">
            <span class="font-mono font-bold text-tertiary text-[12px] bg-tertiary/10 px-2 py-0.5 rounded-full">{l2_count}</span>
            <div class="w-full bg-gradient-to-t from-emerald-600 to-teal-400 rounded-full hover:brightness-125 transition-all shadow-m3-glow" style="height: {l2_pct}%;"></div>
            <span class="text-[11px] text-on-surface-variant text-center whitespace-nowrap mt-1">Level 2 (Low)</span>
          </div>
          <!-- Level 3 -->
          <div class="flex flex-col items-center gap-2 flex-1 h-full justify-end group">
            <span class="font-mono font-bold text-lime-400 text-[12px] bg-lime-400/10 px-2 py-0.5 rounded-full">{l3_count}</span>
            <div class="w-full bg-gradient-to-t from-lime-600 to-emerald-400 rounded-full hover:brightness-125 transition-all shadow-m3-glow" style="height: {l3_pct}%;"></div>
            <span class="text-[11px] text-on-surface font-bold text-center whitespace-nowrap mt-1">Level 3 (Mod)</span>
          </div>
          <!-- Level 4 -->
          <div class="flex flex-col items-center gap-2 flex-1 h-full justify-end group">
            <span class="font-mono font-bold text-orange-400 text-[12px] bg-orange-400/10 px-2 py-0.5 rounded-full">{l4_count}</span>
            <div class="w-full bg-gradient-to-t from-orange-600 to-amber-400 rounded-full hover:brightness-125 transition-all shadow-m3-glow" style="height: {l4_pct}%;"></div>
            <span class="text-[11px] text-on-surface-variant text-center whitespace-nowrap mt-1">Level 4 (High)</span>
          </div>
          <!-- Level 5 -->
          <div class="flex flex-col items-center gap-2 flex-1 h-full justify-end group">
            <span class="font-mono font-bold text-rose-400 text-[12px] bg-rose-400/10 px-2 py-0.5 rounded-full">{l5_count}</span>
            <div class="w-full bg-gradient-to-t from-rose-700 to-red-500 rounded-full hover:brightness-125 transition-all shadow-m3-error-glow" style="height: {l5_pct}%;"></div>
            <span class="text-[11px] text-on-surface-variant text-center whitespace-nowrap mt-1">Level 5 (Crit)</span>
          </div>
        </div>
        <div class="text-center text-outline text-[11px] font-mono pt-3 border-t border-white/5 mt-3">Severity Scale Matrix</div>
      </div>

      <!-- Chart 4: Most Frequent Offense Modalities -->
      <div class="bg-surface-container-lowest/80 rounded-[28px] p-5 border border-white/5 flex flex-col justify-between shadow-m3-1">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-[13px] font-bold text-on-surface">Most Frequent Offense Modalities</h3>
          <span class="text-[10px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">TOP SUBTYPES</span>
        </div>
        <div class="flex flex-col gap-2 pt-1">
          {modalities_html}
        </div>
        <div class="text-center text-outline text-[11px] font-mono mt-3 pt-2 border-t border-white/5">Incident Subtype Distribution</div>
      </div>
    </div>
  </div>

  <!-- TAB PANE 2: SECTOR SAFETY & PROXIMITY RANKING -->
  <div id="tab-pane-sectors" class="hidden flex-col gap-4">
    <div>
      <h2 class="text-xl font-extrabold text-on-surface tracking-tight">Bhopal Neighborhood Safety Index &amp; Sector Safety Analysis</h2>
      <p class="text-xs text-on-surface-variant mt-0.5">Composite risk evaluations computed using geodesic distance metrics to nearest safety posts.</p>
    </div>
    <div class="overflow-x-auto rounded-2xl border border-white/10 bg-surface-container-lowest/80">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-surface-container-high/60 text-[11px] uppercase tracking-wider text-on-surface-variant font-mono">
            <th class="py-3 px-3">Neighborhood</th>
            <th class="py-3 px-3">Incidents</th>
            <th class="py-3 px-3">Avg Severity</th>
            <th class="py-3 px-3">Nighttime Ratio</th>
            <th class="py-3 px-3">Dominant Crime</th>
            <th class="py-3 px-3">Risk Score</th>
            <th class="py-3 px-3">Safety Tier</th>
          </tr>
        </thead>
        <tbody>
          {sector_table_rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAB PANE 3: FILTERED RECORDS EXPLORER -->
  <div id="tab-pane-records" class="hidden flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-extrabold text-on-surface tracking-tight">Filtered Crime Records Explorer</h2>
        <p class="text-xs text-on-surface-variant mt-0.5">Search and inspect active dataset incidents.</p>
      </div>
      <button onclick="downloadCSV()" class="px-4 py-2 rounded-full bg-primary-container text-on-primary-container font-bold text-[12px] flex items-center gap-1.5 shadow-m3-glow hover:brightness-110 transition-all cursor-pointer">
        <span class="material-symbols-outlined text-[16px]">download</span>
        Download CSV
      </button>
    </div>
    <div class="overflow-x-auto max-h-96 rounded-2xl border border-white/10 bg-surface-container-lowest/80">
      <table class="w-full text-left border-collapse text-[11px]" id="records-table">
        <thead class="sticky top-0 bg-surface-container-high z-10 border-b border-white/10 text-on-surface-variant font-mono">
          <tr>
            <th class="py-2.5 px-3">Incident ID</th>
            <th class="py-2.5 px-3">Date</th>
            <th class="py-2.5 px-3">Sector</th>
            <th class="py-2.5 px-3">Category</th>
            <th class="py-2.5 px-3">Offense Detail</th>
            <th class="py-2.5 px-3">Time</th>
            <th class="py-2.5 px-3">Severity</th>
            <th class="py-2.5 px-3">Nearest Thana</th>
          </tr>
        </thead>
        <tbody id="records-table-body">
          <!-- Populated by JS -->
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- Bottom Helpline Banner -->
<footer class="bg-gradient-to-r from-surface-container to-surface-container-high p-5 md:p-6 rounded-[28px] shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 border border-white/5 relative overflow-hidden mt-3">
  <div class="absolute -right-10 -bottom-10 w-48 h-48 bg-primary/5 rounded-full blur-2xl pointer-events-none"></div>
  <div class="flex flex-col w-full gap-4 relative z-10">
    <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-2xl bg-primary-container flex items-center justify-center text-on-primary-container flex-shrink-0 shadow-md">
          <span class="material-symbols-outlined text-[28px]">shield</span>
        </div>
        <div class="flex flex-col">
          <span class="text-lg font-bold text-on-surface mt-0.5">Need assistance or witnessed an incident in Bhopal?</span>
          <span class="text-xs text-on-surface-variant">Emergency helpline and citizen assistance portal.</span>
        </div>
      </div>
      <div class="flex items-center gap-3 w-full md:w-auto shrink-0">
        <a class="flex-1 md:flex-initial flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-5 py-2.5 rounded-full text-[12px] font-bold shadow-m3-error-glow fluid-transition hover:scale-105 active:scale-95 border border-red-400/40 shrink-0" href="tel:112">
          <span class="material-symbols-outlined text-[17px]">emergency</span>
          <span>Dial 112 SOS</span>
        </a>
      </div>
    </div>
  </div>
</footer>

</div>

<!-- Floating Navigation Dock -->
<nav id="floating-dock" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 rounded-full px-5 py-2.5 bg-[#0b1329]/95 backdrop-blur-2xl border border-sky-500/30 shadow-[0_20px_50px_rgba(0,0,0,0.7),0_0_25px_rgba(56,189,248,0.2)] flex items-center gap-2.5 md:gap-4">
  <!-- Map -->
  <button id="nav-btn-map" onclick="navigateToMap()" class="dock-btn bg-sky-400 text-slate-950 font-bold px-4 py-1.5 rounded-full flex items-center gap-2 text-sm shadow-md shadow-sky-500/30 transition-all cursor-pointer">
    <span class="material-symbols-outlined text-[18px]">map</span>
    <span>Map</span>
  </button>
  <!-- Analyze -->
  <button id="nav-btn-analytics" onclick="navigateToAnalytics()" class="dock-btn text-slate-300 hover:text-white hover:bg-white/10 px-3.5 py-1.5 rounded-full flex items-center gap-2 text-sm transition-all cursor-pointer">
    <span class="material-symbols-outlined text-[18px]">insights</span>
    <span class="font-medium">Analyze</span>
  </button>
  <!-- Hotspots -->
  <button id="nav-btn-hotspots" onclick="navigateToHotspots()" class="dock-btn text-slate-300 hover:text-white hover:bg-white/10 px-3.5 py-1.5 rounded-full flex items-center gap-2 text-sm transition-all cursor-pointer">
    <span class="material-symbols-outlined text-[18px]">radar</span>
    <span class="font-medium">Hotspots</span>
  </button>
  <!-- Records -->
  <button id="nav-btn-records" onclick="navigateToRecords()" class="dock-btn text-slate-300 hover:text-white hover:bg-white/10 px-3.5 py-1.5 rounded-full flex items-center gap-2 text-sm transition-all cursor-pointer">
    <span class="material-symbols-outlined text-[18px]">table_chart</span>
    <span class="font-medium">Records</span>
  </button>
  <div class="h-5 w-px bg-white/15"></div>
  <!-- SOS -->
  <a id="nav-btn-sos" class="bg-red-600 hover:bg-red-500 text-white font-bold px-4 py-1.5 rounded-full flex items-center gap-2 text-sm shadow-lg shadow-red-600/40 tracking-wide transition-all" href="tel:112">
    <span class="material-symbols-outlined text-[18px]">emergency</span>
    <span>SOS 112</span>
  </a>
</nav>

<!-- Leaflet JS & Leaflet Plugins -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

<!-- Bhopal Crime Records Dataset -->
<script>
  const ALL_CRIMES = {crime_json};
  const POLICE_STATIONS = {ps_json};
  const SAFE_CORRIDORS = {corridors_json};

  // State
  let currentFiltered = [...ALL_CRIMES];
  let currentVizMode = 'cluster'; // 'cluster' or 'density'
  let currentCategory = 'ALL';
  let currentTimeOfDay = 'ALL';
  let currentZone = 'ALL';
  let minSeverity = 1;
  let showPolice = true;
  let showCorridors = true;

  // Leaflet Map Objects
  let map, markerClusterGroup, heatLayer, policeFeatureGroup, corridorFeatureGroup;

  function initMap() {{
    map = L.map('leaflet-map', {{
      center: [23.2500, 77.4170],
      zoom: 12,
      zoomControl: true,
      preferCanvas: true
    }});

    // High performance ESRI World Street Map (unrestricted, zero key)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      attribution: '&copy; Esri &mdash; Bhopal Civic Safety Intelligence',
      maxZoom: 18
    }}).addTo(map);

    markerClusterGroup = L.markerClusterGroup({{
      maxClusterRadius: 45,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false
    }}).addTo(map);

    policeFeatureGroup = L.featureGroup().addTo(map);
    corridorFeatureGroup = L.featureGroup().addTo(map);

    renderMapLayers();
    renderRecordsTable();
  }}

  function getCategoryColor(cat) {{
    switch (cat) {{
      case "Property Crime & Theft": return "#F59E0B";
      case "Assault & Physical Offenses": return "#EF4444";
      case "Public Harassment / Women's Safety": return "#A855F7";
      case "Vandalism / Petty Mischief": return "#EAB308";
      default: return "#38BDF8";
    }}
  }}

  function renderMapLayers() {{
    // 1. Clear existing layers
    markerClusterGroup.clearLayers();
    if (heatLayer && map.hasLayer(heatLayer)) {{
      map.removeLayer(heatLayer);
    }}
    policeFeatureGroup.clearLayers();
    corridorFeatureGroup.clearLayers();

    // 2. Render Crime Incidents
    if (currentVizMode === 'cluster') {{
      currentFiltered.forEach(c => {{
        const color = getCategoryColor(c.category);
        const sevColor = c.severity <= 2 ? '#10B981' : c.severity === 3 ? '#F59E0B' : '#EF4444';

        const popupHtml = `
          <div style="font-family:'Roboto Flex',sans-serif; width:220px; font-size:12px; color:#dfe2ee; line-height:1.4;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:5px; margin-bottom:6px;">
              <b style="color:#ffffff;">${{c.id}}</b>
              <span style="background:${{color}}25; color:${{color}}; border:1px solid ${{color}}60; padding:1px 6px; border-radius:10px; font-size:9.5px; font-weight:700;">
                ${{c.category}}
              </span>
            </div>
            <div style="margin-bottom:3px;"><b>📍 Sector:</b> ${{c.neighborhood}}</div>
            <div style="margin-bottom:3px;"><b>⚠️ Offense:</b> ${{c.subtype}}</div>
            <div style="margin-bottom:3px;"><b>🕒 Time:</b> ${{c.time_of_day}}</div>
            <div style="margin-bottom:5px; display:flex; align-items:center; gap:6px;">
              <b>Severity:</b>
              <span style="background:${{sevColor}}; color:#fff; font-weight:bold; padding:1px 6px; border-radius:4px; font-size:10px;">
                Lv ${{c.severity}}/5
              </span>
            </div>
            <div style="background:#0b0f17; padding:4px 6px; border-radius:6px; font-size:10px; color:#38bdf8; border:1px solid #1e293b;">
              🛡️ Nearest Station: ${{c.nearest_ps}} (${{c.dist_km}} km)
            </div>
          </div>
        `;

        const circle = L.circleMarker([c.lat, c.lon], {{
          radius: 7,
          color: '#ffffff',
          weight: 1.5,
          fillColor: color,
          fillOpacity: 0.85
        }}).bindPopup(popupHtml);

        markerClusterGroup.addLayer(circle);
      }});
      if (!map.hasLayer(markerClusterGroup)) {{
        map.addLayer(markerClusterGroup);
      }}
    }} else if (currentVizMode === 'density') {{
      const heatPoints = currentFiltered.map(c => [c.lat, c.lon, c.severity / 5.0]);
      heatLayer = L.heatLayer(heatPoints, {{
        radius: 26,
        blur: 20,
        maxZoom: 14,
        gradient: {{
          0.2: "#38bdf8",
          0.4: "#22c55e",
          0.6: "#eab308",
          0.8: "#f97316",
          1.0: "#dc2626"
        }}
      }}).addTo(map);
    }}

    // 3. Render Police Stations
    if (showPolice) {{
      POLICE_STATIONS.forEach(ps => {{
        const isMahila = ps.name.includes("Mahila");
        const iconHtml = `
          <div style="background:${{isMahila ? '#9333EA' : '#0284C7'}}; width:26px; height:26px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#fff; border:2px solid #fff; box-shadow:0 0 10px rgba(56,189,248,0.5);">
            <span class="material-symbols-outlined" style="font-size:16px;">${{isMahila ? 'shield_person' : 'local_police'}}</span>
          </div>
        `;
        const customIcon = L.divIcon({{ html: iconHtml, className: '', iconSize: [26, 26] }});
        
        const popup = `
          <div style="font-family:'Roboto Flex',sans-serif; width:200px; font-size:12px; color:#dfe2ee;">
            <b style="color:#38bdf8; font-size:13px;">🛡️ ${{ps.name}}</b>
            <div style="margin-top:3px; color:#94a3b8;">${{ps.jurisdiction}}</div>
            <div style="margin-top:3px; color:#34d399; font-weight:bold;">📞 ${{ps.phone}}</div>
          </div>
        `;
        L.marker([ps.lat, ps.lon], {{ icon: customIcon }}).bindPopup(popup).addTo(policeFeatureGroup);
      }});
    }}

    // 4. Render Safe Corridors
    if (showCorridors) {{
      SAFE_CORRIDORS.forEach(sc => {{
        L.polyline(sc.coords, {{
          color: '#10b981',
          weight: 4,
          opacity: 0.8,
          dashArray: '6, 6'
        }}).bindTooltip(`⚡ ${{sc.name}} (${{sc.status}})`).addTo(corridorFeatureGroup);
      }});
    }}

    document.getElementById('telemetry-node-count').innerText = currentFiltered.length;
  }}

  // Filter Pipeline
  function applyFilters() {{
    currentFiltered = ALL_CRIMES.filter(c => {{
      const matchCat = currentCategory === 'ALL' || c.category === currentCategory;
      const matchTime = currentTimeOfDay === 'ALL' || c.time_of_day === currentTimeOfDay;
      const matchZone = currentZone === 'ALL' || c.neighborhood === currentZone;
      const matchSev = c.severity >= minSeverity;
      return matchCat && matchTime && matchZone && matchSev;
    }});

    // Update KPIs
    updateKPIs();
    renderMapLayers();
    renderRecordsTable();
  }}

  function updateKPIs() {{
    document.getElementById('metric-total-count').innerText = currentFiltered.length;
    if (currentFiltered.length > 0) {{
      // Mode crime
      const counts = {{}};
      currentFiltered.forEach(c => {{ counts[c.category] = (counts[c.category] || 0) + 1; }});
      const topCat = Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
      document.getElementById('metric-top-crime').innerText = topCat;
      const pct = Math.round((counts[topCat] / currentFiltered.length) * 100);
      document.getElementById('metric-top-crime-sub').innerText = `${{pct}}% of selection (${{counts[topCat]}} cases)`;

      // Mode zone
      const zcounts = {{}};
      currentFiltered.forEach(c => {{ zcounts[c.neighborhood] = (zcounts[c.neighborhood] || 0) + 1; }});
      const topZ = Object.keys(zcounts).reduce((a, b) => zcounts[a] > zcounts[b] ? a : b);
      document.getElementById('metric-top-sector').innerText = topZ;
      document.getElementById('metric-top-sector-sub').innerText = `${{zcounts[topZ]}} reported events`;
      document.getElementById('ribbon-active-zone').innerText = `Zone: ${{topZ}}`;

      // Avg severity
      const avg = (currentFiltered.reduce((sum, c) => sum + c.severity, 0) / currentFiltered.length).toFixed(2);
      document.getElementById('metric-avg-sev').innerText = avg;
    }} else {{
      document.getElementById('metric-top-crime').innerText = "None";
      document.getElementById('metric-top-sector').innerText = "None";
      document.getElementById('metric-avg-sev').innerText = "0.0";
    }}
  }}

  // Analyze Button handler: applies filters, updates views, and scrolls to analytics section
  function applyFiltersAndAnalyze() {{
    applyFilters();
    switchTab('analytics');
    scrollToAnalytics();
  }}

  function setVizMode(mode) {{
    currentVizMode = mode;
    const clBtn = document.getElementById('viz-cluster-btn');
    const deBtn = document.getElementById('viz-density-btn');
    const tCl = document.getElementById('toggle-layer-cluster');
    const tDe = document.getElementById('toggle-layer-density');
    const indicator = document.getElementById('map-mode-indicator');

    if (mode === 'cluster') {{
      clBtn.className = 'py-1 px-2.5 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition text-[11px] flex items-center justify-center gap-1.5 cursor-pointer';
      deBtn.className = 'py-1 px-2.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high text-center fluid-transition text-[11px] cursor-pointer';
      tCl.className = 'map-layer-toggle active px-3 py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-[11px] shadow-m3-glow fluid-transition flex items-center gap-1 cursor-pointer';
      tDe.className = 'map-layer-toggle px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-[11px] font-medium fluid-transition cursor-pointer';
      indicator.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-primary"></span> Mode: 📍 Marker Cluster';
    }} else {{
      deBtn.className = 'py-1 px-2.5 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition text-[11px] flex items-center justify-center gap-1.5 cursor-pointer';
      clBtn.className = 'py-1 px-2.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high text-center fluid-transition text-[11px] cursor-pointer';
      tDe.className = 'map-layer-toggle active px-3 py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-[11px] shadow-m3-glow fluid-transition flex items-center gap-1 cursor-pointer';
      tCl.className = 'map-layer-toggle px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-[11px] font-medium fluid-transition cursor-pointer';
      indicator.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-primary"></span> Mode: 🔥 Kernel Density';
    }}
    renderMapLayers();
  }}

  function filterByCategory(cat) {{
    currentCategory = cat;
    document.getElementById('cat-filter-select').value = cat;
    document.getElementById('cat-badge-label').innerText = cat === 'ALL' ? 'All Categories' : cat;
    applyFilters();
  }}

  function setTimeFilter(time) {{
    currentTimeOfDay = time;
    const bAll = document.getElementById('time-btn-all');
    const bNight = document.getElementById('time-btn-night');
    const bDay = document.getElementById('time-btn-day');

    bAll.className = 'py-1 rounded-full text-on-surface-variant hover:text-on-surface text-center fluid-transition cursor-pointer';
    bNight.className = 'py-1 rounded-full text-on-surface-variant hover:text-on-surface text-center fluid-transition cursor-pointer';
    bDay.className = 'py-1 rounded-full text-on-surface-variant hover:text-on-surface text-center fluid-transition cursor-pointer';

    if (time === 'ALL') {{
      bAll.className = 'py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition cursor-pointer';
      document.getElementById('time-filter-label').innerText = 'All Day';
    }} else if (time === 'Nighttime/Post-10 PM') {{
      bNight.className = 'py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition cursor-pointer';
      document.getElementById('time-filter-label').innerText = 'Nighttime / Post-10 PM';
    }} else {{
      bDay.className = 'py-1 rounded-full bg-primary-container text-on-primary-container font-bold text-center shadow-m3-glow fluid-transition cursor-pointer';
      document.getElementById('time-filter-label').innerText = 'Daytime';
    }}
    applyFilters();
  }}

  function filterByZone(zone) {{
    currentZone = zone;
    document.getElementById('zone-filter-select').value = zone;
    const quickSel = document.getElementById('quick-ward-select');
    if (quickSel) quickSel.value = zone;
    applyFilters();
    if (zone !== 'ALL') {{
      const match = currentFiltered.find(c => c.neighborhood.toLowerCase().includes(zone.toLowerCase()));
      if (match) {{
        map.flyTo([match.lat, match.lon], 14, {{ animate: true, duration: 1.2 }});
      }}
    }}
  }}

  function setSeverityThreshold(val) {{
    minSeverity = parseInt(val);
    document.getElementById('sev-slider-val').innerText = `Lv ${{val}}+`;
    applyFilters();
  }}

  function togglePoliceLayer(checked) {{
    showPolice = checked;
    renderMapLayers();
  }}

  function toggleCorridorsLayer(checked) {{
    showCorridors = checked;
    renderMapLayers();
  }}

  function resetAllFilters() {{
    currentCategory = 'ALL';
    currentTimeOfDay = 'ALL';
    currentZone = 'ALL';
    minSeverity = 1;
    document.getElementById('cat-filter-select').value = 'ALL';
    document.getElementById('cat-badge-label').innerText = 'All Categories';
    document.getElementById('zone-filter-select').value = 'ALL';
    const quickSel = document.getElementById('quick-ward-select');
    if (quickSel) quickSel.value = 'ALL';
    document.getElementById('sev-slider').value = 1;
    document.getElementById('sev-slider-val').innerText = 'Lv 1+ (All)';
    clearSearch();
    setTimeFilter('ALL');
    centerBhopal();
  }}

  // Connected Search Functions
  function handleSearch(query) {{
    const q = query.toLowerCase().trim();
    const clearBtn = document.getElementById('search-clear-btn');
    if (!q) {{
      if (clearBtn) clearBtn.classList.add('hidden');
      applyFilters();
      return;
    }}
    if (clearBtn) clearBtn.classList.remove('hidden');

    currentFiltered = ALL_CRIMES.filter(c => 
      c.id.toLowerCase().includes(q) ||
      c.neighborhood.toLowerCase().includes(q) ||
      c.subtype.toLowerCase().includes(q) ||
      c.category.toLowerCase().includes(q) ||
      c.nearest_ps.toLowerCase().includes(q)
    );
    updateKPIs();
    renderMapLayers();
    renderRecordsTable();
  }}

  function executeSearch(query) {{
    const q = query.toLowerCase().trim();
    if (!q) return;

    // Check if query matches a known sector
    const sectorMatch = ALL_CRIMES.find(c => c.neighborhood.toLowerCase().includes(q));
    if (sectorMatch) {{
      map.flyTo([sectorMatch.lat, sectorMatch.lon], 14, {{ animate: true, duration: 1.5 }});
      scrollToMap();
    }} else if (currentFiltered.length > 0) {{
      scrollToMap();
    }}
  }}

  function clearSearch() {{
    const inp = document.getElementById('global-search-input');
    if (inp) inp.value = '';
    const clearBtn = document.getElementById('search-clear-btn');
    if (clearBtn) clearBtn.classList.add('hidden');
    applyFilters();
  }}

  function centerBhopal() {{
    map.flyTo([23.2500, 77.4170], 12, {{ animate: true, duration: 1.2 }});
  }}

  function toggleMapFullscreen() {{
    const el = document.getElementById('map-frame-container');
    if (!document.fullscreenElement) {{
      el.requestFullscreen().catch(err => alert(`Fullscreen Error: ${{err.message}}`));
    }} else {{
      document.exitFullscreen();
    }}
  }}

  function toggleTheme() {{
    document.documentElement.classList.toggle('dark');
  }}

  function switchTab(tabName) {{
    const pAnalytics = document.getElementById('tab-pane-analytics');
    const pSectors = document.getElementById('tab-pane-sectors');
    const pRecords = document.getElementById('tab-pane-records');

    const bAnalytics = document.getElementById('tab-btn-analytics');
    const bSectors = document.getElementById('tab-btn-sectors');
    const bRecords = document.getElementById('tab-btn-records');

    [bAnalytics, bSectors, bRecords].forEach(b => {{
      b.className = 'px-4 py-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high fluid-transition cursor-pointer';
    }});

    pAnalytics.classList.add('hidden');
    pSectors.classList.add('hidden');
    pRecords.classList.add('hidden');

    if (tabName === 'analytics') {{
      pAnalytics.classList.remove('hidden');
      bAnalytics.className = 'px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container font-bold shadow-m3-glow fluid-transition cursor-pointer';
    }} else if (tabName === 'sectors') {{
      pSectors.classList.remove('hidden');
      bSectors.className = 'px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container font-bold shadow-m3-glow fluid-transition cursor-pointer';
    }} else {{
      pRecords.classList.remove('hidden');
      bRecords.className = 'px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container font-bold shadow-m3-glow fluid-transition cursor-pointer';
    }}
  }}

  function renderRecordsTable() {{
    const tbody = document.getElementById('records-table-body');
    if (!tbody) return;
    const rows = currentFiltered.slice(0, 30).map(c => `
      <tr class="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer" onclick="zoomToRecord(${{c.lat}}, ${{c.lon}})">
        <td class="py-2 px-3 font-mono font-bold text-primary">${{c.id}}</td>
        <td class="py-2 px-3 text-on-surface-variant">${{c.date}}</td>
        <td class="py-2 px-3 font-medium">${{c.neighborhood}}</td>
        <td class="py-2 px-3">${{c.category}}</td>
        <td class="py-2 px-3 text-on-surface-variant">${{c.subtype}}</td>
        <td class="py-2 px-3 text-on-surface-variant">${{c.time_of_day}}</td>
        <td class="py-2 px-3 font-mono font-bold text-amber-400">Lv ${{c.severity}}/5</td>
        <td class="py-2 px-3 text-sky-400 font-mono">${{c.nearest_ps}} (${{c.dist_km}}km)</td>
      </tr>
    `).join('');
    tbody.innerHTML = rows;
  }}

  function zoomToRecord(lat, lon) {{
    map.flyTo([lat, lon], 15, {{ animate: true, duration: 1.2 }});
    scrollToMap();
  }}

  function downloadCSV() {{
    const headers = ["incident_id", "date", "neighborhood", "category", "subtype", "time_of_day", "severity", "nearest_ps", "dist_km"];
    const csvRows = [headers.join(",")];
    currentFiltered.forEach(c => {{
      const row = [c.id, c.date, `"${{c.neighborhood}}"`, `"${{c.category}}"`, `"${{c.subtype}}"`, `"${{c.time_of_day}}"`, c.severity, `"${{c.nearest_ps}}"`, c.dist_km];
      csvRows.push(row.join(","));
    }});
    const blob = new Blob([csvRows.join("\\n")], {{ type: 'text/csv' }});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', `bhopal_safety_intelligence_${{Date.now()}}.csv`);
    a.click();
  }}

  // Connected Navigation Bar Actions
  function setDockActive(btnId) {{
    document.querySelectorAll('.dock-btn').forEach(b => {{
      b.className = 'dock-btn text-slate-300 hover:text-white hover:bg-white/10 px-3.5 py-1.5 rounded-full flex items-center gap-2 text-sm transition-all cursor-pointer';
    }});
    const active = document.getElementById(btnId);
    if (active) {{
      active.className = 'dock-btn bg-sky-400 text-slate-950 font-bold px-4 py-1.5 rounded-full flex items-center gap-2 text-sm shadow-md shadow-sky-500/30 transition-all cursor-pointer';
    }}
  }}

  function navigateToMap() {{
    setDockActive('nav-btn-map');
    scrollToMap();
  }}

  function navigateToAnalytics() {{
    setDockActive('nav-btn-analytics');
    switchTab('analytics');
    scrollToAnalytics();
  }}

  function navigateToHotspots() {{
    setDockActive('nav-btn-hotspots');
    setVizMode('density');
    scrollToMap();
  }}

  function navigateToRecords() {{
    setDockActive('nav-btn-records');
    switchTab('records');
    scrollToAnalytics();
  }}

  function scrollToMap() {{
    document.getElementById('map-frame-container').scrollIntoView({{ behavior: 'smooth' }});
  }}

  function scrollToAnalytics() {{
    document.getElementById('analytics-section').scrollIntoView({{ behavior: 'smooth' }});
  }}

  // Initialize Map after DOM loads
  window.addEventListener('DOMContentLoaded', () => {{
    setTimeout(initMap, 200);
  }});
</script>
</body>
</html>
"""
    return html_template


if __name__ == "__main__":
    from data_generator import generate_crime_dataset
    from spatial_analytics import compute_sector_risk_index
    df = generate_crime_dataset(50)
    risk_df = compute_sector_risk_index(df)
    html = generate_material_active_html(df, risk_df)
    print("Generated Material Active HTML length:", len(html))
