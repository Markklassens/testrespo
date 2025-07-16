import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Helmet } from 'react-helmet-async';
import { 
  EyeIcon, 
  HeartIcon, 
  ClockIcon, 
  UserIcon,
  CalendarIcon,
  TagIcon,
  ShareIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import { fetchBlog, likeBlog } from '../store/slices/blogsSlice';
import { fetchCategories } from '../store/slices/categoriesSlice';
import { useAuth } from '../contexts/AuthContext';

const BlogDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useAuth();
  
  const { currentBlog, loading, error } = useSelector(state => state.blogs);
  const { categories } = useSelector(state => state.categories);
  
  const [isLiked, setIsLiked] = useState(false);

  useEffect(() => {
    if (id) {
      dispatch(fetchBlog(id));
      dispatch(fetchCategories());
    }
  }, [dispatch, id]);

  const handleLike = async () => {
    if (!user) {
      toast.error('Please login to like this blog');
      return;
    }

    try {
      await dispatch(likeBlog(id)).unwrap();
      setIsLiked(true);
      toast.success('Blog liked!');
    } catch (error) {
      toast.error('Failed to like blog');
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: currentBlog.title,
          text: currentBlog.excerpt || 'Check out this blog post',
          url: window.location.href,
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Uncategorized';
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Blog Not Found
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The blog post you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate('/blogs')}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200"
          >
            Back to Blogs
          </button>
        </div>
      </div>
    );
  }

  if (!currentBlog) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Helmet>
        <title>{currentBlog.meta_title || currentBlog.title} - MarketMindAI</title>
        <meta name="description" content={currentBlog.meta_description || currentBlog.excerpt} />
        <meta property="og:title" content={currentBlog.title} />
        <meta property="og:description" content={currentBlog.excerpt} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={window.location.href} />
        {currentBlog.featured_image && (
          <meta property="og:image" content={currentBlog.featured_image} />
        )}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={currentBlog.title} />
        <meta name="twitter:description" content={currentBlog.excerpt} />
        {currentBlog.featured_image && (
          <meta name="twitter:image" content={currentBlog.featured_image} />
        )}
      </Helmet>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <div className="mb-6">
          <Link
            to="/blogs"
            className="inline-flex items-center text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to Blogs
          </Link>
        </div>

        {/* Blog Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden mb-8">
          {/* Featured Image */}
          {currentBlog.featured_image && (
            <div className="h-64 md:h-80 bg-gray-200 dark:bg-gray-600">
              <img 
                src={currentBlog.featured_image} 
                alt={currentBlog.title}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <div className="p-6 md:p-8">
            {/* Category & Meta */}
            <div className="flex items-center mb-4">
              <span className="bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-3 py-1 rounded-full text-sm font-medium">
                {getCategoryName(currentBlog.category_id)}
              </span>
              <span className="ml-4 text-sm text-gray-500 dark:text-gray-400">
                {formatDate(currentBlog.created_at)}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-6">
              {currentBlog.title}
            </h1>

            {/* Author & Meta Info */}
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-6 mb-6">
              <div className="flex items-center space-x-6">
                <div className="flex items-center">
                  <UserIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {currentBlog.author?.full_name || 'Anonymous'}
                  </span>
                </div>
                <div className="flex items-center">
                  <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {currentBlog.reading_time} min read
                  </span>
                </div>
                <div className="flex items-center">
                  <EyeIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {currentBlog.views} views
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleLike}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    isLiked 
                      ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300' 
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  <HeartIcon className="h-5 w-5" />
                  <span>{currentBlog.likes}</span>
                </button>
                <button
                  onClick={handleShare}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <ShareIcon className="h-5 w-5" />
                  <span>Share</span>
                </button>
              </div>
            </div>

            {/* Excerpt */}
            {currentBlog.excerpt && (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
                <p className="text-gray-700 dark:text-gray-300 italic">
                  {currentBlog.excerpt}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Blog Content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 md:p-8">
          <div 
            className="prose prose-lg max-w-none dark:prose-invert prose-headings:text-gray-900 dark:prose-headings:text-white prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-a:text-purple-600 dark:prose-a:text-purple-400 prose-strong:text-gray-900 dark:prose-strong:text-white"
            dangerouslySetInnerHTML={{ __html: currentBlog.content }}
          />
        </div>

        {/* Tags */}
        {currentBlog.tags && currentBlog.tags.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mt-6">
            <div className="flex items-center mb-4">
              <TagIcon className="h-5 w-5 text-gray-400 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Tags
              </h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {currentBlog.tags.map((tag, index) => (
                <span
                  key={index}
                  className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-sm"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Related Posts */}
        {/* You can add related posts functionality here */}
      </div>
    </div>
  );
};

export default BlogDetail;