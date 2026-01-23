// src/components/dashboard/sections/Performance.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, TrendingDown, Award, AlertTriangle, CheckCircle,
  Clock, Zap, ArrowUp, ArrowDown, Activity, RefreshCw, Download,
  BarChart3
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, ComposedChart, Line
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { cn } from '../../../utils/cn';
import { auth } from '../../../services/firebase.config';
import toast from 'react-hot-toast';
import PerformanceChart from '../PerformanceChart';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

interface SemesterData {
  semester: number;
  sgpi: number;
  credits: number;
  courses: number;
  rank?: number;
}

interface CoursePerformance {
  courseCode: string;
  courseName: string;
  grade: string;
  credits: number;
  marks: number;
}

interface SkillAssessment {
  skill: string;
  proficiency: number;
  lastAssessed: string;
}

interface MenteeComparison {
  topPerformers: number;
  averagePerformers: number;
  needsAttention: number;
}

interface PredictionFactor {
  factor: string;
  impact: number;
}

interface PredictedPerformance {
  nextSemester: number;
  confidence: number;
  factors: PredictionFactor[];
}

interface PerformanceData {
  currentSGPI: number;
  previousSGPI: number;
  trend: 'up' | 'down' | 'stable';
  percentageChange: number;
  semesterWiseData: SemesterData[];
  courseWisePerformance: CoursePerformance[];
  skillsAssessment: SkillAssessment[];
  menteeComparison: MenteeComparison;
  predictedPerformance: PredictedPerformance;
}

