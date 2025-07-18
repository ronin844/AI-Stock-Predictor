# AI Stock Predictor Frontend

A React-based frontend application for the AI Stock Predictor project that provides an intuitive interface for viewing stock forecasts and dashboard analytics.

## Features

- **Dashboard**: Overview of key metrics including total products, active stores, low stock alerts, and recent predictions
- **Stock Forecast**: Interactive form to select store and product combinations and view detailed 7-day forecasts with charts
- **Navigation**: Clean navigation between different sections
- **Data Integration**: Uses CSV files from the project's outputs directory for real forecast data

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and navigate to `http://localhost:3000`

## Usage

### Dashboard
- View key performance indicators (KPIs) including:
  - Total Products: Number of unique products in the system
  - Active Stores: Number of stores being monitored
  - Low Stock Alerts: Count of products with shortage status
  - Average Accuracy: Model prediction accuracy
- Review recent predictions in a tabular format

### Stock Forecast
1. Select a Store ID from the dropdown
2. Select a Product ID from the dropdown
3. Click "Get Forecast" to view:
   - Current stock levels
   - 7-day predicted demand
   - Stock status (surplus/shortage/balanced)
   - Daily forecast chart showing predicted units sold over 7 days

## Data Sources

The frontend connects to the FastAPI service running on `http://localhost:8000` and uses the following endpoints:
- `GET /stores`: Retrieves list of available stores
- `GET /products`: Retrieves list of available products  
- `POST /predict`: Gets forecast data for a specific store-product combination

The API reads data from CSV files in the `outputs` directory:
- `outputs/predictions.csv`: Contains store-product combinations with current inventory, predicted demand, and status
- `outputs/forecast_daily.csv`: Contains daily forecast data for chart visualization

## Technology Stack

- **React**: Frontend framework
- **Material-UI**: UI component library
- **Chart.js**: Data visualization
- **React Router**: Navigation
- **Axios**: HTTP client (for future API integration)

## File Structure

```
frontend/
├── public/
│   ├── predictions.csv
│   ├── forecast_daily.csv
│   └── index.html
├── src/
│   ├── components/
│   │   ├── App.js
│   │   ├── Dashboard.js
│   │   ├── Forecast.js
│   │   └── LoginPage.js
│   ├── context/
│   │   └── AuthContext.js
│   ├── App.css
│   └── index.js
├── package.json
└── README.md
```

## Development

To make changes to the frontend:
1. Edit the relevant component files in the `src` directory
2. The development server will automatically reload with your changes
3. For production builds, run `npm run build`

## Notes

- The application currently uses CSV files for data. For production use, these could be replaced with API calls to a backend service.
- Authentication components are included but currently use mock data for demonstration purposes.
