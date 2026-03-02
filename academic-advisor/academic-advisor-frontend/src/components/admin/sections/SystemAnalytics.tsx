// academic-advisor/academic-advisor-frontend/src/components/admin/sections/SystemAnalytics.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, TrendingUp, Users } from 'lucide-react';
import apiClient from '../../../services/api.service';

const SystemAnalytics: React.FC = () => {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['admin-analytics'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/analytics/overview');
      return res.data;
    },
    staleTime: 60 * 1000,
  });

  const { data: deptComparison } = useQuery({
    queryKey: ['admin-dept-comparison'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/analytics/department-comparison');
      return res.data;
    },
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-48 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const perfDist = analytics?.performance_distribution || {};
  const maxPerf = Math.max(...Object.values(perfDist).map(Number), 1);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">System Analytics</h2>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg"><Users className="w-5 h-5 text-blue-600" /></div>
            <div>
              <p className="text-sm text-gray-500">Total Students</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics?.total_students || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg"><TrendingUp className="w-5 h-5 text-green-600" /></div>
            <div>
              <p className="text-sm text-gray-500">Average CGPA</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics?.average_cgpa?.toFixed(2) || 'N/A'}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg"><BarChart3 className="w-5 h-5 text-purple-600" /></div>
            <div>
              <p className="text-sm text-gray-500">Departments</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{Object.keys(analytics?.department_distribution || {}).length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Distribution */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Performance Distribution</h3>
        <div className="space-y-3">
          {[
            { key: 'excellent', label: 'Excellent (≥8.5)', color: 'bg-green-500' },
            { key: 'good', label: 'Good (7.0–8.5)', color: 'bg-blue-500' },
            { key: 'average', label: 'Average (5.5–7.0)', color: 'bg-yellow-500' },
            { key: 'poor', label: 'Poor (<5.5)', color: 'bg-red-500' },
          ].map(({ key, label, color }) => (
            <div key={key} className="flex items-center gap-4">
              <span className="w-36 text-sm text-gray-600 dark:text-gray-400">{label}</span>
              <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-6 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${((perfDist[key] || 0) / maxPerf) * 100}%` }}
                  transition={{ duration: 0.8, delay: 0.2 }}
                  className={`${color} h-full rounded-full flex items-center justify-end pr-2`}
                >
                  <span className="text-xs text-white font-medium">{perfDist[key] || 0}</span>
                </motion.div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Department Comparison */}
      {deptComparison?.departments?.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Department Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  {['Department', 'Students', 'Avg CGPA', 'Max', 'Min'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {deptComparison.departments.map((d: any) => (
                  <tr key={d.department} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{d.department}</td>
                    <td className="px-4 py-3">{d.student_count}</td>
                    <td className="px-4 py-3 font-semibold">{d.average_cgpa}</td>
                    <td className="px-4 py-3 text-green-600">{d.max_cgpa}</td>
                    <td className="px-4 py-3 text-red-600">{d.min_cgpa}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top Weak Subjects */}
      {analytics?.top_weak_subjects?.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Most Common Weak Subjects</h3>
          <div className="space-y-2">
            {analytics.top_weak_subjects.map((ws: any, idx: number) => (
              <div key={ws.subject} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/10 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 bg-red-200 dark:bg-red-800 rounded-full flex items-center justify-center text-xs font-bold text-red-700 dark:text-red-300">
                    {idx + 1}
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{ws.subject}</span>
                </div>
                <span className="text-sm text-red-600 dark:text-red-400 font-medium">{ws.count} students</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemAnalytics;