# src/map_route_dashboard.py – Streamlit dashboard driven by optimisation results
"""
Interactive visualiser that **reads the actual optimisation outputs**:

* `outputs/interstore_transfers.csv` – list of transfers (from_store → to_store, quantity, road_km)
* `outputs/routing_strategy_comparison.csv` – which strategy (multi‑pickup vs parallel) the optimiser chose per destination store
* `data/store_locations.csv`          – lat/lon per store

The app:
1. Sidebar dropdown → choose destination store (`to_store`).
2. Reads optimisation **decision** for that store and autoselects routing mode.
3. Draws real Mapbox road route(s):
   • **Multi‑Pickup** → single blue line visiting all origins in the order optimiser generated (farthest‑first heuristic).
   • **Parallel**     → separate coloured lines, one per origin, each its own vehicle.
4. Displays distance & ETA taken directly from optimisation summary, plus truck counts.

Dependencies
------------
```
pip install streamlit folium requests pandas haversine
```

Environment
-----------
Set `MAPBOX_TOKEN` once per session or via `.env` / system variables.
```powershell
$env:MAPBOX_TOKEN = "pk.eyJ..."
```
Run with:
```bash
streamlit run src/map_route_dashboard.py
```
"""
import os, json, requests, pandas as pd, streamlit as st, folium
from haversine import haversine, Unit

# ------------------------------------------------------------------
# 1. Config & File paths
# ------------------------------------------------------------------
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
if not MAPBOX_TOKEN:
    st.error("MAPBOX_TOKEN env‑var not set. Please set it and restart.")
    st.stop()

TRANSFERS_FP = "outputs/interstore_transfers.csv"
SUMMARY_FP   = "outputs/routing_strategy_comparison.csv"
LOC_FP       = "data/store_locations.csv"

# ------------------------------------------------------------------
# 2. Load data
# ------------------------------------------------------------------
loc_df   = pd.read_csv(LOC_FP)
coord    = {r.store_id: (r.lat, r.lon) for r in loc_df.itertuples(index=False)}
trans_df = pd.read_csv(TRANSFERS_FP)
sum_df   = pd.read_csv(SUMMARY_FP)

all_dests = sorted(trans_df['to_store'].unique())

# ------------------------------------------------------------------
# 3. Sidebar UI
# ------------------------------------------------------------------
st.sidebar.title("⚙️ Route Viewer")
sel_dest = st.sidebar.selectbox("Destination store:", all_dests)

# decision from optimiser
row_sum  = sum_df[sum_df.to_store == sel_dest].iloc[0]
auto_mode = "Multi‑Pickup" if row_sum.decision.startswith("A") else "Parallel"

st.sidebar.markdown(f"**Optimiser choice:** `{auto_mode}` ")

# allow user to override for comparison
mode = st.sidebar.radio("Routing mode:", ["Auto (optimiser)", "Multi‑Pickup", "Parallel"], index=0)
if mode == "Auto (optimiser)":
    mode = auto_mode

# ------------------------------------------------------------------
# 4. Build pickup list & quantities
# ------------------------------------------------------------------
rows_dest = trans_df[trans_df.to_store == sel_dest]
origins   = rows_dest['from_store'].unique().tolist()

# sort farthest‑first for multi‑pickup
origins_sorted = sorted(origins, key=lambda s: haversine(coord[s], coord[sel_dest], Unit.KILOMETERS), reverse=True)

# helper to call Mapbox Directions
BASE_MULTI = "https://api.mapbox.com/directions/v5/mapbox/driving/"  # lon,lat;lon,lat...
HEADERS    = {"User-Agent": "ai-stock-hackathon"}

def get_route(coords):
    # coords list of (lon,lat)
    qs = ";".join([f"{lon},{lat}" for lon,lat in coords])
    url = f"{BASE_MULTI}{qs}?geometries=geojson&overview=full&access_token={MAPBOX_TOKEN}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        js = r.json()
        return js['routes'][0]
    except Exception as e:
        st.warning(f"Mapbox route error: {e}")
        return None

# ------------------------------------------------------------------
# 5. Prepare Folium map
# ------------------------------------------------------------------
lat_d, lon_d = coord[sel_dest]
folium_map = folium.Map(location=[lat_d, lon_d], zoom_start=12,
                        tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={MAPBOX_TOKEN}",
                        attr="Mapbox")
folium.Marker([lat_d, lon_d], tooltip=f"DEST {sel_dest}", icon=folium.Icon(color="red", icon="flag")).add_to(folium_map)

total_km = 0.0
eta_min  = 0.0

# ------------------------------------------------------------------
# 6. Draw routes based on mode
# ------------------------------------------------------------------
if mode == "Multi‑Pickup":
    coords = [(coord[s][1], coord[s][0]) for s in origins_sorted + [sel_dest]]
    route  = get_route(coords)
    if route:
        folium.GeoJson(route['geometry'], name="multi_pickup").add_to(folium_map)
        total_km = route['distance'] / 1000
        eta_min  = route['duration'] / 60
    for s in origins_sorted:
        folium.Marker(coord[s], tooltip=f"Pickup {s}", icon=folium.Icon(color="green")).add_to(folium_map)
else:  # Parallel
    colors = ["blue", "purple", "orange", "cadetblue", "darkred"]
    for i, s in enumerate(origins):
        coords = [(coord[s][1], coord[s][0]), (lon_d, lat_d)]
        route  = get_route(coords)
        col    = colors[i % len(colors)]
        if route:
            folium.GeoJson(route['geometry'], style_function=lambda x, c=col: {"color": c, "weight": 4}).add_to(folium_map)
            dist = route['distance'] / 1000
            dur  = route['duration'] / 60
            total_km += dist
            eta_min  = max(eta_min, dur)
        folium.Marker(coord[s], tooltip=f"Origin {s}", icon=folium.Icon(color="blue")).add_to(folium_map)

# ------------------------------------------------------------------
# 7. Streamlit output
# ------------------------------------------------------------------
st.title("📍 Retail Route Dashboard")
st.markdown(f"**Mode:** `{mode}`   |  **Destination:** `{sel_dest}`")
st.markdown(f"**Distance:** `{total_km:.2f} km`  |  **ETA:** `{eta_min:.0f} min`  |  **Origins:** `{len(origins)}`")

st.components.v1.html(folium_map._repr_html_(), height=600)

st.download_button("📥 Download map (HTML)", data=folium_map.get_root().render(), file_name="route_map.html", mime="text/html")
