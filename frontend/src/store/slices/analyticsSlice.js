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
      total_users: 0,
      total_tools: 0,
      total_blogs: 0,
      total_reviews: 0,
      recent_blogs: [],
      recent_reviews: []
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