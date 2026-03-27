// academic-advisor/academic-advisor-frontend/src/pages/Dashboard/AdminDashboard.tsx
import React, { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api.service';
import AdminSidebar from './../../components/admin/AdminSidebar';
import AdminHeader from './../../components/admin/AdminHeader';
import LoadingSkeleton from '../../components/dashboard/common/LoadingSkeleton';

const AdminOverview = lazy(() => import('.././../components/admin/sections/AdminOverview'));
const StudentManagement = lazy(() => import('.././../components/admin/sections/StudentManagement'));
const FacultyManagement = lazy(() => import('.././../components/admin/sections/FacultyManagement'));
const CurriculumManagement = lazy(() => import('.././../components/admin/sections/CurriculumManagement'));
const SystemAnalytics = lazy(() => import('.././../components/admin/sections/SystemAnalytics'));
const SettingsSection = lazy(() => import('../../components/dashboard/sections/Settings'));
const BulkMarksUpload = lazy(() => import('../../components/admin/sections/BulkMarksUpload'));

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, loading: authLoading } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setIsSidebarOpen(false);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/stats');
      return res.data;
    },
    enabled: !!user?.uid,
    staleTime: 60 * 1000,
  });

  const handleSidebarToggle = useCallback(() => {
    setIsSidebarOpen(prev => !prev);
  }, []);

  const handleSectionChange = useCallback((section: string) => {
    setActiveSection(section);
    if (isMobile) setIsSidebarOpen(false);
  }, [isMobile]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const renderContent = () => {
    switch (activeSection) {
      case 'overview':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <AdminOverview stats={stats} />
          </Suspense>
        );
      case 'students':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <StudentManagement />
          </Suspense>
        );
      case 'faculty':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <FacultyManagement />
          </Suspense>
        );
      case 'curriculum':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <CurriculumManagement />
          </Suspense>
        );
      case 'analytics':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <SystemAnalytics />
          </Suspense>
        );
              case 'bulk-upload':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <BulkMarksUpload />
          </Suspense>
        );
      case 'settings':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <SettingsSection facultyId={user?.uid || ''} />
          </Suspense>
        );
      default:
        return (
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500 dark:text-gray-400">Section not found</p>
          </div>
        );
    }
  };

  if (authLoading || statsLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'dark' : ''}`}>
      <div className="bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 transition-colors duration-300">
        <Toaster position="top-right" toastOptions={{ className: 'dark:bg-gray-800 dark:text-white', duration: 4000 }} />

        <AdminHeader
          user={user}
          onMenuClick={handleSidebarToggle}
          onThemeToggle={toggleTheme}
          theme={theme as 'light' | 'dark'}
          onLogout={handleLogout}
        />

        <div className="flex h-[calc(100vh-64px)] relative">
          {isMobile && isSidebarOpen && (
            <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setIsSidebarOpen(false)} />
          )}

          <AnimatePresence>
            {isSidebarOpen && (
              <motion.aside
                initial={{ x: -300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className={`${isMobile ? 'fixed' : 'relative'} z-50 w-72 bg-white dark:bg-gray-800 shadow-xl overflow-hidden h-full border-r border-gray-200 dark:border-gray-700`}
              >
                <AdminSidebar
                  activeSection={activeSection}
                  onSectionChange={handleSectionChange}
                  stats={stats}
                />
              </motion.aside>
            )}
          </AnimatePresence>

          <main className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
            <div className="p-6 max-w-7xl mx-auto">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeSection}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {renderContent()}
                </motion.div>
              </AnimatePresence>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;