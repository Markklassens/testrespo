import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import StarRating from './StarRating';
import { 
  createToolReview, 
  updateToolReview, 
  createBlogReview, 
  updateBlogReview 
} from '../store/slices/reviewsSlice';

const ReviewForm = ({ 
  isOpen, 
  onClose, 
  itemId, 
  itemType = 'tool', // 'tool' or 'blog'
  existingReview = null,
  onSuccess
}) => {
  const dispatch = useDispatch();
  const [formData, setFormData] = useState({
    rating: 0,
    title: '',
    content: '',
    pros: '',
    cons: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (existingReview) {
      setFormData({
        rating: existingReview.rating || 0,
        title: existingReview.title || '',
        content: existingReview.content || '',
        pros: existingReview.pros || '',
        cons: existingReview.cons || ''
      });
    } else {
      setFormData({
        rating: 0,
        title: '',
        content: '',
        pros: '',
        cons: ''
      });
    }
  }, [existingReview, isOpen]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleRatingChange = (rating) => {
    setFormData(prev => ({
      ...prev,
      rating
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.rating === 0) {
      toast.error('Please select a rating');
      return;
    }
    
    if (!formData.title.trim()) {
      toast.error('Please enter a review title');
      return;
    }
    
    if (!formData.content.trim()) {
      toast.error('Please enter review content');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const reviewData = {
        rating: formData.rating,
        title: formData.title.trim(),
        content: formData.content.trim(),
        pros: formData.pros.trim() || null,
        cons: formData.cons.trim() || null
      };

      if (existingReview) {
        // Update existing review
        if (itemType === 'tool') {
          await dispatch(updateToolReview({ 
            reviewId: existingReview.id, 
            reviewData 
          })).unwrap();
        } else {
          await dispatch(updateBlogReview({ 
            reviewId: existingReview.id, 
            reviewData 
          })).unwrap();
        }
        toast.success('Review updated successfully!');
      } else {
        // Create new review
        if (itemType === 'tool') {
          await dispatch(createToolReview({ 
            toolId: itemId, 
            reviewData 
          })).unwrap();
        } else {
          await dispatch(createBlogReview({ 
            blogId: itemId, 
            reviewData 
          })).unwrap();
        }
        toast.success('Review created successfully!');
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (error) {
      console.error('Error submitting review:', error);
      toast.error(error.message || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>
        
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                {existingReview ? 'Edit Review' : `Write a Review`}
              </h3>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Rating *
                </label>
                <StarRating
                  rating={formData.rating}
                  onRatingChange={handleRatingChange}
                  size="lg"
                  readonly={false}
                  showRating={false}
                />
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Review Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Enter a brief title for your review"
                  required
                />
              </div>

              {/* Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Review Content *
                </label>
                <textarea
                  name="content"
                  value={formData.content}
                  onChange={handleInputChange}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white resize-none"
                  placeholder="Share your detailed experience..."
                  required
                />
              </div>

              {/* Pros */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Pros (Optional)
                </label>
                <textarea
                  name="pros"
                  value={formData.pros}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white resize-none"
                  placeholder="What did you like most about it?"
                />
              </div>

              {/* Cons */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Cons (Optional)
                </label>
                <textarea
                  name="cons"
                  value={formData.cons}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-700 dark:text-white resize-none"
                  placeholder="What could be improved?"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Submitting...' : (existingReview ? 'Update Review' : 'Submit Review')}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewForm;