import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Provider, useDispatch } from 'react-redux';
import { Toaster } from 'react-hot-toast';
import { HelmetProvider } from 'react-helmet-async';
import { store } from './store';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { initializeFromStorage } from './store/slices/comparisonSlice';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import DiscoverPage from './pages/DiscoverPage';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import Tools from './pages/Tools';
import ToolDetail from './pages/ToolDetail';
import Blogs from './pages/Blogs';
import BlogDetail from './pages/BlogDetail';
import AdminPanel from './pages/AdminPanel';
import MyBlogs from './pages/MyBlogs';
import Compare from './pages/Compare';
import Profile from './pages/Profile';
import LoadingSpinner from './components/LoadingSpinner';
import './codespaceCompat';
import './App.css';

const queryClient = new QueryClient();

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (!user.is_verified) {
    return <Navigate to="/verify-email" replace />;
  }
  
  if (requiredRole && user.user_type !== requiredRole && 
      !(requiredRole === 'admin' && user.user_type === 'superadmin')) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Public Route Component (redirect to dashboard if already logged in)
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (user && user.is_verified) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function AppContent() {
  const { user, loading } = useAuth();
  const dispatch = useDispatch();
  
  // Initialize comparison from localStorage on app load
  useEffect(() => {
    dispatch(initializeFromStorage());
  }, [dispatch]);
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <main className="pt-16">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/discover" element={<DiscoverPage />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/login" element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } />
          <Route path="/verify-email" element={<VerifyEmail />} />
          
          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/tools" element={
            <ProtectedRoute>
              <Tools />
            </ProtectedRoute>
          } />
          <Route path="/tool/:slug" element={<ToolDetail />} />
          <Route path="/blogs" element={
            <ProtectedRoute>
              <Blogs />
            </ProtectedRoute>
          } />
          <Route path="/my-blogs" element={
            <ProtectedRoute>
              <MyBlogs />
            </ProtectedRoute>
          } />
          <Route path="/blog/:id" element={<BlogDetail />} />
          <Route path="/profile" element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />
          
          {/* Super Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute requiredRole="superadmin">
              <AdminPanel />
            </ProtectedRoute>
          } />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#f9fafb',
            border: '1px solid #374151',
          },
        }}
      />
    </div>
  );
}

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <HelmetProvider>
          <ThemeProvider>
            <AuthProvider>
              <Router>
                <AppContent />
              </Router>
            </AuthProvider>
          </ThemeProvider>
        </HelmetProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;