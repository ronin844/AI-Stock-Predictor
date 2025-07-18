import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import Forecast from './Forecast';
import LoginPage from './LoginPage';
import Dashboard from './Dashboard';
import MapRoute from './MapRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#0061f2',
      dark: '#0044ab',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
      dark: '#1a1f2d',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontSize: '1rem',
          padding: '0.5rem 1.5rem',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
});

function Home() {
  return (
    <div className="container">
      <h2>Welcome to AI Stock Predictor</h2>
      <p>Use the navigation to access the forecast page.</p>
    </div>
  );
}

function PrivateRoute({ children }) {
  const auth = useAuth();
  return auth.isAuthenticated ? children : <Navigate to="/login" />;
}

function Navigation() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  if (isLoginPage) {
    return null;
  }

  return (
    <nav className="main-nav">
      <Link to="/dashboard">Dashboard</Link>
      <Link to="/forecast">Forecast</Link>
      <Link to="/routes">Routes</Link>
      <Link to="/logout" style={{ float: 'right' }}>Logout</Link>
    </nav>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Navigation />
          <main>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/" element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              } />
              <Route path="/dashboard" element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              } />
              <Route path="/forecast" element={
                <PrivateRoute>
                  <Forecast />
                </PrivateRoute>
              } />
              <Route path="/routes" element={
                <PrivateRoute>
                  <MapRoute />
                </PrivateRoute>
              } />
              <Route path="/logout" element={<Logout />} />
            </Routes>
          </main>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

function Logout() {
  const auth = useAuth();
  React.useEffect(() => {
    auth.logout();
  }, [auth]);
  return <Navigate to="/login" />;
}

export default App;
