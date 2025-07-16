import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
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
  EyeIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import BulkUpload from '../components/BulkUpload';
import UserModal from '../components/UserModal';
import ToolModal from '../components/ToolModal';
import BlogModal from '../components/BlogModal';
import { fetchDashboardAnalytics } from '../store/slices/analyticsSlice';
import { fetchTools, deleteTool } from '../store/slices/toolsSlice';
import { fetchBlogs, deleteBlog } from '../store/slices/blogsSlice';
import { fetchCategories, deleteCategory, createCategory } from '../store/slices/categoriesSlice';
import { fetchUsers, deleteUser } from '../store/slices/usersSlice';

const AdminPanel = () => {
  const dispatch = useDispatch();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showToolModal, setShowToolModal] = useState(false);
  const [selectedTool, setSelectedTool] = useState(null);
  const [newCategory, setNewCategory] = useState({ name: '', description: '' });

  const { dashboard, loading: analyticsLoading } = useSelector(state => state.analytics);
  const { tools, loading: toolsLoading } = useSelector(state => state.tools);
  const { blogs, loading: blogsLoading } = useSelector(state => state.blogs);
  const { categories, loading: categoriesLoading } = useSelector(state => state.categories);
  const { users, loading: usersLoading } = useSelector(state => state.users);

  useEffect(() => {
    if (user?.user_type === 'admin' || user?.user_type === 'superadmin') {
      dispatch(fetchDashboardAnalytics());
      dispatch(fetchTools());
      dispatch(fetchBlogs({ status: '' })); // Fetch all blogs including drafts
      dispatch(fetchCategories());
      dispatch(fetchUsers());
    }
  }, [dispatch, user]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBarIcon },
    { id: 'users', label: 'Users', icon: UserGroupIcon },
    { id: 'tools', label: 'Tools', icon: CubeIcon },
    { id: 'blogs', label: 'Blogs', icon: DocumentTextIcon },
    { id: 'categories', label: 'Categories', icon: FolderIcon },
  ];

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      try {
        await dispatch(deleteUser(userId)).unwrap();
        toast.success('User deleted successfully');
      } catch (error) {
        toast.error('Failed to delete user');
      }
    }
  };

  const handleEditUser = (userToEdit) => {
    setSelectedUser(userToEdit);
    setShowUserModal(true);
  };

  const handleCreateUser = () => {
    setSelectedUser(null);
    setShowUserModal(true);
  };

  const handleUserModalClose = () => {
    setShowUserModal(false);
    setSelectedUser(null);
  };

  const handleUserModalSuccess = () => {
    dispatch(fetchUsers());
    dispatch(fetchDashboardAnalytics());
  };

  const handleDeleteTool = async (toolId) => {
    if (window.confirm('Are you sure you want to delete this tool?')) {
      try {
        await dispatch(deleteTool(toolId)).unwrap();
        toast.success('Tool deleted successfully');
      } catch (error) {
        toast.error('Failed to delete tool');
      }
    }
  };

  const handleDeleteBlog = async (blogId) => {
    if (window.confirm('Are you sure you want to delete this blog?')) {
      try {
        await dispatch(deleteBlog(blogId)).unwrap();
        toast.success('Blog deleted successfully');
      } catch (error) {
        toast.error('Failed to delete blog');
      }
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category? This will also delete all tools and blogs in this category.')) {
      try {
        await dispatch(deleteCategory(categoryId)).unwrap();
        toast.success('Category deleted successfully');
      } catch (error) {
        toast.error('Failed to delete category');
      }
    }
  };

  const handleCreateTool = () => {
    setSelectedTool(null);
    setShowToolModal(true);
  };

  const handleEditTool = (tool) => {
    setSelectedTool(tool);
    setShowToolModal(true);
  };

  const handleToolModalClose = () => {
    setShowToolModal(false);
    setSelectedTool(null);
  };

  const handleToolModalSuccess = () => {
    dispatch(fetchTools());
    dispatch(fetchDashboardAnalytics());
  };

  const handleCreateCategory = async () => {
    if (!newCategory.name.trim()) {
      toast.error('Category name is required');
      return;
    }

    try {
      await dispatch(createCategory(newCategory)).unwrap();
      toast.success('Category created successfully');
      setShowCreateCategory(false);
      setNewCategory({ name: '', description: '' });
    } catch (error) {
      toast.error('Failed to create category');
    }
  };

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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (analyticsLoading && !dashboard.total_users) {
    return <LoadingSpinner />;
  }

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
                      ? 'border-purple-500 text-purple-600 dark:text-purple-400'
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
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="bg-blue-500 rounded-lg p-3">
                        <UserGroupIcon className="h-6 w-6 text-white" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          Total Users
                        </p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {dashboard.total_users}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="bg-green-500 rounded-lg p-3">
                        <CubeIcon className="h-6 w-6 text-white" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          Total Tools
                        </p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {dashboard.total_tools}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="bg-purple-500 rounded-lg p-3">
                        <DocumentTextIcon className="h-6 w-6 text-white" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          Total Blogs
                        </p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {dashboard.total_blogs}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center">
                      <div className="bg-yellow-500 rounded-lg p-3">
                        <ChartBarIcon className="h-6 w-6 text-white" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          Total Reviews
                        </p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {dashboard.total_reviews}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Recent Blogs */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Recent Blogs
                    </h3>
                    <div className="space-y-3">
                      {dashboard.recent_blogs?.slice(0, 5).map((blog) => (
                        <div key={blog.id} className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {blog.title}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {blog.views} views • {formatDate(blog.created_at)}
                            </div>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(blog.status)}`}>
                            {blog.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recent Reviews */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Recent Reviews
                    </h3>
                    <div className="space-y-3">
                      {dashboard.recent_reviews?.slice(0, 5).map((review) => (
                        <div key={review.id} className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {review.title}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Rating: {review.rating}/5 • {formatDate(review.created_at)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
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
                    <button
                      onClick={() => setShowBulkUpload(true)}
                      className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
                    >
                      <ArrowUpTrayIcon className="h-4 w-4" />
                      <span>Bulk Upload</span>
                    </button>
                    <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Add Tool
                    </button>
                  </div>
                </div>

                {toolsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  </div>
                ) : (
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
                            Reviews
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Rating
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Views
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {tools.map((tool) => (
                          <tr key={tool.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="flex-shrink-0 h-10 w-10">
                                  {tool.logo_url ? (
                                    <img src={tool.logo_url} alt={tool.name} className="h-10 w-10 rounded-lg object-cover" />
                                  ) : (
                                    <div className="h-10 w-10 bg-gray-300 dark:bg-gray-600 rounded-lg flex items-center justify-center">
                                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        {tool.name.charAt(0)}
                                      </span>
                                    </div>
                                  )}
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {tool.name}
                                  </div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">
                                    {tool.pricing_model}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-900 dark:text-white">
                                {categories.find(cat => cat.id === tool.category_id)?.name || 'Uncategorized'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {tool.total_reviews}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {tool.rating.toFixed(1)}/5
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {tool.views.toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 mr-3">
                                <EyeIcon className="h-4 w-4" />
                              </button>
                              <button className="text-green-600 hover:text-green-900 dark:text-green-400 mr-3">
                                <PencilIcon className="h-4 w-4" />
                              </button>
                              <button 
                                onClick={() => handleDeleteTool(tool.id)}
                                className="text-red-600 hover:text-red-900 dark:text-red-400"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Blogs Tab */}
            {activeTab === 'blogs' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Blog Management
                  </h2>
                  <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create Blog
                  </button>
                </div>

                {blogsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  </div>
                ) : (
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
                        {blogs.map((blog) => (
                          <tr key={blog.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900 dark:text-white max-w-xs truncate">
                                {blog.title}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-900 dark:text-white">
                                {blog.author?.full_name || 'Anonymous'}
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
                              {formatDate(blog.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 mr-3">
                                <EyeIcon className="h-4 w-4" />
                              </button>
                              <button className="text-green-600 hover:text-green-900 dark:text-green-400 mr-3">
                                <PencilIcon className="h-4 w-4" />
                              </button>
                              <button 
                                onClick={() => handleDeleteBlog(blog.id)}
                                className="text-red-600 hover:text-red-900 dark:text-red-400"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Categories Tab */}
            {activeTab === 'categories' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Category Management
                  </h2>
                  <button 
                    onClick={() => setShowCreateCategory(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Category
                  </button>
                </div>

                {categoriesLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {categories.map((category) => (
                      <div key={category.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                          {category.name}
                        </h3>
                        {category.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            {category.description}
                          </p>
                        )}
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Tools:</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {tools.filter(tool => tool.category_id === category.id).length}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Blogs:</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {blogs.filter(blog => blog.category_id === category.id).length}
                            </span>
                          </div>
                        </div>
                        <div className="mt-4 flex space-x-2">
                          <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors duration-200">
                            Edit
                          </button>
                          <button 
                            onClick={() => handleDeleteCategory(category.id)}
                            className="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors duration-200"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    User Management
                  </h2>
                  <button 
                    onClick={handleCreateUser}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add User
                  </button>
                </div>

                {usersLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  </div>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            User
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Email
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
                        {users.map((userData) => (
                          <tr key={userData.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="flex-shrink-0 h-10 w-10">
                                  <div className="h-10 w-10 bg-purple-500 rounded-full flex items-center justify-center">
                                    <span className="text-sm font-medium text-white">
                                      {userData.full_name?.charAt(0)?.toUpperCase() || 'U'}
                                    </span>
                                  </div>
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {userData.full_name}
                                  </div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">
                                    @{userData.username}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-900 dark:text-white">
                                {userData.email}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                userData.user_type === 'superadmin' 
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                  : userData.user_type === 'admin'
                                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                              }`}>
                                {userData.user_type}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                userData.is_active 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              }`}>
                                {userData.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {formatDate(userData.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button 
                                onClick={() => handleEditUser(userData)}
                                className="text-green-600 hover:text-green-900 dark:text-green-400 mr-3"
                              >
                                <PencilIcon className="h-4 w-4" />
                              </button>
                              <button 
                                onClick={() => handleDeleteUser(userData.id)}
                                className="text-red-600 hover:text-red-900 dark:text-red-400"
                                disabled={userData.id === user.id}
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* User Modal */}
      <UserModal
        isOpen={showUserModal}
        onClose={handleUserModalClose}
        user={selectedUser}
        onSuccess={handleUserModalSuccess}
      />

      {/* Bulk Upload Modal */}
      <BulkUpload
        isOpen={showBulkUpload}
        onClose={() => setShowBulkUpload(false)}
        onSuccess={() => {
          dispatch(fetchTools());
          dispatch(fetchDashboardAnalytics());
        }}
      />

      {/* Create Category Modal */}
      {showCreateCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Create New Category
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={newCategory.name}
                    onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter category name..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={newCategory.description}
                    onChange={(e) => setNewCategory({ ...newCategory, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter category description..."
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateCategory(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCategory}
                  disabled={!newCategory.name.trim()}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Category
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;