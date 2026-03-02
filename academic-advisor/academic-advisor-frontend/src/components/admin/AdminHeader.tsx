// academic-advisor/academic-advisor-frontend/src/components/admin/AdminHeader.tsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Menu, Moon, Sun, LogOut, ChevronDown, Shield } from 'lucide-react';
import { cn } from '../../utils/cn';
import toast from 'react-hot-toast';

interface AdminHeaderProps {
  user: any;
  onMenuClick: () => void;
  onThemeToggle: () => void;
  theme: 'light' | 'dark';
  onLogout: () => Promise<void>;
}

const AdminHeader: React.FC<AdminHeaderProps> = ({ user, onMenuClick, onThemeToggle, theme, onLogout }) => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await onLogout();
      toast.success('Logged out');
    } catch {
      toast.error('Logout failed');
    } finally {
      setIsLoggingOut(false);
      setIsProfileOpen(false);
    }
  };

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 h-16 sticky top-0 z-50">
      <div className="px-4 sm:px-6 lg:px-8 h-full">
        <div className="flex items-center justify-between h-full">
          {/* Left */}
          <div className="flex items-center gap-4">
            <button onClick={onMenuClick} className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 lg:hidden">
              <Menu className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <span className="hidden sm:block text-lg font-semibold text-gray-900 dark:text-white">
                Admin Panel
              </span>
            </div>
          </div>

          {/* Right */}
          <div className="flex items-center gap-3">
            <button onClick={onThemeToggle} className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700">
              {theme === 'light' ? <Moon className="w-5 h-5 text-gray-600" /> : <Sun className="w-5 h-5 text-gray-400" />}
            </button>

            <div ref={profileRef} className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-orange-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  {user?.name?.charAt(0) || 'A'}
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.name || 'Admin'}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Administrator</p>
                </div>
                <ChevronDown className={cn('w-4 h-4 text-gray-500 hidden sm:block transition-transform', isProfileOpen && 'rotate-180')} />
              </button>

              <AnimatePresence>
                {isProfileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
                  >
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={handleLogout}
                        disabled={isLoggingOut}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>{isLoggingOut ? 'Logging out...' : 'Logout'}</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AdminHeader;