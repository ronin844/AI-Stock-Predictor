import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import jwtDecode from 'jwt-decode';

const AuthContext = createContext();

// Set the base URL for all axios requests
axios.defaults.baseURL = 'http://localhost:8088';

// Function to set the JWT token for subsequent requests
export const setAuthToken = (token) => {
  if (token) {
    // Apply the authorization token to every request if logged in
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    // Delete the auth header
    delete axios.defaults.headers.common['Authorization'];
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwtDecode(token);
        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          setUser({ username: decoded.sub, role: decoded.role });
          setAuthToken(token);
        } else {
          // Token is expired
          localStorage.removeItem('token');
          setToken(null);
          setAuthToken(null);
        }
      } catch (error) {
        console.error("Invalid token:", error);
        localStorage.removeItem('token');
        setToken(null);
        setAuthToken(null);
      }
    }
    setLoading(false);
  }, [token]);

  const login = async (username, password) => {
    try {
      console.log('Attempting login with:', { username, password });
      console.log('Base URL:', axios.defaults.baseURL);
      
      const response = await axios.post('/auth/token', { username, password });
      console.log('Login response:', response);
      
      const { token } = response.data;
      localStorage.setItem('token', token);
      setToken(token);
      const decoded = jwtDecode(token);
      setUser({ username: decoded.sub, role: decoded.role });
      setAuthToken(token);
      
      console.log('Login successful, user:', { username: decoded.sub, role: decoded.role });
    } catch (error) {
      console.error('Login error:', error);
      console.error('Error response:', error.response);
      throw new Error(error.response?.data || error.message || 'Login failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAuthToken(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      login, 
      logout, 
      isAuthenticated: !!user, 
      loading,
      role: user?.role 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
