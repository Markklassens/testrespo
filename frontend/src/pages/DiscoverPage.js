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
  ChevronRightIcon,
  MagnifyingGlassIcon,
  ArrowRightIcon,
  ClockIcon,
  FireIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../utils/api';

const DiscoverPage = () => {
  const [tools, setTools] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchResults, setSearchResults] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [activeCarousel, setActiveCarousel] = useState('trending');
  
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
    per_page: 50, // Increased to show more tools per page
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  });

  const [collapsedSections, setCollapsedSections] = useState({
    basic: false,
    pricing: true,
    business: true,
    advanced: true
  });

  useEffect(() => {
    Promise.all([
      fetchToolsAnalytics(),
      fetchCategories(),
      fetchTools()
    ]);
  }, []);

  useEffect(() => {
    fetchTools();
  }, [filters, pagination.page]);

  const fetchToolsAnalytics = async () => {
    try {
      const response = await api.get('/api/tools/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/api/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchTools = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...filters,
        page: pagination.page,
        per_page: pagination.per_page
      });

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

  const handleSearch = (e) => {
    if (e.key === 'Enter' || e.type === 'click') {
      setPagination(prev => ({ ...prev, page: 1 }));
      fetchTools();
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 600, behavior: 'smooth' });
  };

  const clearAllFilters = () => {
    const clearedFilters = {
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
    };
    setFilters(clearedFilters);
  };

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
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
        <StarIcon key={`empty-${i}`} className="h-4 w-4 text-gray-300 dark:text-gray-600" />
      );
    }

    return stars;
  };

  const CarouselCard = ({ tool, index }) => (
    <div 
      className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-500 transform hover:-translate-y-2 border border-gray-100 dark:border-gray-700 group min-w-80"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="p-6">
        <div className="flex items-center mb-4">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-purple-200 dark:from-purple-800 dark:to-purple-900 rounded-2xl flex items-center justify-center overflow-hidden shadow-inner">
            {tool.logo_url ? (
              <img 
                src={tool.logo_url} 
                alt={tool.name}
                className="w-full h-full object-cover rounded-2xl"
              />
            ) : (
              <span className="text-2xl font-bold text-purple-600 dark:text-purple-300">
                {tool.name.charAt(0)}
              </span>
            )}
          </div>
          <div className="ml-4 flex-1">
            <div className="flex items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                {tool.name}
              </h3>
              {tool.is_hot && (
                <FireIcon className="h-5 w-5 text-red-500 ml-2 animate-pulse" />
              )}
              {tool.is_featured && (
                <SparklesIcon className="h-5 w-5 text-yellow-500 ml-1 animate-pulse" />
              )}
            </div>
            <div className="flex items-center mt-1">
              {renderStars(tool.rating)}
              <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                ({tool.total_reviews})
              </span>
            </div>
          </div>
        </div>
        
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-2">
          {tool.short_description || tool.description}
        </p>
        
        <div className="flex items-center justify-between">
          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
            tool.pricing_model === 'Free' 
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : tool.pricing_model === 'Freemium'
              ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
              : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
          }`}>
            {tool.pricing_model || 'N/A'}
          </span>
          
          <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
            <EyeIcon className="h-4 w-4 mr-1" />
            {tool.views.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );

  const ToolCard = ({ tool }) => {
    const features = parseFeatures(tool.features);
    
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-1 border border-gray-100 dark:border-gray-700 group overflow-hidden">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center flex-1">
              <div className="w-14 h-14 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 rounded-xl flex items-center justify-center overflow-hidden">
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
              <div className="ml-4 flex-1">
                <div className="flex items-center">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                    {tool.name}
                  </h3>
                  {tool.is_hot && (
                    <FireIcon className="h-4 w-4 text-red-500 ml-2" />
                  )}
                  {tool.is_featured && (
                    <SparklesIcon className="h-4 w-4 text-yellow-500 ml-1" />
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {tool.company_size} • {tool.target_audience}
                </p>
              </div>
            </div>
            <span className={`px-3 py-1 text-xs font-semibold rounded-full shrink-0 ${
              tool.pricing_model === 'Free' 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : tool.pricing_model === 'Freemium'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
            }`}>
              {tool.pricing_model || 'N/A'}
            </span>
          </div>

          <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-2">
            {tool.short_description || tool.description}
          </p>

          <div className="flex flex-wrap gap-2 mb-4">
            {features.slice(0, 3).map((feature, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-lg font-medium"
              >
                {feature}
              </span>
            ))}
            {features.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded-lg">
                +{features.length - 3} more
              </span>
            )}
          </div>

          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              {renderStars(tool.rating)}
              <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                {tool.rating.toFixed(1)} ({tool.total_reviews})
              </span>
            </div>
            <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
              <EyeIcon className="h-4 w-4 mr-1" />
              {tool.views.toLocaleString()}
            </div>
          </div>

          <div className="flex gap-2">
            <button className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white py-2.5 px-4 rounded-xl text-sm font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg">
              View Details
            </button>
            <button className="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 py-2.5 px-3 rounded-xl transition-all duration-200">
              <PlusIcon className="h-4 w-4" />
            </button>
            <button className="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 py-2.5 px-3 rounded-xl transition-all duration-200">
              <HeartIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  };

  const AnimatedCarousel = ({ title, tools, icon: Icon, color, isActive, onClick }) => {
    const [currentSlide, setCurrentSlide] = useState(0);
    const maxSlides = Math.max(0, tools.length - 3);

    const nextSlide = () => {
      setCurrentSlide(prev => Math.min(prev + 1, maxSlides));
    };

    const prevSlide = () => {
      setCurrentSlide(prev => Math.max(prev - 1, 0));
    };

    return (
      <div className={`mb-12 transition-all duration-500 ${isActive ? 'opacity-100' : 'opacity-70'}`}>
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={onClick}
            className={`flex items-center space-x-3 transition-all duration-300 ${
              isActive 
                ? 'text-purple-600 dark:text-purple-400 scale-105' 
                : 'text-gray-700 dark:text-gray-300 hover:text-purple-600 dark:hover:text-purple-400'
            }`}
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color} ${
              isActive ? 'shadow-lg transform scale-110' : 'shadow-md'
            }`}>
              <Icon className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-2xl font-bold">{title}</h2>
          </button>
          
          {tools.length > 3 && (
            <div className="flex space-x-2">
              <button
                onClick={prevSlide}
                disabled={currentSlide === 0}
                className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <ChevronLeftIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <button
                onClick={nextSlide}
                disabled={currentSlide >= maxSlides}
                className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <ChevronRightIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>
          )}
        </div>
        
        {isActive && (
          <div className="overflow-hidden">
            <div 
              className="flex space-x-6 transition-transform duration-500 ease-in-out"
              style={{ transform: `translateX(-${currentSlide * 33.333}%)` }}
            >
              {tools.map((tool, index) => (
                <CarouselCard key={tool.id} tool={tool} index={index} />
              ))}
            </div>
          </div>
        )}
      </div>
    );
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
      <div className="flex items-center justify-center space-x-2 mt-12">
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={!pagination.has_prev}
          className="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <ChevronLeftIcon className="h-5 w-5" />
        </button>

        {startPage > 1 && (
          <>
            <button
              onClick={() => handlePageChange(1)}
              className="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200"
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
            className={`px-4 py-2 rounded-xl transition-all duration-200 ${
              pageNum === currentPage
                ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow-lg transform scale-105'
                : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
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
              className="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-200"
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={!pagination.has_next}
          className="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <ChevronRightIcon className="h-5 w-5" />
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-purple-900/20">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-grid-pattern opacity-10"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-purple-900/20 to-transparent"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              Discover Amazing
              <span className="block bg-gradient-to-r from-yellow-300 to-orange-300 bg-clip-text text-transparent">
                B2B Tools
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-purple-100 mb-10 max-w-4xl mx-auto">
              Explore the most comprehensive directory of business tools. Find, compare, and choose the perfect solutions for your organization.
            </p>
            
            {/* Hero Search */}
            <div className="max-w-3xl mx-auto">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search for tools, categories, or features..."
                  value={filters.q}
                  onChange={(e) => handleFilterChange('q', e.target.value)}
                  onKeyPress={handleSearch}
                  className="w-full px-6 py-4 pl-14 text-lg rounded-2xl border-0 shadow-2xl focus:outline-none focus:ring-4 focus:ring-yellow-300/50 bg-white/95 backdrop-blur-sm dark:bg-gray-800/95 dark:text-white"
                />
                <MagnifyingGlassIcon className="absolute left-5 top-1/2 transform -translate-y-1/2 h-6 w-6 text-gray-400" />
                <button
                  onClick={handleSearch}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-gradient-to-r from-purple-600 to-purple-700 text-white px-6 py-2 rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-200 font-semibold shadow-lg"
                >
                  Search
                </button>
              </div>
            </div>
            
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">1000+</div>
                <div className="text-purple-200">Tools Listed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">50+</div>
                <div className="text-purple-200">Categories</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">10K+</div>
                <div className="text-purple-200">Reviews</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white mb-2">24/7</div>
                <div className="text-purple-200">AI Powered</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Revolving Carousels Section */}
        {analytics && (
          <section className="mb-16">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Explore by Category
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-300">
                Click on any category below to explore the best tools
              </p>
            </div>

            <div className="space-y-8">
              <AnimatedCarousel
                title="🔥 Trending Now"
                tools={analytics.trending_tools}
                icon={FireIcon}
                color="bg-gradient-to-r from-red-500 to-orange-500"
                isActive={activeCarousel === 'trending'}
                onClick={() => setActiveCarousel(activeCarousel === 'trending' ? '' : 'trending')}
              />

              <AnimatedCarousel
                title="⭐ Top Rated"
                tools={analytics.top_rated_tools}
                icon={StarIcon}
                color="bg-gradient-to-r from-yellow-500 to-orange-500"
                isActive={activeCarousel === 'top_rated'}
                onClick={() => setActiveCarousel(activeCarousel === 'top_rated' ? '' : 'top_rated')}
              />

              <AnimatedCarousel
                title="👁️ Most Viewed"
                tools={analytics.most_viewed_tools}
                icon={EyeIcon}
                color="bg-gradient-to-r from-blue-500 to-indigo-500"
                isActive={activeCarousel === 'most_viewed'}
                onClick={() => setActiveCarousel(activeCarousel === 'most_viewed' ? '' : 'most_viewed')}
              />

              <AnimatedCarousel
                title="✨ Featured"
                tools={analytics.featured_tools}
                icon={SparklesIcon}
                color="bg-gradient-to-r from-purple-500 to-pink-500"
                isActive={activeCarousel === 'featured'}
                onClick={() => setActiveCarousel(activeCarousel === 'featured' ? '' : 'featured')}
              />

              <AnimatedCarousel
                title="🚀 New Arrivals"
                tools={analytics.newest_tools}
                icon={ClockIcon}
                color="bg-gradient-to-r from-green-500 to-teal-500"
                isActive={activeCarousel === 'newest'}
                onClick={() => setActiveCarousel(activeCarousel === 'newest' ? '' : 'newest')}
              />

              <AnimatedCarousel
                title="🔥 Hot Picks"
                tools={analytics.hot_tools}
                icon={FireIcon}
                color="bg-gradient-to-r from-orange-500 to-red-500"
                isActive={activeCarousel === 'hot'}
                onClick={() => setActiveCarousel(activeCarousel === 'hot' ? '' : 'hot')}
              />
            </div>
          </section>
        )}

        {/* Filters and Tools Section */}
        <section className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-8 mb-12">
          {/* Filter Controls */}
          <div className="flex flex-col lg:flex-row gap-6 mb-8">
            {/* Search and View Controls */}
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search tools..."
                  value={filters.q}
                  onChange={(e) => handleFilterChange('q', e.target.value)}
                  onKeyPress={handleSearch}
                  className="w-full px-4 py-3 pl-12 border border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                />
                <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              </div>
            </div>

            {/* View Mode Toggle */}
            <div className="flex rounded-xl border border-gray-300 dark:border-gray-600 overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-4 py-3 transition-all duration-200 ${
                  viewMode === 'grid'
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                <Squares2X2Icon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-4 py-3 transition-all duration-200 ${
                  viewMode === 'table'
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                <ListBulletIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Filter Button */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg"
            >
              <AdjustmentsHorizontalIcon className="h-5 w-5" />
              <span>Filters</span>
              {Object.values(filters).some(value => value && value !== 'relevance' && value !== '') && (
                <span className="bg-yellow-400 text-purple-900 text-xs rounded-full h-6 w-6 flex items-center justify-center font-bold">
                  !
                </span>
              )}
            </button>
          </div>

          {/* Advanced Filters Panel */}
          {showFilters && (
            <div className="bg-gray-50 dark:bg-gray-900 rounded-2xl p-6 mb-8 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Advanced Filters</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={clearAllFilters}
                    className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  >
                    Clear All
                  </button>
                  <button
                    onClick={() => setShowFilters(false)}
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Category
                  </label>
                  <select
                    value={filters.category_id}
                    onChange={(e) => handleFilterChange('category_id', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Categories</option>
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>{category.name}</option>
                    ))}
                  </select>
                </div>

                {/* Pricing Model Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Pricing
                  </label>
                  <select
                    value={filters.pricing_model}
                    onChange={(e) => handleFilterChange('pricing_model', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Pricing</option>
                    <option value="Free">Free</option>
                    <option value="Freemium">Freemium</option>
                    <option value="Paid">Paid</option>
                  </select>
                </div>

                {/* Company Size Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Company Size
                  </label>
                  <select
                    value={filters.company_size}
                    onChange={(e) => handleFilterChange('company_size', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Sizes</option>
                    <option value="Startup">Startup</option>
                    <option value="SMB">Small & Medium</option>
                    <option value="Enterprise">Enterprise</option>
                  </select>
                </div>

                {/* Sort Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Sort By
                  </label>
                  <select
                    value={filters.sort_by}
                    onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="relevance">Most Relevant</option>
                    <option value="rating">Highest Rated</option>
                    <option value="trending">Trending</option>
                    <option value="views">Most Viewed</option>
                    <option value="newest">Newest</option>
                    <option value="name">Name (A-Z)</option>
                  </select>
                </div>
              </div>

              {/* Special Filters */}
              <div className="mt-6 flex flex-wrap gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.is_hot === true}
                    onChange={(e) => handleFilterChange('is_hot', e.target.checked ? true : null)}
                    className="mr-2 text-purple-600 focus:ring-purple-500 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Hot Tools Only</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.is_featured === true}
                    onChange={(e) => handleFilterChange('is_featured', e.target.checked ? true : null)}
                    className="mr-2 text-purple-600 focus:ring-purple-500 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Featured Tools Only</span>
                </label>
              </div>
            </div>
          )}

          {/* Active Filters Display */}
          {Object.entries(filters).some(([key, value]) => value && value !== 'relevance' && value !== '') && (
            <div className="mb-6 flex flex-wrap gap-2">
              {Object.entries(filters).map(([key, value]) => {
                if (!value || value === 'relevance' || value === '') return null;
                
                const label = key === 'min_rating' ? `${value}+ stars` :
                             key === 'sort_by' ? `Sort: ${value}` :
                             key === 'q' ? `"${value}"` :
                             `${key.replace('_', ' ')}: ${value}`;
                
                return (
                  <span
                    key={key}
                    className="inline-flex items-center px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-sm rounded-full font-medium"
                  >
                    {label}
                  </span>
                );
              })}
            </div>
          )}

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
          {loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {tools.map(tool => (
                <ToolCard key={tool.id} tool={tool} />
              ))}
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="py-4 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Tool
                      </th>
                      <th className="py-4 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="py-4 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Pricing
                      </th>
                      <th className="py-4 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Rating
                      </th>
                      <th className="py-4 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Views
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {tools.map(tool => (
                      <tr key={tool.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
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
                              <div className="font-semibold text-gray-900 dark:text-white">
                                {tool.name}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {tool.company_size}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-900 dark:text-white">
                          {categories.find(cat => cat.id === tool.category_id)?.name || 'N/A'}
                        </td>
                        <td className="py-4 px-6">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            tool.pricing_model === 'Free' ? 'bg-green-100 text-green-800' :
                            tool.pricing_model === 'Freemium' ? 'bg-blue-100 text-blue-800' :
                            'bg-orange-100 text-orange-800'
                          }`}>
                            {tool.pricing_model || 'N/A'}
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
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!loading && tools.length === 0 && (
            <div className="text-center py-16">
              <div className="text-gray-400 mb-6">
                <FunnelIcon className="h-20 w-20 mx-auto" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                No tools found
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
                Try adjusting your search criteria or filters to find the tools you're looking for.
              </p>
              <button
                onClick={clearAllFilters}
                className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-6 py-3 rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-200 font-semibold"
              >
                Clear All Filters
              </button>
            </div>
          )}

          {/* Pagination */}
          <Pagination />
        </section>
      </div>
    </div>
  );
};

export default DiscoverPage;