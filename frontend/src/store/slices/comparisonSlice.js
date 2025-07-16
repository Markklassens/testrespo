import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../utils/api';

// Helper functions for localStorage
const getStoredComparison = () => {
  try {
    const stored = localStorage.getItem('comparisonTools');
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return [];
  }
};

const setStoredComparison = (tools) => {
  try {
    localStorage.setItem('comparisonTools', JSON.stringify(tools));
  } catch (error) {
    console.error('Error writing to localStorage:', error);
  }
};

// Async thunks
export const fetchComparisonTools = createAsyncThunk(
  'comparison/fetchComparisonTools',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/tools/compare');
      return response.data;
    } catch (error) {
      // If API fails (e.g., user not logged in), return localStorage data
      return getStoredComparison();
    }
  }
);

export const addToComparison = createAsyncThunk(
  'comparison/addToComparison',
  async (toolId, { rejectWithValue, getState }) => {
    try {
      // Try to add to backend first
      await api.post('/api/tools/compare', { tool_id: toolId });
      
      // If successful, also add to localStorage
      const currentTools = getStoredComparison();
      const toolExists = currentTools.find(tool => tool.id === toolId);
      
      if (!toolExists) {
        // Fetch tool details and add to localStorage
        const toolResponse = await api.get(`/api/tools/${toolId}`);
        const newTools = [...currentTools, toolResponse.data];
        setStoredComparison(newTools);
      }
      
      return toolId;
    } catch (error) {
      // If backend fails, try localStorage approach
      try {
        const currentTools = getStoredComparison();
        const toolExists = currentTools.find(tool => tool.id === toolId);
        
        if (toolExists) {
          return rejectWithValue('Tool already in comparison');
        }
        
        if (currentTools.length >= 5) {
          return rejectWithValue('Maximum 5 tools allowed for comparison');
        }
        
        // Fetch tool details and add to localStorage
        const toolResponse = await api.get(`/api/tools/${toolId}`);
        const newTools = [...currentTools, toolResponse.data];
        setStoredComparison(newTools);
        
        return { toolId, tool: toolResponse.data };
      } catch (localError) {
        return rejectWithValue('Failed to add tool to comparison');
      }
    }
  }
);

export const removeFromComparison = createAsyncThunk(
  'comparison/removeFromComparison',
  async (toolId, { rejectWithValue }) => {
    try {
      // Try to remove from backend first
      await api.delete(`/api/tools/compare/${toolId}`);
      
      // Also remove from localStorage
      const currentTools = getStoredComparison();
      const filteredTools = currentTools.filter(tool => tool.id !== toolId);
      setStoredComparison(filteredTools);
      
      return toolId;
    } catch (error) {
      // If backend fails, try localStorage approach
      const currentTools = getStoredComparison();
      const filteredTools = currentTools.filter(tool => tool.id !== toolId);
      setStoredComparison(filteredTools);
      
      return toolId;
    }
  }
);

const comparisonSlice = createSlice({
  name: 'comparison',
  initialState: {
    tools: getStoredComparison(),
    loading: false,
    error: null,
    maxTools: 5
  },
  reducers: {
    clearComparison: (state) => {
      state.tools = [];
      setStoredComparison([]);
    },
    initializeFromStorage: (state) => {
      state.tools = getStoredComparison();
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
        // Also update localStorage with fetched data
        setStoredComparison(action.payload);
      })
      .addCase(fetchComparisonTools.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
        // Fallback to localStorage data
        state.tools = getStoredComparison();
      })
      .addCase(addToComparison.fulfilled, (state, action) => {
        // If localStorage approach was used, tool is already in payload
        if (action.payload.tool) {
          state.tools.push(action.payload.tool);
        }
        // If backend approach was used, tool will be added when we refetch
      })
      .addCase(addToComparison.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(removeFromComparison.fulfilled, (state, action) => {
        state.tools = state.tools.filter(tool => tool.id !== action.payload);
      });
  }
});

export const { clearComparison, initializeFromStorage } = comparisonSlice.actions;
export default comparisonSlice.reducer;