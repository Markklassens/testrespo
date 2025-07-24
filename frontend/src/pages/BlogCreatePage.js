import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { createBlog, updateBlog, fetchCategories } from '../store/slices/blogsSlice';
import EnhancedRichTextEditor from '../components/EnhancedRichTextEditor';
import BlogPreview from '../components/BlogPreview';
import AIContentGenerator from '../components/AIContentGenerator';
import { toast } from 'react-hot-toast';
import { 
  BookmarkIcon, 
  EyeIcon, 
  PencilIcon, 
  SparklesIcon,
  ArrowLeftIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentTextIcon,
  CameraIcon
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid';

const BlogCreatePage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { categories, loading } = useSelector(state => state.blogs);
  const { user } = useSelector(state => state.auth);
  
  // Blog form state
  const [blog, setBlog] = useState({
    title: '',
    content: '',
    category_id: '',
    subcategory_id: '',
    status: 'draft',
    meta_title: '',
    meta_description: '',
    slug: '',
    featured_image: null
  });

  // UI state
  const [showPreview, setShowPreview] = useState(false);
  const [isAIOpen, setIsAIOpen] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('saved'); // 'saving', 'saved', 'error'
  const [wordCount, setWordCount] = useState(0);
  const [readingTime, setReadingTime] = useState(0);
  const [isDirty, setIsDirty] = useState(false);
  const [errors, setErrors] = useState({});

  // Auto-save functionality
  const autoSaveTimer = useRef(null);
  const lastSavedVersion = useRef('');

  // Auto-save effect
  useEffect(() => {
    if (isDirty && blog.title && blog.content) {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current);
      }
      
      autoSaveTimer.current = setTimeout(() => {
        saveAsDraft();
      }, 30000); // Auto-save every 30 seconds
    }

    return () => {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current);
      }
    };
  }, [blog, isDirty]);

  // Load categories on mount
  useEffect(() => {
    dispatch(fetchCategories());
    
    // Load draft from localStorage
    const savedDraft = localStorage.getItem('blog_draft');
    if (savedDraft) {
      try {
        const draft = JSON.parse(savedDraft);
        setBlog(draft);
        setIsDirty(true);
      } catch (error) {
        console.error('Error loading draft:', error);
      }
    }
  }, [dispatch]);

  // Calculate word count and reading time
  useEffect(() => {
    if (blog.content) {
      const text = blog.content.replace(/<[^>]*>/g, ''); // Remove HTML tags
      const words = text.trim().split(/\s+/).filter(word => word.length > 0);
      const count = words.length;
      const time = Math.ceil(count / 200); // Average 200 words per minute
      
      setWordCount(count);
      setReadingTime(time);
    } else {
      setWordCount(0);
      setReadingTime(0);
    }
  }, [blog.content]);

  // Generate slug from title
  const generateSlug = useCallback((title) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9 -]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  }, []);

  // Update blog field
  const updateBlogField = useCallback((field, value) => {
    setBlog(prev => {
      const updated = { ...prev, [field]: value };
      
      // Auto-generate slug from title
      if (field === 'title' && value && !prev.slug) {
        updated.slug = generateSlug(value);
      }
      
      // Auto-generate meta title from title
      if (field === 'title' && value && !prev.meta_title) {
        updated.meta_title = value.slice(0, 60);
      }
      
      return updated;
    });
    
    setIsDirty(true);
    setErrors(prev => ({ ...prev, [field]: '' }));
  }, [generateSlug]);

  // Save as draft
  const saveAsDraft = useCallback(async () => {
    if (!blog.title || !blog.content) return;
    
    const currentVersion = JSON.stringify(blog);
    if (currentVersion === lastSavedVersion.current) return;
    
    setAutoSaveStatus('saving');
    
    try {
      // Save to localStorage
      localStorage.setItem('blog_draft', currentVersion);
      
      // Save to backend if user is logged in
      if (user) {
        const draftData = {
          ...blog,
          status: 'draft'
        };
        
        await dispatch(createBlog(draftData)).unwrap();
      }
      
      setAutoSaveStatus('saved');
      setIsDirty(false);
      lastSavedVersion.current = currentVersion;
      
    } catch (error) {
      setAutoSaveStatus('error');
      console.error('Auto-save failed:', error);
    }
  }, [blog, dispatch, user]);

  // Manual save as draft
  const handleSaveAsDraft = useCallback(async () => {
    if (!validateForm()) return;
    
    setAutoSaveStatus('saving');
    
    try {
      const draftData = {
        ...blog,
        status: 'draft'
      };
      
      await dispatch(createBlog(draftData)).unwrap();
      localStorage.removeItem('blog_draft');
      setAutoSaveStatus('saved');
      setIsDirty(false);
      
      toast.success('Blog saved as draft!');
      
    } catch (error) {
      setAutoSaveStatus('error');
      toast.error('Failed to save draft');
    }
  }, [blog, dispatch]);

  // Publish blog
  const handlePublish = useCallback(async () => {
    if (!validateForm()) return;
    
    try {
      const publishData = {
        ...blog,
        status: 'published'
      };
      
      await dispatch(createBlog(publishData)).unwrap();
      localStorage.removeItem('blog_draft');
      
      toast.success('Blog published successfully!');
      navigate('/blogs');
      
    } catch (error) {
      toast.error('Failed to publish blog');
    }
  }, [blog, dispatch, navigate]);

  // Validate form
  const validateForm = useCallback(() => {
    const newErrors = {};
    
    if (!blog.title.trim()) {
      newErrors.title = 'Title is required';
    }
    
    if (!blog.content.trim()) {
      newErrors.content = 'Content is required';
    }
    
    if (!blog.category_id) {
      newErrors.category_id = 'Category is required';
    }
    
    if (blog.meta_title && blog.meta_title.length > 60) {
      newErrors.meta_title = 'Meta title must be under 60 characters';
    }
    
    if (blog.meta_description && blog.meta_description.length > 160) {
      newErrors.meta_description = 'Meta description must be under 160 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [blog]);

  // Handle AI content insertion
  const handleAIContentInsert = useCallback((content, type) => {
    if (type === 'full_blog') {
      updateBlogField('content', content);
    } else if (type === 'title') {
      updateBlogField('title', content);
    } else if (type === 'introduction') {
      const currentContent = blog.content || '';
      updateBlogField('content', content + '\n\n' + currentContent);
    } else if (type === 'outline') {
      const currentContent = blog.content || '';
      updateBlogField('content', currentContent + '\n\n' + content);
    }
    
    toast.success('AI content inserted successfully!');
  }, [blog.content, updateBlogField]);

  // Handle featured image upload
  const handleFeaturedImageUpload = useCallback((event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        updateBlogField('featured_image', e.target.result);
      };
      reader.readAsDataURL(file);
    }
  }, [updateBlogField]);

  // Get subcategories for selected category
  const getSubcategories = useCallback(() => {
    if (!blog.category_id) return [];
    const category = categories.find(c => c.id === blog.category_id);
    return category ? category.subcategories || [] : [];
  }, [categories, blog.category_id]);

  // Auto-save status icon
  const getAutoSaveIcon = () => {
    switch (autoSaveStatus) {
      case 'saving':
        return <ClockIcon className="h-4 w-4 text-yellow-500 animate-spin" />;
      case 'saved':
        return <CheckCircleIconSolid className="h-4 w-4 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const subcategories = getSubcategories();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/blogs')}
                className="flex items-center space-x-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5" />
                <span>Back to Blogs</span>
              </button>
              <div className="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Create New Blog
              </h1>
            </div>
            
            {/* Auto-save status */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                {getAutoSaveIcon()}
                <span>
                  {autoSaveStatus === 'saving' ? 'Saving...' : 
                   autoSaveStatus === 'saved' ? 'Saved' : 
                   autoSaveStatus === 'error' ? 'Save failed' : 'Not saved'}
                </span>
              </div>
              
              {/* View toggle */}
              <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setShowPreview(false)}
                  className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    !showPreview 
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm' 
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <PencilIcon className="h-4 w-4" />
                  <span>Edit</span>
                </button>
                <button
                  onClick={() => setShowPreview(true)}
                  className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    showPreview 
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm' 
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <EyeIcon className="h-4 w-4" />
                  <span>Preview</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Editor Section */}
          <div className={`xl:col-span-2 ${showPreview ? 'hidden xl:block' : ''}`}>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-6">
                {/* Blog Title */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Blog Title *
                  </label>
                  <input
                    type="text"
                    value={blog.title}
                    onChange={(e) => updateBlogField('title', e.target.value)}
                    className={`w-full px-4 py-3 text-xl font-semibold border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                      errors.title ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    }`}
                    placeholder="Enter your blog title..."
                  />
                  {errors.title && (
                    <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.title}</p>
                  )}
                </div>

                {/* Featured Image */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Featured Image
                  </label>
                  <div className="flex items-center space-x-4">
                    {blog.featured_image && (
                      <img
                        src={blog.featured_image}
                        alt="Featured"
                        className="w-16 h-16 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
                      />
                    )}
                    <label className="flex items-center space-x-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                      <CameraIcon className="h-5 w-5 text-gray-500" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {blog.featured_image ? 'Change Image' : 'Upload Image'}
                      </span>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFeaturedImageUpload}
                        className="hidden"
                      />
                    </label>
                  </div>
                </div>

                {/* Categories */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Category *
                    </label>
                    <select
                      value={blog.category_id}
                      onChange={(e) => {
                        updateBlogField('category_id', e.target.value);
                        updateBlogField('subcategory_id', ''); // Reset subcategory
                      }}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                        errors.category_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                      }`}
                    >
                      <option value="">Select a category</option>
                      {categories.map(category => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                    {errors.category_id && (
                      <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.category_id}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Subcategory
                    </label>
                    <select
                      value={blog.subcategory_id}
                      onChange={(e) => updateBlogField('subcategory_id', e.target.value)}
                      disabled={!blog.category_id || subcategories.length === 0}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <option value="">Select a subcategory</option>
                      {subcategories.map(sub => (
                        <option key={sub.id} value={sub.id}>
                          {sub.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Content Editor */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Content *
                    </label>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                      <span>{wordCount} words</span>
                      <span>•</span>
                      <span>{readingTime} min read</span>
                    </div>
                  </div>
                  <div className={`border rounded-lg ${errors.content ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`}>
                    <EnhancedRichTextEditor
                      value={blog.content}
                      onChange={(content) => updateBlogField('content', content)}
                      placeholder="Start writing your blog content..."
                      height="400px"
                    />
                  </div>
                  {errors.content && (
                    <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.content}</p>
                  )}
                </div>

                {/* SEO Section */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">SEO Settings</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Meta Title ({blog.meta_title.length}/60)
                      </label>
                      <input
                        type="text"
                        value={blog.meta_title}
                        onChange={(e) => updateBlogField('meta_title', e.target.value)}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                          errors.meta_title ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                        }`}
                        placeholder="SEO optimized title for search engines"
                      />
                      {errors.meta_title && (
                        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.meta_title}</p>
                      )}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Meta Description ({blog.meta_description.length}/160)
                      </label>
                      <textarea
                        value={blog.meta_description}
                        onChange={(e) => updateBlogField('meta_description', e.target.value)}
                        rows={3}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                          errors.meta_description ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                        }`}
                        placeholder="Brief description that appears in search results"
                      />
                      {errors.meta_description && (
                        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.meta_description}</p>
                      )}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        URL Slug
                      </label>
                      <input
                        type="text"
                        value={blog.slug}
                        onChange={(e) => updateBlogField('slug', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="url-friendly-slug"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 mt-8">
                  <button
                    onClick={handleSaveAsDraft}
                    disabled={loading || !blog.title || !blog.content}
                    className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <BookmarkIcon className="h-5 w-5" />
                    <span>Save as Draft</span>
                  </button>
                  
                  <button
                    onClick={handlePublish}
                    disabled={loading || !blog.title || !blog.content || !blog.category_id}
                    className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <CheckCircleIcon className="h-5 w-5" />
                    <span>Publish Blog</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Preview & AI Section */}
          <div className={`xl:col-span-1 ${!showPreview ? 'hidden xl:block' : ''}`}>
            <div className="space-y-6">
              {/* Preview Section */}
              {showPreview && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Preview</h3>
                    <BlogPreview blog={blog} />
                  </div>
                </div>
              )}

              {/* AI Content Generator */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="p-6">
                  <button
                    onClick={() => setIsAIOpen(!isAIOpen)}
                    className="flex items-center justify-between w-full text-left"
                  >
                    <div className="flex items-center space-x-2">
                      <SparklesIcon className="h-5 w-5 text-purple-600" />
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        AI Content Generator
                      </h3>
                    </div>
                    {isAIOpen ? (
                      <ChevronUpIcon className="h-5 w-5 text-gray-500" />
                    ) : (
                      <ChevronDownIcon className="h-5 w-5 text-gray-500" />
                    )}
                  </button>
                  
                  {isAIOpen && (
                    <div className="mt-4">
                      <AIContentGenerator
                        onContentGenerated={handleAIContentInsert}
                        blogTitle={blog.title}
                        blogCategory={categories.find(c => c.id === blog.category_id)?.name || ''}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlogCreatePage;