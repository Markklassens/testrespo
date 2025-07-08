import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ChartBarIcon, CubeIcon, DocumentTextIcon, UserGroupIcon } from '@heroicons/react/24/outline';

const Home = () => {
  const { user } = useAuth();

  const features = [
    {
      icon: CubeIcon,
      title: 'B2B Tools Directory',
      description: 'Discover and compare the best B2B tools for your business needs.',
    },
    {
      icon: DocumentTextIcon,
      title: 'Expert Blogging',
      description: 'Create and publish high-quality content with our rich text editor.',
    },
    {
      icon: ChartBarIcon,
      title: 'Analytics & Insights',
      description: 'Get detailed analytics on tool performance and user engagement.',
    },
    {
      icon: UserGroupIcon,
      title: 'Community Driven',
      description: 'Join a community of professionals sharing insights and reviews.',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-primary-600 to-primary-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Welcome to <span className="text-yellow-300">MarketMindAI</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto">
              Your ultimate B2B tools directory and blogging platform. 
              Discover, compare, and review the best tools for your business.
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
                  className="bg-white hover:bg-gray-100 text-primary-600 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
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
                  className="bg-white hover:bg-gray-100 text-primary-600 px-8 py-3 rounded-lg text-lg font-semibold transition-colors duration-200"
                >
                  Sign In
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose MarketMindAI?
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Everything you need to discover, evaluate, and share insights about B2B tools
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-gray-50 dark:bg-gray-700 p-6 rounded-xl hover:shadow-lg transition-shadow duration-300"
              >
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
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
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                1000+
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                B2B Tools Listed
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                500+
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                Expert Reviews
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                10K+
              </div>
              <div className="text-xl text-gray-600 dark:text-gray-300">
                Active Users
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600 dark:bg-primary-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Join thousands of professionals who trust MarketMindAI for their B2B tool discovery and content creation needs.
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