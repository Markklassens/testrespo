import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { WifiIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const IntelligentLoadingScreen = () => {
  const { loading, connectionStatus, backendUrl } = useAuth();

  if (!loading) return null;

  return (
    <div className="fixed inset-0 bg-white dark:bg-gray-900 flex items-center justify-center z-50">
      <div className="text-center">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full mb-4">
            <WifiIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            MarketMindAI
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Connecting to backend services...
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-center space-x-2">
            <ArrowPathIcon className="h-5 w-5 text-purple-600 animate-spin" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {connectionStatus === 'checking' ? 'Finding best backend server...' : 
               connectionStatus === 'connected' ? 'Connected! Loading application...' :
               'Connecting to backend...'}
            </span>
          </div>

          {backendUrl && (
            <div className="text-xs text-gray-500 dark:text-gray-500">
              Backend: {backendUrl}
            </div>
          )}

          <div className="w-64 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-purple-600 h-2 rounded-full transition-all duration-500"
              style={{ 
                width: connectionStatus === 'connected' ? '100%' : 
                       connectionStatus === 'checking' ? '60%' : '20%' 
              }}
            />
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-500">
            Intelligent backend detection enabled
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligentLoadingScreen;