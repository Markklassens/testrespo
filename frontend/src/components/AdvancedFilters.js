import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Select from 'react-select';
import { 
  FunnelIcon, 
  XMarkIcon, 
  ChevronDownIcon, 
  ChevronUpIcon,
  AdjustmentsHorizontalIcon 
} from '@heroicons/react/24/outline';
import api from '../utils/api';

const AdvancedFilters = ({ isOpen, onClose, onApply, filters, setFilters }) => {
  const [localFilters, setLocalFilters] = useState(filters);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [collapsedSections, setCollapsedSections] = useState({
    basic: false,
    advanced: true,
    business: true,
    location: true
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    if (selectedCategory) {
      fetchSubcategories(selectedCategory.value);
    }
  }, [selectedCategory]);

  useEffect(() => {
    setLocalFilters(filters);
    if (filters.category_id) {
      const category = categories.find(cat => cat.id === filters.category_id);
      setSelectedCategory(category ? { value: category.id, label: category.name } : null);
    }
  }, [filters, categories]);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/api/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchSubcategories = async (categoryId) => {
    try {
      const response = await api.get(`/api/subcategories?category_id=${categoryId}`);
      setSubcategories(response.data);
    } catch (error) {
      console.error('Error fetching subcategories:', error);
    }
  };

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const pricingOptions = [
    { value: '', label: 'All Pricing Models' },
    { value: 'Free', label: 'Free' },
    { value: 'Freemium', label: 'Freemium' },
    { value: 'Paid', label: 'Paid' }
  ];

  const companySizeOptions = [
    { value: '', label: 'All Company Sizes' },
    { value: 'Startup', label: 'Startup (1-10 employees)' },
    { value: 'SMB', label: 'Small & Medium Business (11-500)' },
    { value: 'Enterprise', label: 'Enterprise (500+)' },
    { value: 'All', label: 'All Sizes' }
  ];

  const industryOptions = [
    { value: '', label: 'All Industries' },
    { value: 'Technology', label: 'Technology' },
    { value: 'Finance', label: 'Finance & Banking' },
    { value: 'Healthcare', label: 'Healthcare' },
    { value: 'Education', label: 'Education' },
    { value: 'Retail', label: 'Retail & E-commerce' },
    { value: 'Manufacturing', label: 'Manufacturing' },
    { value: 'Marketing', label: 'Marketing & Advertising' },
    { value: 'Real Estate', label: 'Real Estate' },
    { value: 'Legal', label: 'Legal Services' },
    { value: 'Consulting', label: 'Consulting' }
  ];

  const employeeSizeOptions = [
    { value: '', label: 'All Employee Counts' },
    { value: '1-10', label: '1-10 employees' },
    { value: '11-50', label: '11-50 employees' },
    { value: '51-200', label: '51-200 employees' },
    { value: '201-1000', label: '201-1000 employees' },
    { value: '1000+', label: '1000+ employees' }
  ];

  const revenueRangeOptions = [
    { value: '', label: 'All Revenue Ranges' },
    { value: '<1M', label: 'Under $1M' },
    { value: '1M-10M', label: '$1M - $10M' },
    { value: '10M-100M', label: '$10M - $100M' },
    { value: '100M+', label: '$100M+' }
  ];

  const sortOptions = [
    { value: 'relevance', label: 'Most Relevant' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'trending', label: 'Trending' },
    { value: 'views', label: 'Most Viewed' },
    { value: 'newest', label: 'Newest First' },
    { value: 'oldest', label: 'Oldest First' },
    { value: 'name', label: 'Name (A-Z)' }
  ];

  const ratingOptions = [
    { value: null, label: 'Any Rating' },
    { value: 4.5, label: '4.5+ Stars' },
    { value: 4.0, label: '4.0+ Stars' },
    { value: 3.5, label: '3.5+ Stars' },
    { value: 3.0, label: '3.0+ Stars' }
  ];

  const categoryOptions = [
    { value: '', label: 'All Categories' },
    ...categories.map(cat => ({ value: cat.id, label: cat.name }))
  ];

  const subcategoryOptions = [
    { value: '', label: 'All Subcategories' },
    ...subcategories.map(subcat => ({ value: subcat.id, label: subcat.name }))
  ];

  const handleLocalFilterChange = (key, value) => {
    setLocalFilters(prev => ({ ...prev, [key]: value }));
    
    if (key === 'category_id') {
      setSelectedCategory(value ? categoryOptions.find(opt => opt.value === value) : null);
      // Reset subcategory when category changes
      setLocalFilters(prev => ({ ...prev, subcategory_id: '' }));
    }
  };

  const handleApplyFilters = () => {
    setFilters(localFilters);
    onApply();
    onClose();
  };

  const handleClearFilters = () => {
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
    setLocalFilters(clearedFilters);
    setSelectedCategory(null);
    setFilters(clearedFilters);
  };

  const customSelectStyles = {
    control: (provided, state) => ({
      ...provided,
      backgroundColor: 'var(--bg-color)',
      borderColor: state.isFocused ? '#7c3aed' : '#d1d5db',
      color: 'var(--text-color)',
      minHeight: '40px'
    }),
    menu: (provided) => ({
      ...provided,
      backgroundColor: 'var(--bg-color)',
      border: '1px solid #d1d5db'
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected ? '#7c3aed' : state.isFocused ? '#f3f4f6' : 'transparent',
      color: state.isSelected ? 'white' : 'var(--text-color)'
    }),
    singleValue: (provided) => ({
      ...provided,
      color: 'var(--text-color)'
    })
  };

  const FilterSection = ({ title, sectionKey, children }) => (
    <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
      <button
        onClick={() => toggleSection(sectionKey)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {collapsedSections[sectionKey] ? (
          <ChevronDownIcon className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronUpIcon className="h-5 w-5 text-gray-500" />
        )}
      </button>
      
      {!collapsedSections[sectionKey] && (
        <div className="mt-4 space-y-4">
          {children}
        </div>
      )}
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <AdjustmentsHorizontalIcon className="h-6 w-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Advanced Filters
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Filter Content */}
        <div className="p-6 space-y-6">
          {/* Basic Filters */}
          <FilterSection title="Basic Filters" sectionKey="basic">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Keywords
              </label>
              <input
                type="text"
                value={localFilters.q || ''}
                onChange={(e) => handleLocalFilterChange('q', e.target.value)}
                placeholder="Search tools, features, or descriptions..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Category & Subcategory */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category
                </label>
                <Select
                  value={categoryOptions.find(opt => opt.value === localFilters.category_id)}
                  onChange={(option) => handleLocalFilterChange('category_id', option?.value || '')}
                  options={categoryOptions}
                  styles={customSelectStyles}
                  placeholder="Select category..."
                  isClearable
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Subcategory
                </label>
                <Select
                  value={subcategoryOptions.find(opt => opt.value === localFilters.subcategory_id)}
                  onChange={(option) => handleLocalFilterChange('subcategory_id', option?.value || '')}
                  options={subcategoryOptions}
                  styles={customSelectStyles}
                  placeholder="Select subcategory..."
                  isClearable
                  isDisabled={!selectedCategory}
                />
              </div>
            </div>

            {/* Pricing Model & Rating */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Pricing Model
                </label>
                <Select
                  value={pricingOptions.find(opt => opt.value === localFilters.pricing_model)}
                  onChange={(option) => handleLocalFilterChange('pricing_model', option?.value || '')}
                  options={pricingOptions}
                  styles={customSelectStyles}
                  placeholder="Select pricing..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Minimum Rating
                </label>
                <Select
                  value={ratingOptions.find(opt => opt.value === localFilters.min_rating)}
                  onChange={(option) => handleLocalFilterChange('min_rating', option?.value || null)}
                  options={ratingOptions}
                  styles={customSelectStyles}
                  placeholder="Select minimum rating..."
                />
              </div>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sort By
              </label>
              <Select
                value={sortOptions.find(opt => opt.value === localFilters.sort_by)}
                onChange={(option) => handleLocalFilterChange('sort_by', option?.value || 'relevance')}
                options={sortOptions}
                styles={customSelectStyles}
                placeholder="Select sort order..."
              />
            </div>
          </FilterSection>

          {/* Advanced Filters */}
          <FilterSection title="Advanced Filters" sectionKey="advanced">
            {/* Special Flags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={localFilters.is_hot === true}
                    onChange={(e) => handleLocalFilterChange('is_hot', e.target.checked ? true : null)}
                    className="mr-2 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Hot/Trending Tools Only</span>
                </label>
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={localFilters.is_featured === true}
                    onChange={(e) => handleLocalFilterChange('is_featured', e.target.checked ? true : null)}
                    className="mr-2 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Featured Tools Only</span>
                </label>
              </div>
            </div>

            {/* Industry */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Industry
              </label>
              <Select
                value={industryOptions.find(opt => opt.value === localFilters.industry)}
                onChange={(option) => handleLocalFilterChange('industry', option?.value || '')}
                options={industryOptions}
                styles={customSelectStyles}
                placeholder="Select industry..."
                isClearable
              />
            </div>
          </FilterSection>

          {/* Business Details */}
          <FilterSection title="Business Details" sectionKey="business">
            {/* Company Size & Employee Size */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Target Company Size
                </label>
                <Select
                  value={companySizeOptions.find(opt => opt.value === localFilters.company_size)}
                  onChange={(option) => handleLocalFilterChange('company_size', option?.value || '')}
                  options={companySizeOptions}
                  styles={customSelectStyles}
                  placeholder="Select company size..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Employee Count
                </label>
                <Select
                  value={employeeSizeOptions.find(opt => opt.value === localFilters.employee_size)}
                  onChange={(option) => handleLocalFilterChange('employee_size', option?.value || '')}
                  options={employeeSizeOptions}
                  styles={customSelectStyles}
                  placeholder="Select employee range..."
                />
              </div>
            </div>

            {/* Revenue Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Revenue Range
              </label>
              <Select
                value={revenueRangeOptions.find(opt => opt.value === localFilters.revenue_range)}
                onChange={(option) => handleLocalFilterChange('revenue_range', option?.value || '')}
                options={revenueRangeOptions}
                styles={customSelectStyles}
                placeholder="Select revenue range..."
                isClearable
              />
            </div>
          </FilterSection>

          {/* Location */}
          <FilterSection title="Location & Geography" sectionKey="location">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Location/Headquarters
              </label>
              <input
                type="text"
                value={localFilters.location || ''}
                onChange={(e) => handleLocalFilterChange('location', e.target.value)}
                placeholder="e.g., San Francisco, USA"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </FilterSection>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <button
            onClick={handleClearFilters}
            className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 font-medium"
          >
            Clear All
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleApplyFilters}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedFilters;