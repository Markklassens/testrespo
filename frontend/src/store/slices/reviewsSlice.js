import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks
export const fetchReviews = createAsyncThunk(
  'reviews/fetchReviews',
  async ({ toolId, userId, skip = 0, limit = 20 } = {}) => {
    const params = new URLSearchParams({ skip, limit });
    if (toolId) params.append('tool_id', toolId);
    if (userId) params.append('user_id', userId);
    const response = await api.get(`/api/reviews?${params}`);
    return response.data;
  }
);

export const createReview = createAsyncThunk(
  'reviews/createReview',
  async (reviewData) => {
    const response = await api.post('/api/reviews', reviewData);
    return response.data;
  }
);

const reviewsSlice = createSlice({
  name: 'reviews',
  initialState: {
    reviews: [],
    loading: false,
    error: null,
    pagination: {
      skip: 0,
      limit: 20
    }
  },
  reducers: {
    clearReviews: (state) => {
      state.reviews = [];
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchReviews.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchReviews.fulfilled, (state, action) => {
        state.loading = false;
        state.reviews = action.payload;
      })
      .addCase(fetchReviews.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(createReview.fulfilled, (state, action) => {
        state.reviews.unshift(action.payload);
      });
  }
});

export const { clearReviews, setPagination } = reviewsSlice.actions;
export default reviewsSlice.reducer;