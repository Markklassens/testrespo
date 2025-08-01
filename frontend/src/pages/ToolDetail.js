import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  StarIcon, 
  EyeIcon, 
  HeartIcon, 
  ShareIcon, 
  GlobeAltIcon,
  BuildingOffice2Icon,
  UserGroupIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  CheckCircleIcon,
  LinkIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import { Helmet } from 'react-helmet-async';
import LoadingSpinner from '../components/LoadingSpinner';
import ReviewSection from '../components/ReviewSection';
import api from '../utils/api';

const ToolDetail = () => {
  const { slug } = useParams();
  const [tool, setTool] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [relatedTools, setRelatedTools] = useState([]);
  const [isLiked, setIsLiked] = useState(false);

  useEffect(() => {
    fetchTool();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const fetchTool = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/tools/slug/${slug}`);
      setTool(response.data);
      
      // Fetch related tools
      if (response.data.category_id) {
        const relatedResponse = await api.get(`/api/tools/search?category_id=${response.data.category_id}&per_page=4`);
        setRelatedTools(relatedResponse.data.tools.filter(t => t.id !== response.data.id));
      }
    } catch (error) {
      setError('Tool not found');
      console.error('Error fetching tool:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    try {
      await api.post(`/api/tools/${tool.id}/like`);
      setIsLiked(!isLiked);
      toast.success(isLiked ? 'Removed from favorites' : 'Added to favorites');
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: tool.name,
          text: tool.short_description,
          url: window.location.href
        });
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      // Fallback to clipboard
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard');
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <StarIconSolid key={i} className="h-5 w-5 text-yellow-400" />
      );
    }

    if (hasHalfStar) {
      stars.push(
        <StarIcon key="half" className="h-5 w-5 text-yellow-400" />
      );
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(
        <StarIcon key={`empty-${i}`} className="h-5 w-5 text-gray-300" />
      );
    }

    return stars;
  };

  const parseFeatures = (features) => {
    try {
      return JSON.parse(features || '[]');
    } catch {
      return features ? features.split(',').map(f => f.trim()) : [];
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error || !tool) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Tool Not Found
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The tool you're looking for doesn't exist or has been removed.
          </p>
          <Link
            to="/tools"
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Browse All Tools
          </Link>
        </div>
      </div>
    );
  }

  const features = parseFeatures(tool.features);
  const metaTitle = tool.ai_meta_title || tool.meta_title || `${tool.name} - ${tool.short_description}`;
  const metaDescription = tool.ai_meta_description || tool.meta_description || tool.short_description;

  return (
    <>
      <Helmet>
        <title>{metaTitle}</title>
        <meta name="description" content={metaDescription} />
        <meta property="og:title" content={metaTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={window.location.href} />
        {tool.logo_url && <meta property="og:image" content={tool.logo_url} />}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metaTitle} />
        <meta name="twitter:description" content={metaDescription} />
        {tool.logo_url && <meta name="twitter:image" content={tool.logo_url} />}
      </Helmet>

      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Breadcrumb */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <nav className="flex text-sm text-gray-500 dark:text-gray-400">
              <Link to="/" className="hover:text-purple-600">Home</Link>
              <span className="mx-2">/</span>
              <Link to="/tools" className="hover:text-purple-600">Tools</Link>
              <span className="mx-2">/</span>
              <span className="text-gray-900 dark:text-white">{tool.name}</span>
            </nav>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {/* Header */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-16 h-16 bg-gray-200 dark:bg-gray-600 rounded-xl flex items-center justify-center overflow-hidden mr-4">
                      {tool.logo_url ? (
                        <img 
                          src={tool.logo_url} 
                          alt={tool.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-2xl font-bold text-gray-600 dark:text-gray-300">
                          {tool.name.charAt(0)}
                        </span>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center mb-2">
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                          {tool.name}
                        </h1>
                        {tool.is_hot && (
                          <span className="ml-2 text-lg" title="Hot Tool">🔥</span>
                        )}
                        {tool.is_featured && (
                          <span className="ml-1 text-lg" title="Featured Tool">✨</span>
                        )}
                      </div>
                      <p className="text-gray-600 dark:text-gray-400 mb-2">
                        {tool.short_description}
                      </p>
                      <div className="flex items-center">
                        <div className="flex items-center mr-4">
                          {renderStars(tool.rating)}
                          <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                            {tool.rating.toFixed(1)} ({tool.total_reviews} reviews)
                          </span>
                        </div>
                        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                          <EyeIcon className="h-4 w-4 mr-1" />
                          {tool.views.toLocaleString()} views
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={handleLike}
                      className={`p-2 rounded-lg transition-colors ${
                        isLiked 
                          ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400' 
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      <HeartIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={handleShare}
                      className="p-2 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      <ShareIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-4">
                  {tool.website_url && (
                    <a
                      href={tool.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                    >
                      <span>Visit Website</span>
                      <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                    </a>
                  )}
                  <button className="flex items-center space-x-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
                    <span>Add to Compare</span>
                  </button>
                </div>
              </div>

              {/* Description */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  About {tool.name}
                </h2>
                <div className="prose prose-gray dark:prose-invert max-w-none">
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    {tool.description}
                  </p>
                </div>
              </div>

              {/* Features */}
              {features.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    Key Features
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {features.map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                        <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Generated Content */}
              {tool.ai_content && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    AI-Generated Insights
                  </h2>
                  <div className="prose prose-gray dark:prose-invert max-w-none">
                    <div dangerouslySetInnerHTML={{ __html: tool.ai_content }} />
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1">
              {/* Quick Info */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Quick Info
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <CurrencyDollarIcon className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Pricing</p>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {tool.pricing_model}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <BuildingOffice2Icon className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Company Size</p>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {tool.company_size}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <UserGroupIcon className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Target Audience</p>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {tool.target_audience}
                      </p>
                    </div>
                  </div>
                  
                  {tool.industry && (
                    <div className="flex items-center">
                      <ChartBarIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Industry</p>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {tool.industry}
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {tool.location && (
                    <div className="flex items-center">
                      <GlobeAltIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Location</p>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {tool.location}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Pricing Details */}
              {tool.pricing_details && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Pricing Details
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {tool.pricing_details}
                  </p>
                </div>
              )}

              {/* Integrations */}
              {tool.integrations && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Integrations
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {tool.integrations.split(',').map((integration, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-full"
                      >
                        {integration.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Related Tools */}
          {relatedTools.length > 0 && (
            <div className="mt-12">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Related Tools
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {relatedTools.map(relatedTool => (
                  <Link
                    key={relatedTool.id}
                    to={`/tool/${relatedTool.slug}`}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center mb-3">
                      <div className="w-10 h-10 bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center overflow-hidden mr-3">
                        {relatedTool.logo_url ? (
                          <img 
                            src={relatedTool.logo_url} 
                            alt={relatedTool.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span className="text-sm font-bold text-gray-600 dark:text-gray-300">
                            {relatedTool.name.charAt(0)}
                          </span>
                        )}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {relatedTool.name}
                        </h3>
                        <div className="flex items-center">
                          {renderStars(relatedTool.rating)}
                          <span className="ml-1 text-xs text-gray-500">
                            {relatedTool.rating.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {relatedTool.short_description}
                    </p>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default ToolDetail;