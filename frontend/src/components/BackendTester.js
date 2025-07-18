import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BackendTester = () => {
  const [testResults, setTestResults] = useState({});
  const [testing, setTesting] = useState(false);

  const possibleBackendUrls = [
    'https://psychic-space-potato-x54gpgwg9pw626rpp-8001.app.github.dev',
    'https://652511bd-95fd-487c-8258-e1c95dd730f8.preview.emergentagent.com',
    'http://localhost:8001',
    'https://localhost:8001',
    // Add more possible URLs based on your environment
  ];

  const testBackendUrl = async (url) => {
    try {
      const response = await axios.get(`${url}/api/health`, {
        timeout: 5000,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      return { success: true, data: response.data, status: response.status };
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        status: error.response?.status || 'Network Error'
      };
    }
  };

  const testAllUrls = async () => {
    setTesting(true);
    const results = {};
    
    for (const url of possibleBackendUrls) {
      console.log(`Testing ${url}...`);
      results[url] = await testBackendUrl(url);
    }
    
    setTestResults(results);
    setTesting(false);
  };

  useEffect(() => {
    testAllUrls();
  }, []);

  return (
    <div className="fixed top-4 right-4 bg-white p-4 rounded-lg shadow-lg border max-w-md z-50">
      <h3 className="font-bold text-lg mb-2">Backend URL Tester</h3>
      <button
        onClick={testAllUrls}
        disabled={testing}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {testing ? 'Testing...' : 'Test All URLs'}
      </button>
      
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {Object.entries(testResults).map(([url, result]) => (
          <div key={url} className="border-b pb-2">
            <div className="text-sm font-medium break-all">{url}</div>
            <div className={`text-xs ${result.success ? 'text-green-600' : 'text-red-600'}`}>
              {result.success ? (
                <span>✅ SUCCESS - Status: {result.status}</span>
              ) : (
                <span>❌ FAILED - {result.error}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BackendTester;