// src/components/dashboard/cards/QuickActionsCard.tsx
import React from 'react';
import { motion } from 'framer-motion';
import {
  Calendar, MessageSquare, FileText, Users,
  Video, BarChart, BookOpen, Settings
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const QuickActionsCard: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const navigate = useNavigate();

  const actions = [
    {
      icon: Calendar,
      label: 'Schedule Meeting',
      description: 'Book a session with students',
      color: 'from-blue-500 to-blue-600',
      onClick: () => navigate('/faculty/appointments')
    },
    {
      icon: MessageSquare,
      label: 'Send Message',
      description: 'Communicate with mentees',
      color: 'from-green-500 to-green-600',
      onClick: () => navigate('/faculty/messages')
    },
    {
      icon: FileText,
      label: 'Upload CV',
      description: 'Update your profile',
      color: 'from-purple-500 to-purple-600',
      onClick: () => navigate('/faculty/cv-analysis')
    },
    {
      icon: Users,
      label: 'View Mentees',
      description: 'Check student progress',
      color: 'from-orange-500 to-orange-600',
      onClick: () => navigate('/faculty/mentees')
    },
    {
      icon: Video,
      label: 'Start Session',
      description: 'Begin video meeting',
      color: 'from-red-500 to-red-600',
      onClick: () => window.open('/meeting', '_blank')
    },
    {
      icon: BarChart,
      label: 'View Analytics',
      description: 'Performance insights',
      color: 'from-indigo-500 to-indigo-600',
      onClick: () => navigate('/faculty/analytics')
    }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Quick Actions
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {actions.map((action, index) => {
          const Icon = action.icon;
          return (
            <motion.button
              key={action.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={action.onClick}
              className="group relative p-4 bg-gray-50 dark:bg-gray-700 rounded-xl hover:shadow-lg transition-all duration-300 overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-r ${action.color} opacity-0 group-hover:opacity-10 transition-opacity`} />
              <div className="relative">
                <div className={`w-12 h-12 mx-auto mb-3 rounded-lg bg-gradient-to-r ${action.color} p-2.5`}>
                  <Icon className="w-full h-full text-white" />
                </div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {action.label}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {action.description}
                </p>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};

export default QuickActionsCard;