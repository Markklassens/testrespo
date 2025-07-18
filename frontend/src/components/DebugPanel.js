import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  CogIcon, 
  XMarkIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

const DebugPanel = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState({});
  const { debugConnectivity, testBackendConnection, user } = useAuth();

  // Show debug panel in development OR for SuperAdmins
  const isDevelopment = process.env.NODE_ENV === 'development' || 
                       window.location.hostname === 'localhost' ||
                       window.location.hostname.includes('github.dev') ||
                       window.location.hostname.includes('emergentagent.com');
  
  const isSuperAdmin = user?.user_type === 'superadmin';
  const shouldShowDebugPanel = isDevelopment || isSuperAdmin;

  const fetchDebugData = async () => {
    setLoading(true);
    try {
      const data = await debugConnectivity();
      setDebugData(data);
    } catch (error) {
      console.error('Debug data fetch failed:', error);
      setDebugData({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !debugData) {
      fetchDebugData();
    }
  }, [isOpen]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const renderValue = (value, key = '') => {
    if (typeof value === 'object' && value !== null) {
      return (
        <div className="ml-4">
          <button
            onClick={() => toggleSection(key)}
            className="flex items-center text-sm text-blue-600 hover:text-blue-800 mb-1"
          >
            {expandedSections[key] ? (
              <ChevronDownIcon className="h-4 w-4" />
            ) : (
              <ChevronRightIcon className="h-4 w-4" />
            )}
            <span className="ml-1">{Array.isArray(value) ? `Array (${value.length})` : 'Object'}</span>
          </button>
          {expandedSections[key] && (
            <div className="ml-4 border-l border-gray-300 pl-4">
              {Object.entries(value).map(([k, v]) => (
                <div key={k} className="mb-1">
                  <span className="font-medium text-gray-700">{k}:</span>
                  <span className="ml-2">{renderValue(v, `${key}.${k}`)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
    
    if (typeof value === 'boolean') {
      return <span className={`px-2 py-1 rounded text-xs ${value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{value.toString()}</span>;
    }
    
    if (typeof value === 'string' && value.length > 50) {
      return <span className="text-sm text-gray-600 break-all">{value}</span>;
    }
    
    return <span className="text-sm text-gray-900">{value?.toString() || 'null'}</span>;
  };

  if (!isDevelopment) {
    return null;
  }

  return (
    <>
      {/* Debug Panel Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 left-4 bg-gray-800 text-white p-3 rounded-full shadow-lg hover:bg-gray-700 z-50"
        title="Toggle Debug Panel"
      >
        <CogIcon className="h-5 w-5" />
      </button>

      {/* Debug Panel */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Debug Panel</h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={fetchDebugData}
                  disabled={loading}
                  className="flex items-center space-x-1 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="p-4 overflow-y-auto max-h-[70vh]">
              {loading && (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <p className="mt-2 text-gray-600">Loading debug data...</p>
                </div>
              )}
              
              {debugData && !loading && (
                <div className="space-y-6">
                  {/* Environment Info */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">Environment</h3>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="font-medium">NODE_ENV:</span> 
                        <span className="ml-2">{process.env.NODE_ENV}</span>
                      </div>
                      <div>
                        <span className="font-medium">Backend URL:</span> 
                        <span className="ml-2 text-blue-600">{process.env.REACT_APP_BACKEND_URL}</span>
                      </div>
                      <div>
                        <span className="font-medium">Current URL:</span> 
                        <span className="ml-2 text-blue-600">{window.location.href}</span>
                      </div>
                      <div>
                        <span className="font-medium">Local Storage Token:</span> 
                        {renderValue(!!localStorage.getItem('token'))}
                      </div>
                    </div>
                  </div>

                  {/* Debug Data */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">Backend Debug Data</h3>
                    {debugData.error ? (
                      <div className="text-red-600 text-sm">{debugData.error}</div>
                    ) : (
                      <div className="space-y-2 text-sm">
                        {Object.entries(debugData).map(([key, value]) => (
                          <div key={key} className="border-b border-gray-200 pb-2">
                            <span className="font-medium text-gray-700">{key}:</span>
                            <div className="ml-2">{renderValue(value, key)}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Connection Test */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">Connection Test</h3>
                    <button
                      onClick={testBackendConnection}
                      className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                    >
                      Test Backend Connection
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DebugPanel;