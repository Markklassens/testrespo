import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
  EyeIcon, 
  HeartIcon, 
  ClockIcon, 
  UserIcon,
  PencilIcon,
  PlusIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import { fetchBlogs, likeBlog } from '../store/slices/blogsSlice';
import { fetchCategories } from '../store/slices/categoriesSlice';
import { useAuth } from '../contexts/AuthContext';

const Blogs = () => {
  const dispatch = useDispatch();
  const { user } = useAuth();
  const { blogs, loading, error, filters } = useSelector(state => state.blogs);
  const { categories } = useSelector(state => state.categories);
  
  const [searchInput, setSearchInput] = useState(filters.search);

  useEffect(() => {
    dispatch(fetchBlogs(filters));
    dispatch(fetchCategories());
  }, [dispatch, filters]);

  useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      dispatch(fetchBlogs({ ...filters, search: searchInput, skip: 0 }));
    }
  };

  const handleLikeBlog = async (blogId) => {
    try {
      await dispatch(likeBlog(blogId)).unwrap();
      toast.success('Blog liked!');
    } catch (error) {
      toast.error('Failed to like blog');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const generateSlug = (title) => {
    return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
  };

  const generateExcerpt = (content) => {
    // Strip HTML and take first 150 characters
    const text = content.replace(/<[^>]*>/g, '');
    return text.length > 150 ? text.substring(0, 150) + '...' : text;
  };

  if (loading && blogs.length === 0) {
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
                Blog Posts
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Insights, tips, and stories from the B2B world
              </p>
            </div>
            <div className="flex space-x-4">
              {user && (
                <Link
                  to="/my-blogs"
                  className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
                >
                  <DocumentTextIcon className="h-5 w-5" />
                  <span>My Blogs</span>
                </Link>
              )}
              {user && (
                <Link
                  to="/blog/create"
                  className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
                >
                  <PlusIcon className="h-5 w-5" />
                  <span>Write a Blog</span>
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Posts
              </label>
              <input
                type="text"
                id="search"
                placeholder="Search by title or content..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyPress={handleSearch}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <select
                id="category"
                value={filters.category_id}
                onChange={(e) => dispatch(fetchBlogs({ ...filters, category_id: e.target.value, skip: 0 }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">All Categories</option>
                {categories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort */}
            <div>
              <label htmlFor="sort" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sort By
              </label>
              <select
                id="sort"
                value={filters.sort_by}
                onChange={(e) => dispatch(fetchBlogs({ ...filters, sort_by: e.target.value, skip: 0 }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="created_at">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="views">Most Viewed</option>
                <option value="likes">Most Liked</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-300">
              Error loading blogs: {error}
            </p>
          </div>
        )}

        {/* Featured Blog */}
        {blogs.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden mb-8">
            <div className="md:flex">
              <div className="md:w-1/3">
                <div className="h-48 md:h-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                  {blogs[0].featured_image ? (
                    <img 
                      src={blogs[0].featured_image} 
                      alt={blogs[0].title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Featured Image</span>
                  )}
                </div>
              </div>
              <div className="md:w-2/3 p-6">
                <div className="flex items-center mb-2">
                  <span className="bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded-full text-xs font-medium">
                    Featured
                  </span>
                  <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                    {categories.find(cat => cat.id === blogs[0].category_id)?.name || 'Uncategorized'}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                  {blogs[0].title}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {blogs[0].excerpt || generateExcerpt(blogs[0].content)}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <UserIcon className="h-4 w-4 mr-1" />
                    {blogs[0].author?.full_name || 'Anonymous'}
                    <span className="mx-2">•</span>
                    {formatDate(blogs[0].created_at)}
                    <span className="mx-2">•</span>
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {blogs[0].reading_time} min read
                  </div>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => handleLikeBlog(blogs[0].id)}
                      className="flex items-center space-x-1 text-gray-500 hover:text-red-500 transition-colors"
                    >
                      <HeartIcon className="h-4 w-4" />
                      <span>{blogs[0].likes}</span>
                    </button>
                    <Link
                      to={`/blog/${blogs[0].id}`}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                      Read More
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Blog Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {blogs.slice(1).map(blog => (
            <div key={blog.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
              <div className="h-48 bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                {blog.featured_image ? (
                  <img 
                    src={blog.featured_image} 
                    alt={blog.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-gray-500 dark:text-gray-400">Blog Image</span>
                )}
              </div>
              <div className="p-6">
                <div className="flex items-center mb-2">
                  <span className="bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-2 py-1 rounded-full text-xs font-medium">
                    {categories.find(cat => cat.id === blog.category_id)?.name || 'Uncategorized'}
                  </span>
                  <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(blog.created_at)}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                  {blog.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
                  {blog.excerpt || generateExcerpt(blog.content)}
                </p>
                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                  <div className="flex items-center">
                    <UserIcon className="h-4 w-4 mr-1" />
                    {blog.author?.full_name || 'Anonymous'}
                  </div>
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {blog.reading_time} min
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 space-x-4">
                    <div className="flex items-center">
                      <EyeIcon className="h-4 w-4 mr-1" />
                      {blog.views}
                    </div>
                    <button
                      onClick={() => handleLikeBlog(blog.id)}
                      className="flex items-center hover:text-red-500 transition-colors"
                    >
                      <HeartIcon className="h-4 w-4 mr-1" />
                      {blog.likes}
                    </button>
                  </div>
                  <Link
                    to={`/blog/${blog.id}`}
                    className="text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 font-medium text-sm"
                  >
                    Read More
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {!loading && blogs.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <PencilIcon className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No blog posts found
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {user ? 'Be the first to write a blog post!' : 'Check back later for new content.'}
            </p>
            {user && (
              <Link
                to="/blog/create"
                className="text-purple-600 hover:text-purple-700 font-medium"
              >
                Write Your First Blog
              </Link>
            )}
          </div>
        )}

        {/* Loading More */}
        {loading && blogs.length > 0 && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Blogs;