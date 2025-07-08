import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { EyeIcon, HeartIcon, ClockIcon, UserIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/LoadingSpinner';

const Blogs = () => {
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  // Mock data - this will be replaced with real API calls
  const mockBlogs = [
    {
      id: '1',
      title: 'How to Choose the Right CRM for Your Business in 2024',
      excerpt: 'Selecting the perfect CRM system is crucial for business growth. Here\'s a comprehensive guide to help you make the right choice.',
      content: 'Full blog content here...',
      author: 'John Smith',
      created_at: '2024-01-15T10:30:00Z',
      views: 1234,
      likes: 89,
      reading_time: 8,
      featured_image: '/api/placeholder/400/200',
      category: 'CRM',
      status: 'published'
    },
    {
      id: '2',
      title: 'Top 10 Marketing Automation Tools for Small Businesses',
      excerpt: 'Discover the best marketing automation tools that can help small businesses scale their marketing efforts effectively.',
      content: 'Full blog content here...',
      author: 'Sarah Johnson',
      created_at: '2024-01-12T14:45:00Z',
      views: 2567,
      likes: 156,
      reading_time: 12,
      featured_image: '/api/placeholder/400/200',
      category: 'Marketing',
      status: 'published'
    },
    {
      id: '3',
      title: 'The Future of Remote Work: Tools and Strategies',
      excerpt: 'Explore the latest tools and strategies that are shaping the future of remote work and team collaboration.',
      content: 'Full blog content here...',
      author: 'Mike Chen',
      created_at: '2024-01-10T09:15:00Z',
      views: 987,
      likes: 67,
      reading_time: 6,
      featured_image: '/api/placeholder/400/200',
      category: 'Productivity',
      status: 'published'
    },
  ];

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'CRM', label: 'CRM' },
    { value: 'Marketing', label: 'Marketing' },
    { value: 'Productivity', label: 'Productivity' },
    { value: 'Analytics', label: 'Analytics' },
    { value: 'HR', label: 'Human Resources' },
  ];

  const sortOptions = [
    { value: 'newest', label: 'Newest First' },
    { value: 'oldest', label: 'Oldest First' },
    { value: 'views', label: 'Most Viewed' },
    { value: 'likes', label: 'Most Liked' },
  ];

  const filteredBlogs = mockBlogs.filter(blog => {
    const matchesSearch = blog.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         blog.excerpt.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || blog.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const sortedBlogs = [...filteredBlogs].sort((a, b) => {
    switch (sortBy) {
      case 'newest':
        return new Date(b.created_at) - new Date(a.created_at);
      case 'oldest':
        return new Date(a.created_at) - new Date(b.created_at);
      case 'views':
        return b.views - a.views;
      case 'likes':
        return b.likes - a.likes;
      default:
        return 0;
    }
  });

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
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
            <Link
              to="/blogs/create"
              className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              Write a Blog
            </Link>
          </div>
        </div>

        {/* Filters */}
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
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <select
                id="category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
              >
                {categories.map(category => (
                  <option key={category.value} value={category.value}>
                    {category.label}
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
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
              >
                {sortOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Featured Blog */}
        {sortedBlogs.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden mb-8">
            <div className="md:flex">
              <div className="md:w-1/3">
                <div className="h-48 md:h-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                  <span className="text-gray-500 dark:text-gray-400">Featured Image</span>
                </div>
              </div>
              <div className="md:w-2/3 p-6">
                <div className="flex items-center mb-2">
                  <span className="bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 px-2 py-1 rounded-full text-xs font-medium">
                    Featured
                  </span>
                  <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                    {sortedBlogs[0].category}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                  {sortedBlogs[0].title}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {sortedBlogs[0].excerpt}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <UserIcon className="h-4 w-4 mr-1" />
                    {sortedBlogs[0].author}
                    <span className="mx-2">•</span>
                    {formatDate(sortedBlogs[0].created_at)}
                    <span className="mx-2">•</span>
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {sortedBlogs[0].reading_time} min read
                  </div>
                  <Link
                    to={`/blogs/${sortedBlogs[0].id}`}
                    className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                  >
                    Read More
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Blog Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedBlogs.slice(1).map(blog => (
            <div key={blog.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
              <div className="h-48 bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                <span className="text-gray-500 dark:text-gray-400">Blog Image</span>
              </div>
              <div className="p-6">
                <div className="flex items-center mb-2">
                  <span className="bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-2 py-1 rounded-full text-xs font-medium">
                    {blog.category}
                  </span>
                  <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(blog.created_at)}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                  {blog.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
                  {blog.excerpt}
                </p>
                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                  <div className="flex items-center">
                    <UserIcon className="h-4 w-4 mr-1" />
                    {blog.author}
                  </div>
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {blog.reading_time} min
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <EyeIcon className="h-4 w-4 mr-1" />
                    {blog.views}
                    <HeartIcon className="h-4 w-4 ml-4 mr-1" />
                    {blog.likes}
                  </div>
                  <Link
                    to={`/blogs/${blog.id}`}
                    className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium text-sm"
                  >
                    Read More
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {sortedBlogs.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              No blog posts found matching your criteria.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Blogs;