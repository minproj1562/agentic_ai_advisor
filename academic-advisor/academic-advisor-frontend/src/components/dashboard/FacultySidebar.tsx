// src/components/dashboard/FacultySidebar.tsx
import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  Calendar,
  Bell,
  Settings,
  Brain,
  FileText,
  UserCircle,
  BookOpen,
  AlertTriangle
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface FacultySidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  facultyData?: any;
  notificationCount?: number;
  pendingMeetings?: number;
}

const FacultySidebar: React.FC<FacultySidebarProps> = ({
  activeSection,
  onSectionChange,
  facultyData,
  notificationCount = 0,
  pendingMeetings = 0
}) => {
  // Simplified menu - only essential items per requirements
  const menuItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'students', label: 'Student Analysis', icon: Users, description: 'View student data & projects' },
    { id: 'resources', label: 'Learning Resources', icon: BookOpen, description: 'Upload & manage resources' },
    { id: 'remedial', label: 'Remedial Students', icon: AlertTriangle, description: 'Track struggling students' },
    { id: 'meetings', label: 'Meeting Requests', icon: Calendar, badge: pendingMeetings },
    { id: 'calendar', label: 'Schedule Calendar', icon: Calendar },
    { id: 'profile', label: 'My Profile', icon: UserCircle },
    { id: 'cv-analysis', label: 'CV & Expertise', icon: Brain },
    { id: 'notifications', label: 'Notifications', icon: Bell, badge: notificationCount },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="h-full bg-white dark:bg-gray-800 p-4 flex flex-col">
      {/* Faculty Profile Summary */}
      <div className="mb-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl">
        <div className="flex items-center gap-3 mb-3">
          {facultyData?.photo_url ? (
            <img 
              src={facultyData.photo_url} 
              alt={facultyData.name}
              className="w-12 h-12 rounded-full object-cover border-2 border-indigo-500"
            />
          ) : (
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
              {facultyData?.name?.charAt(0) || 'F'}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-900 dark:text-white truncate">
              {facultyData?.name || 'Faculty'}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
              {facultyData?.designation || 'Professor'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
              {facultyData?.department || 'Department'}
            </p>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-white dark:bg-gray-700 p-2 rounded-lg text-center">
            <p className="text-gray-500 dark:text-gray-400">Mentees</p>
            <p className="font-bold text-gray-900 dark:text-white">
              {facultyData?.mentee_count || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-700 p-2 rounded-lg text-center">
            <p className="text-gray-500 dark:text-gray-400">Pending</p>
            <p className="font-bold text-orange-600 dark:text-orange-400">
              {pendingMeetings}
            </p>
          </div>
        </div>
        
        {/* Profile Completeness */}
        {facultyData?.profile_completeness !== undefined && (
          <div className="mt-3">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-500 dark:text-gray-400">Profile</span>
              <span className="text-gray-700 dark:text-gray-300">
                {facultyData.profile_completeness}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-1.5 rounded-full transition-all"
                style={{ width: `${facultyData.profile_completeness}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 space-y-1 overflow-y-auto">
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
              <span className="text-sm font-medium flex-1 text-left">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={cn(
                  "px-2 py-0.5 rounded-full text-xs font-medium",
                  isActive
                    ? "bg-indigo-200 dark:bg-indigo-800 text-indigo-800 dark:text-indigo-200"
                    : "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
                )}>
                  {item.badge > 9 ? '9+' : item.badge}
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 px-2">
          QUICK ACTIONS
        </p>
        <button
          onClick={() => onSectionChange('meetings')}
          className="w-full text-left text-xs px-3 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg hover:from-indigo-100 hover:to-purple-100 dark:hover:from-indigo-800/20 dark:hover:to-purple-800/20 transition-colors text-indigo-700 dark:text-indigo-300 font-medium"
        >
          📅 View Meeting Requests
        </button>
      </div>
    </div>
  );
};

export default FacultySidebar;