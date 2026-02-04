// src/components/dashboard/sections/FacultyOverview.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { 
  Users, Calendar, Bell, TrendingUp, 
  Clock, CheckCircle, AlertCircle, ArrowRight 
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';

interface FacultyOverviewProps {
  facultyId: string;
  facultyData: any;
  meetingData: any;
}

const FacultyOverview: React.FC<FacultyOverviewProps> = ({
  facultyId,
  facultyData,
  meetingData
}) => {
  const pendingCount = meetingData?.pending?.length || 0;
  const upcomingCount = meetingData?.accepted?.length || 0;

  const stats = [
    {
      title: 'Total Mentees',
      value: facultyData?.mentee_count || 0,
      icon: Users,
      color: 'from-blue-500 to-indigo-500',
      change: '+2 this month',
    },
    {
      title: 'Pending Requests',
      value: pendingCount,
      icon: Clock,
      color: 'from-orange-500 to-red-500',
      urgent: pendingCount > 0,
    },
    {
      title: 'Upcoming Meetings',
      value: upcomingCount,
      icon: Calendar,
      color: 'from-green-500 to-emerald-500',
    },
    {
      title: 'Profile Score',
      value: `${facultyData?.profile_completeness || 0}%`,
      icon: TrendingUp,
      color: 'from-purple-500 to-pink-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Welcome back, {facultyData?.name?.split(' ')[0] || 'Professor'}! 👋
        </h1>
        <p className="text-indigo-100">
          {pendingCount > 0 
            ? `You have ${pendingCount} pending meeting request${pendingCount > 1 ? 's' : ''} to review.`
            : 'All caught up! No pending requests.'}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg ${
                stat.urgent ? 'ring-2 ring-orange-500' : ''
              }`}
            >
              <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${stat.color} opacity-10 rounded-bl-full`} />
              
              <div className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${stat.color} mb-4`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              
              <h3 className="text-3xl font-bold text-gray-900 dark:text-white">
                {stat.value}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {stat.title}
              </p>
              
              {stat.change && (
                <p className="text-xs text-green-600 dark:text-green-400 mt-2">
                  {stat.change}
                </p>
              )}
              
              {stat.urgent && (
                <span className="absolute top-4 right-4 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-orange-500" />
                </span>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Meeting Requests */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Pending Requests
            </h3>
            {pendingCount > 0 && (
              <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-full text-xs font-medium">
                {pendingCount} pending
              </span>
            )}
          </div>

          {pendingCount === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-3" />
              <p className="text-gray-600 dark:text-gray-400">
                No pending requests
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {meetingData?.pending?.slice(0, 3).map((request: any, index: number) => (
                <motion.div
                  key={request.request_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                    {request.student_name?.charAt(0) || 'S'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {request.student_name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {request.subject}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDistanceToNow(new Date(request.created_at), { addSuffix: true })}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    request.urgency === 'high' 
                      ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  }`}>
                    {request.urgency}
                  </span>
                </motion.div>
              ))}
              
              {pendingCount > 3 && (
                <button className="w-full py-2 text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-medium flex items-center justify-center gap-1">
                  View all {pendingCount} requests
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Upcoming Meetings */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Upcoming Meetings
            </h3>
            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-full text-xs font-medium">
              {upcomingCount} scheduled
            </span>
          </div>

          {upcomingCount === 0 ? (
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 dark:text-gray-400">
                No upcoming meetings
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {meetingData?.accepted?.slice(0, 3).map((meeting: any, index: number) => (
                <motion.div
                  key={meeting.request_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800"
                >
                  <div className="p-2 bg-green-500 rounded-lg">
                    <Calendar className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {meeting.student_name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {meeting.subject}
                    </p>
                    {meeting.scheduled_meeting && (
                      <div className="flex items-center gap-2 mt-1 text-xs text-green-700 dark:text-green-400">
                        <Clock className="w-3 h-3" />
                        {format(new Date(meeting.scheduled_meeting.date), 'MMM d')} at {meeting.scheduled_meeting.start_time}
                        <span>• {meeting.scheduled_meeting.venue}</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Profile Completeness */}
      {facultyData?.profile_completeness < 100 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-6 border border-amber-200 dark:border-amber-800"
        >
          <div className="flex items-start gap-4">
            <div className="p-3 bg-amber-500 rounded-lg">
              <AlertCircle className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-amber-900 dark:text-amber-100 mb-1">
                Complete Your Profile
              </h3>
              <p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
                Your profile is {facultyData?.profile_completeness}% complete. 
                A complete profile helps students find and connect with you better.
              </p>
              <div className="w-full bg-amber-200 dark:bg-amber-800 rounded-full h-2 mb-3">
                <div
                  className="bg-gradient-to-r from-amber-500 to-orange-500 h-2 rounded-full transition-all"
                  style={{ width: `${facultyData?.profile_completeness}%` }}
                />
              </div>
              <button className="text-sm font-medium text-amber-700 dark:text-amber-300 hover:text-amber-800 flex items-center gap-1">
                Complete profile
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default FacultyOverview;