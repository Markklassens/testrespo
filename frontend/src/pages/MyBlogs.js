import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
  EyeIcon, 
  HeartIcon, 
  ClockIcon, 
  UserIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
  DocumentTextIcon,
  BookmarkIcon,
  CheckCircleIcon,
  XCircleIcon,
  CalendarIcon,
  TagIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import { fetchBlogs, deleteBlog, updateBlog } from '../store/slices/blogsSlice';
import { fetchCategories } from '../store/slices/categoriesSlice';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';

const MyBlogs = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { blogs, loading, error } = useSelector(state => state.blogs);
  const { categories } = useSelector(state => state.categories);
  
  const [activeTab, setActiveTab] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [userBlogs, setUserBlogs] = useState([]);
  const [blogStats, setBlogStats] = useState({
    total: 0,
    published: 0,
    drafts: 0,
    totalViews: 0,
    totalLikes: 0
  });

  useEffect(() => {
    if (user) {
      fetchUserBlogs();
      dispatch(fetchCategories());
    }
  }, [user, dispatch]);

  const fetchUserBlogs = async () => {
    try {
      // Fetch both published and draft blogs for the current user
      const [publishedResponse, draftResponse] = await Promise.all([
        api.get('/api/blogs?status=published&author_id=' + user.id),
        api.get('/api/blogs?status=draft&author_id=' + user.id)
      ]);

      const published = publishedResponse.data || [];
      const drafts = draftResponse.data || [];
      const allBlogs = [...published, ...drafts];

      setUserBlogs(allBlogs);
      
      // Calculate stats
      setBlogStats({
        total: allBlogs.length,
        published: published.length,
        drafts: drafts.length,
        totalViews: published.reduce((sum, blog) => sum + (blog.views || 0), 0),
        totalLikes: published.reduce((sum, blog) => sum + (blog.likes || 0), 0)
      });
    } catch (error) {
      console.error('Error fetching user blogs:', error);
      toast.error('Failed to load your blogs');
    }
  };

  const handleDeleteBlog = async (blogId) => {
    if (window.confirm('Are you sure you want to delete this blog?')) {
      try {
        await dispatch(deleteBlog(blogId)).unwrap();
        toast.success('Blog deleted successfully');
        fetchUserBlogs(); // Refresh the list
      } catch (error) {
        toast.error('Failed to delete blog');
      }
    }
  };

  const handlePublishDraft = async (blog) => {
    try {
      await dispatch(updateBlog({ 
        id: blog.id, 
        data: { 
          ...blog, 
          status: 'published',
          published_at: new Date().toISOString()
        } 
      })).unwrap();
      toast.success('Blog published successfully');
      fetchUserBlogs(); // Refresh the list
    } catch (error) {
      toast.error('Failed to publish blog');
    }
  };

  const handleUnpublishBlog = async (blog) => {
    try {
      await dispatch(updateBlog({ 
        id: blog.id, 
        data: { 
          ...blog, 
          status: 'draft',
          published_at: null
        } 
      })).unwrap();
      toast.success('Blog moved to drafts');
      fetchUserBlogs(); // Refresh the list
    } catch (error) {
      toast.error('Failed to unpublish blog');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not published';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Uncategorized';
  };

  const getFilteredBlogs = () => {
    let filtered = userBlogs;
    
    // Filter by tab
    if (activeTab === 'published') {
      filtered = filtered.filter(blog => blog.status === 'published');
    } else if (activeTab === 'drafts') {
      filtered = filtered.filter(blog => blog.status === 'draft');
    }
    
    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(blog => 
        blog.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        blog.content.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  };

  const filteredBlogs = getFilteredBlogs();

  const tabs = [
    { id: 'all', label: 'All Blogs', count: blogStats.total },
    { id: 'published', label: 'Published', count: blogStats.published },
    { id: 'drafts', label: 'Drafts', count: blogStats.drafts }
  ];

  if (loading && userBlogs.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                My Blogs
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage your blog posts and drafts
              </p>
            </div>
            <Link
              to="/blogs"
              className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              <PlusIcon className="h-5 w-5" />
              <span>Write New Blog</span>
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Blogs</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{blogStats.total}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Published</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{blogStats.published}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <EyeIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Views</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{blogStats.totalViews}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <HeartIcon className="h-8 w-8 text-red-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Likes</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{blogStats.totalLikes}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs and Search */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <nav className="flex space-x-8" aria-label="Tabs">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                      activeTab === tab.id
                        ? 'border-purple-500 text-purple-600 dark:text-purple-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                    }`}
                  >
                    <span>{tab.label}</span>
                    <span className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-1 rounded-full text-xs">
                      {tab.count}
                    </span>
                  </button>
                ))}
              </nav>
              
              <div className="p-4">
                <input
                  type="text"
                  placeholder="Search blogs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Blogs List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
          {filteredBlogs.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {activeTab === 'drafts' ? 'No drafts found' : 
                 activeTab === 'published' ? 'No published blogs found' : 
                 'No blogs found'}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {activeTab === 'drafts' ? 'Start writing your first draft!' : 
                 activeTab === 'published' ? 'Publish your first blog!' : 
                 'Create your first blog post!'}
              </p>
              <Link
                to="/blogs"
                className="inline-flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
              >
                <PlusIcon className="h-5 w-5" />
                <span>Write Blog</span>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredBlogs.map((blog) => (
                <div key={blog.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {blog.title}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          blog.status === 'published' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                        }`}>
                          {blog.status}
                        </span>
                        <span className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-1 rounded-full text-xs">
                          {getCategoryName(blog.category_id)}
                        </span>
                      </div>
                      
                      <p className="text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                        {blog.excerpt || blog.content.replace(/<[^>]*>/g, '').substring(0, 150) + '...'}
                      </p>
                      
                      <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center">
                          <CalendarIcon className="h-4 w-4 mr-1" />
                          {blog.status === 'published' ? formatDate(blog.published_at) : `Created ${formatDate(blog.created_at)}`}
                        </div>
                        {blog.status === 'published' && (
                          <>
                            <div className="flex items-center">
                              <EyeIcon className="h-4 w-4 mr-1" />
                              {blog.views || 0}
                            </div>
                            <div className="flex items-center">
                              <HeartIcon className="h-4 w-4 mr-1" />
                              {blog.likes || 0}
                            </div>
                          </>
                        )}
                        <div className="flex items-center">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {blog.reading_time || 1} min read
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3 ml-4">
                      {blog.status === 'published' && (
                        <Link
                          to={`/blog/${blog.id}`}
                          className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium text-sm"
                        >
                          View
                        </Link>
                      )}
                      
                      <Link
                        to={`/blogs/edit/${blog.id}`}
                        className="text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 font-medium text-sm"
                      >
                        Edit
                      </Link>
                      
                      {blog.status === 'draft' ? (
                        <button
                          onClick={() => handlePublishDraft(blog)}
                          className="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 font-medium text-sm"
                        >
                          Publish
                        </button>
                      ) : (
                        <button
                          onClick={() => handleUnpublishBlog(blog)}
                          className="text-yellow-600 hover:text-yellow-700 dark:text-yellow-400 dark:hover:text-yellow-300 font-medium text-sm"
                        >
                          Unpublish
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDeleteBlog(blog.id)}
                        className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 font-medium text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Performance Insights */}
        {blogStats.published > 0 && (
          <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <ChartBarIcon className="h-6 w-6 text-purple-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Performance Insights
              </h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Average Views per Blog</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Math.round(blogStats.totalViews / blogStats.published)}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Average Likes per Blog</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Math.round(blogStats.totalLikes / blogStats.published)}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Engagement Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {blogStats.totalViews > 0 ? Math.round((blogStats.totalLikes / blogStats.totalViews) * 100) : 0}%
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyBlogs;