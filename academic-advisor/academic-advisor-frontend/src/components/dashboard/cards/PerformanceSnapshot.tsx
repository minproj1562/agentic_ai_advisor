// src/components/dashboard/cards/PerformanceSnapshot.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Users, Clock, Award } from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { auth } from '../../../services/firebase.config';

const PerformanceSnapshot: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const { data: performanceData } = useQuery({
    queryKey: ['performanceSnapshot', facultyId],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `http://localhost:8000/api/v1/faculty/${facultyId}/performance-snapshot`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    }
  });

  const weeklyData = performanceData?.weekly || [
    { day: 'Mon', sessions: 4, rating: 4.5 },
    { day: 'Tue', sessions: 6, rating: 4.7 },
    { day: 'Wed', sessions: 5, rating: 4.6 },
    { day: 'Thu', sessions: 7, rating: 4.8 },
    { day: 'Fri', sessions: 8, rating: 4.9 },
    { day: 'Sat', sessions: 3, rating: 4.5 },
    { day: 'Sun', sessions: 2, rating: 4.6 }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          Performance Snapshot
        </h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Last 7 days
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Session Trend */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Weekly Sessions
          </h4>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="sessions"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Rating Trend */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Average Rating
          </h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="day" />
              <YAxis domain={[4, 5]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="rating"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="text-center">
          <Users className="w-6 h-6 mx-auto mb-2 text-indigo-600" />
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {performanceData?.totalSessions || 35}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Sessions</p>
        </div>
        <div className="text-center">
          <Clock className="w-6 h-6 mx-auto mb-2 text-green-600" />
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {performanceData?.avgDuration || '45m'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Avg Duration</p>
        </div>
        <div className="text-center">
          <Award className="w-6 h-6 mx-auto mb-2 text-yellow-600" />
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {performanceData?.avgRating || 4.7}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Rating</p>
        </div>
        <div className="text-center">
          <TrendingUp className="w-6 h-6 mx-auto mb-2 text-purple-600" />
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {performanceData?.improvement || '+15%'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Growth</p>
        </div>
      </div>
    </div>
  );
};

export default PerformanceSnapshot;