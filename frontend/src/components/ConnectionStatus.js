import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

const ConnectionStatus = () => {
  const { connectionStatus, testBackendConnection } = useAuth();

  const handleRetry = async () => {
    try {
      await testBackendConnection();
    } catch (error) {
      console.error('Retry connection failed:', error);
    }
  };

  if (connectionStatus === 'connected') {
    return (
      <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2 z-50">
        <CheckCircleIcon className="h-5 w-5" />
        <span className="text-sm">Connected</span>
      </div>
    );
  }

  if (connectionStatus === 'disconnected') {
    return (
      <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2 z-50">
        <XCircleIcon className="h-5 w-5" />
        <span className="text-sm">Disconnected</span>
        <button 
          onClick={handleRetry}
          className="ml-2 p-1 hover:bg-red-600 rounded"
          title="Retry connection"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>
    );
  }

  if (connectionStatus === 'checking') {
    return (
      <div className="fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2 z-50">
        <ExclamationTriangleIcon className="h-5 w-5" />
        <span className="text-sm">Checking connection...</span>
      </div>
    );
  }

  return null;
};

export default ConnectionStatus;