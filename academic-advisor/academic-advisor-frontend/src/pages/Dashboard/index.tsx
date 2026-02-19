// academic-advisor/academic-advisor-frontend/src/pages/Dashboard/index.tsx
import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import StudentDashboard from './StudentDashboard';
import FacultyDashboard from './FacultyDashboard';
import { Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const { user, loading } = useAuth();
  const [dashboardReady, setDashboardReady] = useState(false);

  useEffect(() => {
    // Simulate dashboard initialization only if user is authenticated
    if (user) {
      const timer = setTimeout(() => {
        setDashboardReady(true);
      }, 500);

      return () => clearTimeout(timer);
    } else {
      // If no user, set dashboardReady to true immediately to avoid unnecessary delay
      setDashboardReady(true);
    }
  }, [user]);

  if (loading || !dashboardReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Loading your personalized dashboard...</p>
        </motion.div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Please login to view your dashboard</p>
      </div>
    );
  }

  // Render role-specific dashboard
  if (user.role === 'student') {
    return <StudentDashboard />;
  } 
  else if (user.role === 'faculty') {
    return <FacultyDashboard />;
  } else {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Invalid user role</p>
      </div>
    );
  }
};

export default Dashboard;