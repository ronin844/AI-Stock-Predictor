import pandas as pd
import numpy as np
import os

# Read data
sales = pd.read_csv("data/sales.csv", parse_dates=["date"])
weather = pd.read_csv("data/weather.csv", parse_dates=["date"])
holidays = pd.read_csv("data/holidays.csv", parse_dates=["date"])

# Merge weather
df = sales.merge(weather, on=["store_id", "date"], how="left")

# Merge holiday
df = df.merge(holidays, on="date", how="left")
df["is_holiday"] = df["is_holiday"].fillna(0).astype(int)

# Sort
df = df.sort_values(["store_id", "product_id", "date"])

# --- Create Lag Features ---
for lag in [1, 2, 3, 7]:
    df[f"lag_{lag}"] = df.groupby(["store_id", "product_id"])["units_sold"].shift(lag)

# Drop rows with missing lags
df = df.dropna(subset=[f"lag_{l}" for l in [1, 2, 3, 7]])

# --- Output for model training ---
os.makedirs("features", exist_ok=True)
df.to_csv("features/train_data.csv", index=False)
print("✅ train_data.csv saved with shape:", df.shape)
