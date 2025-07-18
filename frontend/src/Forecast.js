import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Autocomplete,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE_URL = 'http://localhost:8000';

function Forecast() {
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [stores, setStores] = useState([]);
  const [products, setProducts] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchStoresAndProducts = async () => {
      try {
        // Fetch stores
        const storesResponse = await fetch(`${API_BASE_URL}/stores`);
        const storesData = await storesResponse.json();
        setStores(storesData.stores);

        // Fetch products
        const productsResponse = await fetch(`${API_BASE_URL}/products`);
        const productsData = await productsResponse.json();
        setProducts(productsData.products);
      } catch (err) {
        console.error('Error fetching stores and products:', err);
        setError('Failed to load stores and products. Make sure the API server is running on port 8000.');
      }
    };

    fetchStoresAndProducts();
  }, []);

  const fetchForecast = async () => {
    if (!storeId || !productId) {
      setError('Please select both store and product');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          store_id: storeId,
          product_id: productId
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch forecast');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error('Forecast error:', err);
      setError(err.message || 'Error fetching forecast data');
    }
    setLoading(false);
  };

  const dailyLabels = result ? result.daily_forecast.map((_, i) => `Day ${i + 1}`) : [];

  const chartData = {
    labels: dailyLabels,
    datasets: [
      {
        label: 'Daily Forecasted Units Sold',
        data: result ? result.daily_forecast : [],
        fill: false,
        borderColor: '#0061f2',
        backgroundColor: 'rgba(0, 97, 242, 0.1)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: '7-Day Sales Forecast',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Box sx={{ flexGrow: 1, padding: 3, backgroundColor: '#f4f6f8', minHeight: '100vh' }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: '#172B4D', mb: 4 }}>
        Stock Forecast
      </Typography>

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={5}>
                <Autocomplete
                  value={storeId}
                  onChange={(event, newValue) => setStoreId(newValue)}
                  options={stores || []}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Store ID"
                      variant="outlined"
                      fullWidth
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={5}>
                <Autocomplete
                  value={productId}
                  onChange={(event, newValue) => setProductId(newValue)}
                  options={products || []}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Product ID"
                      variant="outlined"
                      fullWidth
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <Button
                  onClick={fetchForecast}
                  disabled={loading}
                  variant="contained"
                  fullWidth
                  sx={{
                    height: '56px',
                    bgcolor: '#0061f2',
                    '&:hover': { bgcolor: '#0044ab' },
                  }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Get Forecast'}
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Results Section */}
        {error && (
          <Grid item xs={12}>
            <Alert severity="error">{error}</Alert>
          </Grid>
        )}

        {result && (
          <>
            {/* KPI Cards */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="textSecondary">Current Stock</Typography>
                <Typography variant="h4">{result.current_stock}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="textSecondary">Predicted Demand (7 days)</Typography>
                <Typography variant="h4">{result.predicted_demand}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="textSecondary">Status</Typography>
                <Typography 
                  variant="h4" 
                  color={
                    result.status === 'surplus' ? 'success.main' :
                    result.status === 'shortage' ? 'error.main' :
                    'info.main'
                  }
                >
                  {result.status ? result.status.charAt(0).toUpperCase() + result.status.slice(1) : 'Unknown'}
                </Typography>
              </Paper>
            </Grid>

            {/* Chart */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Box sx={{ height: 400 }}>
                  <Line data={chartData} options={chartOptions} />
                </Box>
              </Paper>
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
}

export default Forecast;
