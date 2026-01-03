// src/components/dashboard/FacultySidebar.tsx
import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  FileText,
  Calendar,
  Bell,
  Settings,
  BarChart,
  Brain,
  BookOpen,
  MessageSquare,
  Award,
  TrendingUp,
  Sparkles
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface FacultySidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  facultyData?: any;
}

const FacultySidebar: React.FC<FacultySidebarProps> = ({
  activeSection,
  onSectionChange,
  facultyData
}) => {
  const menuItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'mentees', label: 'My Mentees', icon: Users },
    { id: 'cv-analysis', label: 'CV Analysis', icon: Brain },
    { id: 'appointments', label: 'Appointments', icon: Calendar },
    { id: 'performance', label: 'Performance', icon: TrendingUp },
    { id: 'ai-insights', label: 'AI Insights', icon: Sparkles },
    { id: 'research', label: 'Research Areas', icon: BookOpen },
    { id: 'publications', label: 'Publications', icon: FileText },
    { id: 'messages', label: 'Messages', icon: MessageSquare },
    { id: 'achievements', label: 'Achievements', icon: Award },
    { id: 'analytics', label: 'Analytics', icon: BarChart },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="h-full bg-white dark:bg-gray-800 p-4">
      {/* Faculty Profile Summary */}
      <div className="mb-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 bg-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
            {facultyData?.name?.charAt(0) || 'F'}
          </div>
          <div>
            <p className="font-semibold text-gray-900 dark:text-white">
              {facultyData?.name || 'Faculty'}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              {facultyData?.department || 'Department'}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-white dark:bg-gray-700 p-2 rounded">
            <p className="text-gray-500 dark:text-gray-400">Mentees</p>
            <p className="font-bold text-gray-900 dark:text-white">
              {facultyData?.menteeCount || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-700 p-2 rounded">
            <p className="text-gray-500 dark:text-gray-400">Sessions</p>
            <p className="font-bold text-gray-900 dark:text-white">
              {facultyData?.sessionCount || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <motion.button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                isActive
                  ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
              )}
              whileHover={{ x: isActive ? 0 : 4 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{item.label}</span>
              {item.id === 'notifications' && (
                <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                  3
                </span>
              )}
              {item.id === 'ai-insights' && (
                <span className="ml-auto bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-0.5 rounded-full">
                  New
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Quick Actions */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-3">
          QUICK ACTIONS
        </p>
        <div className="space-y-2">
          <button
            onClick={() => onSectionChange('appointments')}
            className="w-full text-left text-xs px-3 py-2 bg-white dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          >
            Schedule Meeting
          </button>
          <button
            onClick={() => onSectionChange('cv-analysis')}
            className="w-full text-left text-xs px-3 py-2 bg-white dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          >
            Upload CV
          </button>
          <button
            onClick={() => onSectionChange('ai-insights')}
            className="w-full text-left text-xs px-3 py-2 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded hover:from-purple-100 hover:to-pink-100 dark:hover:from-purple-800/20 dark:hover:to-pink-800/20 transition-colors"
          >
            View AI Insights
          </button>
        </div>
      </div>
    </div>
  );
};

export default FacultySidebar;