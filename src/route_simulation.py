# src/route_simulation.py – strategy‑A vs B using Mapbox distances
import os, math, pathlib, pandas as pd, requests
from haversine import haversine, Unit

SPEED = 40          # km/h fallback
GRACE = 2           # hours
MAX   = 100         # units per truck

DATA = pathlib.Path("data")
OUT  = pathlib.Path("outputs")
T_CSV = OUT / "interstore_transfers.csv"
LOC   = DATA / "store_locations.csv"

TOKEN = os.getenv("MAPBOX_TOKEN")
if not TOKEN: raise RuntimeError("MAPBOX_TOKEN not set")
URL   = "https://api.mapbox.com/directions/v5/mapbox/driving/{x1},{y1};{x2},{y2}?access_token=" + TOKEN

locs = pd.read_csv(LOC) ; co = {r.store_id:(r.lat,r.lon) for r in locs.itertuples(index=False)}
tr  = pd.read_csv(T_CSV)

cache={}
def dkm(a,b):
    if (a,b) in cache: return cache[(a,b)]
    try:
        r = requests.get(URL.format(x1=co[a][1],y1=co[a][0],x2=co[b][1],y2=co[b][0]),timeout=4).json()
        km = r["routes"][0]["distance"]/1e3
    except Exception:
        km = haversine(co[a],co[b],Unit.KILOMETERS)
    cache[(a,b)] = km
    return km

def h(km): return km/SPEED

rows=[]
for dest in tr.to_store.unique():
    sub = tr[tr.to_store==dest]
    # ---- Strategy B ----
    vehB=0; times=[]
    for o,g in sub.groupby("from_store"):
        trips=math.ceil(g.quantity.sum()/MAX); vehB+=trips
        km1 = g.road_km.iloc[0] if "road_km" in g else dkm(o,dest)
        times.extend([h(km1)]*trips)
    timeB = max(times) if times else 0
    # ---- Strategy A ----
    origins = sorted(sub.from_store.unique(), key=lambda s: dkm(s,dest), reverse=True)
    route_km = sum(dkm(origins[i],origins[i+1]) for i in range(len(origins)-1)) + dkm(origins[-1], dest)
    timeA = h(route_km)
    decision = "A (multi‑pickup)" if (timeB-timeA)<GRACE else "B (parallel bundled)"
    rows.append(dict(to_store=dest,num_origins=len(origins),veh_A=1,veh_B=vehB,
                     time_A_hr=round(timeA,2),time_B_hr=round(timeB,2),decision=decision))
pd.DataFrame(rows).to_csv(OUT/"routing_strategy_comparison.csv",index=False)
print("✅ routing_strategy_comparison.csv (Mapbox) saved")
