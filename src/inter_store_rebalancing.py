# src/inter_store_rebalancing.py – Mapbox driving‑distance‑aware transfers
"""
Same greedy surplus→shortage algorithm but uses **Mapbox Directions API**.

Free tier: 100 k direction requests / month.
"""
import os, math, pathlib, requests, numpy as np, pandas as pd
from haversine import haversine, Unit

DATA_DIR   = pathlib.Path("data")
OUT_DIR    = pathlib.Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

pred      = pd.read_csv(OUT_DIR / "predictions.csv")
locs      = pd.read_csv(DATA_DIR / "store_locations.csv")
coord     = {r.store_id: (r.lat, r.lon) for r in locs.itertuples(index=False)}

TOKEN     = os.getenv("MAPBOX_TOKEN")
if not TOKEN:
    raise RuntimeError("MAPBOX_TOKEN env‑var not set")

MB_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{lon1},{lat1};{lon2},{lat2}?geometries=geojson&access_token=" + TOKEN
dist_cache = {}

def road_km(a: str, b: str) -> float:
    if (a, b) in dist_cache:
        return dist_cache[(a, b)]
    url = MB_URL.format(lon1=coord[a][1], lat1=coord[a][0],
                        lon2=coord[b][1], lat2=coord[b][0])
    try:
        js = requests.get(url, timeout=5).json()
        km = js["routes"][0]["distance"] / 1000
    except Exception:
        km = haversine(coord[a], coord[b], Unit.KILOMETERS)
    dist_cache[(a, b)] = km
    return km

transfers = []
for product in pred.product_id.unique():
    p = pred[pred.product_id == product].copy()
    surplus  = p[p.status == "surplus"].copy()
    surplus["qty"] = np.ceil(surplus.current_inventory - surplus.predicted_7_day_sales).astype(int)
    surplus = surplus[surplus.qty > 0]

    shortage = p[p.status == "shortage"].copy()
    shortage["need"] = np.ceil(shortage.predicted_7_day_sales - shortage.current_inventory).astype(int)
    shortage = shortage[shortage.need > 0]

    while not shortage.empty and not surplus.empty:
        best = None ; best_d = math.inf
        for si, s in surplus.iterrows():
            for di, d in shortage.iterrows():
                dkm = road_km(s.store_id, d.store_id)
                if dkm < best_d:
                    best = (si, di, dkm)
                    best_d = dkm
        si, di, dkm = best
        qty = min(surplus.at[si, "qty"], shortage.at[di, "need"])
        transfers.append(dict(product_id=product,
                              from_store=surplus.at[si, "store_id"],
                              to_store=shortage.at[di, "store_id"],
                              quantity=int(qty),
                              road_km=round(dkm,2)))
        surplus.at[si, "qty"]   -= qty
        shortage.at[di, "need"] -= qty
        surplus  = surplus[surplus.qty  > 0]
        shortage = shortage[shortage.need > 0]

pd.DataFrame(transfers).to_csv(OUT_DIR / "interstore_transfers.csv", index=False)
print("✅ interstore_transfers.csv (Mapbox) saved")
