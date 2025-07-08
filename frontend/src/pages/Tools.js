import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  StarIcon, 
  EyeIcon, 
  HeartIcon, 
  ShareIcon, 
  FunnelIcon,
  ScaleIcon,
  PlusIcon 
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import AdvancedFilters from '../components/AdvancedFilters';
import ToolComparison from '../components/ToolComparison';
import { fetchTools } from '../store/slices/toolsSlice';
import { addToComparison, fetchComparisonTools } from '../store/slices/comparisonSlice';
import { fetchCategories } from '../store/slices/categoriesSlice';

const Tools = () => {
  const dispatch = useDispatch();
  const { tools, loading, error, filters, total } = useSelector(state => state.tools);
  const { tools: comparisonTools } = useSelector(state => state.comparison);
  const [showFilters, setShowFilters] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [searchInput, setSearchInput] = useState(filters.search);

  useEffect(() => {
    dispatch(fetchTools(filters));
    dispatch(fetchCategories());
    dispatch(fetchComparisonTools());
  }, [dispatch, filters]);

  useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      dispatch(fetchTools({ ...filters, search: searchInput, skip: 0 }));
    }
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
      await dispatch(addToComparison(toolId)).unwrap();
      await dispatch(fetchComparisonTools());
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
                Discover, compare, and review the best B2B tools for your business
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
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyPress={handleSearch}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
              />
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
        <div className="mb-6">
          <p className="text-gray-600 dark:text-gray-400">
            {loading ? 'Loading...' : `Found ${total || tools.length} tools`}
            {filters.search && ` for "${filters.search}"`}
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-300">
              Error loading tools: {error}
            </p>
          </div>
        )}

        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map(tool => {
            const features = parseFeatures(tool.features);
            const isInComparison = comparisonTools.some(compTool => compTool.id === tool.id);
            
            return (
              <div key={tool.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
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
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {tool.name}
                        </h3>
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
          })}
        </div>

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
        onApply={() => dispatch(fetchTools(filters))}
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