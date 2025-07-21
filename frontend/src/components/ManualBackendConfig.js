import React, { useState, useEffect } from 'react';
import { XMarkIcon, CheckCircleIcon, XCircleIcon, CogIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import axios from 'axios';

const ManualBackendConfig = ({ isOpen, onClose, onUrlChange }) => {
  const [customUrl, setCustomUrl] = useState('');
  const [isTestingUrl, setIsTestingUrl] = useState(false);
  const [testResults, setTestResults] = useState({});
  const [currentUrl, setCurrentUrl] = useState('');
  const [savedUrls, setSavedUrls] = useState([]);

  // Only allow in development environment
  const isDev = process.env.NODE_ENV === 'development';

  useEffect(() => {
    // Load saved URLs and current URL from localStorage
    const saved = JSON.parse(localStorage.getItem('savedBackendUrls') || '[]');
    const current = localStorage.getItem('currentBackendUrl') || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    
    setSavedUrls(saved);
    setCurrentUrl(current);
    setCustomUrl(current);
  }, [isOpen]);

  const testBackendUrl = async (url) => {
    if (!url.trim()) {
      toast.error('Please enter a backend URL');
      return false;
    }

    // Clean and validate URL
    let cleanUrl = url.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = `https://${cleanUrl}`;
    }
    
    // Remove trailing slash
    cleanUrl = cleanUrl.replace(/\/$/, '');

    setIsTestingUrl(true);
    const startTime = Date.now();

    try {
      // Test the health endpoint
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(`${cleanUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        mode: 'cors',
      });

      clearTimeout(timeoutId);
      
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        const result = {
          success: true,
          status: response.status,
          responseTime,
          data,
          url: cleanUrl
        };
        
        setTestResults({ [cleanUrl]: result });
        toast.success(`✅ Backend connected successfully! (${responseTime}ms)`);
        return { success: true, url: cleanUrl, data };
      } else {
        const result = {
          success: false,
          status: response.status,
          error: `HTTP ${response.status}: ${response.statusText}`,
          responseTime,
          url: cleanUrl
        };
        
        setTestResults({ [cleanUrl]: result });
        toast.error(`❌ Connection failed: ${result.error}`);
        return { success: false, error: result.error };
      }
    } catch (error) {
      const result = {
        success: false,
        error: error.name === 'AbortError' ? 'Connection timeout' : error.message,
        responseTime: Date.now() - startTime,
        url: cleanUrl
      };
      
      setTestResults({ [cleanUrl]: result });
      toast.error(`❌ Connection failed: ${result.error}`);
      return { success: false, error: result.error };
    } finally {
      setIsTestingUrl(false);
    }
  };

  const handleTestConnection = async () => {
    await testBackendUrl(customUrl);
  };

  const handleSaveAndUse = async () => {
    const testResult = await testBackendUrl(customUrl);
    
    if (testResult.success) {
      const { url } = testResult;
      
      // Save to localStorage
      localStorage.setItem('currentBackendUrl', url);
      
      // Add to saved URLs if not already present
      const saved = JSON.parse(localStorage.getItem('savedBackendUrls') || '[]');
      if (!saved.includes(url)) {
        saved.unshift(url); // Add to beginning
        if (saved.length > 5) saved.pop(); // Keep only 5 recent URLs
        localStorage.setItem('savedBackendUrls', JSON.stringify(saved));
        setSavedUrls(saved);
      }
      
      // Configure axios with new URL
      axios.defaults.baseURL = url;
      
      setCurrentUrl(url);
      
      // Notify parent component
      if (onUrlChange) {
        onUrlChange(url);
      }
      
      toast.success('✅ Backend URL saved and applied!');
      onClose();
    }
  };

  const handleUseSavedUrl = async (url) => {
    setCustomUrl(url);
    const testResult = await testBackendUrl(url);
    
    if (testResult.success) {
      localStorage.setItem('currentBackendUrl', url);
      axios.defaults.baseURL = url;
      setCurrentUrl(url);
      
      if (onUrlChange) {
        onUrlChange(url);
      }
      
      toast.success('✅ Backend URL applied!');
      onClose();
    }
  };

  const handleRemoveSavedUrl = (urlToRemove) => {
    const updated = savedUrls.filter(url => url !== urlToRemove);
    setSavedUrls(updated);
    localStorage.setItem('savedBackendUrls', JSON.stringify(updated));
    toast.success('URL removed from saved list');
  };

  const suggestedUrls = [
    'http://localhost:8001',
    'https://localhost:8001',
    'http://127.0.0.1:8001',
  ];

  if (!isOpen || !isDev) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <CogIcon className="h-6 w-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Backend URL Configuration
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <XMarkIcon className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Development Environment Warning */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center space-x-2">
              <div className="bg-yellow-500 text-white px-2 py-1 rounded text-xs font-bold">
                DEV
              </div>
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Development Environment Only
              </h3>
            </div>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-2">
              This manual backend configuration feature is only available in development mode. 
              In production, the backend URL is fixed for security and stability.
            </p>
          </div>

          {/* Current URL Status */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
              Current Backend URL
            </h3>
            <div className="text-sm text-blue-700 dark:text-blue-300 font-mono break-all">
              {currentUrl}
            </div>
          </div>

          {/* Manual URL Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Enter Backend URL
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                placeholder="https://your-backend-url.com or localhost:8001"
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                disabled={isTestingUrl}
              />
              <button
                onClick={handleTestConnection}
                disabled={isTestingUrl || !customUrl.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2 min-w-[100px] justify-center"
              >
                {isTestingUrl ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                ) : (
                  <span>Test</span>
                )}
              </button>
            </div>
            
            {/* Test Results */}
            {Object.entries(testResults).map(([url, result]) => (
              <div key={url} className={`mt-2 p-3 rounded-lg ${result.success ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
                <div className="flex items-center space-x-2">
                  {result.success ? (
                    <CheckCircleIcon className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircleIcon className="h-5 w-5 text-red-600" />
                  )}
                  <span className={`text-sm font-medium ${result.success ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}`}>
                    {result.success ? `✅ Connected (${result.responseTime}ms)` : `❌ ${result.error}`}
                  </span>
                </div>
                {result.success && result.data && (
                  <div className="mt-2 text-xs text-green-700 dark:text-green-300">
                    App: {result.data.app} | Version: {result.data.version} | Status: {result.data.status}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3">
            <button
              onClick={handleSaveAndUse}
              disabled={isTestingUrl || !customUrl.trim()}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              Test & Save URL
            </button>
          </div>

          {/* Suggested URLs */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Quick Options
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {suggestedUrls.map((url) => (
                <button
                  key={url}
                  onClick={() => setCustomUrl(url)}
                  className="text-left px-3 py-2 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg text-sm font-mono text-gray-700 dark:text-gray-300 transition-colors"
                >
                  {url}
                </button>
              ))}
            </div>
          </div>

          {/* Saved URLs */}
          {savedUrls.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Recently Used URLs
              </h3>
              <div className="space-y-2">
                {savedUrls.map((url) => (
                  <div
                    key={url}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <span className="text-sm font-mono text-gray-700 dark:text-gray-300 flex-1 mr-2 break-all">
                      {url}
                    </span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleUseSavedUrl(url)}
                        className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
                      >
                        Use
                      </button>
                      <button
                        onClick={() => handleRemoveSavedUrl(url)}
                        className="p-1 text-gray-400 hover:text-red-500"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
            <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
              💡 Instructions
            </h3>
            <div className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
              <p>• Enter your backend URL (with or without http/https)</p>
              <p>• Click "Test" to verify the connection</p>
              <p>• Click "Test & Save URL" to use the URL for all API calls</p>
              <p>• The system will remember recently used URLs</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManualBackendConfig;