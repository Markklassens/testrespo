import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks for user management
export const fetchUsers = createAsyncThunk(
  'users/fetchUsers',
  async ({ skip = 0, limit = 100, search = '', user_type = '', is_active = null } = {}) => {
    const params = new URLSearchParams();
    if (skip) params.append('skip', skip);
    if (limit) params.append('limit', limit);
    if (search) params.append('search', search);
    if (user_type) params.append('user_type', user_type);
    if (is_active !== null) params.append('is_active', is_active);
    
    const response = await api.get(`/api/superadmin/users?${params}`);
    return response.data;
  }
);

export const fetchUser = createAsyncThunk(
  'users/fetchUser',
  async (userId) => {
    const response = await api.get(`/api/admin/users/${userId}`);
    return response.data;
  }
);

export const createUser = createAsyncThunk(
  'users/createUser',
  async (userData) => {
    const response = await api.post('/api/admin/users', userData);
    return response.data;
  }
);

export const updateUser = createAsyncThunk(
  'users/updateUser',
  async ({ id, data }) => {
    const response = await api.put(`/api/admin/users/${id}`, data);
    return response.data;
  }
);

export const deleteUser = createAsyncThunk(
  'users/deleteUser',
  async (userId) => {
    await api.delete(`/api/admin/users/${userId}`);
    return userId;
  }
);

const usersSlice = createSlice({
  name: 'users',
  initialState: {
    users: [],
    currentUser: null,
    loading: false,
    error: null,
    total: 0,
    pagination: {
      skip: 0,
      limit: 100
    },
    filters: {
      search: '',
      user_type: '',
      is_active: null
    }
  },
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        search: '',
        user_type: '',
        is_active: null
      };
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    clearCurrentUser: (state) => {
      state.currentUser = null;
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch users
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload;
        state.total = action.payload.length;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      // Fetch single user
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.currentUser = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      // Create user
      .addCase(createUser.fulfilled, (state, action) => {
        state.users.unshift(action.payload);
        state.total += 1;
      })
      .addCase(createUser.rejected, (state, action) => {
        state.error = action.error.message;
      })
      // Update user
      .addCase(updateUser.fulfilled, (state, action) => {
        const index = state.users.findIndex(user => user.id === action.payload.id);
        if (index !== -1) {
          state.users[index] = action.payload;
        }
        if (state.currentUser?.id === action.payload.id) {
          state.currentUser = action.payload;
        }
      })
      .addCase(updateUser.rejected, (state, action) => {
        state.error = action.error.message;
      })
      // Delete user
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.users = state.users.filter(user => user.id !== action.payload);
        state.total -= 1;
        if (state.currentUser?.id === action.payload) {
          state.currentUser = null;
        }
      })
      .addCase(deleteUser.rejected, (state, action) => {
        state.error = action.error.message;
      });
  }
});

export const { 
  setFilters, 
  clearFilters, 
  setPagination, 
  clearCurrentUser,
  clearError
} = usersSlice.actions;

export default usersSlice.reducer;