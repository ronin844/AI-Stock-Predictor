import pandas as pd
import pathlib
import random

# Create data directories if they don't exist
data_dir = pathlib.Path("data")
outputs_dir = pathlib.Path("outputs")
data_dir.mkdir(exist_ok=True)
outputs_dir.mkdir(exist_ok=True)

# Generate sample store locations
stores = [f"store_{i}" for i in range(1, 6)]
store_locations = pd.DataFrame({
    'store_id': stores,
    'lat': [random.uniform(30, 40) for _ in stores],
    'lon': [random.uniform(-120, -110) for _ in stores],
    'city': [f"City {i}" for i in range(1, 6)]
})
store_locations.to_csv(data_dir / "store_locations.csv", index=False)

# Generate sample inventory
products = [f"product_{i}" for i in range(1, 11)]
inventory_data = []
for store in stores:
    for product in products:
        inventory_data.append({
            'store_id': store,
            'product_id': product,
            'current_inventory': random.randint(50, 200)
        })
inventory_df = pd.DataFrame(inventory_data)
inventory_df.to_csv(data_dir / "inventory.csv", index=False)

# Generate sample predictions
predictions_data = []
for store in stores:
    for product in products:
        current_stock = random.randint(50, 200)
        predicted_demand = random.randint(30, 180)
        status = 'surplus' if current_stock > predicted_demand else 'shortage'
        predictions_data.append({
            'store_id': store,
            'product_id': product,
            'current_inventory': current_stock,
            'predicted_7_day_sales': predicted_demand,
            'status': status
        })
predictions_df = pd.DataFrame(predictions_data)
predictions_df.to_csv(outputs_dir / "predictions.csv", index=False)

# Generate daily forecast data
daily_data = []
for store in stores:
    for product in products:
        base_demand = random.randint(5, 25)
        for day in range(1, 8):
            daily_data.append({
                'store_id': store,
                'product_id': product,
                'date': f'2024-01-{day:02d}',
                'predicted_units_sold': max(0, base_demand + random.randint(-5, 5))
            })
daily_df = pd.DataFrame(daily_data)
daily_df.to_csv(outputs_dir / "forecast_daily.csv", index=False)

print("Sample data generated successfully!")
