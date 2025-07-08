import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { 
  ChartBarIcon, 
  CubeIcon, 
  DocumentTextIcon, 
  UserGroupIcon,
  PlusIcon,
  EyeIcon,
  HeartIcon,
  StarIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const { user } = useAuth();

  const stats = [
    {
      name: 'Tools Reviewed',
      value: '12',
      icon: CubeIcon,
      color: 'bg-blue-500',
      change: '+2',
      changeType: 'positive'
    },
    {
      name: 'Blogs Published',
      value: '8',
      icon: DocumentTextIcon,
      color: 'bg-green-500',
      change: '+3',
      changeType: 'positive'
    },
    {
      name: 'Total Views',
      value: '1,234',
      icon: EyeIcon,
      color: 'bg-purple-500',
      change: '+156',
      changeType: 'positive'
    },
    {
      name: 'Likes Received',
      value: '89',
      icon: HeartIcon,
      color: 'bg-red-500',
      change: '+12',
      changeType: 'positive'
    },
  ];

  const quickActions = [
    {
      name: 'Write a Blog',
      description: 'Create a new blog post',
      href: '/blogs/create',
      icon: PlusIcon,
      color: 'bg-blue-500'
    },
    {
      name: 'Review a Tool',
      description: 'Share your experience with a tool',
      href: '/tools',
      icon: StarIcon,
      color: 'bg-yellow-500'
    },
    {
      name: 'Explore Tools',
      description: 'Discover new B2B tools',
      href: '/tools',
      icon: CubeIcon,
      color: 'bg-green-500'
    },
    {
      name: 'View Analytics',
      description: 'Check your content performance',
      href: '/analytics',
      icon: ChartBarIcon,
      color: 'bg-purple-500'
    },
  ];

  const recentActivity = [
    {
      type: 'blog',
      title: 'How to Choose the Right CRM for Your Business',
      action: 'published',
      time: '2 hours ago',
      views: 45
    },
    {
      type: 'review',
      title: 'Salesforce CRM Review',
      action: 'reviewed',
      time: '1 day ago',
      rating: 4.5
    },
    {
      type: 'tool',
      title: 'HubSpot Marketing Hub',
      action: 'compared',
      time: '3 days ago',
      rating: 4.2
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user?.full_name}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Here's what's happening with your MarketMindAI account.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className={`${stat.color} rounded-lg p-3`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {stat.name}
                  </p>
                  <div className="flex items-center">
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stat.value}
                    </p>
                    <span className={`ml-2 text-sm font-medium ${
                      stat.changeType === 'positive' 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      {stat.change}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h2>
              <div className="space-y-3">
                {quickActions.map((action, index) => (
                  <Link
                    key={index}
                    to={action.href}
                    className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-200"
                  >
                    <div className={`${action.color} rounded-lg p-2`}>
                      <action.icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {action.name}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {action.description}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Recent Activity
              </h2>
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-start p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="flex-shrink-0">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        activity.type === 'blog' 
                          ? 'bg-blue-100 dark:bg-blue-900' 
                          : activity.type === 'review'
                          ? 'bg-yellow-100 dark:bg-yellow-900'
                          : 'bg-green-100 dark:bg-green-900'
                      }`}>
                        {activity.type === 'blog' && (
                          <DocumentTextIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                        )}
                        {activity.type === 'review' && (
                          <StarIcon className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                        )}
                        {activity.type === 'tool' && (
                          <CubeIcon className="h-4 w-4 text-green-600 dark:text-green-400" />
                        )}
                      </div>
                    </div>
                    <div className="ml-4 flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {activity.title}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {activity.action} • {activity.time}
                      </p>
                      {activity.views && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {activity.views} views
                        </p>
                      )}
                      {activity.rating && (
                        <div className="flex items-center mt-1">
                          <StarIcon className="h-3 w-3 text-yellow-400 fill-current" />
                          <span className="text-xs text-gray-600 dark:text-gray-400 ml-1">
                            {activity.rating}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* User Type Specific Content */}
        {(user?.user_type === 'admin' || user?.user_type === 'superadmin') && (
          <div className="mt-8">
            <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <UserGroupIcon className="h-8 w-8 text-white" />
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-white">
                    Admin Dashboard
                  </h3>
                  <p className="text-primary-100 mt-1">
                    Manage users, tools, and content from the admin panel
                  </p>
                </div>
                <div className="ml-auto">
                  <Link
                    to="/admin"
                    className="bg-white text-primary-600 hover:bg-gray-100 px-4 py-2 rounded-lg font-medium transition-colors duration-200"
                  >
                    Go to Admin Panel
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;