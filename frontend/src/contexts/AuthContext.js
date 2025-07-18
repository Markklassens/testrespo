import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import intelligentConnector from '../services/IntelligentBackendConnector';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [backendUrl, setBackendUrl] = useState(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  // Initialize intelligent connection
  useEffect(() => {
    const initializeConnection = async () => {
      try {
        console.log('🚀 Initializing intelligent backend connection...');
        setConnectionStatus('checking');
        
        // Force use the known working URL
        const workingUrl = 'https://cce2b6c3-1a87-4b89-ba91-78109b03f3ef.preview.emergentagent.com';
        
        // Configure axios directly
        axios.defaults.baseURL = workingUrl;
        axios.defaults.timeout = 30000;
        axios.defaults.headers.common['Content-Type'] = 'application/json';
        
        // Test the connection
        const testResponse = await axios.get('/api/health');
        console.log('✅ Direct connection test successful:', testResponse.status);
        
        setBackendUrl(workingUrl);
        setConnectionStatus('connected');
        setConnectionAttempts(0);
        
        console.log('✅ Backend connection established:', workingUrl);
        // Only show success toast on first connection, not on retries
        if (connectionAttempts === 0) {
          toast.success('Connected to backend', { 
            duration: 2000,
            id: 'connection-success',
          });
        }
        
        // Try to load user from token
        const token = localStorage.getItem('token');
        if (token) {
          try {
            const response = await axios.get('/api/auth/me', {
              headers: { Authorization: `Bearer ${token}` }
            });
            setUser(response.data);
          } catch (error) {
            console.log('Token invalid, removing...');
            localStorage.removeItem('token');
          }
        }
      } catch (error) {
        console.error('❌ Failed to establish backend connection:', error);
        setConnectionStatus('disconnected');
        setConnectionAttempts(prev => prev + 1);
        
        // Only show error toast if we haven't exceeded retry limit and it's not a repeated failure
        if (connectionAttempts < 3 && connectionStatus !== 'disconnected') {
          toast.error(`Connection failed. Retrying... (${connectionAttempts + 1}/3)`, {
            duration: 2000,
            id: 'connection-error', // Prevents duplicate toasts
          });
        }
        
        // Retry after delay, but with exponential backoff
        setTimeout(() => {
          if (connectionAttempts < 3) {
            initializeConnection();
          } else {
            toast.error('Unable to connect to backend. Please refresh the page if issues persist.', {
              duration: 5000,
              id: 'connection-max-retries',
            });
          }
        }, Math.min(2000 * Math.pow(2, connectionAttempts), 10000));
      } finally {
        setLoading(false);
      }
    };

    // Only initialize if we don't have a connection or if we're retrying
    if (connectionStatus !== 'connected' || connectionAttempts > 0) {
      initializeConnection();
    }

    // Cleanup - remove the intelligent connector listener for now
    return () => {
      // Empty cleanup
    };
  }, [connectionAttempts, connectionStatus]);

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setUser(userData);
      toast.success('Login successful!');
      
      return userData;
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post('/api/auth/register', userData);
      toast.success('Registration successful! Please check your email to verify your account.');
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      const message = error.response?.data?.detail || 'Registration failed';
      toast.error(message);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.success('Logged out successfully');
  };

  const verifyEmail = async (token) => {
    try {
      const response = await axios.post('/api/auth/verify-email', { token });
      toast.success('Email verified successfully!');
      return response.data;
    } catch (error) {
      console.error('Email verification error:', error);
      const message = error.response?.data?.detail || 'Email verification failed';
      toast.error(message);
      throw error;
    }
  };

  const forgotPassword = async (email) => {
    try {
      const response = await axios.post('/api/auth/forgot-password', { email });
      toast.success('Password reset email sent!');
      return response.data;
    } catch (error) {
      console.error('Forgot password error:', error);
      const message = error.response?.data?.detail || 'Failed to send reset email';
      toast.error(message);
      throw error;
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      const response = await axios.post('/api/auth/reset-password', { 
        token, 
        new_password: newPassword 
      });
      toast.success('Password reset successful!');
      return response.data;
    } catch (error) {
      console.error('Reset password error:', error);
      const message = error.response?.data?.detail || 'Password reset failed';
      toast.error(message);
      throw error;
    }
  };

  const testBackendConnection = async () => {
    try {
      setConnectionStatus('checking');
      await intelligentConnector.refreshConnection();
      setConnectionStatus('connected');
      toast.success('Connection test successful!');
    } catch (error) {
      setConnectionStatus('disconnected');
      toast.error('Connection test failed');
      throw error;
    }
  };

  const debugConnectivity = async () => {
    try {
      const connectionStatus = intelligentConnector.getConnectionStatus();
      const response = await axios.get('/api/debug/connectivity');
      
      return {
        frontend: {
          currentUrl: window.location.href,
          backendUrl: backendUrl,
          connectionStatus: connectionStatus,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        },
        backend: response.data
      };
    } catch (error) {
      return {
        frontend: {
          currentUrl: window.location.href,
          backendUrl: backendUrl,
          connectionStatus: intelligentConnector.getConnectionStatus(),
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        },
        backend: { error: error.message }
      };
    }
  };

  const value = {
    user,
    loading,
    connectionStatus,
    backendUrl,
    login,
    register,
    logout,
    verifyEmail,
    forgotPassword,
    resetPassword,
    testBackendConnection,
    debugConnectivity,
    // Additional utility functions
    refreshConnection: () => intelligentConnector.refreshConnection(),
    getConnectionStatus: () => intelligentConnector.getConnectionStatus(),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};