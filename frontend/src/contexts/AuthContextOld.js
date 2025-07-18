import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Enhanced axios configuration with debugging
axios.defaults.baseURL = API_URL;
axios.defaults.timeout = 30000; // 30 second timeout
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Enhanced logging for debugging
const logRequest = (config) => {
  console.log('API Request:', {
    url: config.url,
    method: config.method,
    baseURL: config.baseURL,
    headers: config.headers,
    data: config.data
  });
};

const logResponse = (response) => {
  console.log('API Response:', {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
    data: response.data
  });
};

const logError = (error) => {
  console.error('API Error:', {
    message: error.message,
    code: error.code,
    config: error.config,
    response: error.response
  });
};

// Add request interceptor with enhanced debugging
axios.interceptors.request.use(
  (config) => {
    logRequest(config);
    
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add debug headers
    config.headers['X-Frontend-Version'] = '2.0.0';
    config.headers['X-Request-Time'] = new Date().toISOString();
    
    return config;
  },
  (error) => {
    logError(error);
    return Promise.reject(error);
  }
);

// Add response interceptor with enhanced error handling
axios.interceptors.response.use(
  (response) => {
    logResponse(response);
    return response;
  },
  (error) => {
    logError(error);
    
    if (error.response?.status === 401) {
      toast.error('Session expired. Please login again.');
      localStorage.removeItem('token');
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      toast.error('Access denied. You don\'t have permission to perform this action.');
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
      toast.error('Network error. Please check your connection and try again.');
    } else if (error.code === 'TIMEOUT') {
      toast.error('Request timeout. Please try again.');
    } else if (!error.response) {
      toast.error('Unable to connect to server. Please check your connection.');
    }
    
    return Promise.reject(error);
  }
);

// Test backend connectivity
const testBackendConnection = async () => {
  try {
    const response = await axios.get('/api/health');
    console.log('Backend health check successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Backend health check failed:', error);
    throw error;
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('checking');

  // Check backend connectivity on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        await testBackendConnection();
        setConnectionStatus('connected');
      } catch (error) {
        setConnectionStatus('disconnected');
        toast.error('Unable to connect to backend server');
      }
    };

    checkConnection();
    
    // Check connection every 5 minutes
    const interval = setInterval(checkConnection, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/me');
      setUser(response.data);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Error fetching user:', error);
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
      } else {
        setConnectionStatus('disconnected');
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      await fetchUser();
      setConnectionStatus('connected');
      toast.success('Login successful!');
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      if (error.code === 'NETWORK_ERROR' || !error.response) {
        setConnectionStatus('disconnected');
        return { 
          success: false, 
          error: 'Unable to connect to server. Please check your connection.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post('/api/auth/register', userData);
      setConnectionStatus('connected');
      toast.success('Registration successful! Please check your email for verification.');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      if (error.code === 'NETWORK_ERROR' || !error.response) {
        setConnectionStatus('disconnected');
        return { 
          success: false, 
          error: 'Unable to connect to server. Please check your connection.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const verifyEmail = async (token) => {
    try {
      const response = await axios.post('/api/auth/verify-email', { token });
      setConnectionStatus('connected');
      toast.success('Email verified successfully!');
      return { success: true, message: response.data.message };
    } catch (error) {
      console.error('Email verification error:', error);
      if (error.code === 'NETWORK_ERROR' || !error.response) {
        setConnectionStatus('disconnected');
        return { 
          success: false, 
          error: 'Unable to connect to server. Please check your connection.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Verification failed' 
      };
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      const response = await axios.post('/api/auth/request-password-reset', { email });
      setConnectionStatus('connected');
      toast.success('Password reset email sent!');
      return { success: true, message: response.data.message };
    } catch (error) {
      console.error('Password reset request error:', error);
      if (error.code === 'NETWORK_ERROR' || !error.response) {
        setConnectionStatus('disconnected');
        return { 
          success: false, 
          error: 'Unable to connect to server. Please check your connection.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Request failed' 
      };
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      const response = await axios.post('/api/auth/reset-password', { 
        token, 
        new_password: newPassword 
      });
      setConnectionStatus('connected');
      toast.success('Password reset successful!');
      return { success: true, message: response.data.message };
    } catch (error) {
      console.error('Password reset error:', error);
      if (error.code === 'NETWORK_ERROR' || !error.response) {
        setConnectionStatus('disconnected');
        return { 
          success: false, 
          error: 'Unable to connect to server. Please check your connection.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Password reset failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    toast.success('Logged out successfully!');
  };

  // Debug function for testing connectivity
  const debugConnectivity = async () => {
    try {
      const response = await axios.get('/api/debug/connectivity');
      console.log('Debug connectivity:', response.data);
      return response.data;
    } catch (error) {
      console.error('Debug connectivity error:', error);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    connectionStatus,
    login,
    register,
    verifyEmail,
    requestPasswordReset,
    resetPassword,
    logout,
    fetchUser,
    testBackendConnection,
    debugConnectivity
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};