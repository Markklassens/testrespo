import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { 
  PencilIcon, 
  TrashIcon, 
  CheckCircleIcon,
  UserCircleIcon 
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import StarRating from './StarRating';
import ReviewForm from './ReviewForm';
import { deleteToolReview, deleteBlogReview } from '../store/slices/reviewsSlice';
import { useAuth } from '../contexts/AuthContext';

const ReviewCard = ({ 
  review, 
  itemId, 
  itemType = 'tool', // 'tool' or 'blog'
  onReviewUpdated 
}) => {
  const dispatch = useDispatch();
  const { user } = useAuth();
  const [showEditForm, setShowEditForm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isOwnReview = user && review.user_id === user.id;
  const canDelete = isOwnReview || (user && ['admin', 'superadmin'].includes(user.user_type));

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this review?')) {
      return;
    }

    setIsDeleting(true);
    try {
      if (itemType === 'tool') {
        await dispatch(deleteToolReview(review.id)).unwrap();
      } else {
        await dispatch(deleteBlogReview(review.id)).unwrap();
      }
      toast.success('Review deleted successfully');
      if (onReviewUpdated) onReviewUpdated();
    } catch (error) {
      console.error('Error deleting review:', error);
      toast.error('Failed to delete review');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEditSuccess = () => {
    if (onReviewUpdated) onReviewUpdated();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <UserCircleIcon className="h-10 w-10 text-gray-400" />
            <div className="ml-3">
              <div className="flex items-center">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {review.user?.full_name || 'Anonymous User'}
                </p>
                {review.is_verified && (
                  <CheckCircleIcon className="h-4 w-4 text-green-500 ml-1" title="Verified Review" />
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {formatDate(review.created_at)}
              </p>
            </div>
          </div>
          
          {(isOwnReview || canDelete) && (
            <div className="flex space-x-2">
              {isOwnReview && (
                <button
                  onClick={() => setShowEditForm(true)}
                  className="text-gray-400 hover:text-purple-600 transition-colors"
                  title="Edit Review"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
              )}
              {canDelete && (
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                  title="Delete Review"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
        </div>

        <div className="mb-3">
          <StarRating 
            rating={review.rating} 
            readonly 
            size="sm"
            showRating={false}
          />
        </div>

        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {review.title}
        </h4>

        <p className="text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
          {review.content}
        </p>

        {(review.pros || review.cons) && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            {review.pros && (
              <div className="mb-3">
                <h5 className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                  👍 Pros
                </h5>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {review.pros}
                </p>
              </div>
            )}
            
            {review.cons && (
              <div>
                <h5 className="text-sm font-medium text-red-700 dark:text-red-400 mb-1">
                  👎 Cons
                </h5>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {review.cons}
                </p>
              </div>
            )}
          </div>
        )}

        {review.helpful_count > 0 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {review.helpful_count} people found this helpful
            </p>
          </div>
        )}
      </div>

      {/* Edit Review Modal */}
      <ReviewForm
        isOpen={showEditForm}
        onClose={() => setShowEditForm(false)}
        itemId={itemId}
        itemType={itemType}
        existingReview={review}
        onSuccess={handleEditSuccess}
      />
    </>
  );
};

export default ReviewCard;