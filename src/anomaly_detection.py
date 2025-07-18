# src/anomaly_detection.py
import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load historical sales
sales = pd.read_csv(os.path.join(DATA_DIR, "sales.csv"), parse_dates=["date"])

# Compute rolling metrics
sales = sales.sort_values(["store_id", "product_id", "date"])
sales["rolling_mean"] = sales.groupby(["store_id", "product_id"])["units_sold"].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
sales["rolling_std"]  = sales.groupby(["store_id", "product_id"])["units_sold"].transform(lambda x: x.rolling(window=7, min_periods=1).std().fillna(0))

# Z-score based anomaly detection
sales["z_score"] = (sales["units_sold"] - sales["rolling_mean"]) / sales["rolling_std"].replace(0, 1)
sales["anomaly"] = sales["z_score"].abs() > 2.5

# Save anomalies only
anomalies = sales[sales["anomaly"]].copy()
anomalies.to_csv(os.path.join(OUTPUT_DIR, "anomalies.csv"), index=False)

print("✅ Anomalies detected and saved → outputs/anomalies.csv")
