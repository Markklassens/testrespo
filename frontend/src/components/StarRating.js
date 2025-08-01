import React from 'react';
import { StarIcon } from '@heroicons/react/24/solid';
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline';

const StarRating = ({ 
  rating, 
  onRatingChange, 
  readonly = false, 
  size = 'sm',
  showRating = true,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
    xl: 'h-8 w-8'
  };

  const handleStarClick = (newRating) => {
    if (!readonly && onRatingChange) {
      onRatingChange(newRating);
    }
  };

  const handleStarHover = (starIndex) => {
    if (!readonly) {
      // You can implement hover effect here if needed
    }
  };

  return (
    <div className={`flex items-center ${className}`}>
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map((starIndex) => {
          const isFilled = starIndex <= rating;
          const StarComponent = isFilled ? StarIcon : StarOutlineIcon;
          
          return (
            <button
              key={starIndex}
              type="button"
              className={`
                ${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110 transition-transform'}
                ${isFilled ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'}
                focus:outline-none focus:ring-2 focus:ring-purple-500 rounded
              `}
              onClick={() => handleStarClick(starIndex)}
              onMouseEnter={() => handleStarHover(starIndex)}
              disabled={readonly}
            >
              <StarComponent className={sizeClasses[size]} />
            </button>
          );
        })}
      </div>
      
      {showRating && (
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
          {rating > 0 ? rating.toFixed(1) : '0.0'}
        </span>
      )}
    </div>
  );
};

export default StarRating;