import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks
export const fetchBlogs = createAsyncThunk(
  'blogs/fetchBlogs',
  async ({ skip = 0, limit = 20, ...filters } = {}) => {
    const params = new URLSearchParams({ skip, limit, ...filters });
    const response = await api.get(`/api/blogs?${params}`);
    return response.data;
  }
);

export const fetchBlog = createAsyncThunk(
  'blogs/fetchBlog',
  async (blogId) => {
    const response = await api.get(`/api/blogs/${blogId}`);
    return response.data;
  }
);

export const createBlog = createAsyncThunk(
  'blogs/createBlog',
  async (blogData) => {
    const response = await api.post('/api/blogs', blogData);
    return response.data;
  }
);

export const updateBlog = createAsyncThunk(
  'blogs/updateBlog',
  async ({ id, data }) => {
    const response = await api.put(`/api/blogs/${id}`, data);
    return response.data;
  }
);

export const deleteBlog = createAsyncThunk(
  'blogs/deleteBlog',
  async (blogId) => {
    await api.delete(`/api/blogs/${blogId}`);
    return blogId;
  }
);

export const likeBlog = createAsyncThunk(
  'blogs/likeBlog',
  async (blogId) => {
    const response = await api.post(`/api/blogs/${blogId}/like`);
    return { blogId, likes: response.data.likes };
  }
);

const blogsSlice = createSlice({
  name: 'blogs',
  initialState: {
    blogs: [],
    currentBlog: null,
    loading: false,
    error: null,
    total: 0,
    pagination: {
      skip: 0,
      limit: 20
    },
    filters: {
      search: '',
      status: 'published',
      category_id: '',
      author_id: '',
      sort_by: 'created_at'
    },
    drafts: []
  },
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        search: '',
        status: 'published',
        category_id: '',
        author_id: '',
        sort_by: 'created_at'
      };
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    clearCurrentBlog: (state) => {
      state.currentBlog = null;
    },
    saveDraft: (state, action) => {
      const existingIndex = state.drafts.findIndex(draft => draft.id === action.payload.id);
      if (existingIndex !== -1) {
        state.drafts[existingIndex] = action.payload;
      } else {
        state.drafts.push(action.payload);
      }
    },
    removeDraft: (state, action) => {
      state.drafts = state.drafts.filter(draft => draft.id !== action.payload);
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch blogs
      .addCase(fetchBlogs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBlogs.fulfilled, (state, action) => {
        state.loading = false;
        state.blogs = action.payload;
        state.total = action.payload.length;
      })
      .addCase(fetchBlogs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      // Fetch single blog
      .addCase(fetchBlog.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBlog.fulfilled, (state, action) => {
        state.loading = false;
        state.currentBlog = action.payload;
      })
      .addCase(fetchBlog.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      // Create blog
      .addCase(createBlog.fulfilled, (state, action) => {
        state.blogs.unshift(action.payload);
        // Remove from drafts if it was a draft
        state.drafts = state.drafts.filter(draft => draft.slug !== action.payload.slug);
      })
      // Update blog
      .addCase(updateBlog.fulfilled, (state, action) => {
        const index = state.blogs.findIndex(blog => blog.id === action.payload.id);
        if (index !== -1) {
          state.blogs[index] = action.payload;
        }
        if (state.currentBlog?.id === action.payload.id) {
          state.currentBlog = action.payload;
        }
      })
      // Delete blog
      .addCase(deleteBlog.fulfilled, (state, action) => {
        state.blogs = state.blogs.filter(blog => blog.id !== action.payload);
        if (state.currentBlog?.id === action.payload) {
          state.currentBlog = null;
        }
      })
      // Like blog
      .addCase(likeBlog.fulfilled, (state, action) => {
        const { blogId, likes } = action.payload;
        const blog = state.blogs.find(b => b.id === blogId);
        if (blog) {
          blog.likes = likes;
        }
        if (state.currentBlog?.id === blogId) {
          state.currentBlog.likes = likes;
        }
      });
  }
});

export const { 
  setFilters, 
  clearFilters, 
  setPagination, 
  clearCurrentBlog,
  saveDraft,
  removeDraft
} = blogsSlice.actions;

export default blogsSlice.reducer;