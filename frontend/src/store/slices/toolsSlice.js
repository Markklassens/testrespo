import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks
export const fetchTools = createAsyncThunk(
  'tools/fetchTools',
  async ({ skip = 0, limit = 20, ...filters } = {}) => {
    const params = new URLSearchParams({ skip, limit, ...filters });
    const response = await api.get(`/api/tools/search?${params}`);
    return response.data;
  }
);

export const fetchTool = createAsyncThunk(
  'tools/fetchTool',
  async (toolId) => {
    const response = await api.get(`/api/tools/${toolId}`);
    return response.data;
  }
);

export const createTool = createAsyncThunk(
  'tools/createTool',
  async (toolData) => {
    const response = await api.post('/api/tools', toolData);
    return response.data;
  }
);

export const updateTool = createAsyncThunk(
  'tools/updateTool',
  async ({ id, data }) => {
    const response = await api.put(`/api/tools/${id}`, data);
    return response.data;
  }
);

export const deleteTool = createAsyncThunk(
  'tools/deleteTool',
  async (toolId) => {
    await api.delete(`/api/tools/${toolId}`);
    return toolId;
  }
);

export const bulkUploadTools = createAsyncThunk(
  'tools/bulkUploadTools',
  async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/tools/bulk-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
);

export const downloadCsvTemplate = createAsyncThunk(
  'tools/downloadCsvTemplate',
  async () => {
    const response = await api.get('/api/admin/tools/sample-csv', {
      responseType: 'blob'
    });
    return response.data;
  }
);

export const assignToolToAdmin = createAsyncThunk(
  'tools/assignToolToAdmin',
  async ({ toolId, adminId }) => {
    const response = await api.post(`/api/admin/tools/${toolId}/assign`, {
      admin_id: adminId
    });
    return response.data;
  }
);

export const unassignToolFromAdmin = createAsyncThunk(
  'tools/unassignToolFromAdmin',
  async (toolId) => {
    const response = await api.delete(`/api/admin/tools/${toolId}/assign`);
    return response.data;
  }
);

export const getToolAssignments = createAsyncThunk(
  'tools/getToolAssignments',
  async () => {
    const response = await api.get('/api/admin/tools/assignments');
    return response.data;
  }
);

export const getAssignedTools = createAsyncThunk(
  'tools/getAssignedTools',
  async () => {
    const response = await api.get('/api/admin/tools/assigned');
    return response.data;
  }
);

const toolsSlice = createSlice({
  name: 'tools',
  initialState: {
    tools: [],
    currentTool: null,
    loading: false,
    error: null,
    total: 0,
    pagination: {
      skip: 0,
      limit: 20
    },
    filters: {
      search: '',
      category_id: '',
      subcategory_id: '',
      pricing_model: '',
      company_size: '',
      min_rating: null,
      sort_by: 'relevance'
    },
    csvUpload: {
      loading: false,
      result: null,
      error: null
    },
    assignments: {
      loading: false,
      list: [],
      error: null
    },
    assignedTools: {
      loading: false,
      list: [],
      error: null
    }
  },
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        search: '',
        category_id: '',
        subcategory_id: '',
        pricing_model: '',
        company_size: '',
        min_rating: null,
        sort_by: 'relevance'
      };
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    clearCurrentTool: (state) => {
      state.currentTool = null;
    },
    clearCsvUploadResult: (state) => {
      state.csvUpload.result = null;
      state.csvUpload.error = null;
    },
    clearAssignments: (state) => {
      state.assignments.list = [];
      state.assignments.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch tools
      .addCase(fetchTools.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTools.fulfilled, (state, action) => {
        state.loading = false;
        state.tools = action.payload.tools || action.payload;
        state.total = action.payload.total || action.payload.length;
      })
      .addCase(fetchTools.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      // Fetch single tool
      .addCase(fetchTool.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTool.fulfilled, (state, action) => {
        state.loading = false;
        state.currentTool = action.payload;
      })
      .addCase(fetchTool.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      // Create tool
      .addCase(createTool.fulfilled, (state, action) => {
        state.tools.unshift(action.payload);
      })
      // Update tool
      .addCase(updateTool.fulfilled, (state, action) => {
        const index = state.tools.findIndex(tool => tool.id === action.payload.id);
        if (index !== -1) {
          state.tools[index] = action.payload;
        }
        if (state.currentTool?.id === action.payload.id) {
          state.currentTool = action.payload;
        }
      })
      // Delete tool
      .addCase(deleteTool.fulfilled, (state, action) => {
        state.tools = state.tools.filter(tool => tool.id !== action.payload);
        if (state.currentTool?.id === action.payload) {
          state.currentTool = null;
        }
      })
      // Bulk upload
      .addCase(bulkUploadTools.pending, (state) => {
        state.csvUpload.loading = true;
        state.csvUpload.error = null;
      })
      .addCase(bulkUploadTools.fulfilled, (state, action) => {
        state.csvUpload.loading = false;
        state.csvUpload.result = action.payload;
      })
      .addCase(bulkUploadTools.rejected, (state, action) => {
        state.csvUpload.loading = false;
        state.csvUpload.error = action.error.message;
      });
  }
});

export const { 
  setFilters, 
  clearFilters, 
  setPagination, 
  clearCurrentTool,
  clearCsvUploadResult 
} = toolsSlice.actions;

export default toolsSlice.reducer;