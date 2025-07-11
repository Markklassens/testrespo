import { configureStore } from '@reduxjs/toolkit';
import toolsReducer from './slices/toolsSlice';
import blogsReducer from './slices/blogsSlice';
import categoriesReducer from './slices/categoriesSlice';
import comparisonReducer from './slices/comparisonSlice';
import reviewsReducer from './slices/reviewsSlice';
import commentsReducer from './slices/commentsSlice';
import analyticsReducer from './slices/analyticsSlice';
import usersReducer from './slices/usersSlice';

export const store = configureStore({
  reducer: {
    tools: toolsReducer,
    blogs: blogsReducer,
    categories: categoriesReducer,
    comparison: comparisonReducer,
    reviews: reviewsReducer,
    comments: commentsReducer,
    analytics: analyticsReducer,
    users: usersReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST']
      }
    })
});

// TypeScript type definitions would go here if this were a .ts file
// export type RootState = ReturnType<typeof store.getState>;
// export type AppDispatch = typeof store.dispatch;