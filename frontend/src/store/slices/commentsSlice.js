import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks
export const fetchComments = createAsyncThunk(
  'comments/fetchComments',
  async ({ blogId, skip = 0, limit = 50 } = {}) => {
    const params = new URLSearchParams({ skip, limit });
    if (blogId) params.append('blog_id', blogId);
    const response = await api.get(`/api/comments?${params}`);
    return response.data;
  }
);

export const createComment = createAsyncThunk(
  'comments/createComment',
  async (commentData) => {
    const response = await api.post('/api/comments', commentData);
    return response.data;
  }
);

const commentsSlice = createSlice({
  name: 'comments',
  initialState: {
    comments: [],
    loading: false,
    error: null,
    pagination: {
      skip: 0,
      limit: 50
    }
  },
  reducers: {
    clearComments: (state) => {
      state.comments = [];
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchComments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComments.fulfilled, (state, action) => {
        state.loading = false;
        state.comments = action.payload;
      })
      .addCase(fetchComments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(createComment.fulfilled, (state, action) => {
        state.comments.unshift(action.payload);
      });
  }
});

export const { clearComments, setPagination } = commentsSlice.actions;
export default commentsSlice.reducer;