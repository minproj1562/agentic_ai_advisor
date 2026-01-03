// src/components/dashboard/sections/Performance.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, TrendingDown, Award, Target, Calendar,
  Download, Filter, ChevronDown, AlertTriangle, CheckCircle,
  Clock, BarChart3, Users, BookOpen, Zap, Star, ArrowUp,
  ArrowDown, Activity, RefreshCw
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, ComposedChart
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { format, startOfMonth, endOfMonth, eachDayOfInterval } from 'date-fns';
import { cn } from '../../../utils/cn';
import { auth } from '../../../services/firebase.config';
import toast from 'react-hot-toast';

interface PerformanceData {
  currentSGPI: number;
  previousSGPI: number;
  trend: 'up' | 'down' | 'stable';
  percentageChange: number;
  semesterWiseData: Array<{
    semester: number;
    sgpi: number;
    credits: number;
    courses: number;
    rank?: number;
  }>;
  courseWisePerformance: Array<{
    courseCode: string;
    courseName: string;
    grade: string;
    credits: number;
    marks: number;
  }>;
  skillsAssessment: Array<{
    skill: string;
    proficiency: number;
    lastAssessed: Date;
  }>;
  menteeComparison: {
    topPerformers: number;
    averagePerformers: number;
    needsAttention: number;
  };
  predictedPerformance: {
    nextSemester: number;
    confidence: number;
    factors: Array<{
      factor: string;
      impact: number;
    }>;
  };
}

