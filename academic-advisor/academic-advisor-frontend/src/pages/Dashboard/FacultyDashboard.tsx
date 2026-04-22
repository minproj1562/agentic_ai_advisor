// src/pages/Dashboard/FacultyDashboard.tsx
import React, { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { Edit3, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { doc, getDoc } from 'firebase/firestore';

import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api.service';
import { db } from '../../services/firebase.config';

// Core Components
import FacultyHeader from '../../components/dashboard/FacultyHeader';
import FacultySidebar from '../../components/dashboard/FacultySidebar';
import LoadingSkeleton from '../../components/dashboard/common/LoadingSkeleton';

// Lazy load sections
const FacultyOverview        = lazy(() => import('../../components/dashboard/sections/FacultyOverview'));
const StudentAnalysisSection = lazy(() => import('../../components/dashboard/sections/StudentAnalysisSection'));
const MeetingManagement      = lazy(() => import('../../components/meetings/FacultyMeetingManagement'));
const MeetingsCalendar       = lazy(() => import('../../components/meetings/MeetingsCalendar'));
const FacultyProfileView     = lazy(() => import('../../components/dashboard/sections/FacultyProfileView'));
const CVAnalysisSection      = lazy(() => import('../../components/dashboard/sections/CVAnalysisSection'));
const MessagesSection        = lazy(() => import('../../components/dashboard/sections/Messages'));
const NotificationsSection   = lazy(() => import('../../components/dashboard/sections/NotificationsSection'));
const SettingsSection        = lazy(() => import('../../components/dashboard/sections/Settings'));

const FacultyDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, loading: authLoading } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [isSidebarOpen, setIsSidebarOpen]   = useState(true);
  const [activeSection, setActiveSection]   = useState<string>('overview');
  const [isMobile, setIsMobile]             = useState(false);

  // ✅ NEW: must change password state
  const [mustChangePassword, setMustChangePassword]   = useState(false);
  const [passwordBannerDismissed, setPasswordBannerDismissed] = useState(false);

  // ── Mobile check ───────────────────────────────────────────────────────────
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

  // ✅ NEW: Check must_change_password flag from Firestore
  useEffect(() => {
    const checkPasswordFlag = async () => {
      if (!user?.uid) return;
      try {
        const userDoc = await getDoc(doc(db, 'users', user.uid));
        if (userDoc.exists()) {
          const data = userDoc.data();
          setMustChangePassword(data?.must_change_password === true);
        }
      } catch (error) {
        console.error('Error checking password flag:', error);
      }
    };
    checkPasswordFlag();
  }, [user?.uid]);

  // ── Queries ────────────────────────────────────────────────────────────────

  const {
    data: facultyData,
    isLoading: profileLoading,
    error: profileError,
  } = useQuery({
    queryKey: ['faculty-profile', user?.uid],
    queryFn: async () => {
      const response = await apiClient.get('/faculty-profile/me');
      return response.data;
    },
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
  });

  const { data: meetingData } = useQuery({
    queryKey: ['faculty-meetings', user?.uid],
    queryFn: async () => {
      const response = await apiClient.get('/meetings/faculty/requests');
      return response.data;
    },
    enabled: !!user?.uid,
    staleTime: 60 * 1000,
  });

  const { data: notificationData } = useQuery({
    queryKey: ['notifications-count', user?.uid],
    queryFn: async () => {
      const response = await apiClient.get('/notifications/unread-count');
      return response.data;
    },
    enabled: !!user?.uid,
    staleTime: 30 * 1000,
  });

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleSidebarToggle = useCallback(() => {
    setIsSidebarOpen((prev) => !prev);
  }, []);

  const handleSectionChange = useCallback(
    (section: string) => {
      setActiveSection(section);
      if (isMobile) setIsSidebarOpen(false);
    },
    [isMobile]
  );

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleEditProfile = () => {
    navigate('/faculty/profile-edit', {
      state: { editMode: true, profile: facultyData },
    });
  };

  // ✅ NEW: Go to password tab in settings
  const handleGoToChangePassword = () => {
    setActiveSection('settings');
    setPasswordBannerDismissed(false);
    if (isMobile) setIsSidebarOpen(false);
  };

  // ── Derived data ───────────────────────────────────────────────────────────

  const headerFacultyData = facultyData
    ? {
        id:           facultyData.user_id,
        name:         facultyData.name,
        email:        facultyData.email,
        department:   facultyData.department,
        profilePhoto: facultyData.uniform_profile?.personal_info?.photo_url,
        role:         facultyData.designation || 'Professor',
        expertise:    facultyData.uniform_profile?.research_expertise?.primary_areas || [],
        joinedDate:   new Date(facultyData.created_at),
        totalMentees: facultyData.mentee_count || 0,
      }
    : undefined;

  const stats = {
    totalMentees:        facultyData?.mentee_count || 0,
    atRiskStudents:      0,
    improvingStudents:   0,
    upcomingSlots:       meetingData?.accepted?.length || 0,
    unreadNotifications: notificationData?.unread_count || 0,
  };

  // ── Section renderer ───────────────────────────────────────────────────────

  const renderContent = () => {
    const sectionProps = {
      facultyId:   user?.uid || '',
      facultyData,
    };

    switch (activeSection) {
      case 'overview':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <FacultyOverview {...sectionProps} meetingData={meetingData} />
          </Suspense>
        );

      case 'students':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <StudentAnalysisSection {...sectionProps} />
          </Suspense>
        );

      case 'meetings':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <MeetingManagement />
          </Suspense>
        );

      case 'calendar':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Meeting Calendar
              </h2>
              <MeetingsCalendar />
            </div>
          </Suspense>
        );

      case 'profile':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <FacultyProfileView {...sectionProps} />
          </Suspense>
        );

      case 'cv-analysis':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <CVAnalysisSection {...sectionProps} />
          </Suspense>
        );

      case 'messages':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <MessagesSection facultyId={user?.uid || ''} />
          </Suspense>
        );

      case 'notifications':
        return (
          <Suspense fallback={<LoadingSkeleton />}>
            <NotificationsSection userId={user?.uid || ''} />
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

  // ── Guards ─────────────────────────────────────────────────────────────────

  if (authLoading || profileLoading) {
    return <LoadingSkeleton />;
  }

  if (profileError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center max-w-md p-8 bg-white dark:bg-gray-800 rounded-xl shadow-xl">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Unable to Load Profile
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            There was an error loading your profile. Please try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'dark' : ''}`}>
      <div className="bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 transition-colors duration-300">
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'dark:bg-gray-800 dark:text-white',
            duration: 4000,
          }}
        />

        {/* Header */}
        <FacultyHeader
          faculty={headerFacultyData}
          onMenuClick={handleSidebarToggle}
          onThemeToggle={toggleTheme}
          theme={theme as 'light' | 'dark'}
          stats={stats}
          onLogout={handleLogout}
        />

        <div className="flex h-[calc(100vh-64px)] relative">

          {/* Mobile overlay */}
          {isMobile && isSidebarOpen && (
            <div
              className="fixed inset-0 bg-black/50 z-40"
              onClick={() => setIsSidebarOpen(false)}
            />
          )}

          {/* Sidebar */}
          <AnimatePresence>
            {isSidebarOpen && (
              <motion.aside
                initial={{ x: -300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className={`${
                  isMobile ? 'fixed' : 'relative'
                } z-50 w-72 bg-white dark:bg-gray-800 shadow-xl overflow-hidden h-full border-r border-gray-200 dark:border-gray-700`}
              >
                <FacultySidebar
                  activeSection={activeSection}
                  onSectionChange={handleSectionChange}
                  facultyData={{
                    ...facultyData,
                    photo_url: facultyData?.uniform_profile?.personal_info?.photo_url,
                  }}
                  notificationCount={notificationData?.unread_count || 0}
                  pendingMeetings={meetingData?.pending?.length || 0}
                />
              </motion.aside>
            )}
          </AnimatePresence>

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">

            {/* ✅ Amber password alert banner */}
            <AnimatePresence>
              {mustChangePassword &&
                !passwordBannerDismissed &&
                activeSection !== 'settings' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="mx-6 mt-4"
                  >
                    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-xl p-4 flex items-center justify-between gap-4">
                      {/* Left: icon + text */}
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="flex-shrink-0 w-9 h-9 bg-amber-100 dark:bg-amber-900/40 rounded-lg flex items-center justify-center">
                          <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                            Security Alert: Change your default password
                          </p>
                          <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5 truncate">
                            Your account uses the default password{' '}
                            <code className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 py-0.5 rounded">
                              Fcrit@2025
                            </code>
                            . Please update it to secure your account.
                          </p>
                        </div>
                      </div>

                      {/* Right: action buttons */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={handleGoToChangePassword}
                          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-medium transition-colors whitespace-nowrap"
                        >
                          Change Now →
                        </button>
                        <button
                          onClick={() => setPasswordBannerDismissed(true)}
                          className="px-3 py-2 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded-lg text-xs transition-colors whitespace-nowrap"
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
            </AnimatePresence>

            {/* Page content */}
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

export default FacultyDashboard;