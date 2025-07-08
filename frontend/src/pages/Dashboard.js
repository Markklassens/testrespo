import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  CubeIcon, 
  DocumentTextIcon, 
  UserGroupIcon, 
  ChartBarIcon,
  PlusIcon,
  EyeIcon,
  HeartIcon,
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  KeyIcon,
  RocketLaunchIcon,
  ArrowTrendingUpIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import AIContentGenerator from '../components/AIContentGenerator';
import APIKeyManager from '../components/APIKeyManager';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [aiHistory, setAiHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAIGenerator, setShowAIGenerator] = useState(false);
  const [showAPIKeyManager, setShowAPIKeyManager] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    fetchAIHistory();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch analytics for admin users
      if (user.user_type === 'admin' || user.user_type === 'superadmin') {
        const response = await api.get('/api/analytics/dashboard');
        setStats({
          total_users: response.data.total_users,
          total_tools: response.data.total_tools,
          total_blogs: response.data.total_blogs,
          total_reviews: response.data.total_reviews
        });
        setRecentActivity([
          ...response.data.recent_blogs.slice(0, 3).map(blog => ({
            ...blog,
            type: 'blog',
            icon: DocumentTextIcon,
            action: 'published'
          })),
          ...response.data.recent_reviews.slice(0, 2).map(review => ({
            ...review,
            type: 'review',
            icon: ChatBubbleLeftRightIcon,
            action: 'reviewed'
          }))
        ]);
      } else {
        // For regular users, show personal stats
        setStats({
          my_blogs: 0,
          my_reviews: 0,
          tools_compared: 0,
          ai_content_generated: 0
        });
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAIHistory = async () => {
    try {
      const response = await api.get('/api/ai/content-history?limit=5');
      setAiHistory(response.data);
    } catch (error) {
      console.error('Error fetching AI history:', error);
    }
  };

  const handleAIContentGenerated = (content) => {
    toast.success('Content generated! You can now use it in your blogs.');
    fetchAIHistory(); // Refresh AI history
  };

  const quickActions = [
    {
      title: 'Generate AI Content',
      description: 'Create blogs and content with AI assistance',
      icon: SparklesIcon,
      color: 'bg-purple-500',
      action: () => setShowAIGenerator(true),
      disabled: !user.groq_api_key && !user.claude_api_key,
      disabledText: 'Configure API keys first'
    },
    {
      title: 'Manage API Keys',
      description: 'Configure Groq and Claude API keys',
      icon: KeyIcon,
      color: 'bg-blue-500',
      action: () => setShowAPIKeyManager(true)
    },
    {
      title: 'Create Blog Post',
      description: 'Write and publish a new blog post',
      icon: DocumentTextIcon,
      color: 'bg-green-500',
      link: '/blogs/create'
    },
    {
      title: 'Explore Tools',
      description: 'Discover and compare B2B tools',
      icon: CubeIcon,
      color: 'bg-orange-500',
      link: '/tools'
    },
    {
      title: 'View Analytics',
      description: 'Check your content performance',
      icon: ChartBarIcon,
      color: 'bg-indigo-500',
      link: '/analytics',
      adminOnly: true
    },
    {
      title: 'Manage Users',
      description: 'User management and permissions',
      icon: UserGroupIcon,
      color: 'bg-red-500',
      link: '/admin',
      adminOnly: true
    }
  ];

  const filteredActions = quickActions.filter(action => 
    !action.adminOnly || user.user_type === 'admin' || user.user_type === 'superadmin'
  );

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user?.full_name || user?.username}! 👋
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {user.user_type === 'admin' || user.user_type === 'superadmin' 
              ? 'Here\'s your platform overview and AI-powered content tools.'
              : 'Here\'s your personal dashboard with AI-powered content creation tools.'
            }
          </p>
        </div>

        {/* API Key Status */}
        {(!user.groq_api_key && !user.claude_api_key) && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-8">
            <div className="flex items-start">
              <SparklesIcon className="h-5 w-5 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Unlock AI-Powered Content Creation
                </h3>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  Configure your Groq or Claude API keys to access AI content generation features.
                </p>
                <button
                  onClick={() => setShowAPIKeyManager(true)}
                  className="mt-2 text-sm bg-yellow-100 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200 px-3 py-1 rounded hover:bg-yellow-200 dark:hover:bg-yellow-700 transition-colors"
                >
                  Configure API Keys
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {user.user_type === 'admin' || user.user_type === 'superadmin' ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <UserGroupIcon className="h-8 w-8 text-blue-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Users</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_users}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <CubeIcon className="h-8 w-8 text-green-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Tools</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_tools}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-8 w-8 text-purple-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Blogs</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_blogs}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <ChatBubbleLeftRightIcon className="h-8 w-8 text-orange-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Reviews</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_reviews}</p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-8 w-8 text-purple-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">My Blogs</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.my_blogs}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <ChatBubbleLeftRightIcon className="h-8 w-8 text-orange-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">My Reviews</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.my_reviews}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <CubeIcon className="h-8 w-8 text-green-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Tools Compared</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.tools_compared}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <SparklesIcon className="h-8 w-8 text-blue-500" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">AI Content Generated</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{aiHistory.length}</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Quick Actions
                </h2>
                <RocketLaunchIcon className="h-5 w-5 text-gray-400" />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredActions.map((action, index) => (
                  <div key={index} className="relative">
                    {action.link ? (
                      <Link
                        to={action.link}
                        className="block p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all duration-200 hover:-translate-y-1"
                      >
                        <ActionContent action={action} />
                      </Link>
                    ) : (
                      <button
                        onClick={action.action}
                        disabled={action.disabled}
                        className={`w-full text-left p-4 rounded-lg border border-gray-200 dark:border-gray-700 transition-all duration-200 ${
                          action.disabled 
                            ? 'opacity-50 cursor-not-allowed' 
                            : 'hover:shadow-md hover:-translate-y-1'
                        }`}
                      >
                        <ActionContent action={action} />
                        {action.disabled && (
                          <p className="text-xs text-red-500 mt-2">{action.disabledText}</p>
                        )}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity & AI History */}
          <div className="space-y-6">
            {/* AI Content History */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Recent AI Content
                </h2>
                <SparklesIcon className="h-5 w-5 text-purple-500" />
              </div>
              
              {aiHistory.length > 0 ? (
                <div className="space-y-3">
                  {aiHistory.map((content, index) => (
                    <div key={index} className="border-l-4 border-purple-500 pl-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                        {content.content_type.replace('_', ' ')}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Generated with {content.provider} • {new Date(content.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                        {content.generated_content.substring(0, 100)}...
                      </p>
                    </div>
                  ))}
                  <button
                    onClick={() => setShowAIGenerator(true)}
                    className="w-full text-center text-sm text-purple-600 hover:text-purple-700 font-medium mt-3"
                  >
                    Generate More Content
                  </button>
                </div>
              ) : (
                <div className="text-center py-4">
                  <SparklesIcon className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                    No AI content generated yet
                  </p>
                  <button
                    onClick={() => {
                      if (!user.groq_api_key && !user.claude_api_key) {
                        setShowAPIKeyManager(true);
                      } else {
                        setShowAIGenerator(true);
                      }
                    }}
                    className="text-sm bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition-colors"
                  >
                    {!user.groq_api_key && !user.claude_api_key ? 'Setup API Keys' : 'Generate Content'}
                  </button>
                </div>
              )}
            </div>

            {/* Recent Activity */}
            {recentActivity.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Recent Activity
                  </h2>
                  <TrendingUpIcon className="h-5 w-5 text-green-500" />
                </div>
                
                <div className="space-y-3">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <activity.icon className="h-5 w-5 text-gray-400 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 dark:text-white">
                          <span className="font-medium">{activity.title}</span>
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {activity.action} • {new Date(activity.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Content Generator Modal */}
      <AIContentGenerator
        isOpen={showAIGenerator}
        onClose={() => setShowAIGenerator(false)}
        onContentGenerated={handleAIContentGenerated}
      />

      {/* API Key Manager Modal */}
      <APIKeyManager
        isOpen={showAPIKeyManager}
        onClose={() => setShowAPIKeyManager(false)}
      />
    </div>
  );
};

const ActionContent = ({ action }) => (
  <>
    <div className="flex items-center">
      <div className={`w-10 h-10 ${action.color} rounded-lg flex items-center justify-center`}>
        <action.icon className="h-5 w-5 text-white" />
      </div>
      <div className="ml-3">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
          {action.title}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {action.description}
        </p>
      </div>
    </div>
  </>
);

export default Dashboard;