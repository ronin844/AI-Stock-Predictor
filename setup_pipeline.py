import os, pathlib
import subprocess

# Define required outputs
required_files = [
    "data/merged.csv",
    "data/inventory.csv",
    "outputs/predictions.csv",
    "outputs/forecast_daily.csv",
    "outputs/interstore_transfers.csv",
]

# Check what’s missing
missing = [f for f in required_files if not pathlib.Path(f).exists()]

if missing:
    print("🛠 Detected missing files:", missing)
    print("⚙️  Running necessary pipeline steps...")

    subprocess.run(["python", "src/merge_data.py"])
    subprocess.run(["python", "src/train_model.py"])
    subprocess.run(["python", "src/forecast_and_detect.py"])
    subprocess.run(["python", "src/inter_store_rebalancing.py"])
    subprocess.run(["python", "src/route_simulation.py"])
    print("✅ Setup complete.")
else:
    print("✅ All required files exist. Skipping setup.")
