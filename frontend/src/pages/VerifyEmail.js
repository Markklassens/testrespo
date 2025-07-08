import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [verificationStatus, setVerificationStatus] = useState('pending');
  const [loading, setLoading] = useState(false);
  const { verifyEmail } = useAuth();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      handleVerification();
    }
  }, [token]);

  const handleVerification = async () => {
    setLoading(true);
    
    try {
      const result = await verifyEmail(token);
      
      if (result.success) {
        setVerificationStatus('success');
        toast.success('Email verified successfully!');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setVerificationStatus('error');
        toast.error(result.error);
      }
    } catch (error) {
      setVerificationStatus('error');
      toast.error('Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="xl" />
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Verifying your email...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          {verificationStatus === 'success' && (
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 dark:bg-green-900">
              <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          )}
          
          {verificationStatus === 'error' && (
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900">
              <XCircleIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
          )}
          
          <h2 className="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
            {verificationStatus === 'success' && 'Email Verified!'}
            {verificationStatus === 'error' && 'Verification Failed'}
            {verificationStatus === 'pending' && 'Email Verification'}
          </h2>
          
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {verificationStatus === 'success' && 'Your email has been successfully verified. You will be redirected to the login page shortly.'}
            {verificationStatus === 'error' && 'The verification link is invalid or has expired. Please request a new verification email.'}
            {verificationStatus === 'pending' && !token && 'Please check your email for the verification link.'}
          </p>
        </div>

        {verificationStatus === 'pending' && !token && (
          <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Verification Email Sent
                </h3>
                <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                  <p>
                    We've sent a verification email to your inbox. Please click the link in the email to verify your account.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {verificationStatus === 'success' && (
          <div className="text-center">
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              Go to Login
            </button>
          </div>
        )}

        {verificationStatus === 'error' && (
          <div className="text-center space-y-4">
            <button
              onClick={() => navigate('/register')}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              Register Again
            </button>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              Back to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;