const Performance: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const [timeRange, setTimeRange] = useState<'semester' | 'year' | 'all'>('semester');
  const [selectedView, setSelectedView] = useState<'overview' | 'detailed' | 'comparison'>('overview');
  const [selectedSemester, setSelectedSemester] = useState<number | null>(null);

  const { data: performanceData, isLoading, refetch } = useQuery({
    queryKey: ['performance', facultyId, timeRange],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/performance?range=${timeRange}`, // Fixed: Changed process.env to import.meta.env
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch performance data');
      return response.json() as Promise<PerformanceData>;
    }
  });

  const chartColors = {
    primary: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    purple: '#8b5cf6'
  };

  const getTrendIcon = () => {
    if (!performanceData) return null;
    
    if (performanceData.trend === 'up') {
      return <TrendingUp className="w-6 h-6 text-green-500" />;
    } else if (performanceData.trend === 'down') {
      return <TrendingDown className="w-6 h-6 text-red-500" />;
    }
    return <Activity className="w-6 h-6 text-gray-500" />;
  };

  const getGradeColor = (grade: string) => {
    const gradeColors: Record<string, string> = {
      'A+': 'text-green-600 bg-green-100',
      'A': 'text-green-600 bg-green-100',
      'B+': 'text-blue-600 bg-blue-100',
      'B': 'text-blue-600 bg-blue-100',
      'C+': 'text-yellow-600 bg-yellow-100',
      'C': 'text-yellow-600 bg-yellow-100',
      'D': 'text-orange-600 bg-orange-100',
      'F': 'text-red-600 bg-red-100'
    };
    return gradeColors[grade] || 'text-gray-600 bg-gray-100';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Performance Analytics
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track academic performance and progress over time
          </p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            {(['semester', 'year', 'all'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={cn(
                  'px-4 py-2 text-sm font-medium rounded-md capitalize transition-all',
                  timeRange === range
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                )}
              >
                {range}
              </button>
            ))}
          </div>

          <button
            onClick={() => refetch()}
            className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
          >
            <RefreshCw className={cn("w-5 h-5", isLoading && "animate-spin")} />
          </button>

          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all">
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>
      </div>

      {performanceData && (
        <>
          {/* Key Performance Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-800/20 rounded-xl p-6 border border-indigo-200 dark:border-indigo-800"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-indigo-500 rounded-lg">
                  <Award className="w-6 h-6 text-white" />
                </div>
                {getTrendIcon()}
              </div>
              <p className="text-sm text-indigo-700 dark:text-indigo-300 mb-1">
                Current SGPI
              </p>
              <p className="text-3xl font-bold text-indigo-900 dark:text-indigo-100">
                {performanceData.currentSGPI.toFixed(2)}
              </p>
              <div className={cn(
                "flex items-center gap-1 mt-2 text-sm",
                performanceData.percentageChange > 0
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
              )}>
                {performanceData.percentageChange > 0 ? (
                  <ArrowUp className="w-4 h-4" />
                ) : (
                  <ArrowDown className="w-4 h-4" />
                )}
                <span>{Math.abs(performanceData.percentageChange)}%</span>
                <span className="text-gray-500 dark:text-gray-400">vs last semester</span>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-6 border border-green-200 dark:border-green-800"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-green-500 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
              </div>
              <p className="text-sm text-green-700 dark:text-green-300 mb-1">
                Top Performers
              </p>
              <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                {performanceData.menteeComparison.topPerformers}
              </p>
              <p className="text-xs text-green-600 dark:text-green-400 mt-2">
                SGPI ≥ 8.5
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-xl p-6 border border-yellow-200 dark:border-yellow-800"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-yellow-500 rounded-lg">
                  <Clock className="w-6 h-6 text-white" />
                </div>
              </div>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-1">
                Average Performers
              </p>
              <p className="text-3xl font-bold text-yellow-900 dark:text-yellow-100">
                {performanceData.menteeComparison.averagePerformers}
              </p>
              <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-2">
                SGPI 6.5-8.5
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-xl p-6 border border-red-200 dark:border-red-800"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-red-500 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-white" />
                </div>
              </div>
              <p className="text-sm text-red-700 dark:text-red-300 mb-1">
                Needs Attention
              </p>
              <p className="text-3xl font-bold text-red-900 dark:text-red-100">
                {performanceData.menteeComparison.needsAttention}
              </p>
              <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                SGPI &lt; 6.5
              </p>
            </motion.div>
          </div>

          {/* View Tabs */}
          <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
            {(['overview', 'detailed', 'comparison'] as const).map((view) => (
              <button
                key={view}
                onClick={() => setSelectedView(view)}
                className={cn(
                  'px-6 py-3 text-sm font-medium capitalize transition-all',
                  selectedView === view
                    ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                )}
              >
                {view}
              </button>
            ))}
          </div>

          {/* Content Based on Selected View */}
          <AnimatePresence mode="wait">
            {selectedView === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Performance Trend Chart */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
                    Performance Trend
                  </h3>
                  
                  <ResponsiveContainer width="100%" height={350}>
                    <AreaChart data={performanceData.semesterWiseData}>
                      <defs>
                        <linearGradient id="colorSGPI" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.3}/>
                          <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                      <XAxis
                        dataKey="semester"
                        tick={{ fontSize: 12 }}
                        label={{ value: 'Semester', position: 'insideBottom', offset: -5 }}
                      />
                      <YAxis
                        domain={[0, 10]}
                        tick={{ fontSize: 12 }}
                        label={{ value: 'SGPI', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: '1px solid #e5e7eb',
                          borderRadius: '0.5rem',
                          padding: '0.75rem'
                        }}
                      />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="sgpi"
                        stroke={chartColors.primary}
                        strokeWidth={2}
                        fill="url(#colorSGPI)"
                        name="SGPI"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Semester Statistics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Recent Semesters */}
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Recent Semesters
                    </h3>
                    <div className="space-y-3">
                      {performanceData.semesterWiseData.slice(-4).reverse().map((sem, index) => (
                        <motion.div
                          key={sem.semester}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors cursor-pointer"
                          onClick={() => setSelectedSemester(sem.semester)}
                        >
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                              <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                                {sem.semester}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white">
                                Semester {sem.semester}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {sem.credits} Credits • {sem.courses} Courses
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {sem.sgpi.toFixed(2)}
                            </p>
                            {sem.rank && (
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Rank: {sem.rank}
                              </p>
                            )}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>

                  {/* Skills Assessment Radar */}
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Skills Assessment
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                      <RadarChart data={performanceData.skillsAssessment.slice(0, 6)}>
                        <PolarGrid stroke="#e5e7eb" />
                        <PolarAngleAxis
                          dataKey="skill"
                          tick={{ fontSize: 11 }}
                        />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                        <Radar
                          name="Proficiency"
                          dataKey="proficiency"
                          stroke={chartColors.primary}
                          fill={chartColors.primary}
                          fillOpacity={0.3}
                        />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </motion.div>
            )}

            {selectedView === 'detailed' && (
              <motion.div
                key="detailed"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden"
              >
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Course-wise Performance
                  </h3>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Course Code
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Course Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Credits
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Marks
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Grade
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Performance
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {performanceData.courseWisePerformance.map((course, index) => (
                        <motion.tr
                          key={course.courseCode}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                            {course.courseCode}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                            {course.courseName}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                            {course.credits}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                            {course.marks}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={cn(
                              "px-3 py-1 text-xs font-medium rounded-full",
                              getGradeColor(course.grade)
                            )}>
                              {course.grade}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                  className={cn(
                                    "h-2 rounded-full",
                                    course.marks >= 90 ? "bg-green-500" :
                                    course.marks >= 75 ? "bg-blue-500" :
                                    course.marks >= 60 ? "bg-yellow-500" : "bg-red-500"
                                  )}
                                  style={{ width: `${course.marks}%` }}
                                />
                              </div>
                              <span className="text-xs text-gray-600 dark:text-gray-400">
                                {course.marks}%
                              </span>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {selectedView === 'comparison' && (
              <motion.div
                key="comparison"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Predicted Performance */}
                <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl shadow-lg p-6 text-white">
                  <div className="flex items-center gap-3 mb-4">
                    <Zap className="w-6 h-6" />
                    <h3 className="text-xl font-semibold">AI Performance Prediction</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                      <p className="text-sm opacity-90 mb-1">Predicted Next Semester SGPI</p>
                      <p className="text-3xl font-bold">
                        {performanceData.predictedPerformance.nextSemester.toFixed(2)}
                      </p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 bg-white/20 rounded-full h-2">
                          <div
                            className="bg-white h-2 rounded-full"
                            style={{ width: `${performanceData.predictedPerformance.confidence}%` }}
                          />
                        </div>
                        <span className="text-xs opacity-90">
                          {performanceData.predictedPerformance.confidence}% confidence
                        </span>
                      </div>
                    </div>
                    
                    <div className="md:col-span-2 bg-white/10 backdrop-blur-sm rounded-lg p-4">
                      <p className="text-sm opacity-90 mb-3">Key Influencing Factors</p>
                      <div className="space-y-2">
                        {performanceData.predictedPerformance.factors.map((factor, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <span className="text-sm">{factor.factor}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-24 bg-white/20 rounded-full h-2">
                                <div
                                  className="bg-white h-2 rounded-full"
                                  style={{ width: `${Math.abs(factor.impact)}%` }}
                                />
                              </div>
                              <span className={cn(
                                "text-xs font-medium",
                                factor.impact > 0 ? "text-green-300" : "text-red-300"
                              )}>
                                {factor.impact > 0 ? '+' : ''}{factor.impact}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Department Comparison */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
                    Department Comparison
                  </h3>
                  
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      data={[
                        { category: 'Your Mentees', avgSGPI: performanceData.currentSGPI },
                        { category: 'Dept Average', avgSGPI: 7.2 },
                        { category: 'Top 10%', avgSGPI: 8.8 }
                      ]}
                    >
                      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                      <XAxis dataKey="category" />
                      <YAxis domain={[0, 10]} />
                      <Tooltip />
                      <Bar dataKey="avgSGPI" radius={[8, 8, 0, 0]}>
                        {['#6366f1', '#f59e0b', '#10b981'].map((color, index) => (
                          <Cell key={`cell-${index}`} fill={color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
};

export default Performance;