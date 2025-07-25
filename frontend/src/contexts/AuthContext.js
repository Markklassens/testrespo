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

  // Initialize intelligent connection using IntelligentBackendConnector
  useEffect(() => {
    const initializeConnection = async () => {
      try {
        console.log('🚀 Initializing intelligent backend connection...');
        setConnectionStatus('checking');
        
        // Set up connection status listener
        const connectionCallback = (isConnected, url, error) => {
          if (isConnected) {
            // Configure axios with the working URL
            axios.defaults.baseURL = url;
            axios.defaults.timeout = 30000;
            axios.defaults.headers.common['Content-Type'] = 'application/json';
            
            setConnectionStatus('connected');
            setBackendUrl(url);
            setConnectionAttempts(0);
            console.log('✅ Backend connection established:', url);
            toast.success('Connected to backend', { 
              duration: 2000,
              id: 'connection-success',
            });
          } else {
            setConnectionStatus('disconnected');
            setConnectionAttempts(prev => prev + 1);
            console.error('❌ Backend connection lost:', error?.message || 'Unknown error');
          }
        };

        // Add connection listener
        intelligentConnector.onConnectionChange(connectionCallback);
        
        // Check if there's a manually configured URL in localStorage
        const manualUrl = localStorage.getItem('manualBackendUrl');
        let backendUrl;
        
        if (manualUrl) {
          console.log('📌 Using manually configured URL:', manualUrl);
          backendUrl = manualUrl;
          
          // Test the manual URL first
          const testResult = await intelligentConnector.testBackendUrl(manualUrl);
          if (testResult.success) {
            // Configure axios directly with manual URL
            axios.defaults.baseURL = manualUrl;
            axios.defaults.timeout = 30000;
            axios.defaults.headers.common['Content-Type'] = 'application/json';
            
            intelligentConnector.currentUrl = manualUrl;
            intelligentConnector.isConnected = true;
            intelligentConnector.startHealthCheck();
            
            setBackendUrl(manualUrl);
            setConnectionStatus('connected');
            setConnectionAttempts(0);
            
            console.log('✅ Manual backend URL connection successful:', manualUrl);
            toast.success('Connected to backend (manual config)', { 
              duration: 2000,
              id: 'connection-success',
            });
          } else {
            console.warn('⚠️  Manual URL failed, falling back to intelligent detection');
            localStorage.removeItem('manualBackendUrl');
            backendUrl = await intelligentConnector.setupAxiosConfig();
          }
        } else {
          // Use intelligent connector for automatic detection
          await intelligentConnector.setupAxiosConfig();
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
        
        // Only show error toast if we haven't exceeded retry limit
        if (connectionAttempts < 3) {
          toast.error(`Connection failed. Retrying... (${connectionAttempts + 1}/3)`, {
            duration: 3000,
            id: 'connection-error',
          });
          
          // Retry after delay
          setTimeout(() => {
            initializeConnection();
          }, Math.min(2000 * Math.pow(2, connectionAttempts), 10000));
        } else {
          toast.error('Unable to connect to backend. Please refresh the page.', {
            duration: 8000,
            id: 'connection-max-retries',
          });
        }
      } finally {
        setLoading(false);
      }
    };

    // Only initialize if we don't have a connection
    if (connectionStatus !== 'connected') {
      initializeConnection();
    }
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
      
      // Check if there's a manually configured URL
      const manualUrl = localStorage.getItem('manualBackendUrl');
      if (manualUrl) {
        // Test the manual URL
        const testResult = await intelligentConnector.testBackendUrl(manualUrl);
        if (testResult.success) {
          axios.defaults.baseURL = manualUrl;
          intelligentConnector.currentUrl = manualUrl;
          intelligentConnector.isConnected = true;
          intelligentConnector.startHealthCheck();
          setBackendUrl(manualUrl);
          setConnectionStatus('connected');
          toast.success('Manual backend connection successful!');
          return;
        } else {
          console.warn('Manual URL failed, removing from storage');
          localStorage.removeItem('manualBackendUrl');
        }
      }
      
      // Fall back to intelligent connector
      await intelligentConnector.refreshConnection();
      setConnectionStatus('connected');
      toast.success('Connection test successful!');
    } catch (error) {
      setConnectionStatus('disconnected');
      toast.error('Connection test failed');
      throw error;
    }
  };

  const setManualBackendUrl = async (url) => {
    try {
      setConnectionStatus('checking');
      
      // Test the URL first
      const testResult = await intelligentConnector.testBackendUrl(url);
      if (testResult.success) {
        // Store as manual URL
        localStorage.setItem('manualBackendUrl', url);
        
        // Configure axios
        axios.defaults.baseURL = url;
        axios.defaults.timeout = 30000;
        axios.defaults.headers.common['Content-Type'] = 'application/json';
        
        // Update intelligent connector
        intelligentConnector.currentUrl = url;
        intelligentConnector.isConnected = true;
        intelligentConnector.startHealthCheck();
        
        setBackendUrl(url);
        setConnectionStatus('connected');
        
        toast.success('Manual backend URL configured successfully!');
        return true;
      } else {
        setConnectionStatus('disconnected');
        toast.error(`Failed to connect to ${url}: ${testResult.error}`);
        return false;
      }
    } catch (error) {
      setConnectionStatus('disconnected');
      toast.error('Failed to configure backend URL');
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
    setManualBackendUrl,
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