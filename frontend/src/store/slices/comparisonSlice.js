import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Async thunks
export const fetchComparisonTools = createAsyncThunk(
  'comparison/fetchComparisonTools',
  async () => {
    const response = await api.get('/api/tools/compare');
    return response.data;
  }
);

export const addToComparison = createAsyncThunk(
  'comparison/addToComparison',
  async (toolId) => {
    await api.post('/api/tools/compare', { tool_id: toolId });
    return toolId;
  }
);

export const removeFromComparison = createAsyncThunk(
  'comparison/removeFromComparison',
  async (toolId) => {
    await api.delete(`/api/tools/compare/${toolId}`);
    return toolId;
  }
);

const comparisonSlice = createSlice({
  name: 'comparison',
  initialState: {
    tools: [],
    loading: false,
    error: null,
    maxTools: 5
  },
  reducers: {
    clearComparison: (state) => {
      state.tools = [];
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchComparisonTools.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComparisonTools.fulfilled, (state, action) => {
        state.loading = false;
        state.tools = action.payload;
      })
      .addCase(fetchComparisonTools.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(addToComparison.fulfilled, (state, action) => {
        // Tool will be added when we refetch
      })
      .addCase(removeFromComparison.fulfilled, (state, action) => {
        state.tools = state.tools.filter(tool => tool.id !== action.payload);
      });
  }
});

export const { clearComparison } = comparisonSlice.actions;
export default comparisonSlice.reducer;