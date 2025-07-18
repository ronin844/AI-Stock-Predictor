# AI Stock Predictor

This project is a full-stack AI-powered stock prediction and route optimization system designed for retail stores. It combines a Python FastAPI backend with a React frontend to provide real-time stock forecasts and optimized delivery routes.

## Technologies Used

- **Backend:** FastAPI, Python, Pandas, Uvicorn
- **Frontend:** React.js, React Router, Chart.js, Mapbox, Folium
- **Data:** CSV files for input data and prediction outputs
- **Visualization:** Interactive charts and maps for forecasts and routes

## Project Structure

```
ai-stock-predictor/
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── App.js     # Main app with routing and navigation
│   │   ├── Dashboard.js
│   │   ├── Forecast.js
│   │   └── MapRoute.js
│   └── package.json
├── src/               # Python backend API server
│   ├── serve_api.py   # FastAPI server exposing prediction and route endpoints
│   └── generate_sample_~data.py  # Script to generate sample CSV data
├── data/              # Input CSV data files
│   ├── store_locations.csv
│   └── inventory.csv
└── outputs/           # Generated prediction CSV files
    ├── predictions.csv
    └── forecast_daily.csv
```

## How It Works

### Backend

- The backend is implemented using FastAPI and serves as the core engine for stock forecasting and route data.
- It reads input data from CSV files in the `data/` directory and prediction outputs from the `outputs/` directory.
- The backend exposes several REST API endpoints:
  - `POST /predict`: Accepts a JSON payload with `store_id` and `product_id` and returns:
    - Current stock level for the product at the store
    - Predicted demand for the next 7 days
    - Stock status (surplus, shortage, or balanced)
    - Daily forecast data for visualization
  - `GET /dashboard`: Returns aggregated dashboard metrics such as total stores, total products, low stock alerts, and recent predictions.
  - `GET /stores` and `GET /products`: Provide lists of available stores and products for frontend dropdowns.
  - `GET /route-data` and `GET /route-data/{destination}`: Provide routing and transfer data for route visualization.
- The backend uses pandas for data processing and includes CORS middleware to allow requests from the frontend.

### Frontend

- The frontend is a React application with routing and navigation using React Router.
- It provides three main pages:
  - **Dashboard:** Displays summary metrics and recent alerts.
  - **Forecast:** Allows users to select a store and product, fetches forecast data from the backend, and displays it with charts.
  - **Routes:** Visualizes optimized delivery routes on an interactive map using Mapbox and Folium.
- The Forecast page dynamically fetches available stores and products to populate dropdowns.
- On user input, it calls the backend `/predict` API and displays the results including current stock, predicted demand, and a line chart of daily forecasted sales.

### Route Optimization Logic

- The system uses a 2-hour grace period to decide between two routing modes:
  - **Multi-pickup Mode:** A single truck visits multiple stores in a farthest-first order.
  - **Parallel Mode:** Multiple trucks make direct trips from origins to the destination.
- This decision is based on the time difference between routes, optimizing for delivery efficiency and resource utilization.

### Implementation Details

- **Backend:**
  - Uses FastAPI to create RESTful endpoints.
  - Reads and processes CSV data with pandas.
  - Implements CORS middleware to allow frontend communication.
  - Runs on port 8000 by default.
- **Frontend:**
  - Built with React and React Router for SPA navigation.
  - Uses Chart.js for rendering forecast line charts.
  - Uses Mapbox and Folium for interactive route maps.
  - Runs on port 3000 by default.
- **Data Flow:**
  - Frontend fetches data from backend APIs.
  - User inputs on the frontend trigger API calls to fetch predictions.
  - Backend returns processed data for display and visualization.

## Installation

1. **Backend Setup**
```bash
pip install fastapi uvicorn pandas pyngrok
cd src
python serve_api.py
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

3. Open `http://localhost:3000` in your browser to access the app.

## Usage

- Navigate between Dashboard, Forecast, and Routes pages.
- Use the Forecast page to get stock predictions by selecting store and product.
- Use the Routes page to view optimized delivery routes and statistics.

## API Endpoints

- `GET /dashboard` - Dashboard metrics and recent predictions
- `GET /stores` - List of available stores
- `GET /products` - List of available products
- `POST /predict` - Get stock prediction for store/product
- `GET /route-data` - Get all route optimization data
- `GET /route-data/{destination}` - Get specific destination route data

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
