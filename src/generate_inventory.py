import pandas as pd
import numpy as np

sales_df = pd.read_csv("data/sales.csv")

# Compute 7-day expected demand
avg_sales = (
    sales_df
    .groupby(["store_id", "product_id"])["units_sold"]
    .mean()
    .reset_index()
)
avg_sales["expected_7_day_sales"] = avg_sales["units_sold"] * 7

# Add variation to simulate surplus/shortage/balanced
np.random.seed(42)
def add_variation(expected):
    # ±30% range, with roughly equal chance of surplus/shortage
    variation_factor = np.random.normal(loc=1.0, scale=0.3)
    return max(0, int(expected * variation_factor))

avg_sales["current_inventory"] = avg_sales["expected_7_day_sales"].apply(add_variation)

# Final inventory format
inventory_df = avg_sales[["store_id", "product_id", "current_inventory"]]
inventory_df.to_csv("data/inventory.csv", index=False)
print("✅ inventory.csv saved with varied inventory levels")
