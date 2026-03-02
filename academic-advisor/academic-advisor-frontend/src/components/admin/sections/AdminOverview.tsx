// academic-advisor/academic-advisor-frontend/src/components/admin/sections/AdminOverview.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { Users, GraduationCap, BookOpen, Calendar, Activity, AlertTriangle } from 'lucide-react';

interface AdminOverviewProps {
  stats: any;
}

const AdminOverview: React.FC<AdminOverviewProps> = ({ stats }) => {
  const cards = [
    { label: 'Total Students', value: stats?.total_students || 0, icon: Users, color: 'from-blue-500 to-indigo-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
    { label: 'Total Faculty', value: stats?.total_faculty || 0, icon: GraduationCap, color: 'from-purple-500 to-pink-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
    { label: 'Active Electives', value: stats?.total_electives || 0, icon: BookOpen, color: 'from-green-500 to-emerald-500', bg: 'bg-green-50 dark:bg-green-900/20' },
    { label: 'Pending Meetings', value: stats?.pending_meetings || 0, icon: Calendar, color: 'from-orange-500 to-red-500', bg: 'bg-orange-50 dark:bg-orange-900/20' },
    { label: 'Total Projects', value: stats?.total_projects || 0, icon: Activity, color: 'from-cyan-500 to-blue-500', bg: 'bg-cyan-50 dark:bg-cyan-900/20' },
    { label: 'Pending Faculty', value: stats?.pending_faculty || 0, icon: AlertTriangle, color: 'from-yellow-500 to-orange-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20' },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-gradient-to-r from-red-600 via-orange-500 to-yellow-500 rounded-2xl shadow-xl text-white"
      >
        <h1 className="text-3xl font-bold mb-2">Admin Dashboard 🛡️</h1>
        <p className="text-lg opacity-90">
          System overview for {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden group hover:shadow-2xl transition-all"
            >
              <div className="p-6">
                <div className={`inline-flex p-3 rounded-lg ${card.bg} mb-4`}>
                  <Icon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{card.label}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{card.value}</p>
              </div>
              <div className={`h-1 bg-gradient-to-r ${card.color}`} />
            </motion.div>
          );
        })}
      </div>

      {/* Disclaimer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl"
      >
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-amber-900 dark:text-amber-100 text-sm">Disclaimer</h4>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
              The AI-based recommendations and analyses provided in this system are meant as suggestions only.
              Students should not rely fully on the AI's interpretation and are encouraged to consult with
              faculty advisors for academic decisions.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Firestore User Breakdown */}
      {stats?.firestore_users && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Registered Users (Firebase)</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(stats.firestore_users).map(([role, count]) => (
              <div key={role} className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{count as number}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{role}s</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOverview;