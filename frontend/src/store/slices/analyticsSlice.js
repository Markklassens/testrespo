import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks
export const fetchDashboardAnalytics = createAsyncThunk(
  'analytics/fetchDashboardAnalytics',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/admin/analytics/advanced');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch analytics');
    }
  }
);

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState: {
    dashboard: {
      user_stats: {
        total: 0,
        active: 0,
        verified: 0,
        admins: 0
      },
      content_stats: {
        total_tools: 0,
        featured_tools: 0,
        total_blogs: 0,
        published_blogs: 0
      },
      review_stats: {
        total: 0,
        verified: 0,
        average_rating: 0
      },
      recent_activity: {
        users: [],
        reviews: []
      }
    },
    loading: false,
    error: null
  },
  reducers: {
    clearAnalytics: (state) => {
      state.dashboard = {
        total_users: 0,
        total_tools: 0,
        total_blogs: 0,
        total_reviews: 0,
        recent_blogs: [],
        recent_reviews: []
      };
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.dashboard = action.payload;
      })
      .addCase(fetchDashboardAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});

export const { clearAnalytics } = analyticsSlice.actions;
export default analyticsSlice.reducer;