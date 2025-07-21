class IntelligentBackendConnector {
  constructor() {
    this.currentUrl = null;
    this.testResults = {};
    this.isConnected = false;
    this.retryCount = 0;
    this.maxRetries = 3;
    this.connectionCallbacks = [];
    this.healthCheckInterval = null;
    this.healthCheckEnabled = false;
  }

  // Start periodic health checks (only when connected)
  startHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    
    this.healthCheckEnabled = true;
    this.healthCheckInterval = setInterval(async () => {
      if (this.isConnected && this.currentUrl) {
        try {
          await this.testBackendUrl(this.currentUrl, 3000);
        } catch (error) {
          console.log('🔄 Health check failed, attempting reconnection...');
          this.isConnected = false;
          this.connectionCallbacks.forEach(callback => callback(false, this.currentUrl, error));
          
          // Try to reconnect
          setTimeout(async () => {
            try {
              await this.reconnect();
            } catch (reconnectError) {
              console.error('❌ Health check reconnection failed:', reconnectError);
            }
          }, 5000);
        }
      }
    }, 30000); // Check every 30 seconds
  }

  // Stop health checks
  stopHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    this.healthCheckEnabled = false;
  }

  // Generate possible backend URLs based on current environment
  generatePossibleUrls() {
    const currentHost = window.location.hostname;
    const currentProtocol = window.location.protocol;
    const currentPort = window.location.port;
    
    const urls = [];
    
    // Add stored working URL if available (prioritize this)
    const storedUrl = localStorage.getItem('workingBackendUrl');
    if (storedUrl) {
      urls.unshift(storedUrl);
    }
    
    // Add environment variable if available
    const envBackendUrl = process.env.REACT_APP_BACKEND_URL || window.REACT_APP_BACKEND_URL;
    if (envBackendUrl) {
      urls.unshift(envBackendUrl);
    }
    
    // Add the current known working URL
    urls.push('https://ead17737-3aad-4c63-83bd-251d24940a74.preview.emergentagent.com');
    
    // Also add the localhost option (current backend)
    urls.push('http://localhost:8001');
    
    // Extract base domain patterns
    if (currentHost.includes('github.dev')) {
      // GitHub Codespace patterns
      const basePattern = currentHost.replace('-3000.app.github.dev', '');
      urls.push(`https://${basePattern}-8001.app.github.dev`);
      urls.push(`https://${basePattern}-8001.github.dev`);
    }
    
    if (currentHost.includes('emergentagent.com')) {
      // Emergentagent patterns
      const basePattern = currentHost.replace(/^.*?\./, '');
      urls.push(`https://${basePattern}`);
      urls.push(`https://api.${basePattern}`);
    }
    
    if (currentHost.includes('localhost') || currentHost.includes('127.0.0.1')) {
      // Local development
      urls.push('http://localhost:8001');
      urls.push('https://localhost:8001');
      urls.push('http://127.0.0.1:8001');
    }
    
    // Remove duplicates and return
    return [...new Set(urls)];
  }

  // Test a single backend URL
  async testBackendUrl(url, timeout = 5000) {
    const startTime = Date.now();
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(`${url}/api/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        mode: 'cors',
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return { 
          success: true, 
          data, 
          status: response.status,
          responseTime: Date.now() - startTime
        };
      } else {
        return { 
          success: false, 
          error: `HTTP ${response.status}: ${response.statusText}`,
          status: response.status 
        };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.name === 'AbortError' ? 'Timeout' : error.message,
        status: 'Network Error'
      };
    }
  }

  // Find the best working backend URL
  async findWorkingBackendUrl() {
    const possibleUrls = this.generatePossibleUrls();
    console.log('🔍 Testing possible backend URLs:', possibleUrls);
    
    const testPromises = possibleUrls.map(async (url) => {
      const startTime = Date.now();
      const result = await this.testBackendUrl(url);
      return { url, ...result, responseTime: Date.now() - startTime };
    });
    
    const results = await Promise.all(testPromises);
    this.testResults = results.reduce((acc, result) => {
      acc[result.url] = result;
      return acc;
    }, {});
    
    // Find the best working URL (prioritize success and response time)
    const workingUrls = results.filter(r => r.success);
    
    if (workingUrls.length === 0) {
      throw new Error('No working backend URL found');
    }
    
    // Sort by response time (fastest first)
    workingUrls.sort((a, b) => a.responseTime - b.responseTime);
    
    const bestUrl = workingUrls[0].url;
    console.log('✅ Best backend URL found:', bestUrl);
    
    // Store the working URL
    localStorage.setItem('workingBackendUrl', bestUrl);
    localStorage.setItem('backendTestResults', JSON.stringify(this.testResults));
    
    return bestUrl;
  }

  // Set up axios with the correct backend URL
  async setupAxiosConfig() {
    try {
      const backendUrl = await this.findWorkingBackendUrl();
      
      // Configure axios
      const axios = require('axios');
      
      // Clear any existing configuration
      delete axios.defaults.baseURL;
      delete axios.defaults.headers.common['Authorization'];
      
      // Set new configuration
      axios.defaults.baseURL = backendUrl;
      axios.defaults.timeout = 30000;
      axios.defaults.headers.common['Content-Type'] = 'application/json';
      
      // Test the configuration immediately
      console.log('🧪 Testing axios configuration with:', backendUrl);
      const testResponse = await axios.get('/api/health');
      console.log('✅ Axios test successful:', testResponse.status);
      
      // Add request interceptor for logging
      axios.interceptors.request.use(
        (config) => {
          console.log('📤 API Request:', config.method?.toUpperCase(), config.url);
          return config;
        },
        (error) => {
          console.error('📤 Request Error:', error);
          return Promise.reject(error);
        }
      );
      
      // Add response interceptor for logging and error handling
      axios.interceptors.response.use(
        (response) => {
          console.log('📥 API Response:', response.status, response.config.url);
          return response;
        },
        async (error) => {
          console.error('📥 Response Error:', error);
          
          // Only attempt reconnection for actual network errors (not 401, 403, etc.)
          const isNetworkError = error.code === 'NETWORK_ERROR' || 
                                error.code === 'ECONNREFUSED' || 
                                !error.response;
          
          if (isNetworkError && this.isConnected) {
            console.log('🔄 Network error detected, attempting to reconnect...');
            this.isConnected = false;
            
            // Notify listeners about disconnection
            this.connectionCallbacks.forEach(callback => callback(false, this.currentUrl, error));
            
            // Attempt to reconnect after a delay
            setTimeout(async () => {
              try {
                await this.reconnect();
              } catch (reconnectError) {
                console.error('❌ Reconnection failed:', reconnectError);
              }
            }, 3000);
          }
          
          return Promise.reject(error);
        }
      );
      
      this.currentUrl = backendUrl;
      this.isConnected = true;
      this.retryCount = 0;
      
      // Start health checks only when connected
      this.startHealthCheck();
      
      // Notify all listeners
      this.connectionCallbacks.forEach(callback => callback(true, backendUrl));
      
      return backendUrl;
    } catch (error) {
      console.error('❌ Failed to setup backend connection:', error);
      this.isConnected = false;
      this.stopHealthCheck();
      
      // Notify all listeners
      this.connectionCallbacks.forEach(callback => callback(false, null, error));
      
      throw error;
    }
  }

  // Reconnect with exponential backoff
  async reconnect() {
    if (this.retryCount >= this.maxRetries) {
      console.error('❌ Max reconnection attempts reached');
      this.stopHealthCheck();
      return false;
    }
    
    this.retryCount++;
    const delay = Math.min(1000 * Math.pow(2, this.retryCount), 10000);
    
    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.retryCount}/${this.maxRetries})`);
    
    await new Promise(resolve => setTimeout(resolve, delay));
    
    try {
      await this.setupAxiosConfig();
      console.log('✅ Reconnection successful');
      return true;
    } catch (error) {
      console.error('❌ Reconnection failed:', error);
      return false;
    }
  }

  // Add connection status listener
  onConnectionChange(callback) {
    this.connectionCallbacks.push(callback);
  }

  // Remove connection status listener
  offConnectionChange(callback) {
    this.connectionCallbacks = this.connectionCallbacks.filter(cb => cb !== callback);
  }

  // Get current connection status
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      currentUrl: this.currentUrl,
      testResults: this.testResults,
      retryCount: this.retryCount
    };
  }

  // Force refresh connection
  async refreshConnection() {
    console.log('🔄 Forcing connection refresh...');
    this.stopHealthCheck();
    localStorage.removeItem('workingBackendUrl');
    localStorage.removeItem('backendTestResults');
    this.isConnected = false;
    this.retryCount = 0;
    return await this.setupAxiosConfig();
  }
}

// Create singleton instance
const intelligentConnector = new IntelligentBackendConnector();

export default intelligentConnector;