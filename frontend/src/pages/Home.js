import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  ChartBarIcon, 
  CubeIcon, 
  DocumentTextIcon, 
  UserGroupIcon,
  StarIcon,
  EyeIcon,
  ClockIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import api from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';

const Home = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    fetchToolsAnalytics();
  }, []);

  const fetchToolsAnalytics = async () => {
    try {
      const response = await api.get('/api/tools/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: CubeIcon,
      title: 'B2B Tools Directory',
      description: 'Discover and compare the best B2B tools with advanced filtering and AI-powered recommendations.',
    },
    {
      icon: DocumentTextIcon,
      title: 'AI-Powered Content',
      description: 'Create high-quality content with integrated Groq and Claude AI assistance.',
    },
    {
      icon: ChartBarIcon,
      title: 'Analytics & Insights',
      description: 'Get detailed analytics on tool performance and user engagement with trending insights.',
    },
    {
      icon: UserGroupIcon,
      title: 'Community Driven',
      description: 'Join a community of professionals sharing insights, reviews, and AI-generated content.',
    },
  ];

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

  const AnimatedCarousel = ({ title, tools, icon: Icon, color }) => {
    if (!tools || tools.length === 0) return null;

    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8">
        <div className="flex items-center mb-6">
          <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center mr-4`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h3>
        </div>
        
        <div className="relative overflow-hidden">
          <div 
            className="flex transition-transform duration-500 ease-in-out"
            style={{ transform: `translateX(-${currentSlide * 33.333}%)` }}
          >
            {tools.map((tool) => (
              <div key={tool.id} className="w-1/3 flex-shrink-0 px-3">
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 h-full transform hover:scale-105 transition-all duration-300">
                  <div className="flex items-center mb-3">
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
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 dark:text-white text-sm truncate">
                        {tool.name}
                      </h4>
                      <div className="flex items-center">
                        {renderStars(tool.rating)}
                        <span className="ml-1 text-xs text-gray-600 dark:text-gray-400">
                          {tool.rating.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {tool.short_description || tool.description}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex items-center">
                      <EyeIcon className="h-3 w-3 mr-1" />
                      {tool.views.toLocaleString()}
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      tool.pricing_model === 'Free' 
                        ? 'bg-green-100 text-green-700'
                        : tool.pricing_model === 'Freemium'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-orange-100 text-orange-700'
                    }`}>
                      {tool.pricing_model}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {tools.length > 3 && (
            <>
              <button
                onClick={() => setCurrentSlide(Math.max(0, currentSlide - 1))}
                className="absolute left-0 top-1/2 transform -translate-y-1/2 bg-white dark:bg-gray-800 rounded-full p-2 shadow-lg disabled:opacity-50"
                disabled={currentSlide === 0}
              >
                <ArrowRightIcon className="h-4 w-4 text-gray-600 dark:text-gray-400 rotate-180" />
              </button>
              <button
                onClick={() => setCurrentSlide(Math.min(tools.length - 3, currentSlide + 1))}
                className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-white dark:bg-gray-800 rounded-full p-2 shadow-lg disabled:opacity-50"
                disabled={currentSlide >= tools.length - 3}
              >
                <ArrowRightIcon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-purple-600 to-purple-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Welcome to <span className="text-yellow-300">MarketMindAI</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 max-w-4xl mx-auto">
              Your ultimate AI-powered B2B tools directory and content platform. 
              Discover, compare, and create with advanced AI assistance.
            </p>
            {user ? (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/dashboard"
                  className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
                >
                  Go to Dashboard
                </Link>
                <Link
                  to="/tools"
                  className="bg-white hover:bg-gray-100 text-purple-600 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
                >
                  Explore Tools
                </Link>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/register"
                  className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
                >
                  Get Started
                </Link>
                <Link
                  to="/login"
                  className="bg-white hover:bg-gray-100 text-purple-600 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
                >
                  Sign In
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Animated Tool Carousels */}
      {loading ? (
        <div className="py-20 flex justify-center">
          <LoadingSpinner />
        </div>
      ) : analytics && (
        <section className="py-20 bg-gray-50 dark:bg-gray-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Discover the Best B2B Tools
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                Explore our curated collection of top-rated, trending, and newest tools
              </p>
            </div>

            <AnimatedCarousel
              title="🔥 Trending Tools"
              tools={analytics.trending_tools}
              icon={TrendingUpIcon}
              color="bg-red-500"
            />

            <AnimatedCarousel
              title="⭐ Top Rated Tools"
              tools={analytics.top_rated_tools}
              icon={StarIcon}
              color="bg-yellow-500"
            />

            <AnimatedCarousel
              title="👁️ Most Viewed"
              tools={analytics.most_viewed_tools}
              icon={EyeIcon}
              color="bg-blue-500"
            />

            <AnimatedCarousel
              title="✨ Featured Tools"
              tools={analytics.featured_tools}
              icon={SparklesIcon}
              color="bg-purple-500"
            />

            <AnimatedCarousel
              title="🚀 New Arrivals"
              tools={analytics.newest_tools}
              icon={ClockIcon}
              color="bg-green-500"
            />

            <AnimatedCarousel
              title="🔥 Hot Tools"
              tools={analytics.hot_tools}
              icon={TrendingUpIcon}
              color="bg-orange-500"
            />

            <div className="text-center mt-12">
              <Link
                to="/tools"
                className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200 inline-flex items-center"
              >
                View All Tools
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="py-20 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose MarketMindAI?
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Everything you need to discover, evaluate, and create content about B2B tools with AI
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-gray-50 dark:bg-gray-700 p-6 rounded-xl hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1"
              >
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                1000+
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                B2B Tools Listed
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                500+
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                Expert Reviews
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                10K+
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                Active Users
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                AI
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                Powered Content
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-purple-600 dark:bg-purple-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Join thousands of professionals who trust MarketMindAI for their B2B tool discovery and AI-powered content creation needs.
          </p>
          {!user && (
            <Link
              to="/register"
              className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
            >
              Start Free Today
            </Link>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;