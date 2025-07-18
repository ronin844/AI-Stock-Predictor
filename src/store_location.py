import pandas as pd
import random
import os

# ----- Bhopal bounds -----
CITY_BOUNDS = {
    "Bhopal": {
        "lat": (23.20, 23.35),
        "lon": (77.30, 77.45),
    }
}

NUM_STORES = 5  # Adjust as needed
output_path = "data/store_locations.csv"

rows = []
for i in range(1, NUM_STORES + 1):
    store_id = f"store_{i}"
    lat = round(random.uniform(*CITY_BOUNDS["Bhopal"]["lat"]), 6)
    lon = round(random.uniform(*CITY_BOUNDS["Bhopal"]["lon"]), 6)
    rows.append({"store_id": store_id, "city": "Bhopal", "lat": lat, "lon": lon})

df = pd.DataFrame(rows)
os.makedirs("data", exist_ok=True)
df.to_csv(output_path, index=False)
print(f"✅ Store locations for Bhopal saved to → {output_path}")
