// academic-advisor/academic-advisor-frontend/src/components/admin/AdminSidebar.tsx
import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, Users, GraduationCap, BookOpen,
  BarChart3, Settings, Shield
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface AdminSidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  stats?: any;
}

const AdminSidebar: React.FC<AdminSidebarProps> = ({
  activeSection,
  onSectionChange,
  stats,
}) => {
  const menuItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'students', label: 'Students', icon: Users, badge: stats?.total_students },
    { id: 'faculty', label: 'Faculty', icon: GraduationCap, badge: stats?.total_faculty },
    { id: 'curriculum', label: 'Curriculum', icon: BookOpen },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="h-full bg-white dark:bg-gray-800 p-4 flex flex-col">
      {/* Admin Badge */}
      <div className="mb-6 p-4 bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 rounded-xl">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-900 dark:text-white">Admin Panel</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">System Management</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-white dark:bg-gray-700 p-2 rounded-lg text-center">
            <p className="text-gray-500 dark:text-gray-400">Students</p>
            <p className="font-bold text-gray-900 dark:text-white">{stats?.total_students || 0}</p>
          </div>
          <div className="bg-white dark:bg-gray-700 p-2 rounded-lg text-center">
            <p className="text-gray-500 dark:text-gray-400">Faculty</p>
            <p className="font-bold text-gray-900 dark:text-white">{stats?.total_faculty || 0}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
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
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
              )}
              whileHover={{ x: isActive ? 0 : 4 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium flex-1 text-left">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={cn(
                  'px-2 py-0.5 rounded-full text-xs font-medium',
                  isActive
                    ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
                )}>
                  {item.badge}
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>
    </div>
  );
};

export default AdminSidebar;