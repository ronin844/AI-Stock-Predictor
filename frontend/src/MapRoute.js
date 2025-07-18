import React, { useState, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  Grid,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Navigation as NavigationIcon,
  Timer as TimerIcon,
  LocalShipping as TruckIcon,
} from '@mui/icons-material';

// Set Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1Ijoicm9uaW4wODA0IiwiYSI6ImNtYzNldnVyNTAwMjQybHNhODJ4dTFtMzgifQ.gICZEncdQpQ2bp9QQ67t7A';

const API_BASE_URL = 'http://localhost:8000';

function MapRoute() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState('');
  const [routingMode, setRoutingMode] = useState('auto');
  const [optimizerChoice, setOptimizerChoice] = useState('');
  const [destinations, setDestinations] = useState([]);
  const [routeData, setRouteData] = useState(null);
  const [transferDetails, setTransferDetails] = useState([]);
  const [currentData, setCurrentData] = useState(null);
  const [routeStats, setRouteStats] = useState(null);

  // Constants from backend
  const SPEED_KMPH = 40;
  const GRACE_HOURS = 2;
  const MAX_UNITS_PER_TRUCK = 100;

  const calculateRouteStats = (data) => {
    const destLocation = data.locations[selectedDestination];
    const origins = data.origins;
    const transfers = data.transfers;

    // Strategy B: Parallel bundled (with load split)
    let vehiclesB = 0;
    let timesB = [];
    
    // Group transfers by origin
    const originGroups = {};
    transfers.forEach(transfer => {
      if (!originGroups[transfer.from_store]) {
        originGroups[transfer.from_store] = 0;
      }
      originGroups[transfer.from_store] += transfer.quantity;
    });

    // Calculate parallel routes
    Object.entries(originGroups).forEach(([origin, totalQty]) => {
      const trips = Math.ceil(totalQty / MAX_UNITS_PER_TRUCK);
      const dist = data.locations[origin] ? 
        haversineDistance(data.locations[origin], destLocation) : 0;
      vehiclesB += trips;
      const time = (dist / SPEED_KMPH);
      timesB.push(...Array(trips).fill(time));
    });
    const timeB = Math.max(...timesB);

    // Strategy A: Multi-pickup (one truck)
    // Sort origins farthest-first
    const sortedOrigins = [...origins].sort((a, b) => {
      const distA = data.locations[a] ? 
        haversineDistance(data.locations[a], destLocation) : 0;
      const distB = data.locations[b] ? 
        haversineDistance(data.locations[b], destLocation) : 0;
      return distB - distA;
    });

    // Calculate multi-pickup route distance
    let routeKm = 0;
    for (let i = 0; i < sortedOrigins.length - 1; i++) {
      if (data.locations[sortedOrigins[i]] && data.locations[sortedOrigins[i + 1]]) {
        routeKm += haversineDistance(
          data.locations[sortedOrigins[i]], 
          data.locations[sortedOrigins[i + 1]]
        );
      }
    }
    if (sortedOrigins.length > 0 && data.locations[sortedOrigins[sortedOrigins.length - 1]]) {
      routeKm += haversineDistance(
        data.locations[sortedOrigins[sortedOrigins.length - 1]], 
        destLocation
      );
    }
    const timeA = routeKm / SPEED_KMPH;

    // Decision logic with 2-hour grace period
    const decision = (timeB - timeA) < GRACE_HOURS ? 
      'Multi-Pickup' : 'Parallel';

    setRouteStats({
      vehiclesA: 1,
      vehiclesB,
      timeA,
      timeB,
      decision,
      sortedOrigins,
      routeKmA: routeKm,
      routeKmB: Object.entries(originGroups).reduce((total, [origin, qty]) => {
        const dist = data.locations[origin] ? 
          haversineDistance(data.locations[origin], destLocation) : 0;
        return total + (dist * Math.ceil(qty / MAX_UNITS_PER_TRUCK));
      }, 0)
    });

    // Set optimizer choice based on decision
    setOptimizerChoice(decision);
    
    // Only auto-set routing mode if it's currently set to auto
    if (routingMode === 'auto') {
      setRoutingMode(decision.toLowerCase().replace('-', '-'));
    }
  };

  const getCurrentRouteStats = () => {
    if (!routeStats || !currentData) return routeData;

    const currentMode = routingMode === 'auto' ? routeStats.decision.toLowerCase().replace('-', '-') : routingMode;
    
    if (currentMode === 'multi-pickup') {
      return {
        totalDistance: routeStats.routeKmA?.toFixed(2) || routeData?.totalDistance,
        estimatedTime: (routeStats.timeA * 60)?.toFixed(0) || routeData?.estimatedTime,
        origins: routeStats.vehiclesA || routeData?.origins,
        totalQuantity: routeData?.totalQuantity,
        vehicles: routeStats.vehiclesA
      };
    } else {
      return {
        totalDistance: routeStats.routeKmB?.toFixed(2) || routeData?.totalDistance,
        estimatedTime: (routeStats.timeB * 60)?.toFixed(0) || routeData?.estimatedTime,
        origins: routeData?.origins,
        totalQuantity: routeData?.totalQuantity,
        vehicles: routeStats.vehiclesB
      };
    }
  };

  const haversineDistance = (point1, point2) => {
    const R = 6371; // Earth's radius in km
    const dLat = toRad(point2.lat - point1.lat);
    const dLon = toRad(point2.lon - point1.lon);
    const lat1 = toRad(point1.lat);
    const lat2 = toRad(point2.lat);

    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.sin(dLon/2) * Math.sin(dLon/2) * 
              Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const toRad = (value) => value * Math.PI / 180;

  useEffect(() => {
    const fetchRouteData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/route-data`);
        if (!response.ok) {
          throw new Error('Failed to fetch route data');
        }
        const data = await response.json();
        
        setDestinations(data.destinations);
        
        if (data.destinations.length > 0) {
          setSelectedDestination(data.destinations[0]);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching route data:', err);
        setError('Failed to load route data. Make sure the API server is running.');
        setLoading(false);
      }
    };

    fetchRouteData();
  }, []);

  useEffect(() => {
    if (!selectedDestination) return;

    const fetchDestinationData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/route-data/${selectedDestination}`);
        if (!response.ok) {
          throw new Error('Failed to fetch destination data');
        }
        const data = await response.json();

        setCurrentData(data);

        // Update route data
        setRouteData({
          totalDistance: data.statistics.total_distance,
          estimatedTime: data.statistics.estimated_time,
          origins: data.statistics.origin_count,
          totalQuantity: data.statistics.total_quantity,
        });

        setTransferDetails(data.transfers);

        // Calculate routing strategy with 2-hour grace period
        calculateRouteStats(data);

        // Initialize or update map
        if (mapContainer.current && !map.current) {
          initializeMap(data);
        } else if (map.current) {
          updateMapForDestination(data);
        }

      } catch (err) {
        console.error('Error fetching destination data:', err);
        setError('Failed to load destination data');
      }
    };

    fetchDestinationData();
  }, [selectedDestination]);

  useEffect(() => {
    if (currentData && map.current) {
      updateMapForDestination(currentData);
    }
  }, [routingMode]);

  const initializeMap = (data) => {
    const destLocation = data.locations[selectedDestination];
    if (!destLocation) return;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [destLocation.lon, destLocation.lat],
        zoom: 12,
      });

      // Simple load event
      map.current.on('load', () => {
        setTimeout(() => {
          updateMapForDestination(data);
        }, 1000);
      });

      map.current.on('error', (e) => {
        console.error('Mapbox error:', e);
      });
    } catch (error) {
      console.error('Error initializing map:', error);
      setError('Failed to initialize map. Please check your internet connection.');
    }
  };

  const updateMapForDestination = (data) => {
    if (!map.current || !selectedDestination) return;

    // Clear existing markers and routes
    const existingMarkers = document.querySelectorAll('.mapboxgl-marker');
    existingMarkers.forEach(marker => marker.remove());

    // Remove existing route layers and sources
    try {
      const existingLayers = map.current.getStyle()?.layers || [];
      existingLayers.forEach(layer => {
        if (layer.id.startsWith('route-')) {
          try {
            if (map.current.getLayer(layer.id)) {
              map.current.removeLayer(layer.id);
            }
            if (map.current.getSource(layer.id)) {
              map.current.removeSource(layer.id);
            }
          } catch (e) {
            console.warn('Error removing layer/source:', e);
          }
        }
      });
    } catch (e) {
      console.warn('Error accessing map style:', e);
    }

    // Add destination marker
    const destLocation = data.locations[selectedDestination];
    if (!destLocation) return;

    new mapboxgl.Marker({ color: 'red' })
      .setLngLat([destLocation.lon, destLocation.lat])
      .setPopup(new mapboxgl.Popup().setHTML(`<strong>Destination: ${selectedDestination}</strong><br/>${destLocation.city || 'Unknown City'}`))
      .addTo(map.current);

    const colors = ['#3388ff', '#ff8833', '#33ff88', '#ff3388', '#8833ff'];
    const origins = routeStats?.sortedOrigins || data.origins;

    if (routingMode === 'multi-pickup' || (routingMode === 'auto' && routeStats?.decision === 'Multi-Pickup')) {
      // Draw multi-pickup route
      const waypoints = [...origins.map(origin => data.locations[origin]), destLocation];
      const coordinates = waypoints.map(loc => [loc.lon, loc.lat]);
      
      // Add origin markers in order
      origins.forEach((origin, index) => {
        const originLocation = data.locations[origin];
        if (originLocation) {
          new mapboxgl.Marker({ color: 'green' })
            .setLngLat([originLocation.lon, originLocation.lat])
            .setPopup(new mapboxgl.Popup().setHTML(`<strong>Stop ${index + 1}: ${origin}</strong><br/>${originLocation.city || 'Unknown City'}`))
            .addTo(map.current);
        }
      });

      // Draw sequential route
      for (let i = 0; i < coordinates.length - 1; i++) {
        drawRoute(
          { lon: coordinates[i][0], lat: coordinates[i][1] },
          { lon: coordinates[i + 1][0], lat: coordinates[i + 1][1] },
          '#3388ff',
          `route-${i}`
        );
      }
    } else {
      // Draw parallel routes
      origins.forEach((origin, index) => {
        const originLocation = data.locations[origin];
        if (originLocation) {
          new mapboxgl.Marker({ color: 'green' })
            .setLngLat([originLocation.lon, originLocation.lat])
            .setPopup(new mapboxgl.Popup().setHTML(`<strong>Origin: ${origin}</strong><br/>${originLocation.city || 'Unknown City'}`))
            .addTo(map.current);

          drawRoute(originLocation, destLocation, colors[index % colors.length], `route-${origin}`);
        }
      });
    }

    // Fit map to show all markers
    if (origins.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      bounds.extend([destLocation.lon, destLocation.lat]);
      origins.forEach(origin => {
        const loc = data.locations[origin];
        if (loc) bounds.extend([loc.lon, loc.lat]);
      });
      map.current.fitBounds(bounds, { padding: 50 });
    }
  };

  const drawRoute = async (origin, destination, color, routeId) => {
    try {
      const query = await fetch(
        `https://api.mapbox.com/directions/v5/mapbox/driving/${origin.lon},${origin.lat};${destination.lon},${destination.lat}?steps=true&geometries=geojson&access_token=${mapboxgl.accessToken}`,
        { method: 'GET' }
      );
      const json = await query.json();
      const data = json.routes[0];
      const route = data.geometry.coordinates;
      
      const geojson = {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: route
        }
      };

      // Add route source and layer
      if (map.current.getSource(routeId)) {
        map.current.getSource(routeId).setData(geojson);
      } else {
        map.current.addSource(routeId, {
          type: 'geojson',
          data: geojson
        });

        map.current.addLayer({
          id: routeId,
          type: 'line',
          source: routeId,
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': color,
            'line-width': 5,
            'line-opacity': 0.75
          }
        });
      }
    } catch (error) {
      console.error('Error drawing route:', error);
      // Fallback: draw straight line
      drawStraightLine(origin, destination, color, routeId);
    }
  };

  const drawStraightLine = (origin, destination, color, routeId) => {
    const geojson = {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [
          [origin.lon, origin.lat],
          [destination.lon, destination.lat]
        ]
      }
    };

    if (map.current.getSource(routeId)) {
      map.current.getSource(routeId).setData(geojson);
    } else {
      map.current.addSource(routeId, {
        type: 'geojson',
        data: geojson
      });

      map.current.addLayer({
        id: routeId,
        type: 'line',
        source: routeId,
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': color,
          'line-width': 3,
          'line-opacity': 0.75
        }
      });
    }
  };

  const handleDestinationChange = (event) => {
    setSelectedDestination(event.target.value);
  };

  const handleRoutingModeChange = (event) => {
    const newMode = event.target.value;
    setRoutingMode(newMode);
    
    // Recalculate stats when switching modes
    if (currentData) {
      if (newMode === 'auto') {
        // Reset to optimizer's choice
        const decision = (routeStats.timeB - routeStats.timeA) < GRACE_HOURS ? 
          'Multi-Pickup' : 'Parallel';
        setOptimizerChoice(decision);
        setRoutingMode(decision.toLowerCase());
      }
      // Update map with new mode
      updateMapForDestination(currentData);
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
        📍 Route Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
      )}

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>⚙️ Route Viewer</Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Destination Store</InputLabel>
              <Select
                value={selectedDestination}
                onChange={handleDestinationChange}
                label="Destination Store"
              >
                {destinations.map(dest => (
                  <MenuItem key={dest} value={dest}>{dest}</MenuItem>
                ))}
              </Select>
            </FormControl>

            {optimizerChoice && (
              <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold' }}>
                Optimizer choice: {optimizerChoice}
              </Typography>
            )}

            <Typography variant="subtitle2" gutterBottom>Routing Mode:</Typography>
            <RadioGroup value={routingMode} onChange={handleRoutingModeChange}>
              <FormControlLabel value="auto" control={<Radio />} label="Auto (optimizer)" />
              <FormControlLabel value="multi-pickup" control={<Radio />} label="Multi-Pickup" />
              <FormControlLabel value="parallel" control={<Radio />} label="Parallel" />
            </RadioGroup>
          </Paper>

          {/* Route Statistics */}
          {routeData && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Route Statistics</Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <NavigationIcon sx={{ mr: 1, color: '#0061f2' }} />
                <Typography variant="body2">
                  Distance: {getCurrentRouteStats().totalDistance} km
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimerIcon sx={{ mr: 1, color: '#4caf50' }} />
                <Typography variant="body2">
                  ETA: {getCurrentRouteStats().estimatedTime} min
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TruckIcon sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="body2">
                  Vehicles: {getCurrentRouteStats().vehicles || getCurrentRouteStats().origins}
                </Typography>
              </Box>
              
              <Typography variant="body2">
                Total Quantity: {getCurrentRouteStats().totalQuantity} units
              </Typography>
            </Paper>
          )}
        </Grid>

        {/* Map */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 0, height: 600, overflow: 'hidden' }}>
            <div
              ref={mapContainer}
              style={{ width: '100%', height: '100%' }}
            />
          </Paper>
        </Grid>

        {/* Transfer Details Table */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: 600, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>Transfer Details</Typography>
            {transferDetails.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Product</strong></TableCell>
                      <TableCell><strong>From</strong></TableCell>
                      <TableCell><strong>Qty</strong></TableCell>
                      <TableCell><strong>Dist</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {transferDetails.map((transfer, index) => (
                      <TableRow key={index}>
                        <TableCell>{transfer.product_id}</TableCell>
                        <TableCell>{transfer.from_store}</TableCell>
                        <TableCell>{transfer.quantity}</TableCell>
                        <TableCell>{transfer.road_km}km</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography variant="body2" color="textSecondary">
                No transfer data available.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default MapRoute;
