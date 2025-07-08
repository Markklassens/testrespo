import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Select from 'react-select';
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { setFilters, clearFilters } from '../store/slices/toolsSlice';
import { fetchCategories, fetchSubcategories } from '../store/slices/categoriesSlice';

const AdvancedFilters = ({ isOpen, onClose, onApply }) => {
  const dispatch = useDispatch();
  const { filters } = useSelector(state => state.tools);
  const { categories, subcategories } = useSelector(state => state.categories);
  
  const [localFilters, setLocalFilters] = useState(filters);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    dispatch(fetchCategories());
  }, [dispatch]);

  useEffect(() => {
    if (selectedCategory) {
      dispatch(fetchSubcategories(selectedCategory.value));
    }
  }, [selectedCategory, dispatch]);

  useEffect(() => {
    setLocalFilters(filters);
    if (filters.category_id) {
      const category = categories.find(cat => cat.id === filters.category_id);
      setSelectedCategory(category ? { value: category.id, label: category.name } : null);
    }
  }, [filters, categories]);

  const pricingOptions = [
    { value: '', label: 'All Pricing Models' },
    { value: 'Free', label: 'Free' },
    { value: 'Freemium', label: 'Freemium' },
    { value: 'Paid', label: 'Paid' }
  ];

  const companySizeOptions = [
    { value: '', label: 'All Company Sizes' },
    { value: 'Startup', label: 'Startup' },
    { value: 'SMB', label: 'Small & Medium Business' },
    { value: 'Enterprise', label: 'Enterprise' },
    { value: 'All', label: 'All Sizes' }
  ];

  const sortOptions = [
    { value: 'relevance', label: 'Most Relevant' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'trending', label: 'Trending' },
    { value: 'views', label: 'Most Viewed' },
    { value: 'newest', label: 'Newest First' },
    { value: 'oldest', label: 'Oldest First' }
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
    dispatch(setFilters(localFilters));
    onApply();
    onClose();
  };

  const handleClearFilters = () => {
    dispatch(clearFilters());
    setLocalFilters({
      search: '',
      category_id: '',
      subcategory_id: '',
      pricing_model: '',
      company_size: '',
      min_rating: null,
      sort_by: 'relevance'
    });
    setSelectedCategory(null);
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-6 w-6 text-purple-600" />
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
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Search Keywords
            </label>
            <input
              type="text"
              value={localFilters.search}
              onChange={(e) => handleLocalFilterChange('search', e.target.value)}
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

          {/* Pricing Model & Company Size */}
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
                Company Size
              </label>
              <Select
                value={companySizeOptions.find(opt => opt.value === localFilters.company_size)}
                onChange={(option) => handleLocalFilterChange('company_size', option?.value || '')}
                options={companySizeOptions}
                styles={customSelectStyles}
                placeholder="Select company size..."
              />
            </div>
          </div>

          {/* Rating & Sort */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          </div>
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