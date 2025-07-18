import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Store as StoreIcon,
} from '@mui/icons-material';

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('http://localhost:8000/dashboard');
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }
        const data = await response.json();
        
        setDashboardData({
          totalProducts: data.total_products,
          totalStores: data.total_stores,
          lowStockAlerts: data.low_stock_alerts,
          avgAccuracy: data.avg_accuracy,
          recentPredictions: data.recent_predictions
        });
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError('Failed to load dashboard data. Make sure the API server is running on port 8000.');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'surplus': return 'success';
      case 'shortage': return 'error';
      case 'balanced': return 'info';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, padding: 3, backgroundColor: '#f4f6f8', minHeight: '100vh' }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: '#172B4D', mb: 4 }}>
        AI Stock Predictor Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
      )}

      <Grid container spacing={3}>
        {/* KPI Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Total Products
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.totalProducts}
                  </Typography>
                </Box>
                <InventoryIcon sx={{ fontSize: 40, color: '#0061f2' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Active Stores
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.totalStores}
                  </Typography>
                </Box>
                <StoreIcon sx={{ fontSize: 40, color: '#4caf50' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Low Stock Alerts
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.lowStockAlerts}
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 40, color: '#f44336' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Avg Accuracy
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.avgAccuracy}%
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, color: '#ff9800' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Predictions Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', mb: 2 }}>
              Recent Predictions
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Store ID</strong></TableCell>
                    <TableCell><strong>Product ID</strong></TableCell>
                    <TableCell><strong>Current Stock</strong></TableCell>
                    <TableCell><strong>Predicted Demand</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData?.recentPredictions.map((prediction, index) => (
                    <TableRow key={index}>
                      <TableCell>{prediction.store_id}</TableCell>
                      <TableCell>{prediction.product_id}</TableCell>
                      <TableCell>{prediction.current_stock}</TableCell>
                      <TableCell>{prediction.predicted_demand}</TableCell>
                      <TableCell>
                        <Chip 
                          label={prediction.status ? prediction.status.charAt(0).toUpperCase() + prediction.status.slice(1) : 'Unknown'}
                          color={getStatusColor(prediction.status)}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
