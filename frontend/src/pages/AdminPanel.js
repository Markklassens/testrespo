import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  UserGroupIcon, 
  CubeIcon, 
  DocumentTextIcon, 
  ChartBarIcon,
  FolderIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/LoadingSpinner';

const AdminPanel = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBarIcon },
    { id: 'users', label: 'Users', icon: UserGroupIcon },
    { id: 'tools', label: 'Tools', icon: CubeIcon },
    { id: 'blogs', label: 'Blogs', icon: DocumentTextIcon },
    { id: 'categories', label: 'Categories', icon: FolderIcon },
  ];

  // Mock data
  const stats = [
    { name: 'Total Users', value: '1,234', change: '+12%', color: 'bg-blue-500' },
    { name: 'Active Tools', value: '567', change: '+8%', color: 'bg-green-500' },
    { name: 'Published Blogs', value: '89', change: '+23%', color: 'bg-purple-500' },
    { name: 'Categories', value: '45', change: '+5%', color: 'bg-yellow-500' },
  ];

  const mockUsers = [
    { id: '1', name: 'John Doe', email: 'john@example.com', type: 'user', status: 'active', created: '2024-01-15' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com', type: 'admin', status: 'active', created: '2024-01-10' },
    { id: '3', name: 'Bob Johnson', email: 'bob@example.com', type: 'user', status: 'inactive', created: '2024-01-05' },
  ];

  const mockTools = [
    { id: '1', name: 'Salesforce CRM', category: 'CRM', status: 'active', reviews: 45, rating: 4.5 },
    { id: '2', name: 'HubSpot Marketing', category: 'Marketing', status: 'active', reviews: 32, rating: 4.3 },
    { id: '3', name: 'Slack', category: 'Communication', status: 'pending', reviews: 67, rating: 4.7 },
  ];

  const mockBlogs = [
    { id: '1', title: 'Best CRM Tools 2024', author: 'John Doe', status: 'published', views: 1234, created: '2024-01-15' },
    { id: '2', title: 'Marketing Automation Guide', author: 'Jane Smith', status: 'draft', views: 0, created: '2024-01-14' },
    { id: '3', title: 'Remote Work Tools', author: 'Bob Johnson', status: 'published', views: 567, created: '2024-01-12' },
  ];

  const mockCategories = [
    { id: '1', name: 'CRM', tools: 15, blogs: 8, subcategories: 3 },
    { id: '2', name: 'Marketing', tools: 22, blogs: 12, subcategories: 5 },
    { id: '3', name: 'Communication', tools: 18, blogs: 6, subcategories: 4 },
  ];

  const getStatusBadge = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      inactive: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      published: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    };
    return colors[status] || colors.inactive;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Admin Panel
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your MarketMindAI platform
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
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

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  {stats.map((stat, index) => (
                    <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center">
                        <div className={`${stat.color} rounded-lg p-3`}>
                          <div className="w-6 h-6 bg-white rounded"></div>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            {stat.name}
                          </p>
                          <div className="flex items-center">
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {stat.value}
                            </p>
                            <span className="ml-2 text-sm font-medium text-green-600 dark:text-green-400">
                              {stat.change}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Recent Activity
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          New user registered: john@example.com
                        </span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          Blog post published: "Best CRM Tools 2024"
                        </span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          Tool review submitted for Salesforce CRM
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Quick Actions
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200">
                        Add Tool
                      </button>
                      <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200">
                        Create Blog
                      </button>
                      <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200">
                        Add Category
                      </button>
                      <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200">
                        Manage Users
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    User Management
                  </h2>
                  <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add User
                  </button>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {mockUsers.map((user) => (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {user.name}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {user.email}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-900 dark:text-white capitalize">
                              {user.type}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(user.status)}`}>
                              {user.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {user.created}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 mr-3">
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button className="text-green-600 hover:text-green-900 dark:text-green-400 mr-3">
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button className="text-red-600 hover:text-red-900 dark:text-red-400">
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tools Tab */}
            {activeTab === 'tools' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Tool Management
                  </h2>
                  <div className="flex space-x-3">
                    <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200">
                      Bulk Upload
                    </button>
                    <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Add Tool
                    </button>
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Tool
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Reviews
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Rating
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {mockTools.map((tool) => (
                        <tr key={tool.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {tool.name}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-900 dark:text-white">
                              {tool.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(tool.status)}`}>
                              {tool.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {tool.reviews}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {tool.rating}/5
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 mr-3">
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button className="text-green-600 hover:text-green-900 dark:text-green-400 mr-3">
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button className="text-red-600 hover:text-red-900 dark:text-red-400">
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Similar structure for other tabs... */}
            {activeTab === 'blogs' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Blog Management
                  </h2>
                  <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create Blog
                  </button>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Title
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Author
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Views
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {mockBlogs.map((blog) => (
                        <tr key={blog.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {blog.title}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-900 dark:text-white">
                              {blog.author}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(blog.status)}`}>
                              {blog.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {blog.views}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {blog.created}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 mr-3">
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button className="text-green-600 hover:text-green-900 dark:text-green-400 mr-3">
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button className="text-red-600 hover:text-red-900 dark:text-red-400">
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Categories Tab */}
            {activeTab === 'categories' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Category Management
                  </h2>
                  <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Category
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {mockCategories.map((category) => (
                    <div key={category.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                        {category.name}
                      </h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Tools:</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {category.tools}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Blogs:</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {category.blogs}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Subcategories:</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {category.subcategories}
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 flex space-x-2">
                        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors duration-200">
                          Edit
                        </button>
                        <button className="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors duration-200">
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;