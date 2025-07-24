import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
  DocumentTextIcon,
  EyeIcon,
  BeakerIcon,
  SparklesIcon,
  CloudArrowUpIcon,
  ClockIcon,
  ArrowLeftIcon,
  BookmarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  AdjustmentsHorizontalIcon,
  LightBulbIcon,
  PencilSquareIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import EnhancedRichTextEditor from '../components/EnhancedRichTextEditor';
import { createBlog, updateBlog, fetchBlog } from '../store/slices/blogsSlice';
import { fetchCategories } from '../store/slices/categoriesSlice';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';

const BlogEditor = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { blogId } = useParams();
  const { user } = useAuth();
  const { categories } = useSelector(state => state.categories);
  
  // Editor state
  const [blogData, setBlogData] = useState({
    title: '',
    content: '',
    excerpt: '',
    category_id: '',
    slug: '',
    meta_title: '',
    meta_description: '',
    status: 'draft'
  });
  
  // UI state
  const [activeView, setActiveView] = useState('editor'); // 'editor', 'preview', 'split'
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('saved'); // 'saving', 'saved', 'error'
  const [wordCount, setWordCount] = useState(0);
  const [readingTime, setReadingTime] = useState(0);
  const [lastSaved, setLastSaved] = useState(null);
  const [draftId, setDraftId] = useState(null);
  
  // AI state
  const [aiRequest, setAiRequest] = useState({
    prompt: '',
    content_type: 'full_post',
    tone: 'professional',
    length: 'medium'
  });
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [titleSuggestions, setTitleSuggestions] = useState([]);
  
  // Auto-save timer
  const autoSaveTimer = useRef(null);
  const localSaveTimer = useRef(null);
  
  // Load blog data and categories on mount
  useEffect(() => {
    dispatch(fetchCategories());
    
    if (blogId) {
      dispatch(fetchBlog(blogId))
        .unwrap()
        .then(blog => {
          setBlogData({
            title: blog.title,
            content: blog.content,
            excerpt: blog.excerpt || '',
            category_id: blog.category_id,
            slug: blog.slug,
            meta_title: blog.meta_title || blog.title,
            meta_description: blog.meta_description || '',
            status: blog.status
          });
        })
        .catch(error => {
          toast.error('Failed to load blog');
          navigate('/blogs');
        });
    }
    
    // Load saved draft from localStorage
    const savedDraft = localStorage.getItem('blog_draft');
    if (savedDraft && !blogId) {
      try {
        const draft = JSON.parse(savedDraft);
        setBlogData(draft.data);
        setDraftId(draft.draftId);
        toast.success('Restored unsaved draft');
      } catch (error) {
        console.error('Error loading draft:', error);
      }
    }
  }, [dispatch, blogId, navigate]);
  
  // Auto-save to localStorage
  const saveToLocalStorage = useCallback(() => {
    const draftData = {
      data: blogData,
      draftId: draftId,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem('blog_draft', JSON.stringify(draftData));
  }, [blogData, draftId]);
  
  // Auto-save to database
  const saveToDatabase = useCallback(async () => {
    if (!blogData.title && !blogData.content) return;
    
    setAutoSaveStatus('saving');
    
    try {
      const response = await api.post('/api/ai-blog/auto-save-draft', {
        draft_id: draftId,
        title: blogData.title,
        content: blogData.content,
        category_id: blogData.category_id,
        meta_data: {
          meta_title: blogData.meta_title,
          meta_description: blogData.meta_description
        }
      });
      
      if (!draftId) {
        setDraftId(response.data.draft_id);
      }
      
      setAutoSaveStatus('saved');
      setLastSaved(new Date());
      
    } catch (error) {
      console.error('Auto-save failed:', error);
      setAutoSaveStatus('error');
    }
  }, [blogData, draftId]);
  
  // Update word count and reading time
  useEffect(() => {
    const words = blogData.content ? blogData.content.replace(/<[^>]*>/g, '').split(/\s+/).filter(word => word.length > 0).length : 0;
    setWordCount(words);
    setReadingTime(Math.max(1, Math.round(words / 200)));
  }, [blogData.content]);
  
  // Auto-save timers
  useEffect(() => {
    // Clear existing timers
    if (localSaveTimer.current) clearTimeout(localSaveTimer.current);
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    
    // Save to localStorage immediately
    localSaveTimer.current = setTimeout(saveToLocalStorage, 1000);
    
    // Save to database after 5 seconds
    autoSaveTimer.current = setTimeout(saveToDatabase, 5000);
    
    return () => {
      if (localSaveTimer.current) clearTimeout(localSaveTimer.current);
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, [blogData, saveToLocalStorage, saveToDatabase]);
  
  // Generate slug from title
  const generateSlug = (title) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
  };
  
  // Handle title change
  const handleTitleChange = (title) => {
    setBlogData(prev => ({
      ...prev,
      title,
      slug: generateSlug(title),
      meta_title: title
    }));
  };
  
  // Handle content change
  const handleContentChange = (content) => {
    setBlogData(prev => ({
      ...prev,
      content,
      excerpt: content.replace(/<[^>]*>/g, '').substring(0, 150) + '...'
    }));
  };
  
  // AI content generation
  const generateAIContent = async () => {
    if (!aiRequest.prompt) {
      toast.error('Please enter a prompt');
      return;
    }
    
    setAiLoading(true);
    
    try {
      const response = await api.post('/api/ai-blog/generate-content', {
        prompt: aiRequest.prompt,
        content_type: aiRequest.content_type,
        existing_content: blogData.content,
        title: blogData.title,
        category: categories.find(cat => cat.id === blogData.category_id)?.name || '',
        tone: aiRequest.tone,
        length: aiRequest.length
      });
      
      if (response.data.success) {
        const generatedContent = response.data.content;
        
        if (aiRequest.content_type === 'full_post') {
          handleContentChange(generatedContent);
          if (!blogData.title) {
            const lines = generatedContent.split('\n');
            const firstHeading = lines.find(line => line.startsWith('#'));
            if (firstHeading) {
              handleTitleChange(firstHeading.replace(/^#+\s*/, ''));
            }
          }
        } else if (aiRequest.content_type === 'continuation') {
          handleContentChange(blogData.content + '\n\n' + generatedContent);
        } else {
          // For introduction, body, conclusion - add to existing content
          handleContentChange(blogData.content + '\n\n' + generatedContent);
        }
        
        toast.success(`AI content generated (${response.data.word_count} words)`);
        setAiRequest(prev => ({ ...prev, prompt: '' }));
      }
    } catch (error) {
      toast.error('AI generation failed: ' + error.response?.data?.detail || error.message);
    } finally {
      setAiLoading(false);
    }
  };
  
  // Generate title suggestions
  const generateTitleSuggestions = async () => {
    if (!aiRequest.prompt) {
      toast.error('Please enter a topic');
      return;
    }
    
    setAiLoading(true);
    
    try {
      const response = await api.post('/api/ai-blog/generate-titles', {
        topic: aiRequest.prompt,
        category: categories.find(cat => cat.id === blogData.category_id)?.name || ''
      });
      
      if (response.data.success) {
        setTitleSuggestions(response.data.titles);
        toast.success('Title suggestions generated');
      }
    } catch (error) {
      toast.error('Title generation failed');
    } finally {
      setAiLoading(false);
    }
  };
  
  // Improve content with AI
  const improveContent = async (type = 'enhance') => {
    if (!blogData.content) {
      toast.error('No content to improve');
      return;
    }
    
    setAiLoading(true);
    
    try {
      const response = await api.post('/api/ai-blog/improve-content', {
        content: blogData.content,
        improvement_type: type
      });
      
      if (response.data.success) {
        handleContentChange(response.data.content);
        toast.success(`Content ${type}d successfully`);
      }
    } catch (error) {
      toast.error('Content improvement failed');
    } finally {
      setAiLoading(false);
    }
  };
  
  // Save as draft
  const saveDraft = async () => {
    try {
      if (blogId) {
        await dispatch(updateBlog({
          id: blogId,
          data: { ...blogData, status: 'draft' }
        })).unwrap();
      } else {
        await dispatch(createBlog({ ...blogData, status: 'draft' })).unwrap();
      }
      
      // Clear localStorage draft
      localStorage.removeItem('blog_draft');
      
      toast.success('Draft saved successfully');
      navigate('/blogs');
    } catch (error) {
      toast.error('Failed to save draft');
    }
  };
  
  // Publish blog
  const publishBlog = async () => {
    if (!blogData.title || !blogData.content || !blogData.category_id) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      if (blogId) {
        await dispatch(updateBlog({
          id: blogId,
          data: { ...blogData, status: 'published' }
        })).unwrap();
      } else {
        await dispatch(createBlog({ ...blogData, status: 'published' })).unwrap();
      }
      
      // Clear localStorage draft
      localStorage.removeItem('blog_draft');
      
      toast.success('Blog published successfully');
      navigate('/blogs');
    } catch (error) {
      toast.error('Failed to publish blog');
    }
  };
  
  // Render preview content
  const renderPreview = () => {
    return (
      <div className="prose prose-lg max-w-none dark:prose-invert">
        {blogData.title && (
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {blogData.title}
          </h1>
        )}
        
        {blogData.category_id && (
          <div className="mb-6">
            <span className="bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-3 py-1 rounded-full text-sm font-medium">
              {categories.find(cat => cat.id === blogData.category_id)?.name}
            </span>
          </div>
        )}
        
        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400 mb-8 space-x-4">
          <div className="flex items-center">
            <DocumentTextIcon className="h-4 w-4 mr-1" />
            {wordCount} words
          </div>
          <div className="flex items-center">
            <ClockIcon className="h-4 w-4 mr-1" />
            {readingTime} min read
          </div>
        </div>
        
        <div 
          className="blog-content"
          dangerouslySetInnerHTML={{ __html: blogData.content }}
        />
      </div>
    );
  };
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/blogs')}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </button>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                {blogId ? 'Edit Blog' : 'Create New Blog'}
              </h1>
              
              {/* Auto-save status */}
              <div className="flex items-center space-x-2 text-sm">
                {autoSaveStatus === 'saving' && (
                  <div className="flex items-center text-yellow-600">
                    <ArrowPathIcon className="h-4 w-4 mr-1 animate-spin" />
                    Saving...
                  </div>
                )}
                {autoSaveStatus === 'saved' && (
                  <div className="flex items-center text-green-600">
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Saved {lastSaved && ` • ${lastSaved.toLocaleTimeString()}`}
                  </div>
                )}
                {autoSaveStatus === 'error' && (
                  <div className="flex items-center text-red-600">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                    Save failed
                  </div>
                )}
              </div>
            </div>
            
            {/* View toggle and actions */}
            <div className="flex items-center space-x-4">
              {/* View toggle */}
              <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setActiveView('editor')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    activeView === 'editor'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <PencilSquareIcon className="h-4 w-4 mr-1 inline" />
                  Editor
                </button>
                <button
                  onClick={() => setActiveView('split')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    activeView === 'split'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <DocumentTextIcon className="h-4 w-4 mr-1 inline" />
                  Split
                </button>
                <button
                  onClick={() => setActiveView('preview')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    activeView === 'preview'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <EyeIcon className="h-4 w-4 mr-1 inline" />
                  Preview
                </button>
              </div>
              
              {/* AI Panel Toggle */}
              <button
                onClick={() => setAiPanelOpen(!aiPanelOpen)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  aiPanelOpen
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                <SparklesIcon className="h-4 w-4" />
                <span>AI Assistant</span>
              </button>
              
              {/* Action buttons */}
              <button
                onClick={saveDraft}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
              >
                <BookmarkIcon className="h-4 w-4" />
                <span>Save Draft</span>
              </button>
              
              <button
                onClick={publishBlog}
                disabled={!blogData.title || !blogData.content || !blogData.category_id}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                <CloudArrowUpIcon className="h-4 w-4" />
                <span>Publish</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* AI Panel */}
          {aiPanelOpen && (
            <div className="w-80 flex-shrink-0">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 sticky top-8">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <SparklesIcon className="h-5 w-5 mr-2 text-purple-600" />
                  AI Assistant
                </h3>
                
                <div className="space-y-4">
                  {/* Content Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Content Type
                    </label>
                    <select
                      value={aiRequest.content_type}
                      onChange={(e) => setAiRequest(prev => ({ ...prev, content_type: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="full_post">Full Blog Post</option>
                      <option value="introduction">Introduction</option>
                      <option value="body">Main Content</option>
                      <option value="conclusion">Conclusion</option>
                      <option value="continuation">Continue Existing</option>
                    </select>
                  </div>
                  
                  {/* Prompt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Prompt / Topic
                    </label>
                    <textarea
                      value={aiRequest.prompt}
                      onChange={(e) => setAiRequest(prev => ({ ...prev, prompt: e.target.value }))}
                      placeholder="Enter your topic or specific instructions..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                  
                  {/* Tone and Length */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Tone
                      </label>
                      <select
                        value={aiRequest.tone}
                        onChange={(e) => setAiRequest(prev => ({ ...prev, tone: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="professional">Professional</option>
                        <option value="casual">Casual</option>
                        <option value="technical">Technical</option>
                        <option value="friendly">Friendly</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Length
                      </label>
                      <select
                        value={aiRequest.length}
                        onChange={(e) => setAiRequest(prev => ({ ...prev, length: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="short">Short</option>
                        <option value="medium">Medium</option>
                        <option value="long">Long</option>
                      </select>
                    </div>
                  </div>
                  
                  {/* Action buttons */}
                  <div className="space-y-2">
                    <button
                      onClick={generateAIContent}
                      disabled={aiLoading}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
                    >
                      {aiLoading ? (
                        <ArrowPathIcon className="h-4 w-4 animate-spin" />
                      ) : (
                        <BeakerIcon className="h-4 w-4" />
                      )}
                      <span>Generate Content</span>
                    </button>
                    
                    <button
                      onClick={generateTitleSuggestions}
                      disabled={aiLoading}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
                    >
                      <LightBulbIcon className="h-4 w-4" />
                      <span>Title Ideas</span>
                    </button>
                  </div>
                  
                  {/* Content improvement */}
                  {blogData.content && (
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Improve Content
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => improveContent('enhance')}
                          disabled={aiLoading}
                          className="px-3 py-1 bg-green-100 hover:bg-green-200 text-green-800 rounded text-sm font-medium"
                        >
                          Enhance
                        </button>
                        <button
                          onClick={() => improveContent('simplify')}
                          disabled={aiLoading}
                          className="px-3 py-1 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 rounded text-sm font-medium"
                        >
                          Simplify
                        </button>
                        <button
                          onClick={() => improveContent('professional')}
                          disabled={aiLoading}
                          className="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-sm font-medium"
                        >
                          Polish
                        </button>
                        <button
                          onClick={() => improveContent('expand')}
                          disabled={aiLoading}
                          className="px-3 py-1 bg-purple-100 hover:bg-purple-200 text-purple-800 rounded text-sm font-medium"
                        >
                          Expand
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Title suggestions */}
                  {titleSuggestions.length > 0 && (
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Title Suggestions
                      </label>
                      <div className="space-y-2">
                        {titleSuggestions.map((title, index) => (
                          <button
                            key={index}
                            onClick={() => handleTitleChange(title)}
                            className="w-full text-left px-3 py-2 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg text-sm transition-colors"
                          >
                            {title}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* Main content area */}
          <div className="flex-1">
            {/* Blog metadata */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Title */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={blogData.title}
                    onChange={(e) => handleTitleChange(e.target.value)}
                    placeholder="Enter your blog title..."
                    className="w-full px-4 py-3 text-lg border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Category *
                  </label>
                  <select
                    value={blogData.category_id}
                    onChange={(e) => setBlogData(prev => ({ ...prev, category_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">Select a category</option>
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Slug */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    URL Slug
                  </label>
                  <input
                    type="text"
                    value={blogData.slug}
                    onChange={(e) => setBlogData(prev => ({ ...prev, slug: e.target.value }))}
                    placeholder="url-friendly-slug"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                {/* Meta fields */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Meta Title
                  </label>
                  <input
                    type="text"
                    value={blogData.meta_title}
                    onChange={(e) => setBlogData(prev => ({ ...prev, meta_title: e.target.value }))}
                    placeholder="SEO title"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Meta Description
                  </label>
                  <input
                    type="text"
                    value={blogData.meta_description}
                    onChange={(e) => setBlogData(prev => ({ ...prev, meta_description: e.target.value }))}
                    placeholder="SEO description"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>
            
            {/* Editor/Preview Area */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
              {activeView === 'editor' && (
                <div className="p-6">
                  <EnhancedRichTextEditor
                    value={blogData.content}
                    onChange={handleContentChange}
                    placeholder="Start writing your blog post..."
                    height="600px"
                  />
                </div>
              )}
              
              {activeView === 'preview' && (
                <div className="p-6">
                  {renderPreview()}
                </div>
              )}
              
              {activeView === 'split' && (
                <div className="flex h-[700px]">
                  <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 p-6">
                    <EnhancedRichTextEditor
                      value={blogData.content}
                      onChange={handleContentChange}
                      placeholder="Start writing your blog post..."
                      height="600px"
                    />
                  </div>
                  <div className="w-1/2 p-6 overflow-y-auto">
                    {renderPreview()}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlogEditor;