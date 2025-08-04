import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { PlusIcon, StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import StarRating from './StarRating';
import ReviewCard from './ReviewCard';
import ReviewForm from './ReviewForm';
import LoadingSpinner from './LoadingSpinner';
import { useAuth } from '../contexts/AuthContext';
import {
  fetchToolReviews,
  fetchBlogReviews,
  fetchToolReviewStatus,
  fetchBlogReviewStatus,
  fetchMyToolReview,
  fetchMyBlogReview,
  clearToolReviews,
  clearBlogReviews
} from '../store/slices/reviewsSlice';

const ReviewSection = ({ itemId, itemType = 'tool', title = 'Reviews' }) => {
  const dispatch = useDispatch();
  const { user, loading: authLoading } = useAuth();
  const { 
    toolReviews, 
    blogReviews, 
    reviewStatus, 
    myReview, 
    loading, 
    error 
  } = useSelector(state => state.reviews);
  
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [showAllReviews, setShowAllReviews] = useState(false);

  const reviews = itemType === 'tool' ? toolReviews : blogReviews;
  const displayedReviews = showAllReviews ? reviews : reviews.slice(0, 3);

  useEffect(() => {
    if (itemId) {
      // Clear previous reviews
      if (itemType === 'tool') {
        dispatch(clearToolReviews());
      } else {
        dispatch(clearBlogReviews());
      }

      // Fetch reviews and status
      if (itemType === 'tool') {
        dispatch(fetchToolReviews({ toolId: itemId }));
        if (user) {
          dispatch(fetchToolReviewStatus(itemId));
          dispatch(fetchMyToolReview(itemId)).catch(() => {
            // User hasn't reviewed yet, this is expected
          });
        }
      } else {
        dispatch(fetchBlogReviews({ blogId: itemId }));
        if (user) {
          dispatch(fetchBlogReviewStatus(itemId));
          dispatch(fetchMyBlogReview(itemId)).catch(() => {
            // User hasn't reviewed yet, this is expected
          });
        }
      }
    }
  }, [dispatch, itemId, itemType, user]);

  const handleReviewSuccess = () => {
    // Refresh reviews and status after successful review submission
    if (itemType === 'tool') {
      dispatch(fetchToolReviews({ toolId: itemId }));
      dispatch(fetchToolReviewStatus(itemId));
      dispatch(fetchMyToolReview(itemId)).catch(() => {
        // Ignore error if user hasn't reviewed yet
      });
    } else {
      dispatch(fetchBlogReviews({ blogId: itemId }));
      dispatch(fetchBlogReviewStatus(itemId));
      dispatch(fetchMyBlogReview(itemId)).catch(() => {
        // Ignore error if user hasn't reviewed yet
      });
    }
  };

  const handleWriteReview = () => {
    if (!user) {
      toast.error('Please login to write a review');
      return;
    }
    setShowReviewForm(true);
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

  if (loading && reviews.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {title}
          </h3>
          
          {reviewStatus && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                {renderStars(reviewStatus.average_rating)}
                <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                  {reviewStatus.average_rating.toFixed(1)} ({reviewStatus.total_reviews} reviews)
                </span>
              </div>
            </div>
          )}
        </div>

        {!authLoading && user && !reviewStatus?.has_reviewed && (
          <button
            onClick={handleWriteReview}
            className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            <PlusIcon className="h-4 w-4" />
            <span>Write Review</span>
          </button>
        )}
        
        {authLoading && (
          <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
            <LoadingSpinner size="sm" />
            <span>Loading...</span>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-md mb-4">
          {error}
        </div>
      )}

      {/* User's Own Review */}
      {myReview && (
        <div className="mb-6">
          <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
            Your Review
          </h4>
          <ReviewCard
            review={myReview}
            itemId={itemId}
            itemType={itemType}
            onReviewUpdated={handleReviewSuccess}
          />
        </div>
      )}

      {/* All Reviews */}
      {reviews.length > 0 ? (
        <div className="space-y-4">
          {displayedReviews
            .filter(review => !myReview || review.id !== myReview.id)
            .map(review => (
              <ReviewCard
                key={review.id}
                review={review}
                itemId={itemId}
                itemType={itemType}
                onReviewUpdated={handleReviewSuccess}
              />
            ))}

          {reviews.length > 3 && (
            <div className="text-center pt-4">
              <button
                onClick={() => setShowAllReviews(!showAllReviews)}
                className="text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 font-medium"
              >
                {showAllReviews ? 'Show Less' : `Show All ${reviews.length} Reviews`}
              </button>
            </div>
          )}
        </div>
      ) : (
        !myReview && (
          <div className="text-center py-8">
            <StarIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              No reviews yet. Be the first to share your experience!
            </p>
            {user && (
              <button
                onClick={handleWriteReview}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                Write First Review
              </button>
            )}
          </div>
        )
      )}

      {/* Review Form Modal */}
      <ReviewForm
        isOpen={showReviewForm}
        onClose={() => setShowReviewForm(false)}
        itemId={itemId}
        itemType={itemType}
        onSuccess={handleReviewSuccess}
      />
    </div>
  );
};

export default ReviewSection;