const Performance: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'semester' | 'year' | 'all'>('all');
  const [selectedView, setSelectedView] = useState<'overview' | 'detailed' | 'comparison'>('overview');
  const [selectedSemester, setSelectedSemester] = useState<number | null>(null);

  // Fetch performance data from YOUR backend
  const { data: performanceData, isLoading, error, refetch } = useQuery({
    queryKey: ['studentPerformance', timeRange],
    queryFn: async (): Promise<PerformanceData> => {
      const token = await auth.currentUser?.getIdToken();
      
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(
        `${BACKEND_URL}/api/v1/student/performance?range=${timeRange}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch performance data');
      }
      
      return response.json();
    },
    enabled: !!auth.currentUser,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
  });

  // Listen for academic data updates
  React.useEffect(() => {
    const handleDataUpdate = () => {
      refetch();
      toast.success('Performance data refreshed');
    };

    window.addEventListener('academicDataUpdated', handleDataUpdate);
    window.addEventListener('profileUpdated', handleDataUpdate);

    return () => {
      window.removeEventListener('academicDataUpdated', handleDataUpdate);
      window.removeEventListener('profileUpdated', handleDataUpdate);
    };
  }, [refetch]);

  // Prepare data for PerformanceChart component
  const performanceChartData = useMemo(() => {
    if (!performanceData) return null;
    
    return {
      currentSGPI: performanceData.currentSGPI,
      previousSGPI: performanceData.previousSGPI,
      trend: performanceData.trend,
      percentageChange: performanceData.percentageChange,
      semesterWiseData: performanceData.semesterWiseData.map(sem => ({
        semester: sem.semester,
        sgpi: sem.sgpi,
        credits: sem.credits,
        courses: sem.courses,
      })),
    };
  }, [performanceData]);

  // Prepare data for Recharts
  const rechartsData = useMemo(() => {
    if (!performanceData?.semesterWiseData) return [];
    
    return performanceData.semesterWiseData
      .sort((a, b) => a.semester - b.semester)
      .map(sem => ({
        semester: sem.semester,
        semesterLabel: `Sem ${sem.semester}`,
        sgpi: Number(sem.sgpi.toFixed(2)),
        credits: sem.credits,
        courses: sem.courses,
        rank: sem.rank,
      }));
  }, [performanceData]);

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
      'O': 'text-green-600 bg-green-100',
      'A+': 'text-green-600 bg-green-100',
      'A': 'text-green-500 bg-green-50',
      'B+': 'text-blue-600 bg-blue-100',
      'B': 'text-blue-500 bg-blue-50',
      'C': 'text-yellow-600 bg-yellow-100',
      'P': 'text-orange-600 bg-orange-100',
      'F': 'text-red-600 bg-red-100'
    };
    return gradeColors[grade] || 'text-gray-600 bg-gray-100';
  };

  // Loading State
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 animate-pulse"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse"></div>
          ))}
        </div>
        <div className="h-80 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse"></div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-red-600 dark:text-red-400 font-medium mb-2">
          Failed to load performance data
        </p>
        <p className="text-red-500 dark:text-red-300 text-sm mb-4 text-center max-w-md">
          {error instanceof Error ? error.message : 'Unknown error occurred'}
        </p>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    );
  }

  // No Data State
  if (!performanceData || performanceData.semesterWiseData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600">
        <BarChart3 className="w-16 h-16 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No Performance Data Yet
        </h3>
        <p className="text-gray-600 dark:text-gray-400 text-center max-w-md mb-4">
          Add your academic scores in the Academic Data Entry section to see your performance analytics here.
        </p>
        <a
          href="/dashboard/academic-entry"
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Add Academic Data
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Performance Analytics
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track your academic performance and progress over time
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
                {range === 'semester' ? 'Recent' : range}
              </button>
            ))}
          </div>

          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-all disabled:opacity-50"
            title="Refresh data"
          >
            <RefreshCw className={cn("w-5 h-5", isLoading && "animate-spin")} />
          </button>

          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current SGPI */}
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
              : performanceData.percentageChange < 0
              ? "text-red-600 dark:text-red-400"
              : "text-gray-600 dark:text-gray-400"
          )}>
            {performanceData.percentageChange > 0 ? (
              <ArrowUp className="w-4 h-4" />
            ) : performanceData.percentageChange < 0 ? (
              <ArrowDown className="w-4 h-4" />
            ) : null}
            <span>{Math.abs(performanceData.percentageChange).toFixed(1)}%</span>
            <span className="text-gray-500 dark:text-gray-400">vs previous</span>
          </div>
        </motion.div>

        {/* Previous SGPI */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-500 rounded-lg">
              <Clock className="w-6 h-6 text-white" />
            </div>
          </div>
          <p className="text-sm text-purple-700 dark:text-purple-300 mb-1">
            Previous SGPI
          </p>
          <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
            {performanceData.previousSGPI.toFixed(2)}
          </p>
          <p className="text-xs text-purple-600 dark:text-purple-400 mt-2">
            Last semester performance
          </p>
        </motion.div>

        {/* Total Semesters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-6 border border-green-200 dark:border-green-800"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-500 rounded-lg">
              <CheckCircle className="w-6 h-6 text-white" />
            </div>
          </div>
          <p className="text-sm text-green-700 dark:text-green-300 mb-1">
            Semesters Completed
          </p>
          <p className="text-3xl font-bold text-green-900 dark:text-green-100">
            {performanceData.semesterWiseData.length}
          </p>
          <p className="text-xs text-green-600 dark:text-green-400 mt-2">
            Total credits: {performanceData.semesterWiseData.reduce((sum, s) => sum + s.credits, 0)}
          </p>
        </motion.div>

        {/* Performance Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className={cn(
            "rounded-xl p-6 border",
            performanceData.currentSGPI >= 8.5
              ? "bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800"
              : performanceData.currentSGPI >= 6.5
              ? "bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200 dark:border-yellow-800"
              : "bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800"
          )}
        >
          <div className="flex items-center justify-between mb-4">
            <div className={cn(
              "p-3 rounded-lg",
              performanceData.currentSGPI >= 8.5 ? "bg-green-500" :
              performanceData.currentSGPI >= 6.5 ? "bg-yellow-500" : "bg-red-500"
            )}>
              {performanceData.currentSGPI >= 8.5 ? (
                <Award className="w-6 h-6 text-white" />
              ) : performanceData.currentSGPI >= 6.5 ? (
                <Activity className="w-6 h-6 text-white" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-white" />
              )}
            </div>
          </div>
          <p className={cn(
            "text-sm mb-1",
            performanceData.currentSGPI >= 8.5 ? "text-green-700 dark:text-green-300" :
            performanceData.currentSGPI >= 6.5 ? "text-yellow-700 dark:text-yellow-300" :
            "text-red-700 dark:text-red-300"
          )}>
            Status
          </p>
          <p className={cn(
            "text-2xl font-bold",
            performanceData.currentSGPI >= 8.5 ? "text-green-900 dark:text-green-100" :
            performanceData.currentSGPI >= 6.5 ? "text-yellow-900 dark:text-yellow-100" :
            "text-red-900 dark:text-red-100"
          )}>
            {performanceData.currentSGPI >= 8.5 ? "Excellent" :
             performanceData.currentSGPI >= 6.5 ? "Good" : "Needs Improvement"}
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
            {/* Custom SVG Performance Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <PerformanceChart data={performanceChartData} />
            </div>

            {/* Recharts Performance Trend */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
                Detailed SGPI Trend
              </h3>
              
              {rechartsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={rechartsData}>
                    <defs>
                      <linearGradient id="colorSGPI" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis
                      dataKey="semesterLabel"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis
                      yAxisId="left"
                      domain={[0, 10]}
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => value.toFixed(1)}
                      label={{ value: 'SGPI', angle: -90, position: 'insideLeft' }}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      domain={[0, 'auto']}
                      tick={{ fontSize: 12 }}
                      label={{ value: 'Credits', angle: 90, position: 'insideRight' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '0.5rem',
                        padding: '0.75rem'
                      }}
                      formatter={(value: number, name: string) => {
                        if (name === 'sgpi' || name === 'SGPI Trend') return [value.toFixed(2), 'SGPI'];
                        if (name === 'credits') return [value, 'Credits'];
                        return [value, name];
                      }}
                    />
                    <Legend />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="sgpi"
                      stroke={chartColors.primary}
                      strokeWidth={2}
                      fill="url(#colorSGPI)"
                      name="SGPI"
                    />
                    <Bar
                      yAxisId="right"
                      dataKey="credits"
                      fill={chartColors.success}
                      opacity={0.6}
                      name="Credits"
                      radius={[4, 4, 0, 0]}
                    />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="sgpi"
                      stroke={chartColors.purple}
                      strokeWidth={3}
                      dot={{ fill: chartColors.purple, strokeWidth: 2, r: 5 }}
                      activeDot={{ r: 7 }}
                      name="SGPI Trend"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  No semester data available for chart
                </div>
              )}
            </div>

            {/* Semester Statistics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Semesters */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Semester Performance
                </h3>
                <div className="space-y-3">
                  {performanceData.semesterWiseData
                    .sort((a, b) => b.semester - a.semester)
                    .map((sem, index) => (
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
                {performanceData.skillsAssessment && performanceData.skillsAssessment.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
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
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500">
                    Skills assessment not available
                  </div>
                )}
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
                Course-wise Performance (Current Semester)
              </h3>
            </div>
            
            {performanceData.courseWisePerformance && performanceData.courseWisePerformance.length > 0 ? (
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
                                  "h-2 rounded-full transition-all duration-500",
                                  course.marks >= 90 ? "bg-green-500" :
                                  course.marks >= 75 ? "bg-blue-500" :
                                  course.marks >= 60 ? "bg-yellow-500" :
                                  course.marks >= 40 ? "bg-orange-500" : "bg-red-500"
                                )}
                                style={{ width: `${Math.min(course.marks, 100)}%` }}
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
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                No course performance data available
              </div>
            )}
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
            {performanceData.predictedPerformance && (
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
                          className="bg-white h-2 rounded-full transition-all duration-500"
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
                                className={cn(
                                  "h-2 rounded-full transition-all duration-500",
                                  factor.impact > 0 ? "bg-green-400" : "bg-red-400"
                                )}
                                style={{ width: `${Math.min(Math.abs(factor.impact) * 3, 100)}%` }}
                              />
                            </div>
                            <span className={cn(
                              "text-xs font-medium w-12 text-right",
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
            )}

            {/* SGPI Comparison Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
                SGPI Comparison Across Semesters
              </h3>
              
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rechartsData}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis dataKey="semesterLabel" />
                  <YAxis domain={[0, 10]} tickFormatter={(value) => value.toFixed(1)} />
                  <Tooltip 
                    formatter={(value: number) => [value.toFixed(2), 'SGPI']}
                  />
                  <Bar dataKey="sgpi" radius={[8, 8, 0, 0]}>
                    {rechartsData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.sgpi >= 8.5 ? chartColors.success : 
                              entry.sgpi >= 6.5 ? chartColors.warning : chartColors.danger} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Performance;