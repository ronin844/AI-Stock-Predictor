# src/serve_api.py  – FastAPI service that exposes model forecasts
# ---------------------------------------------------------------------
# This version replaces the generic feature‑based endpoint with a more
# domain‑specific "/predict" route that returns:
#   • next‑7‑day daily forecast (list)
#   • 7‑day sum (predicted_demand)
#   • current_stock (from inventory)
#   • status (surplus / shortage / balanced)
# The route expects JSON: { "store_id": "store_1", "product_id": "product_3" }
# ---------------------------------------------------------------------

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyngrok import ngrok
import pandas as pd
import uvicorn
import os, pathlib

# ------------------------- CONFIG ------------------------------------
PORT          = 8000
DATA_DIR      = pathlib.Path("../outputs")        # predictions & daily file live here
PUBLIC_URL    = os.getenv("PUBLIC_URL")           # optional override
NGROK_TOKEN   = os.getenv("NGROK_AUTHTOKEN", "")  # set as env var if you have one

# ------------------------- NGROK -------------------------------------
# Disabled ngrok tunneling to avoid session limit issues
PUBLIC_URL = None
print(f"🔗 Public URL: {PUBLIC_URL}")

# ------------------------- FASTAPI -----------------------------------
app = FastAPI(title="AI Stock‑Forecast API")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastRequest(BaseModel):
    store_id:   str
    product_id: str

@app.get("/")
async def root():
    return {"message": "Forecast service running", "public_url": PUBLIC_URL}

@app.get("/dashboard")
async def get_dashboard_data():
    try:
        # Get stores and products count
        stores_df = pd.read_csv("../data/store_locations.csv")
        products_df = pd.read_csv("../data/inventory.csv")
        
        total_stores = len(stores_df.store_id.unique())
        total_products = len(products_df.product_id.unique())
        
        # Get predictions data if available
        pred_path = DATA_DIR / "predictions.csv"
        low_stock_alerts = 0
        recent_predictions = []
        
        if pred_path.exists():
            predictions_df = pd.read_csv(pred_path)
            low_stock_alerts = len(predictions_df[predictions_df.status == 'shortage'])
            
            # Get sample recent predictions (first 5)
            sample_predictions = predictions_df.head(5)
            recent_predictions = sample_predictions.to_dict('records')
        
        return {
            "total_stores": total_stores,
            "total_products": total_products,
            "low_stock_alerts": low_stock_alerts,
            "avg_accuracy": 94.2,  # Mock accuracy
            "recent_predictions": recent_predictions
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/predict")
async def predict(req: ForecastRequest):
    try:
        pred_path   = DATA_DIR / "predictions.csv"
        daily_path  = DATA_DIR / "forecast_daily.csv"
        if not pred_path.exists() or not daily_path.exists():
            raise HTTPException(500, "Prediction files not found. Run forecast first.")

        df     = pd.read_csv(pred_path)
        daily  = pd.read_csv(daily_path)

        row_df = df[(df.store_id == req.store_id) & (df.product_id == req.product_id)]
        if row_df.empty:
            raise HTTPException(404, "Store or product not found")
        row = row_df.iloc[0]

        daily_fc = (
            daily[(daily.store_id == req.store_id) & (daily.product_id == req.product_id)]
            .sort_values("date")["predicted_units_sold"].round(2).tolist()
        )

        return {
            "store_id": req.store_id,
            "product_id": req.product_id,
            "current_stock": int(row.current_inventory),
            "predicted_demand": int(row.predicted_7_day_sales),
            "status": row.status,
            "daily_forecast": daily_fc,
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/stores")
async def get_stores():
    try:
        df = pd.read_csv("../data/store_locations.csv")
        return {"stores": df.store_id.unique().tolist()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/products")
async def get_products():
    try:
        df = pd.read_csv("../data/inventory.csv")
        return {"products": df.product_id.unique().tolist()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/route-data")
async def get_route_data():
    try:
        transfers_path = DATA_DIR / "interstore_transfers.csv"
        locations_path = pathlib.Path("../data/store_locations.csv")
        
        if not transfers_path.exists():
            raise HTTPException(500, "Transfers file not found.")
        if not locations_path.exists():
            raise HTTPException(500, "Store locations file not found.")
            
        transfers_df = pd.read_csv(transfers_path)
        locations_df = pd.read_csv(locations_path)
        
        # Convert to dictionaries for JSON response
        transfers = transfers_df.to_dict('records')
        locations = {row['store_id']: {'lat': row['lat'], 'lon': row['lon'], 'city': row['city']} 
                    for _, row in locations_df.iterrows()}
        
        return {
            "transfers": transfers,
            "locations": locations,
            "destinations": sorted(transfers_df['to_store'].unique().tolist())
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/route-data/{destination}")
async def get_route_for_destination(destination: str):
    try:
        transfers_path = DATA_DIR / "interstore_transfers.csv"
        locations_path = pathlib.Path("../data/store_locations.csv")
        
        if not transfers_path.exists():
            raise HTTPException(500, "Transfers file not found.")
        if not locations_path.exists():
            raise HTTPException(500, "Store locations file not found.")
            
        transfers_df = pd.read_csv(transfers_path)
        locations_df = pd.read_csv(locations_path)
        
        # Filter transfers for the destination
        dest_transfers = transfers_df[transfers_df['to_store'] == destination]
        if dest_transfers.empty:
            raise HTTPException(404, f"No transfers found for destination {destination}")
        
        origins = dest_transfers['from_store'].unique().tolist()
        
        # Get location data
        locations = {row['store_id']: {'lat': row['lat'], 'lon': row['lon'], 'city': row['city']} 
                    for _, row in locations_df.iterrows()}
        
        # Calculate statistics
        total_distance = dest_transfers['road_km'].sum()
        total_quantity = dest_transfers['quantity'].sum()
        
        return {
            "destination": destination,
            "origins": origins,
            "transfers": dest_transfers.to_dict('records'),
            "locations": locations,
            "statistics": {
                "total_distance": round(total_distance, 2),
                "total_quantity": int(total_quantity),
                "estimated_time": round(total_distance * 2),  # 2 minutes per km estimate
                "origin_count": len(origins)
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# ------------------------- MAIN --------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
