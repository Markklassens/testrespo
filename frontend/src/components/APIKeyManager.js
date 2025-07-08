import React, { useState, useEffect } from 'react';
import { 
  KeyIcon, 
  XMarkIcon, 
  EyeIcon, 
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../utils/api';

const APIKeyManager = ({ isOpen, onClose }) => {
  const [groqKey, setGroqKey] = useState('');
  const [claudeKey, setClaudeKey] = useState('');
  const [showGroqKey, setShowGroqKey] = useState(false);
  const [showClaudeKey, setShowClaudeKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialGroqKey, setInitialGroqKey] = useState('');
  const [initialClaudeKey, setInitialClaudeKey] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchUserKeys();
    }
  }, [isOpen]);

  const fetchUserKeys = async () => {
    try {
      const response = await api.get('/api/auth/me');
      const { groq_api_key, claude_api_key } = response.data;
      
      setGroqKey(groq_api_key || '');
      setClaudeKey(claude_api_key || '');
      setInitialGroqKey(groq_api_key || '');
      setInitialClaudeKey(claude_api_key || '');
    } catch (error) {
      console.error('Error fetching user keys:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await api.put('/api/auth/api-keys', {
        groq_api_key: groqKey || null,
        claude_api_key: claudeKey || null
      });
      
      toast.success('API keys updated successfully!');
      setInitialGroqKey(groqKey);
      setInitialClaudeKey(claudeKey);
      onClose();
    } catch (error) {
      toast.error('Failed to update API keys');
      console.error('Error updating API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasChanges = () => {
    return groqKey !== initialGroqKey || claudeKey !== initialClaudeKey;
  };

  const maskKey = (key) => {
    if (!key) return '';
    if (key.length <= 8) return key;
    return key.substring(0, 4) + '•'.repeat(key.length - 8) + key.substring(key.length - 4);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <KeyIcon className="h-6 w-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              API Key Management
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Info Banner */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">Secure API Key Storage</p>
                <p>
                  Your API keys are encrypted and stored securely. They enable AI-powered content generation features.
                  You can use either Groq (faster) or Claude (higher quality) or both for redundancy.
                </p>
              </div>
            </div>
          </div>

          {/* Groq API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Groq API Key
            </label>
            <div className="relative">
              <input
                type={showGroqKey ? 'text' : 'password'}
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
                placeholder="Enter your Groq API key..."
                className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
              />
              <button
                type="button"
                onClick={() => setShowGroqKey(!showGroqKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showGroqKey ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Get your free API key from <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:text-purple-700">console.groq.com</a>
              </p>
              {initialGroqKey && (
                <div className="flex items-center text-xs text-green-600">
                  <CheckCircleIcon className="h-4 w-4 mr-1" />
                  <span>Configured</span>
                </div>
              )}
            </div>
            {!showGroqKey && groqKey && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Current: {maskKey(groqKey)}
              </p>
            )}
          </div>

          {/* Claude API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Claude API Key
            </label>
            <div className="relative">
              <input
                type={showClaudeKey ? 'text' : 'password'}
                value={claudeKey}
                onChange={(e) => setClaudeKey(e.target.value)}
                placeholder="Enter your Claude API key..."
                className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
              />
              <button
                type="button"
                onClick={() => setShowClaudeKey(!showClaudeKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showClaudeKey ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Get your API key from <a href="https://console.anthropic.com" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:text-purple-700">console.anthropic.com</a>
              </p>
              {initialClaudeKey && (
                <div className="flex items-center text-xs text-green-600">
                  <CheckCircleIcon className="h-4 w-4 mr-1" />
                  <span>Configured</span>
                </div>
              )}
            </div>
            {!showClaudeKey && claudeKey && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Current: {maskKey(claudeKey)}
              </p>
            )}
          </div>

          {/* Features */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
              Available Features with API Keys:
            </h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                AI-powered blog post generation
              </li>
              <li className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                Tool description creation
              </li>
              <li className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                SEO content optimization
              </li>
              <li className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                Meta title and description generation
              </li>
              <li className="flex items-center">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                Content writing assistance
              </li>
            </ul>
          </div>

          {/* Provider Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Groq</h4>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Ultra-fast generation</li>
                <li>• Free tier available</li>
                <li>• Great for quick content</li>
                <li>• Llama models</li>
              </ul>
            </div>
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Claude</h4>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Higher quality output</li>
                <li>• Better for complex content</li>
                <li>• Excellent for SEO</li>
                <li>• Anthropic's AI</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            💡 You can configure one or both providers for redundancy
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={loading || !hasChanges()}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Saving...' : 'Save Keys'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default APIKeyManager;