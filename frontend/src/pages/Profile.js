import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { UserIcon, KeyIcon, BellIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/LoadingSpinner';
import APIKeyManager from '../components/APIKeyManager';

const Profile = () => {
  const { user, fetchUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [showAPIKeyManager, setShowAPIKeyManager] = useState(false);

  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const tabs = [
    { id: 'profile', label: 'Profile', icon: UserIcon },
    { id: 'security', label: 'Security', icon: ShieldCheckIcon },
    { id: 'ai-keys', label: 'AI Keys', icon: KeyIcon },
    { id: 'notifications', label: 'Notifications', icon: BellIcon },
  ];

  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // API call to update profile
      // const response = await updateProfile(profileData);
      toast.success('Profile updated successfully!');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 6) {
      toast.error('Password must be at least 6 characters long');
      return;
    }

    setLoading(true);

    try {
      // API call to update password
      // const response = await updatePassword(passwordData);
      toast.success('Password updated successfully!');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      toast.error('Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Profile Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your account settings and preferences
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <tab.icon className="h-5 w-5 mr-2" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div>
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Profile Information
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Update your account's profile information and email address.
                  </p>
                </div>

                <form onSubmit={handleProfileSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Full Name
                      </label>
                      <input
                        type="text"
                        id="full_name"
                        name="full_name"
                        value={profileData.full_name}
                        onChange={handleProfileChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>

                    <div>
                      <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Username
                      </label>
                      <input
                        type="text"
                        id="username"
                        name="username"
                        value={profileData.username}
                        onChange={handleProfileChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={profileData.email}
                      onChange={handleProfileChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="flex items-center">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50"
                    >
                      {loading ? <LoadingSpinner size="sm" /> : 'Update Profile'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div>
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Security Settings
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Manage your password and security preferences.
                  </p>
                </div>

                <form onSubmit={handlePasswordSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Current Password
                    </label>
                    <input
                      type="password"
                      id="current_password"
                      name="current_password"
                      value={passwordData.current_password}
                      onChange={handlePasswordChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        New Password
                      </label>
                      <input
                        type="password"
                        id="new_password"
                        name="new_password"
                        value={passwordData.new_password}
                        onChange={handlePasswordChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>

                    <div>
                      <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        id="confirm_password"
                        name="confirm_password"
                        value={passwordData.confirm_password}
                        onChange={handlePasswordChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  </div>

                  <div className="flex items-center">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50"
                    >
                      {loading ? <LoadingSpinner size="sm" /> : 'Update Password'}
                    </button>
                  </div>
                </form>

                {/* Account Info */}
                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                    Account Information
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Account Type:</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                        {user?.user_type}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Email Verified:</span>
                      <span className={`text-sm font-medium ${
                        user?.is_verified 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {user?.is_verified ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Account Status:</span>
                      <span className={`text-sm font-medium ${
                        user?.is_active 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {user?.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div>
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Notification Preferences
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Choose how you want to be notified about activity on your account.
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        Email Notifications
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Receive notifications via email
                      </p>
                    </div>
                    <button className="bg-primary-600 relative inline-flex h-6 w-11 items-center rounded-full transition-colors">
                      <span className="sr-only">Enable notifications</span>
                      <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        Blog Comments
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Get notified when someone comments on your blog posts
                      </p>
                    </div>
                    <button className="bg-primary-600 relative inline-flex h-6 w-11 items-center rounded-full transition-colors">
                      <span className="sr-only">Enable notifications</span>
                      <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        Tool Reviews
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Get notified when someone reviews a tool you've compared
                      </p>
                    </div>
                    <button className="bg-gray-200 relative inline-flex h-6 w-11 items-center rounded-full transition-colors">
                      <span className="sr-only">Enable notifications</span>
                      <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-1" />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        Weekly Digest
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Receive a weekly summary of platform activity
                      </p>
                    </div>
                    <button className="bg-primary-600 relative inline-flex h-6 w-11 items-center rounded-full transition-colors">
                      <span className="sr-only">Enable notifications</span>
                      <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* AI Keys Tab */}
            {activeTab === 'ai-keys' && (
              <div>
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    AI API Keys
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Configure your AI API keys to enable AI-powered content generation features.
                  </p>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <KeyIcon className="h-5 w-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
                    <div className="text-sm text-blue-800 dark:text-blue-200">
                      <p className="font-medium mb-1">API Keys Enable:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>AI-powered blog post generation</li>
                        <li>Tool description creation</li>
                        <li>SEO content optimization</li>
                        <li>Meta title and description generation</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        Groq API Key
                      </h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        Ultra-fast AI generation with Llama models
                      </p>
                      <div className="flex items-center mt-1">
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          user?.groq_api_key ? 'bg-green-500' : 'bg-gray-400'
                        }`}></div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {user?.groq_api_key ? 'Configured' : 'Not configured'}
                        </span>
                      </div>
                    </div>
                    {user?.groq_api_key && (
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                        {user.groq_api_key.substring(0, 4)}...{user.groq_api_key.substring(user.groq_api_key.length - 4)}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        Claude API Key
                      </h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        High-quality AI content with Anthropic's Claude
                      </p>
                      <div className="flex items-center mt-1">
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          user?.claude_api_key ? 'bg-green-500' : 'bg-gray-400'
                        }`}></div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {user?.claude_api_key ? 'Configured' : 'Not configured'}
                        </span>
                      </div>
                    </div>
                    {user?.claude_api_key && (
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                        {user.claude_api_key.substring(0, 4)}...{user.claude_api_key.substring(user.claude_api_key.length - 4)}
                      </span>
                    )}
                  </div>

                  <div className="flex justify-center pt-4">
                    <button
                      onClick={() => setShowAPIKeyManager(true)}
                      className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium transition-colors duration-200 flex items-center"
                    >
                      <KeyIcon className="h-4 w-4 mr-2" />
                      Manage API Keys
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* API Key Manager Modal */}
      <APIKeyManager
        isOpen={showAPIKeyManager}
        onClose={() => setShowAPIKeyManager(false)}
      />
    </div>
  );
};

export default Profile;