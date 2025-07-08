import React, { useState } from 'react';
import { StarIcon, EyeIcon, HeartIcon, ShareIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import LoadingSpinner from '../components/LoadingSpinner';

const Tools = () => {
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('trending');

  // Mock data - this will be replaced with real API calls
  const mockTools = [
    {
      id: '1',
      name: 'Salesforce CRM',
      description: 'World\'s #1 CRM platform for sales, service, and marketing',
      short_description: 'Complete CRM solution for enterprise businesses',
      rating: 4.5,
      total_reviews: 1234,
      views: 5678,
      pricing_model: 'Paid',
      logo_url: '/api/placeholder/100/100',
      category: 'CRM',
      company_size: 'Enterprise',
      features: ['Lead Management', 'Sales Pipeline', 'Analytics', 'Mobile App'],
      trending_score: 95
    },
    {
      id: '2',
      name: 'HubSpot Marketing Hub',
      description: 'All-in-one marketing software to attract, engage, and delight customers',
      short_description: 'Comprehensive marketing automation platform',
      rating: 4.3,
      total_reviews: 987,
      views: 3456,
      pricing_model: 'Freemium',
      logo_url: '/api/placeholder/100/100',
      category: 'Marketing',
      company_size: 'SMB',
      features: ['Email Marketing', 'Social Media', 'Landing Pages', 'Analytics'],
      trending_score: 88
    },
    {
      id: '3',
      name: 'Slack',
      description: 'Team collaboration platform that brings teams together',
      short_description: 'Business communication and collaboration tool',
      rating: 4.7,
      total_reviews: 2567,
      views: 8901,
      pricing_model: 'Freemium',
      logo_url: '/api/placeholder/100/100',
      category: 'Communication',
      company_size: 'All',
      features: ['Messaging', 'File Sharing', 'Video Calls', 'Integrations'],
      trending_score: 92
    },
  ];

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'CRM', label: 'CRM' },
    { value: 'Marketing', label: 'Marketing' },
    { value: 'Communication', label: 'Communication' },
    { value: 'Analytics', label: 'Analytics' },
    { value: 'HR', label: 'Human Resources' },
  ];

  const sortOptions = [
    { value: 'trending', label: 'Trending' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'views', label: 'Most Viewed' },
    { value: 'newest', label: 'Newest' },
  ];

  const filteredTools = mockTools.filter(tool => {
    const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const sortedTools = [...filteredTools].sort((a, b) => {
    switch (sortBy) {
      case 'rating':
        return b.rating - a.rating;
      case 'views':
        return b.views - a.views;
      case 'trending':
        return b.trending_score - a.trending_score;
      default:
        return 0;
    }
  });

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
      );
    }

    if (hasHalfStar) {
      stars.push(
        <StarIcon key="half" className="h-4 w-4 text-yellow-400" />
      );
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(
        <StarIcon key={`empty-${i}`} className="h-4 w-4 text-gray-300" />
      );
    }

    return stars;
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            B2B Tools Directory
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Discover, compare, and review the best B2B tools for your business
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Tools
              </label>
              <input
                type="text"
                id="search"
                placeholder="Search by name or description..."
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

        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedTools.map(tool => (
            <div key={tool.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center">
                      <span className="text-lg font-bold text-gray-600 dark:text-gray-300">
                        {tool.name.charAt(0)}
                      </span>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {tool.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {tool.category} • {tool.company_size}
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    tool.pricing_model === 'Free' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : tool.pricing_model === 'Freemium'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                      : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                  }`}>
                    {tool.pricing_model}
                  </span>
                </div>

                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  {tool.short_description}
                </p>

                {/* Features */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {tool.features.slice(0, 3).map((feature, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md"
                    >
                      {feature}
                    </span>
                  ))}
                  {tool.features.length > 3 && (
                    <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md">
                      +{tool.features.length - 3} more
                    </span>
                  )}
                </div>

                {/* Rating and Stats */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="flex items-center">
                      {renderStars(tool.rating)}
                    </div>
                    <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                      {tool.rating} ({tool.total_reviews} reviews)
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                  <div className="flex items-center">
                    <EyeIcon className="h-4 w-4 mr-1" />
                    {tool.views.toLocaleString()} views
                  </div>
                  <div className="flex items-center">
                    <StarIcon className="h-4 w-4 mr-1" />
                    Trending: {tool.trending_score}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button className="flex-1 bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200">
                    View Details
                  </button>
                  <button className="bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300 py-2 px-3 rounded-md transition-colors duration-200">
                    <HeartIcon className="h-4 w-4" />
                  </button>
                  <button className="bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300 py-2 px-3 rounded-md transition-colors duration-200">
                    <ShareIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {sortedTools.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              No tools found matching your criteria.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Tools;