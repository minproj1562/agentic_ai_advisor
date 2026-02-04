// src/components/FacultyGuard.tsx
import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../services/api.service';
import { Loader2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

interface FacultyGuardProps {
  children: React.ReactNode;
}

const FacultyGuard: React.FC<FacultyGuardProps> = ({ children }) => {
  const { user, loading: authLoading } = useAuth();
  const location = useLocation();
  const [checkingSetup, setCheckingSetup] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkProfileSetup = async () => {
      // Not authenticated or not faculty
      if (!user || user.role !== 'faculty') {
        setCheckingSetup(false);
        return;
      }

      // Skip check if already on setup page
      if (location.pathname === '/faculty/profile-setup') {
        setCheckingSetup(false);
        return;
      }

      try {
        const response = await apiClient.get('/faculty-profile/check-setup-status');
        
        if (!response.data.setup_complete) {
          setNeedsSetup(true);
        }
      } catch (err: any) {
        console.error('Error checking profile setup:', err);
        
        // If 404, profile doesn't exist - needs setup
        if (err.response?.status === 404) {
          setNeedsSetup(true);
        } else {
          // For other errors, allow through but log
          console.warn('Profile check failed, allowing access');
        }
      } finally {
        setCheckingSetup(false);
      }
    };

    if (!authLoading && user) {
      checkProfileSetup();
    } else if (!authLoading) {
      setCheckingSetup(false);
    }
  }, [user, authLoading, location.pathname]);

  // Loading state
  if (authLoading || checkingSetup) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="relative">
            <Loader2 className="w-16 h-16 text-indigo-600 animate-spin mx-auto" />
            <div className="absolute inset-0 w-16 h-16 mx-auto border-4 border-indigo-200 rounded-full" />
          </div>
          <p className="mt-4 text-gray-600 dark:text-gray-400 font-medium">
            Loading your dashboard...
          </p>
        </motion.div>
      </div>
    );
  }

  // Not authenticated
  if (!user) {
    return <Navigate to="/login" state={{ from: location, userType: 'faculty' }} replace />;
  }

  // Not a faculty member
  if (user.role !== 'faculty') {
    return <Navigate to="/student/dashboard" replace />;
  }

  // Needs to complete profile setup
  if (needsSetup && location.pathname !== '/faculty/profile-setup') {
    return <Navigate to="/faculty/profile-setup" replace />;
  }

  // Error state (optional - show inline)
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center max-w-md p-8 bg-white dark:bg-gray-800 rounded-xl shadow-xl">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Something went wrong
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default FacultyGuard;