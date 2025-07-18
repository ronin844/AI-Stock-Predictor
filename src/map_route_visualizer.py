import os, folium, requests, pandas as pd, streamlit as st
from haversine import haversine, Unit

TOKEN = os.getenv("MAPBOX_TOKEN")
if not TOKEN: st.error("MAPBOX_TOKEN env var not set!") ; st.stop()
MB_DIR_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{lon1},{lat1};{lon2},{lat2}?geometries=geojson&access_token="+TOKEN
MB_MULTI   = "https://api.mapbox.com/directions/v5/mapbox/driving/{coords}?geometries=geojson&access_token="+TOKEN

locs  = pd.read_csv("data/store_locations.csv")
coord = {r.store_id:(r.lat,r.lon) for r in locs.itertuples(index=False)}

st.sidebar.header("Route Panel")
dest = st.sidebar.selectbox("Destination store", list(coord.keys()))
mode = st.sidebar.radio("Mode", ["Multi‑Pickup", "Multi‑Vehicle"])

pickups = [s for s in coord if s!=dest]
# sort heuristic
pickups.sort(key=lambda s: haversine(coord[s], coord[dest], Unit.KILOMETERS), reverse=True)

m = folium.Map(location=coord[dest], zoom_start=12,
               tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={TOKEN}",
               attr='Mapbox')

folium.Marker(coord[dest],icon=folium.Icon(color="red",icon="flag"),tooltip=f"DEST {dest}").add_to(m)

total_km=0; total_min=0
if mode=="Multi‑Pickup":
    coords_str=";".join([f"{coord[s][1]},{coord[s][0]}" for s in pickups+[dest]])
    js=requests.get(MB_MULTI.format(coords=coords_str)).json()
    folium.GeoJson(js["routes"][0]["geometry"],name="route").add_to(m)
    total_km = js["routes"][0]["distance"]/1000
    total_min= js["routes"][0]["duration"]/60
    for p in pickups:
        folium.Marker(coord[p],tooltip=f"Pickup {p}",icon=folium.Icon(color="green")).add_to(m)
else:
    for p in pickups:
        js=requests.get(MB_DIR_URL.format(lon1=coord[p][1],lat1=coord[p][0],
                                          lon2=coord[dest][1],lat2=coord[dest][0])).json()
        folium.GeoJson(js["routes"][0]["geometry"]).add_to(m)
        total_km+=js["routes"][0]["distance"]/1000
        total_min=max(total_min, js["routes"][0]["duration"]/60)
        folium.Marker(coord[p],tooltip=f"Vehicle {p}",icon=folium.Icon(color="blue")).add_to(m)

st.title("📍 Mapbox Route Visualizer")
st.write(f"**Mode:** {mode}   •   **Distance:** {total_km:.1f} km   •   **ETA:** {total_min:.0f} min")
st.components.v1.html(m._repr_html_(), height=600, scrolling=True)
