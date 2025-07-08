import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { XMarkIcon, StarIcon, CheckIcon, XMarkIcon as NoIcon } from '@heroicons/react/24/outline';
import { fetchComparisonTools, removeFromComparison } from '../store/slices/comparisonSlice';
import { toast } from 'react-hot-toast';

const ToolComparison = ({ isOpen, onClose }) => {
  const dispatch = useDispatch();
  const { tools, loading } = useSelector(state => state.comparison);

  useEffect(() => {
    if (isOpen) {
      dispatch(fetchComparisonTools());
    }
  }, [isOpen, dispatch]);

  const handleRemoveTool = async (toolId) => {
    try {
      await dispatch(removeFromComparison(toolId)).unwrap();
      toast.success('Tool removed from comparison');
    } catch (error) {
      toast.error('Failed to remove tool from comparison');
    }
  };

  const parseFeatures = (features) => {
    try {
      return JSON.parse(features || '[]');
    } catch {
      return features ? features.split(',').map(f => f.trim()) : [];
    }
  };

  const parseIntegrations = (integrations) => {
    try {
      return JSON.parse(integrations || '[]');
    } catch {
      return integrations ? integrations.split(',').map(i => i.trim()) : [];
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 overflow-y-auto">
      <div className="min-h-screen px-4 py-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Tool Comparison ({tools.length}/5)
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-300">Loading comparison...</p>
              </div>
            ) : tools.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">
                  <svg className="h-16 w-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No tools to compare
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Add tools to your comparison by clicking the "Compare" button on tool cards.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-4 font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700">
                        Feature
                      </th>
                      {tools.map((tool) => (
                        <th key={tool.id} className="text-center p-4 border-b border-gray-200 dark:border-gray-700 min-w-48">
                          <div className="relative">
                            <button
                              onClick={() => handleRemoveTool(tool.id)}
                              className="absolute -top-2 -right-2 p-1 bg-red-100 hover:bg-red-200 rounded-full text-red-600"
                            >
                              <XMarkIcon className="h-4 w-4" />
                            </button>
                            <div className="text-center">
                              {tool.logo_url && (
                                <img
                                  src={tool.logo_url}
                                  alt={tool.name}
                                  className="h-12 w-12 object-contain mx-auto mb-2"
                                />
                              )}
                              <h3 className="font-semibold text-gray-900 dark:text-white">
                                {tool.name}
                              </h3>
                              <div className="flex items-center justify-center mt-1">
                                <StarIcon className="h-4 w-4 text-yellow-400 fill-current" />
                                <span className="ml-1 text-sm text-gray-600 dark:text-gray-300">
                                  {tool.rating.toFixed(1)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {/* Pricing */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Pricing Model
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4 text-center">
                          <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                            tool.pricing_model === 'Free' ? 'bg-green-100 text-green-800' :
                            tool.pricing_model === 'Freemium' ? 'bg-blue-100 text-blue-800' :
                            'bg-orange-100 text-orange-800'
                          }`}>
                            {tool.pricing_model || 'N/A'}
                          </span>
                        </td>
                      ))}
                    </tr>

                    {/* Pricing Details */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Pricing Details
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4 text-center text-sm">
                          {tool.pricing_details || 'N/A'}
                        </td>
                      ))}
                    </tr>

                    {/* Target Audience */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Target Audience
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4 text-center">
                          {tool.target_audience || 'N/A'}
                        </td>
                      ))}
                    </tr>

                    {/* Company Size */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Company Size
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4 text-center">
                          {tool.company_size || 'N/A'}
                        </td>
                      ))}
                    </tr>

                    {/* Features */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Key Features
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4">
                          <div className="space-y-1">
                            {parseFeatures(tool.features).slice(0, 5).map((feature, index) => (
                              <div key={index} className="flex items-center justify-center text-sm">
                                <CheckIcon className="h-4 w-4 text-green-500 mr-1 flex-shrink-0" />
                                <span className="text-gray-600 dark:text-gray-300">{feature}</span>
                              </div>
                            ))}
                            {parseFeatures(tool.features).length > 5 && (
                              <div className="text-xs text-gray-500">
                                +{parseFeatures(tool.features).length - 5} more
                              </div>
                            )}
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Integrations */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Popular Integrations
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4">
                          <div className="flex flex-wrap justify-center gap-1">
                            {parseIntegrations(tool.integrations).slice(0, 3).map((integration, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-xs text-gray-700 dark:text-gray-300"
                              >
                                {integration}
                              </span>
                            ))}
                            {parseIntegrations(tool.integrations).length > 3 && (
                              <span className="text-xs text-gray-500">
                                +{parseIntegrations(tool.integrations).length - 3}
                              </span>
                            )}
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Reviews */}
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        User Reviews
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4 text-center">
                          <div className="text-sm">
                            <div className="flex items-center justify-center mb-1">
                              <StarIcon className="h-4 w-4 text-yellow-400 fill-current mr-1" />
                              <span className="font-medium">{tool.rating.toFixed(1)}</span>
                            </div>
                            <div className="text-gray-600 dark:text-gray-300">
                              {tool.total_reviews} reviews
                            </div>
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Website */}
                    <tr>
                      <td className="p-4 font-medium text-gray-900 dark:text-white">
                        Website
                      </td>
                      {tools.map((tool) => (
                        <td key={tool.id} className="p-4 text-center">
                          {tool.website_url ? (
                            <a
                              href={tool.website_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-purple-600 hover:text-purple-700 text-sm font-medium"
                            >
                              Visit Website
                            </a>
                          ) : (
                            <span className="text-gray-400">N/A</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolComparison;