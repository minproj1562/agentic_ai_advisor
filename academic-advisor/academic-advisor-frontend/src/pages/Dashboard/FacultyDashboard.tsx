// src/pages/Dashboard/FacultyDashboard.tsx
import React, { Suspense, useState, useCallback, useEffect, lazy } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { useTheme } from "../../hooks/useTheme";
import { useDashboardData } from "../../hooks/useDashboardData";
import { useAuth } from '../../contexts/AuthContext';

// Lazy load section components for better performance
const Performance = lazy(() => import('../../components/dashboard/sections/Performance'));
const ResearchAreas = lazy(() => import('../../components/dashboard/sections/ResearchAreas'));
const Publications = lazy(() => import('../../components/dashboard/sections/Publications'));
const Messages = lazy(() => import('../../components/dashboard/sections/Messages'));
const Achievements = lazy(() => import('../../components/dashboard/sections/Achievements'));
const Analytics = lazy(() => import('../../components/dashboard/sections/Analytics'));
const Settings = lazy(() => import('../../components/dashboard/sections/Settings'));

// Fix: Import AIInsightsDashboard differently since it's not a default export
const AIInsightsDashboard = lazy(() => 
  import('../../components/dashboard/AIInsightsDashboard').then(module => ({
    default: module.AIInsightsDashboard
  }))
);

// Component imports
import FacultyHeader from '../../components/dashboard/FacultyHeader';
import FacultySidebar from '../../components/dashboard/FacultySidebar';
import MenteeOverviewCard from '../../components/dashboard/cards/MenteeOverviewCard';
import CVAnalyserCard from '../../components/dashboard/cards/CVAnalyserCard';
import MentorshipSlotsCard from '../../components/dashboard/cards/MentorshipSlotsCard';
import ExpertiseSummaryCard from '../../components/dashboard/cards/ExpertiseSummaryCard';
import NotificationsCard from '../../components/dashboard/cards/NotificationsCard';
import LoadingSkeleton from '../../components/dashboard/common/LoadingSkeleton';
import DashboardOverview from '../../components/dashboard/sections/DashboardOverview';

const FacultyDashboard: React.FC = () => {
  const { user, isAuthenticated, logout, loading: authLoading } = useAuth();
  const { theme, toggleTheme } = useTheme() as { theme: "dark" | "light"; toggleTheme: () => void };
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [isMobile, setIsMobile] = useState(false);

  const facultyId = user?.uid || '';
  const { data, isLoading, isError, error, refetch } = useDashboardData(facultyId);

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      }
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleSidebarToggle = useCallback(() => {
    setIsSidebarOpen(prev => !prev);
  }, []);

  const handleSectionChange = useCallback((section: string) => {
    setActiveSection(section);
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  }, [isMobile]);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const ErrorFallback = ({ error, resetErrorBoundary }: any) => (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full bg-white dark:bg-gray-800 shadow-2xl rounded-2xl p-8"
      >
        <div className="flex items-center justify-center w-16 h-16 mx-auto bg-red-100 dark:bg-red-900/30 rounded-full">
          <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="mt-6 text-2xl font-bold text-center text-gray-900 dark:text-white">
          Oops! Something went wrong
        </h2>
        <p className="mt-3 text-center text-gray-600 dark:text-gray-400">
          {error.message || 'An unexpected error occurred. Please try again or contact support.'}
        </p>
        <div className="mt-8 flex gap-3">
          <button
            onClick={resetErrorBoundary}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all transform hover:scale-105 font-medium"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-xl hover:bg-gray-300 dark:hover:bg-gray-600 transition-all font-medium"
          >
            Go Home
          </button>
        </div>
      </motion.div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'overview':
        return <DashboardOverview data={data} facultyId={facultyId} />;
      case 'mentees':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              My Mentees
            </h2>
            <MenteeOverviewCard mentees={data?.mentees || []} />
          </motion.div>
        );
      case 'cv-analysis':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              CV Analysis & Expertise
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CVAnalyserCard cvMetadata={data?.cvMetadata || null} />
              <ExpertiseSummaryCard
                cvMetadata={data?.cvMetadata || null}
                expertise={data?.faculty.expertise || []}
              />
            </div>
          </motion.div>
        );
      case 'appointments':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Appointments & Scheduling
            </h2>
            <MentorshipSlotsCard slots={data?.mentorshipSlots || []} />
          </motion.div>
        );
      case 'performance':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <Performance facultyId={facultyId} />
          </Suspense>
        );
      case 'ai-insights':
        // For student view, pass student-specific props
        const studentId = user?.role === 'student' ? user.uid : facultyId;
        const semester = parseInt(localStorage.getItem('userSemester') || '5');
        const branch = localStorage.getItem('userBranch') || 'IT';
        
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <AIInsightsDashboard 
              studentId={studentId}
              semester={semester}
              branch={branch}
            />
          </Suspense>
        );
      case 'research':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <ResearchAreas facultyId={facultyId} />
          </Suspense>
        );
      case 'publications':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <Publications facultyId={facultyId} />
          </Suspense>
        );
      case 'messages':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <Messages facultyId={facultyId} />
          </Suspense>
        );
      case 'achievements':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <Achievements facultyId={facultyId} />
          </Suspense>
        );
      case 'analytics':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <Analytics facultyId={facultyId} />
          </Suspense>
        );
      case 'notifications':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Notifications Center
            </h2>
            <NotificationsCard notifications={data?.notifications || []} />
          </motion.div>
        );
      case 'settings':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <Settings facultyId={facultyId} />
          </Suspense>
        );
      default:
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"
              />
              <p className="text-gray-500 dark:text-gray-400">
                Loading section...
              </p>
            </div>
          </div>
        );
    }
  };

  if (authLoading || !isAuthenticated) {
    return <LoadingSkeleton />;
  }

  if (user && user.role !== 'faculty' && user.role !== 'student') {
    return <ErrorFallback error={new Error('Unauthorized access')} resetErrorBoundary={refetch} />;
  }

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError) {
    return <ErrorFallback error={error} resetErrorBoundary={refetch} />;
  }

  // For student users, we might not have faculty data
  if (!data?.faculty && user?.role === 'faculty') {
    return <ErrorFallback error={new Error('Faculty data not found')} resetErrorBoundary={refetch} />;
  }

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onReset={refetch}>
      <div className={`min-h-screen ${theme === 'dark' ? 'dark' : ''}`}>
        <div className="bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:to-gray-800 transition-all duration-300">
          <Toaster 
            position="top-right"
            toastOptions={{
              className: 'dark:bg-gray-800 dark:text-white',
              duration: 4000,
            }}
          />
          
          <FacultyHeader
            faculty={data?.faculty}
            onMenuClick={handleSidebarToggle}
            onThemeToggle={toggleTheme}
            theme={theme}
            stats={data?.stats}
            onLogout={handleLogout}
          />

          <div className="flex h-[calc(100vh-64px)] relative">
            {/* Overlay for mobile */}
            {isMobile && isSidebarOpen && (
              <div
                className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
                onClick={() => setIsSidebarOpen(false)}
              />
            )}

            <AnimatePresence>
              {isSidebarOpen && (
                <motion.aside
                  initial={{ x: -300 }}
                  animate={{ x: 0 }}
                  exit={{ x: -300 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  className={`${
                    isMobile ? 'fixed' : 'relative'
                  } z-50 w-72 bg-white dark:bg-gray-800 shadow-2xl overflow-y-auto h-full border-r border-gray-200 dark:border-gray-700`}
                >
                  <FacultySidebar
                    activeSection={activeSection}
                    onSectionChange={handleSectionChange}
                    facultyData={data?.faculty}
                  />
                </motion.aside>
              )}
            </AnimatePresence>

            <main className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
              <div className="p-6 max-w-7xl mx-auto">
                <AnimatePresence mode="wait">
                  {renderContent()}
                </AnimatePresence>
              </div>
            </main>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default FacultyDashboard;