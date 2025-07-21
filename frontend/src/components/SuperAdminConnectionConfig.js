import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  ServerIcon, 
  CircleStackIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ArrowPathIcon, 
  ExclamationTriangleIcon,
  PlusIcon,
  TrashIcon,
  CogIcon,
  WifiIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import axios from 'axios';

const SuperAdminConnectionConfig = ({ isOpen, onClose }) => {
  const { user, testBackendConnection, connectionStatus, backendUrl } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [testingUrl, setTestingUrl] = useState(null);
  const [customUrls, setCustomUrls] = useState([]);
  const [newUrl, setNewUrl] = useState('');
  const [urlType, setUrlType] = useState('backend'); // 'backend' or 'database'
  const [testResults, setTestResults] = useState({});
  const [connectionConfig, setConnectionConfig] = useState({
    backend_url: '',
    database_url: '',
    timeout: 10000,
    retry_attempts: 3
  });

  const isSuperAdmin = user?.user_type === 'superadmin';

  // Load stored configuration on component mount
  useEffect(() => {
    if (isOpen && isSuperAdmin) {
      loadStoredConfiguration();
    }
  }, [isOpen, isSuperAdmin]);

  const loadStoredConfiguration = () => {
    try {
      const stored = localStorage.getItem('superadmin_connection_config');
      if (stored) {
        const config = JSON.parse(stored);
        setConnectionConfig(config);
        setCustomUrls(config.custom_urls || []);
      }
      
      // Also load test results if available
      const storedResults = localStorage.getItem('connection_test_results');
      if (storedResults) {
        setTestResults(JSON.parse(storedResults));
      }
    } catch (error) {
      console.error('Error loading configuration:', error);
    }
  };

  const saveConfiguration = () => {
    try {
      const config = {
        ...connectionConfig,
        custom_urls: customUrls,
        last_updated: new Date().toISOString()
      };
      localStorage.setItem('superadmin_connection_config', JSON.stringify(config));
      toast.success('Configuration saved successfully');
    } catch (error) {
      console.error('Error saving configuration:', error);
      toast.error('Failed to save configuration');
    }
  };

  const addCustomUrl = () => {
    if (!newUrl.trim()) {
      toast.error('Please enter a valid URL');
      return;
    }

    try {
      new URL(newUrl); // Validate URL format
      const urlEntry = {
        id: Date.now(),
        url: newUrl.trim(),
        type: urlType,
        added_at: new Date().toISOString(),
        last_tested: null,
        status: 'untested'
      };
      
      setCustomUrls(prev => [...prev, urlEntry]);
      setNewUrl('');
      toast.success('URL added successfully');
    } catch (error) {
      toast.error('Please enter a valid URL format');
    }
  };

  const removeCustomUrl = (id) => {
    setCustomUrls(prev => prev.filter(url => url.id !== id));
    toast.success('URL removed');
  };

  const testSingleUrl = async (url) => {
    setTestingUrl(url);
    setIsLoading(true);

    try {
      const startTime = Date.now();
      
      // Test the URL based on type
      let testResult;
      if (url.type === 'backend') {
        testResult = await testBackendUrl(url.url);
      } else {
        testResult = await testDatabaseUrl(url.url);
      }
      
      const responseTime = Date.now() - startTime;
      
      const result = {
        ...testResult,
        responseTime,
        testedAt: new Date().toISOString()
      };

      // Update test results
      setTestResults(prev => ({
        ...prev,
        [url.url]: result
      }));

      // Update custom URLs status
      setCustomUrls(prev => prev.map(u => 
        u.id === url.id 
          ? { ...u, status: result.success ? 'success' : 'failed', last_tested: new Date().toISOString() }
          : u
      ));

      if (result.success) {
        toast.success(`✅ Connection successful (${responseTime}ms)`);
      } else {
        toast.error(`❌ Connection failed: ${result.error}`);
      }

    } catch (error) {
      console.error('Test error:', error);
      toast.error(`Test failed: ${error.message}`);
    } finally {
      setTestingUrl(null);
      setIsLoading(false);
    }
  };

  const testBackendUrl = async (url) => {
    try {
      const response = await axios.get(`${url}/api/health`, {
        timeout: connectionConfig.timeout
      });
      
      return {
        success: true,
        status: response.status,
        data: response.data,
        error: null
      };
    } catch (error) {
      return {
        success: false,
        status: error.response?.status || 'Network Error',
        data: null,
        error: error.response?.statusText || error.message
      };
    }
  };

  const testDatabaseUrl = async (dbUrl) => {
    try {
      // For database URLs, we'll test through our backend API
      const response = await axios.post('/api/superadmin/test-database', {
        database_url: dbUrl
      });
      
      return {
        success: true,
        status: 200,
        data: response.data,
        error: null
      };
    } catch (error) {
      return {
        success: false,
        status: error.response?.status || 'Network Error',
        data: null,
        error: error.response?.data?.detail || error.message
      };
    }
  };

  const applyConfiguration = async (url) => {
    setIsLoading(true);
    
    try {
      if (url.type === 'backend') {
        // Apply backend configuration
        axios.defaults.baseURL = url.url;
        
        // Test the new configuration
        const testResult = await testBackendUrl(url.url);
        
        if (testResult.success) {
          // Update connection config
          setConnectionConfig(prev => ({
            ...prev,
            backend_url: url.url
          }));
          
          saveConfiguration();
          toast.success('✅ Backend URL applied successfully!');
          
          // Refresh the main connection
          await testBackendConnection();
        } else {
          throw new Error(testResult.error);
        }
      } else {
        // Apply database configuration through backend API
        const response = await axios.post('/api/superadmin/update-database-config', {
          database_url: url.url
        });
        
        setConnectionConfig(prev => ({
          ...prev,
          database_url: url.url
        }));
        
        saveConfiguration();
        toast.success('✅ Database configuration updated successfully!');
      }
      
    } catch (error) {
      console.error('Apply configuration error:', error);
      toast.error(`❌ Failed to apply configuration: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testAllUrls = async () => {
    setIsLoading(true);
    
    try {
      const results = {};
      
      for (const url of customUrls) {
        const startTime = Date.now();
        let testResult;
        
        if (url.type === 'backend') {
          testResult = await testBackendUrl(url.url);
        } else {
          testResult = await testDatabaseUrl(url.url);
        }
        
        results[url.url] = {
          ...testResult,
          responseTime: Date.now() - startTime,
          testedAt: new Date().toISOString()
        };
      }
      
      setTestResults(results);
      localStorage.setItem('connection_test_results', JSON.stringify(results));
      
      const successCount = Object.values(results).filter(r => r.success).length;
      const totalCount = Object.keys(results).length;
      
      toast.success(`✅ Tested ${totalCount} URLs - ${successCount} successful`);
      
    } catch (error) {
      console.error('Test all error:', error);
      toast.error('Failed to test all URLs');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !isSuperAdmin) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CogIcon className="h-6 w-6 text-purple-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Super Admin Connection Configuration
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XCircleIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Current Status */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3 flex items-center">
              <WifiIcon className="h-5 w-5 mr-2" />
              Current Connection Status
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-green-100 text-green-600' :
                  connectionStatus === 'checking' ? 'bg-yellow-100 text-yellow-600' :
                  'bg-red-100 text-red-600'
                }`}>
                  {connectionStatus === 'connected' ? <CheckCircleIcon className="h-5 w-5" /> :
                   connectionStatus === 'checking' ? <ArrowPathIcon className="h-5 w-5 animate-spin" /> :
                   <XCircleIcon className="h-5 w-5" />}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Backend Status</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{connectionStatus}</p>
                </div>
              </div>
              <div className="text-sm">
                <p className="text-gray-900 dark:text-white font-medium">Current URL:</p>
                <p className="text-gray-500 dark:text-gray-400 break-all">{backendUrl || 'Not set'}</p>
              </div>
            </div>
          </div>

          {/* Add New URL */}
          <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <PlusIcon className="h-5 w-5 mr-2" />
              Add New Connection URL
            </h3>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="url"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  placeholder="https://example.com or postgresql://user:pass@host:port/db"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white"
                />
              </div>
              <div>
                <select
                  value={urlType}
                  onChange={(e) => setUrlType(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white"
                >
                  <option value="backend">Backend API</option>
                  <option value="database">Database</option>
                </select>
              </div>
              <button
                onClick={addCustomUrl}
                disabled={!newUrl.trim()}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Add</span>
              </button>
            </div>
          </div>

          {/* Custom URLs List */}
          <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <ServerIcon className="h-5 w-5 mr-2" />
                Custom URLs ({customUrls.length})
              </h3>
              {customUrls.length > 0 && (
                <button
                  onClick={testAllUrls}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                >
                  <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  <span>Test All</span>
                </button>
              )}
            </div>

            {customUrls.length === 0 ? (
              <div className="text-center py-8">
                <ServerIcon className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">No custom URLs added yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {customUrls.map((url) => {
                  const testResult = testResults[url.url];
                  return (
                    <div
                      key={url.id}
                      className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              url.type === 'backend' 
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                                : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                            }`}>
                              {url.type === 'backend' ? 'Backend' : 'Database'}
                            </span>
                            <div className={`h-2 w-2 rounded-full ${
                              url.status === 'success' ? 'bg-green-500' :
                              url.status === 'failed' ? 'bg-red-500' :
                              'bg-gray-300'
                            }`} />
                          </div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white mt-1 break-all">
                            {url.url}
                          </p>
                          {testResult && (
                            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                              {testResult.success ? (
                                <span className="text-green-600 dark:text-green-400">
                                  ✅ Response: {testResult.responseTime}ms
                                </span>
                              ) : (
                                <span className="text-red-600 dark:text-red-400">
                                  ❌ Error: {testResult.error}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => testSingleUrl(url)}
                            disabled={isLoading || testingUrl === url}
                            className="p-2 text-blue-600 hover:text-blue-800 disabled:opacity-50"
                            title="Test URL"
                          >
                            <ArrowPathIcon className={`h-4 w-4 ${testingUrl === url ? 'animate-spin' : ''}`} />
                          </button>
                          {testResult && testResult.success && (
                            <button
                              onClick={() => applyConfiguration(url)}
                              disabled={isLoading}
                              className="p-2 text-green-600 hover:text-green-800 disabled:opacity-50"
                              title="Apply Configuration"
                            >
                              <CheckCircleIcon className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => removeCustomUrl(url.id)}
                            className="p-2 text-red-600 hover:text-red-800"
                            title="Remove URL"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Configuration Settings */}
          <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <CogIcon className="h-5 w-5 mr-2" />
              Connection Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Timeout (ms)
                </label>
                <input
                  type="number"
                  value={connectionConfig.timeout}
                  onChange={(e) => setConnectionConfig(prev => ({
                    ...prev,
                    timeout: parseInt(e.target.value)
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Retry Attempts
                </label>
                <input
                  type="number"
                  value={connectionConfig.retry_attempts}
                  onChange={(e) => setConnectionConfig(prev => ({
                    ...prev,
                    retry_attempts: parseInt(e.target.value)
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white"
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={saveConfiguration}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
            >
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuperAdminConnectionConfig;