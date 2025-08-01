import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Tool Reviews Async thunks
export const fetchToolReviews = createAsyncThunk(
  'reviews/fetchToolReviews',
  async ({ toolId, skip = 0, limit = 20 } = {}) => {
    const response = await api.get(`/api/tools/${toolId}/reviews?skip=${skip}&limit=${limit}`);
    return response.data;
  }
);

export const createToolReview = createAsyncThunk(
  'reviews/createToolReview',
  async ({ toolId, reviewData }) => {
    const response = await api.post(`/api/tools/${toolId}/reviews`, reviewData);
    return response.data;
  }
);

export const updateToolReview = createAsyncThunk(
  'reviews/updateToolReview',
  async ({ reviewId, reviewData }) => {
    const response = await api.put(`/api/tools/reviews/${reviewId}`, reviewData);
    return response.data;
  }
);

export const deleteToolReview = createAsyncThunk(
  'reviews/deleteToolReview',
  async (reviewId) => {
    await api.delete(`/api/tools/reviews/${reviewId}`);
    return reviewId;
  }
);

export const fetchToolReviewStatus = createAsyncThunk(
  'reviews/fetchToolReviewStatus',
  async (toolId) => {
    const response = await api.get(`/api/tools/${toolId}/review-status`);
    return response.data;
  }
);

export const fetchMyToolReview = createAsyncThunk(
  'reviews/fetchMyToolReview',
  async (toolId) => {
    const response = await api.get(`/api/tools/${toolId}/reviews/my-review`);
    return response.data;
  }
);

// Blog Reviews Async thunks
export const fetchBlogReviews = createAsyncThunk(
  'reviews/fetchBlogReviews',
  async ({ blogId, skip = 0, limit = 20 } = {}) => {
    const response = await api.get(`/api/blogs/${blogId}/reviews?skip=${skip}&limit=${limit}`);
    return response.data;
  }
);

export const createBlogReview = createAsyncThunk(
  'reviews/createBlogReview',
  async ({ blogId, reviewData }) => {
    const response = await api.post(`/api/blogs/${blogId}/reviews`, reviewData);
    return response.data;
  }
);

export const updateBlogReview = createAsyncThunk(
  'reviews/updateBlogReview',
  async ({ reviewId, reviewData }) => {
    const response = await api.put(`/api/blogs/reviews/${reviewId}`, reviewData);
    return response.data;
  }
);

export const deleteBlogReview = createAsyncThunk(
  'reviews/deleteBlogReview',
  async (reviewId) => {
    await api.delete(`/api/blogs/reviews/${reviewId}`);
    return reviewId;
  }
);

export const fetchBlogReviewStatus = createAsyncThunk(
  'reviews/fetchBlogReviewStatus',
  async (blogId) => {
    const response = await api.get(`/api/blogs/${blogId}/review-status`);
    return response.data;
  }
);

export const fetchMyBlogReview = createAsyncThunk(
  'reviews/fetchMyBlogReview',
  async (blogId) => {
    const response = await api.get(`/api/blogs/${blogId}/reviews/my-review`);
    return response.data;
  }
);

const reviewsSlice = createSlice({
  name: 'reviews',
  initialState: {
    toolReviews: [],
    blogReviews: [],
    reviewStatus: null,
    myReview: null,
    loading: false,
    error: null,
    pagination: {
      skip: 0,
      limit: 20
    }
  },
  reducers: {
    clearReviews: (state) => {
      state.toolReviews = [];
      state.blogReviews = [];
      state.reviewStatus = null;
      state.myReview = null;
    },
    clearToolReviews: (state) => {
      state.toolReviews = [];
    },
    clearBlogReviews: (state) => {
      state.blogReviews = [];
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    }
  },
  extraReducers: (builder) => {
    builder
      // Tool Reviews
      .addCase(fetchToolReviews.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchToolReviews.fulfilled, (state, action) => {
        state.loading = false;
        state.toolReviews = action.payload;
      })
      .addCase(fetchToolReviews.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(createToolReview.fulfilled, (state, action) => {
        state.toolReviews.unshift(action.payload);
      })
      .addCase(updateToolReview.fulfilled, (state, action) => {
        const index = state.toolReviews.findIndex(review => review.id === action.payload.id);
        if (index !== -1) {
          state.toolReviews[index] = action.payload;
        }
        if (state.myReview && state.myReview.id === action.payload.id) {
          state.myReview = action.payload;
        }
      })
      .addCase(deleteToolReview.fulfilled, (state, action) => {
        state.toolReviews = state.toolReviews.filter(review => review.id !== action.payload);
        if (state.myReview && state.myReview.id === action.payload) {
          state.myReview = null;
        }
      })
      .addCase(fetchToolReviewStatus.fulfilled, (state, action) => {
        state.reviewStatus = action.payload;
      })
      .addCase(fetchMyToolReview.fulfilled, (state, action) => {
        state.myReview = action.payload;
      })
      .addCase(fetchMyToolReview.rejected, (state) => {
        state.myReview = null;
      })
      
      // Blog Reviews
      .addCase(fetchBlogReviews.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBlogReviews.fulfilled, (state, action) => {
        state.loading = false;
        state.blogReviews = action.payload;
      })
      .addCase(fetchBlogReviews.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(createBlogReview.fulfilled, (state, action) => {
        state.blogReviews.unshift(action.payload);
      })
      .addCase(updateBlogReview.fulfilled, (state, action) => {
        const index = state.blogReviews.findIndex(review => review.id === action.payload.id);
        if (index !== -1) {
          state.blogReviews[index] = action.payload;
        }
        if (state.myReview && state.myReview.id === action.payload.id) {
          state.myReview = action.payload;
        }
      })
      .addCase(deleteBlogReview.fulfilled, (state, action) => {
        state.blogReviews = state.blogReviews.filter(review => review.id !== action.payload);
        if (state.myReview && state.myReview.id === action.payload) {
          state.myReview = null;
        }
      })
      .addCase(fetchBlogReviewStatus.fulfilled, (state, action) => {
        state.reviewStatus = action.payload;
      })
      .addCase(fetchMyBlogReview.fulfilled, (state, action) => {
        state.myReview = action.payload;
      })
      .addCase(fetchMyBlogReview.rejected, (state) => {
        state.myReview = null;
      });
  }
});

export const { clearReviews, clearToolReviews, clearBlogReviews, setPagination } = reviewsSlice.actions;
export default reviewsSlice.reducer;