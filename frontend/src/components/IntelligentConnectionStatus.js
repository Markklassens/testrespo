import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ArrowPathIcon,
  CogIcon,
  WifiIcon,
  SignalIcon
} from '@heroicons/react/24/outline';

const IntelligentConnectionStatus = () => {
  const { connectionStatus, backendUrl, testBackendConnection, getConnectionStatus, user } = useAuth();
  const [showDetails, setShowDetails] = useState(false);
  const [connectionDetails, setConnectionDetails] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isWidgetVisible, setIsWidgetVisible] = useState(true);
  const [autoHideTimeout, setAutoHideTimeout] = useState(null);

  const isSuperAdmin = user?.user_type === 'superadmin';
  const isDev = process.env.NODE_ENV === 'development';

  // Auto-hide the widget when connected (only in production)
  useEffect(() => {
    if (connectionStatus === 'connected' && !isDev && !isSuperAdmin) {
      // Auto-hide after 5 seconds of being connected
      const timeout = setTimeout(() => {
        setIsWidgetVisible(false);
      }, 5000);
      setAutoHideTimeout(timeout);
    } else if (connectionStatus !== 'connected') {
      // Show widget when not connected
      setIsWidgetVisible(true);
      if (autoHideTimeout) {
        clearTimeout(autoHideTimeout);
        setAutoHideTimeout(null);
      }
    }

    return () => {
      if (autoHideTimeout) {
        clearTimeout(autoHideTimeout);
      }
    };
  }, [connectionStatus, isDev, isSuperAdmin, autoHideTimeout]);

  useEffect(() => {
    if (getConnectionStatus) {
      setConnectionDetails(getConnectionStatus());
    }
  }, [connectionStatus, getConnectionStatus]);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await testBackendConnection();
    } catch (error) {
      console.error('Retry connection failed:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircleIcon className="h-5 w-5" />;
      case 'checking':
        return <ArrowPathIcon className="h-5 w-5 animate-spin" />;
      case 'disconnected':
        return <XCircleIcon className="h-5 w-5" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5" />;
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'checking':
        return 'bg-yellow-500';
      case 'disconnected':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'checking':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  // Show "Show Connection Status" button for SuperAdmin or when widget is hidden
  if ((isSuperAdmin || isDev) && !isWidgetVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsWidgetVisible(true)}
          className="bg-gray-600 text-white px-3 py-2 rounded-lg shadow-lg hover:bg-gray-700 text-sm"
          title="Show connection status widget"
        >
          Show Connection Status
        </button>
      </div>
    );
  }

  // Don't show widget at all if hidden and not admin/dev
  if (!isWidgetVisible && !isSuperAdmin && !isDev) {
    return null;
  }

  // Simple connected status (minimized)
  if (connectionStatus === 'connected' && !showDetails) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <div className="bg-green-500 text-white px-3 py-1 rounded-full shadow-lg flex items-center space-x-2 text-sm">
          <CheckCircleIcon className="h-4 w-4" />
          <span>Connected</span>
          {(isSuperAdmin || isDev) && (
            <>
              <button
                onClick={() => setShowDetails(true)}
                className="p-1 hover:bg-green-600 rounded-full"
                title="Show connection details"
              >
                <CogIcon className="h-3 w-3" />
              </button>
              <button
                onClick={() => setIsWidgetVisible(false)}
                className="p-1 hover:bg-green-600 rounded-full"
                title="Hide connection status widget"
              >
                <XCircleIcon className="h-3 w-3" />
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  // Full widget for non-connected states or when details are requested
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className={`${getStatusColor()} text-white px-4 py-2 rounded-lg shadow-lg max-w-sm`}>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm font-medium">{getStatusText()}</span>
          
          {connectionStatus === 'disconnected' && (
            <button 
              onClick={handleRetry}
              disabled={isRetrying}
              className="p-1 hover:bg-red-600 rounded disabled:opacity-50"
              title="Retry connection"
            >
              <ArrowPathIcon className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} />
            </button>
          )}
          
          {(isSuperAdmin || isDev) && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1 hover:bg-opacity-80 rounded"
              title="Toggle connection details"
            >
              <CogIcon className="h-4 w-4" />
            </button>
          )}
        </div>
        
        {showDetails && (isSuperAdmin || isDev) && (
          <div className="mt-3 pt-3 border-t border-white border-opacity-20">
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span>Backend URL:</span>
                <span className="font-mono text-xs break-all max-w-48">
                  {backendUrl || 'Not set'}
                </span>
              </div>
              
              {connectionDetails && (
                <>
                  <div className="flex items-center justify-between">
                    <span>Retry Count:</span>
                    <span>{connectionDetails.retryCount || 0}</span>
                  </div>
                  
                  {connectionDetails.testResults && (
                    <div className="mt-2">
                      <div className="text-xs font-medium mb-1">Test Results:</div>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {Object.entries(connectionDetails.testResults).map(([url, result]) => (
                          <div key={url} className="flex items-center space-x-2">
                            {result.success ? (
                              <CheckCircleIcon className="h-3 w-3 text-green-300" />
                            ) : (
                              <XCircleIcon className="h-3 w-3 text-red-300" />
                            )}
                            <span className="text-xs break-all">{url}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
              
              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="px-2 py-1 bg-white bg-opacity-20 rounded text-xs hover:bg-opacity-30 disabled:opacity-50"
                >
                  {isRetrying ? 'Testing...' : 'Refresh'}
                </button>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setIsWidgetVisible(false)}
                    className="px-2 py-1 bg-white bg-opacity-20 rounded text-xs hover:bg-opacity-30"
                  >
                    Hide Widget
                  </button>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="px-2 py-1 bg-white bg-opacity-20 rounded text-xs hover:bg-opacity-30"
                  >
                    Hide Details
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligentConnectionStatus;