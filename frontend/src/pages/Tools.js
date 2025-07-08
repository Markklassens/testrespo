import React, { useState, useEffect } from 'react';
import { 
  StarIcon, 
  EyeIcon, 
  HeartIcon, 
  ShareIcon, 
  FunnelIcon,
  ScaleIcon,
  PlusIcon,
  Squares2X2Icon,
  ListBulletIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import AdvancedFilters from '../components/AdvancedFilters';
import ToolComparison from '../components/ToolComparison';
import api from '../utils/api';

const Tools = () => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchResults, setSearchResults] = useState(null);
  const [comparisonTools, setComparisonTools] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'table'
  
  const [filters, setFilters] = useState({
    q: '',
    category_id: '',
    subcategory_id: '',
    pricing_model: '',
    company_size: '',
    industry: '',
    employee_size: '',
    revenue_range: '',
    location: '',
    is_hot: null,
    is_featured: null,
    min_rating: null,
    sort_by: 'relevance'
  });

  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  });

  useEffect(() => {
    fetchTools();
    fetchComparisonTools();
  }, [filters, pagination.page]);

  const fetchTools = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...filters,
        page: pagination.page,
        per_page: pagination.per_page
      });

      // Remove empty values
      Object.keys(filters).forEach(key => {
        if (filters[key] === '' || filters[key] === null) {
          params.delete(key);
        }
      });

      const response = await api.get(`/api/tools/search?${params.toString()}`);
      setSearchResults(response.data);
      setTools(response.data.tools);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        total_pages: response.data.total_pages,
        has_next: response.data.has_next,
        has_prev: response.data.has_prev
      }));
    } catch (error) {
      console.error('Error fetching tools:', error);
      toast.error('Failed to fetch tools');
    } finally {
      setLoading(false);
    }
  };

  const fetchComparisonTools = async () => {
    try {
      const response = await api.get('/api/tools/compare');
      setComparisonTools(response.data);
    } catch (error) {
      console.error('Error fetching comparison tools:', error);
    }
  };

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      setPagination(prev => ({ ...prev, page: 1 }));
      fetchTools();
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAddToComparison = async (toolId) => {
    if (comparisonTools.length >= 5) {
      toast.error('You can compare up to 5 tools maximum');
      return;
    }

    if (comparisonTools.some(tool => tool.id === toolId)) {
      toast.error('Tool is already in comparison');
      return;
    }

    try {
      await api.post('/api/tools/compare', { tool_id: toolId });
      await fetchComparisonTools();
      toast.success('Tool added to comparison');
    } catch (error) {
      toast.error('Failed to add tool to comparison');
    }
  };

  const parseFeatures = (features) => {
    try {
      return JSON.parse(features || '[]');
    } catch {
      return features ? features.split(',').map(f => f.trim()) : [];
    }
  };

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

  const Pagination = () => {
    if (pagination.total_pages <= 1) return null;

    const pageNumbers = [];
    const maxPages = 5;
    const currentPage = pagination.page;
    const totalPages = pagination.total_pages;

    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(totalPages, startPage + maxPages - 1);

    if (endPage - startPage + 1 < maxPages) {
      startPage = Math.max(1, endPage - maxPages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }

    return (
      <div className="flex items-center justify-center space-x-2 mt-8">
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={!pagination.has_prev}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeftIcon className="h-5 w-5" />
        </button>

        {startPage > 1 && (
          <>
            <button
              onClick={() => handlePageChange(1)}
              className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              1
            </button>
            {startPage > 2 && <span className="px-2 text-gray-500">...</span>}
          </>
        )}

        {pageNumbers.map(pageNum => (
          <button
            key={pageNum}
            onClick={() => handlePageChange(pageNum)}
            className={`px-3 py-2 rounded-lg border ${
              pageNum === currentPage
                ? 'bg-purple-600 text-white border-purple-600'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {pageNum}
          </button>
        ))}

        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && <span className="px-2 text-gray-500">...</span>}
            <button
              onClick={() => handlePageChange(totalPages)}
              className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={!pagination.has_next}
          className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRightIcon className="h-5 w-5" />
        </button>
      </div>
    );
  };

  const ToolCard = ({ tool }) => {
    const features = parseFeatures(tool.features);
    const isInComparison = comparisonTools.some(compTool => compTool.id === tool.id);
    
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center overflow-hidden">
                {tool.logo_url ? (
                  <img 
                    src={tool.logo_url} 
                    alt={tool.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-lg font-bold text-gray-600 dark:text-gray-300">
                    {tool.name.charAt(0)}
                  </span>
                )}
              </div>
              <div className="ml-3">
                <div className="flex items-center">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {tool.name}
                  </h3>
                  {tool.is_hot && (
                    <span className="h-4 w-4 text-red-500 ml-2" title="Hot Tool">🔥</span>
                  )}
                  {tool.is_featured && (
                    <span className="h-4 w-4 text-purple-500 ml-1" title="Featured Tool">✨</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {tool.target_audience} • {tool.company_size}
                </p>
              </div>
            </div>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              tool.pricing_model === 'Free' 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : tool.pricing_model === 'Freemium'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
            }`}>
              {tool.pricing_model}
            </span>
          </div>

          <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-2">
            {tool.short_description || tool.description}
          </p>

          {/* Features */}
          <div className="flex flex-wrap gap-2 mb-4">
            {features.slice(0, 3).map((feature, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md"
              >
                {feature}
              </span>
            ))}
            {features.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md">
                +{features.length - 3} more
              </span>
            )}
          </div>

          {/* Additional Info */}
          {(tool.industry || tool.location) && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
              {tool.industry && <span>{tool.industry}</span>}
              {tool.industry && tool.location && <span> • </span>}
              {tool.location && <span>{tool.location}</span>}
            </div>
          )}

          {/* Rating and Stats */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="flex items-center">
                {renderStars(tool.rating)}
              </div>
              <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                {tool.rating.toFixed(1)} ({tool.total_reviews} reviews)
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
              Trending: {tool.trending_score.toFixed(1)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200">
              View Details
            </button>
            
            <button 
              onClick={() => handleAddToComparison(tool.id)}
              disabled={isInComparison || comparisonTools.length >= 5}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                isInComparison 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300'
              }`}
              title={isInComparison ? 'In comparison' : 'Add to comparison'}
            >
              {isInComparison ? (
                <ScaleIcon className="h-4 w-4" />
              ) : (
                <PlusIcon className="h-4 w-4" />
              )}
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
    );
  };

  const ToolTableRow = ({ tool }) => {
    const features = parseFeatures(tool.features);
    const isInComparison = comparisonTools.some(compTool => compTool.id === tool.id);
    
    return (
      <tr className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
        <td className="py-4 px-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center overflow-hidden mr-3">
              {tool.logo_url ? (
                <img 
                  src={tool.logo_url} 
                  alt={tool.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-sm font-bold text-gray-600 dark:text-gray-300">
                  {tool.name.charAt(0)}
                </span>
              )}
            </div>
            <div>
              <div className="flex items-center">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {tool.name}
                </h3>
                {tool.is_hot && (
                  <FireIcon className="h-4 w-4 text-red-500 ml-2" title="Hot Tool" />
                )}
                {tool.is_featured && (
                  <SparklesIcon className="h-4 w-4 text-purple-500 ml-1" title="Featured Tool" />
                )}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {tool.short_description || tool.description.substring(0, 100)}...
              </p>
            </div>
          </div>
        </td>
        
        <td className="py-4 px-6">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            tool.pricing_model === 'Free' 
              ? 'bg-green-100 text-green-800'
              : tool.pricing_model === 'Freemium'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-orange-100 text-orange-800'
          }`}>
            {tool.pricing_model}
          </span>
        </td>
        
        <td className="py-4 px-6">
          <div className="flex items-center">
            {renderStars(tool.rating)}
            <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
              {tool.rating.toFixed(1)}
            </span>
          </div>
        </td>
        
        <td className="py-4 px-6 text-sm text-gray-600 dark:text-gray-400">
          {tool.views.toLocaleString()}
        </td>
        
        <td className="py-4 px-6 text-sm text-gray-600 dark:text-gray-400">
          {tool.company_size}
        </td>
        
        <td className="py-4 px-6">
          <div className="flex gap-2">
            <button className="bg-purple-600 hover:bg-purple-700 text-white py-1 px-3 rounded text-xs">
              View
            </button>
            <button 
              onClick={() => handleAddToComparison(tool.id)}
              disabled={isInComparison || comparisonTools.length >= 5}
              className={`py-1 px-2 rounded text-xs ${
                isInComparison 
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }`}
            >
              {isInComparison ? '✓' : '+'}
            </button>
          </div>
        </td>
      </tr>
    );
  };

  if (loading && tools.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                B2B Tools Directory
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Discover, compare, and review the best B2B tools with AI-powered insights
              </p>
            </div>
            
            {/* Action Buttons */}
            <div className="flex space-x-4">
              {comparisonTools.length > 0 && (
                <button
                  onClick={() => setShowComparison(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <ScaleIcon className="h-5 w-5" />
                  <span>Compare ({comparisonTools.length})</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Search and Quick Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search tools, features, or descriptions..."
                value={filters.q}
                onChange={(e) => setFilters(prev => ({ ...prev, q: e.target.value }))}
                onKeyPress={handleSearch}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
            
            {/* View Mode Toggle */}
            <div className="flex rounded-lg border border-gray-300 dark:border-gray-600">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-4 py-3 rounded-l-lg transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                <Squares2X2Icon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-4 py-3 rounded-r-lg transition-colors ${
                  viewMode === 'table'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                <ListBulletIcon className="h-5 w-5" />
              </button>
            </div>
            
            {/* Advanced Filters Button */}
            <button
              onClick={() => setShowFilters(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              <FunnelIcon className="h-5 w-5" />
              <span>Advanced Filters</span>
              {Object.values(filters).some(value => value && value !== 'relevance' && value !== '') && (
                <span className="bg-purple-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  !
                </span>
              )}
            </button>
          </div>

          {/* Active Filters Display */}
          {Object.entries(filters).some(([key, value]) => value && value !== 'relevance' && value !== '') && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(filters).map(([key, value]) => {
                if (!value || value === 'relevance' || value === '') return null;
                
                const label = key === 'min_rating' ? `${value}+ stars` :
                             key === 'sort_by' ? `Sort: ${value}` :
                             key === 'q' ? `"${value}"` :
                             `${key.replace('_', ' ')}: ${value}`;
                
                return (
                  <span
                    key={key}
                    className="inline-flex items-center px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-sm rounded-full"
                  >
                    {label}
                  </span>
                );
              })}
            </div>
          )}
        </div>

        {/* Results Summary */}
        <div className="mb-6 flex justify-between items-center">
          <p className="text-gray-600 dark:text-gray-400">
            {loading ? 'Loading...' : `Found ${pagination.total || tools.length} tools`}
            {filters.q && ` for "${filters.q}"`}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Page {pagination.page} of {pagination.total_pages}
          </p>
        </div>

        {/* Tools Display */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tools.map(tool => (
              <ToolCard key={tool.id} tool={tool} />
            ))}
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Tool
                  </th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Pricing
                  </th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Rating
                  </th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Views
                  </th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {tools.map(tool => (
                  <ToolTableRow key={tool.id} tool={tool} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Empty State */}
        {!loading && tools.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <FunnelIcon className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No tools found
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Try adjusting your search criteria or filters.
            </p>
            <button
              onClick={() => setShowFilters(true)}
              className="text-purple-600 hover:text-purple-700 font-medium"
            >
              Adjust Filters
            </button>
          </div>
        )}

        {/* Pagination */}
        <Pagination />

        {/* Loading More */}
        {loading && tools.length > 0 && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
          </div>
        )}
      </div>

      {/* Advanced Filters Modal */}
      <AdvancedFilters
        isOpen={showFilters}
        onClose={() => setShowFilters(false)}
        onApply={fetchTools}
        filters={filters}
        setFilters={handleFilterChange}
      />

      {/* Tool Comparison Modal */}
      <ToolComparison
        isOpen={showComparison}
        onClose={() => setShowComparison(false)}
      />
    </div>
  );
};

export default Tools;