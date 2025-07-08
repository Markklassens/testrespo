import React, { useState } from 'react';
import { 
  SparklesIcon, 
  XMarkIcon, 
  DocumentTextIcon,
  CogIcon,
  ClipboardDocumentIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../utils/api';

const AIContentGenerator = ({ isOpen, onClose, onContentGenerated }) => {
  const [prompt, setPrompt] = useState('');
  const [contentType, setContentType] = useState('blog');
  const [provider, setProvider] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [copied, setCopied] = useState(false);

  const contentTypes = [
    { value: 'blog', label: 'Blog Post', description: 'Generate a full blog post with introduction, body, and conclusion' },
    { value: 'tool_description', label: 'Tool Description', description: 'Create compelling product descriptions' },
    { value: 'meta_title', label: 'SEO Meta Title', description: 'Generate SEO-optimized meta titles' },
    { value: 'meta_description', label: 'SEO Meta Description', description: 'Create compelling meta descriptions' },
    { value: 'seo_content', label: 'SEO Content', description: 'Generate search-engine optimized content' }
  ];

  const providers = [
    { value: 'auto', label: 'Auto Select', description: 'Automatically choose the best available provider' },
    { value: 'groq', label: 'Groq (Fast)', description: 'Fast generation with Llama models' },
    { value: 'claude', label: 'Claude (Quality)', description: 'High-quality content with Claude AI' }
  ];

  const samplePrompts = {
    blog: [
      "Write a comprehensive guide about CRM software for small businesses",
      "Create a blog post comparing project management tools",
      "Write about the benefits of marketing automation for B2B companies"
    ],
    tool_description: [
      "Describe a project management tool that helps teams collaborate better",
      "Write about a CRM system designed for sales teams",
      "Describe an email marketing platform with automation features"
    ],
    meta_title: [
      "Best CRM Software for Small Business 2024",
      "Project Management Tools Comparison",
      "Email Marketing Automation Guide"
    ],
    meta_description: [
      "Discover the best CRM software for small businesses. Compare features, pricing, and reviews.",
      "Compare top project management tools. Find the perfect solution for your team's needs.",
      "Learn how email marketing automation can boost your business growth and engagement."
    ],
    seo_content: [
      "Write SEO content about project management software targeting 'best project management tools'",
      "Create SEO-optimized content about CRM systems for 'small business CRM software'",
      "Generate content about email marketing targeting 'email automation tools'"
    ]
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/api/ai/generate-content', {
        prompt: prompt.trim(),
        content_type: contentType,
        provider: provider === 'auto' ? null : provider
      });

      setGeneratedContent(response.data.content);
      toast.success(`Content generated using ${response.data.provider}`);
    } catch (error) {
      if (error.response?.status === 500) {
        toast.error('AI service unavailable. Please check your API keys or try again later.');
      } else {
        toast.error('Failed to generate content. Please try again.');
      }
      console.error('AI generation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(generatedContent);
      setCopied(true);
      toast.success('Content copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy content');
    }
  };

  const handleUseContent = () => {
    if (onContentGenerated) {
      onContentGenerated(generatedContent);
    }
    onClose();
  };

  const handlePromptSample = (sample) => {
    setPrompt(sample);
  };

  const resetGenerator = () => {
    setPrompt('');
    setGeneratedContent('');
    setCopied(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="h-6 w-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              AI Content Generator
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Section */}
            <div className="space-y-6">
              {/* Content Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Content Type
                </label>
                <select
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                >
                  {contentTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {contentTypes.find(t => t.value === contentType)?.description}
                </p>
              </div>

              {/* AI Provider */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  AI Provider
                </label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                >
                  {providers.map(prov => (
                    <option key={prov.value} value={prov.value}>
                      {prov.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {providers.find(p => p.value === provider)?.description}
                </p>
              </div>

              {/* Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Prompt
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe what you want to generate..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              {/* Sample Prompts */}
              {samplePrompts[contentType] && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Sample Prompts
                  </label>
                  <div className="space-y-2">
                    {samplePrompts[contentType].map((sample, index) => (
                      <button
                        key={index}
                        onClick={() => handlePromptSample(sample)}
                        className="w-full text-left p-2 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                      >
                        {sample}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <>
                    <CogIcon className="h-5 w-5 animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <SparklesIcon className="h-5 w-5" />
                    <span>Generate Content</span>
                  </>
                )}
              </button>
            </div>

            {/* Output Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Generated Content
                </label>
                {generatedContent && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCopy}
                      className="flex items-center space-x-1 px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      {copied ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <ClipboardDocumentIcon className="h-4 w-4" />
                      )}
                      <span>{copied ? 'Copied!' : 'Copy'}</span>
                    </button>
                    <button
                      onClick={resetGenerator}
                      className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      Reset
                    </button>
                  </div>
                )}
              </div>

              <div className="relative">
                <textarea
                  value={generatedContent}
                  onChange={(e) => setGeneratedContent(e.target.value)}
                  placeholder="Generated content will appear here..."
                  rows={12}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                />
                {loading && (
                  <div className="absolute inset-0 bg-white dark:bg-gray-700 bg-opacity-75 flex items-center justify-center rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CogIcon className="h-6 w-6 animate-spin text-purple-600" />
                      <span className="text-gray-600 dark:text-gray-300">Generating content...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              {generatedContent && (
                <div className="flex space-x-3">
                  <button
                    onClick={handleUseContent}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg transition-colors"
                  >
                    Use This Content
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={loading || !prompt.trim()}
                    className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Regenerate
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              <p>💡 Tip: Be specific in your prompts for better results</p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIContentGenerator;