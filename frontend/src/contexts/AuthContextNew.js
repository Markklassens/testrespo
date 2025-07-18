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
        
        const workingUrl = await intelligentConnector.setupAxiosConfig();
        
        setBackendUrl(workingUrl);
        setConnectionStatus('connected');
        setConnectionAttempts(0);
        
        console.log('✅ Backend connection established:', workingUrl);
        toast.success('Backend connection established!');
        
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
        
        toast.error('Failed to connect to backend. Retrying...', {
          duration: 5000,
        });
        
        // Retry after delay
        setTimeout(() => {
          if (connectionAttempts < 5) {
            initializeConnection();
          } else {
            toast.error('Maximum connection attempts reached. Please refresh the page.');
          }
        }, 2000 + (connectionAttempts * 1000));
      } finally {
        setLoading(false);
      }
    };

    initializeConnection();

    // Listen for connection changes
    const handleConnectionChange = (isConnected, url, error) => {
      setConnectionStatus(isConnected ? 'connected' : 'disconnected');
      setBackendUrl(url);
      
      if (isConnected) {
        toast.success('Backend reconnected!');
        setConnectionAttempts(0);
      } else {
        toast.error('Backend connection lost');
      }
    };

    intelligentConnector.onConnectionChange(handleConnectionChange);

    // Cleanup
    return () => {
      intelligentConnector.offConnectionChange(handleConnectionChange);
    };
  }, [connectionAttempts]);

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