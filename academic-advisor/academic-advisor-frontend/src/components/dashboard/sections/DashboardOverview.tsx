// src/components/dashboard/sections/DashboardOverview.tsx
import React from 'react';
import { motion } from 'framer-motion';
import {
  Users, TrendingUp, Award, Calendar, BookOpen,
  Activity, Target, Clock, Star
} from 'lucide-react';
import MenteeOverviewCard from '../cards/MenteeOverviewCard';
import CVAnalyserCard from '../cards/CVAnalyserCard';
import MentorshipSlotsCard from '../cards/MentorshipSlotsCard';
import ExpertiseSummaryCard from '../cards/ExpertiseSummaryCard';
import NotificationsCard from '../cards/NotificationsCard';
import QuickActionsCard from '../cards/QuickActionsCard';
import PerformanceSnapshot from '../cards/PerformanceSnapshot';

const DashboardOverview: React.FC<{ data: any; facultyId: string }> = ({ data, facultyId }) => {
  const stats = [
    {
      label: 'Total Mentees',
      value: data?.stats.totalMentees || 0,
      icon: Users,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      change: '+12%',
      changeType: 'increase'
    },
    {
      label: 'At Risk',
      value: data?.stats.atRiskStudents || 0,
      icon: Activity,
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
      change: '-8%',
      changeType: 'decrease'
    },
    {
      label: 'Improving',
      value: data?.stats.improvingStudents || 0,
      icon: TrendingUp,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      change: '+23%',
      changeType: 'increase'
    },
    {
      label: 'Upcoming Slots',
      value: data?.stats.upcomingSlots || 0,
      icon: Calendar,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      change: '+5',
      changeType: 'neutral'
    },
  ];

  return (
    <>
      {/* Welcome Section with Gradient */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 p-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-xl text-white relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative z-10">
          <h1 className="text-4xl font-bold mb-2">
            Welcome back, {data?.faculty.name.split(' ')[0]}! 👋
          </h1>
          <p className="text-xl opacity-90">
            Here's your dashboard overview for {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg backdrop-blur">
              <Star className="w-5 h-5" />
              <span className="font-medium">4.8 Rating</span>
            </div>
            <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg backdrop-blur">
              <Award className="w-5 h-5" />
              <span className="font-medium">Top Mentor</span>
            </div>
            <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg backdrop-blur">
              <Clock className="w-5 h-5" />
              <span className="font-medium">3 Sessions Today</span>
            </div>
          </div>
        </div>
        
        {/* Decorative Elements */}
        <div className="absolute -top-10 -right-10 w-40 h-40 bg-white opacity-5 rounded-full"></div>
        <div className="absolute -bottom-10 -left-10 w-60 h-60 bg-white opacity-5 rounded-full"></div>
      </motion.div>

      {/* Enhanced Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden group hover:shadow-2xl transition-all duration-300"
            >
              <div className="p-6">
                <div className={`absolute inset-0 bg-gradient-to-r ${stat.color} opacity-5 group-hover:opacity-10 transition-opacity`}></div>
                <div className="relative">
                  <div className={`inline-flex p-3 rounded-lg ${stat.bgColor} mb-4`}>
                    <Icon className={`w-6 h-6 bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`} />
                  </div>
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        {stat.label}
                      </p>
                      <p className="text-3xl font-bold text-gray-900 dark:text-white">
                        {stat.value}
                      </p>
                    </div>
                    <div className={`text-sm font-medium ${
                      stat.changeType === 'increase' ? 'text-green-600 dark:text-green-400' :
                      stat.changeType === 'decrease' ? 'text-red-600 dark:text-red-400' :
                      'text-gray-600 dark:text-gray-400'
                    }`}>
                      {stat.change}
                    </div>
                  </div>
                </div>
              </div>
              <div className={`h-1 bg-gradient-to-r ${stat.color}`}></div>
            </motion.div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mb-8"
      >
        <QuickActionsCard facultyId={facultyId} />
      </motion.div>

      {/* Performance Snapshot */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="mb-8"
      >
        <PerformanceSnapshot facultyId={facultyId} />
      </motion.div>

      {/* Main Dashboard Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7 }}
          className="lg:col-span-2 xl:col-span-2"
        >
          <MenteeOverviewCard mentees={data?.mentees || []} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8 }}
        >
          <CVAnalyserCard cvMetadata={data?.cvMetadata} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.9 }}
        >
          <MentorshipSlotsCard slots={data?.mentorshipSlots || []} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.0 }}
        >
          <ExpertiseSummaryCard
            cvMetadata={data?.cvMetadata}
            expertise={data?.faculty.expertise || []}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.1 }}
        >
          <NotificationsCard notifications={data?.notifications || []} />
        </motion.div>
      </div>
    </>
  );
};

export default DashboardOverview;