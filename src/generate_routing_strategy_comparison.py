import os, math, pathlib, pandas as pd, requests
from haversine import haversine, Unit

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
if not MAPBOX_TOKEN:
    raise RuntimeError("MAPBOX_TOKEN not set")

SPEED_KMPH          = 40
GRACE_HOURS         = 2
MAX_UNITS_PER_TRUCK = 100

DATA_DIR = pathlib.Path("data")
OUT_DIR  = pathlib.Path("outputs")
TRANSFERS_FP = OUT_DIR / "interstore_transfers.csv"
LOC_FP       = DATA_DIR / "store_locations.csv"

locs   = pd.read_csv(LOC_FP)
coord = {r.store_id: (r.lat, r.lon) for r in locs.itertuples(index=False)}


BASE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving"
HEADERS  = {"User-Agent": "routing-strategy-comparer"}

leg_cache = {}

def road_km(a, b):
    key = (a, b)
    if key in leg_cache:
        return leg_cache[key]
    try:
        coords = f"{coord[a][1]},{coord[a][0]};{coord[b][1]},{coord[b][0]}"
        url = f"{BASE_URL}/{coords}?access_token={MAPBOX_TOKEN}&geometries=geojson"
        r = requests.get(url, headers=HEADERS, timeout=6)
        js = r.json()
        km = js['routes'][0]['distance'] / 1000.0
        leg_cache[key] = km
        return km
    except:
        km = haversine(coord[a], coord[b], unit=Unit.KILOMETERS)
        leg_cache[key] = km
        return km

def hours(km): return km / SPEED_KMPH

transfers = pd.read_csv(TRANSFERS_FP)
results = []

for dest in transfers["to_store"].unique():
    rows = transfers[transfers.to_store == dest]

    # Strategy B: parallel bundled (with load split)
    veh_B = 0
    times_B = []
    for origin, group in rows.groupby("from_store"):
        total_qty = group["quantity"].sum()
        trips = math.ceil(total_qty / MAX_UNITS_PER_TRUCK)
        dist = road_km(origin, dest)
        veh_B += trips
        times_B.extend([hours(dist)] * trips)
    time_B = max(times_B) if times_B else 0

    # Strategy A: multi-pickup (one truck)
    origins = rows["from_store"].unique().tolist()
    origins.sort(key=lambda s: road_km(s, dest), reverse=True)
    route_km = 0.0
    for i in range(len(origins) - 1):
        route_km += road_km(origins[i], origins[i + 1])
    route_km += road_km(origins[-1], dest)
    time_A = hours(route_km)

    decision = "A (multi-pickup)" if (time_B - time_A) < GRACE_HOURS else "B (parallel bundled)"

    results.append({
        "to_store": dest,
        "num_origins": len(origins),
        "veh_A": 1,
        "veh_B": veh_B,
        "time_A_hr": round(time_A, 2),
        "time_B_hr": round(time_B, 2),
        "decision": decision
    })

summary = pd.DataFrame(results)
OUT_DIR.mkdir(exist_ok=True)
summary.to_csv(OUT_DIR / "routing_strategy_comparison.csv", index=False)
print("\n✅ Saved routing_strategy_comparison.csv (Mapbox version)")
