// components/dashboard/cards/MenteeOverviewCard.tsx
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Student } from '../../../types/dashboard.types';
import { TrendingUp, TrendingDown, AlertTriangle, Search } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

interface MenteeOverviewCardProps {
  mentees: Student[];
}

const MenteeOverviewCard: React.FC<MenteeOverviewCardProps> = ({ mentees }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);

  const filteredMentees = useMemo(() => {
    return mentees.filter(mentee =>
      mentee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      mentee.rollNumber.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [mentees, searchTerm]);

  const getStatusBadge = (status: Student['status']) => {
    const styles = {
      'Active': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'At Risk': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'Improving': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    };
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const getTrendIcon = (trend: number[]) => {
    const lastTwo = trend.slice(-2);
    if (lastTwo[1] > lastTwo[0]) {
      return <TrendingUp className="w-4 h-4 text-green-500" />;
    } else if (lastTwo[1] < lastTwo[0]) {
      return <TrendingDown className="w-4 h-4 text-red-500" />;
    }
    return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Mentee Overview
        </h3>
        
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search mentees..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Mentee Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Student
              </th>
              <th className="text-left py-3 px-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                SGPI
              </th>
              <th className="text-left py-3 px-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Trend
              </th>
              <th className="text-left py-3 px-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="text-left py-3 px-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredMentees.slice(0, 5).map((mentee, index) => (
              <motion.tr
                key={mentee.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <td className="py-3 px-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {mentee.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {mentee.rollNumber}
                    </p>
                  </div>
                </td>
                <td className="py-3 px-2">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    {mentee.currentSGPI.toFixed(2)}
                  </p>
                </td>
                <td className="py-3 px-2">
                  <div className="flex items-center gap-2">
                    {getTrendIcon(mentee.sgpiTrend)}
                    <div className="w-16 h-8">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={mentee.sgpiTrend.map((val, i) => ({ value: val }))}>
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#6366f1"
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-2">
                  {getStatusBadge(mentee.status)}
                </td>
                <td className="py-3 px-2">
                  <button
                    onClick={() => setSelectedStudent(mentee)}
                    className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 text-sm font-medium"
                  >
                    View Details
                  </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* View All Button */}
      <div className="mt-4 text-center">
        <button className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 text-sm font-medium">
          View All {mentees.length} Mentees →
        </button>
      </div>
    </div>
  );
};

export default MenteeOverviewCard;