// src/components/dashboard/sections/Analytics.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3, TrendingUp, Users, BookOpen, Award, Calendar,
  Download, Filter, RefreshCw, ChevronDown, Info, ArrowUp,
  ArrowDown, Activity, Target, Zap, Eye, Clock, Globe,
  CheckCircle
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie,
  RadarChart, Radar, ScatterChart, Scatter, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Treemap
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { format, startOfWeek, endOfWeek, subDays } from 'date-fns';
import { cn } from '../../../utils/cn';
import { auth } from '../../../services/firebase.config';
import toast from 'react-hot-toast';
import { CSVLink } from 'react-csv';

interface AnalyticsData {
  overview: {
    totalMentees: number;
    activeMentees: number;
    avgPerformance: number;
    performanceChange: number;
    sessionsCompleted: number;
    avgSessionRating: number;
    researchPapers: number;
    citations: number;
  };
  performanceTrends: Array<{
    date: string;
    avgSGPI: number;
    attendance: number;
    submissions: number;
  }>;
  menteeDistribution: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  sessionAnalytics: {
    totalSessions: number;
    avgDuration: number;
    completionRate: number;
    satisfactionScore: number;
    topicsDiscussed: Array<{
      topic: string;
      frequency: number;
    }>;
  };
  researchMetrics: {
    papers: number;
    citations: number;
    hIndex: number;
    collaborations: number;
    impactFactor: number;
    trending: Array<{
      paper: string;
      views: number;
      citations: number;
    }>;
  };
  engagementMetrics: {
    weeklyActive: number;
    monthlyActive: number;
    avgResponseTime: number;
    messagesSent: number;
    feedbackScore: number;
  };
}

const Analytics: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [selectedMetric, setSelectedMetric] = useState<'performance' | 'engagement' | 'research'>('performance');
  const [compareMode, setCompareMode] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'pdf' | 'excel'>('csv');

  // Use a direct constant for API URL
  const API_URL = 'http://localhost:3001'; // or your actual API URL

  const { data: analytics, isLoading, refetch } = useQuery({
    queryKey: ['analytics', facultyId, timeRange],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${API_URL}/api/v1/faculty/${facultyId}/analytics?range=${timeRange}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch analytics');
      return response.json() as Promise<AnalyticsData>;
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  const { data: comparativeData } = useQuery({
    queryKey: ['comparative-analytics', facultyId],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${API_URL}/api/v1/faculty/${facultyId}/analytics/comparative`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    },
    enabled: compareMode
  });

  const { data: predictions } = useQuery({
    queryKey: ['predictions', facultyId],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${API_URL}/api/v1/faculty/${facultyId}/analytics/predictions`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    }
  });

  const chartColors = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4'
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload[0]) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs text-gray-600 dark:text-gray-400">
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const StatCard = ({ 
    title, 
    value, 
    change, 
    icon: Icon, 
    color,
    subtitle 
  }: {
    title: string;
    value: string | number;
    change?: number;
    icon: any;
    color: string;
    subtitle?: string;
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border-l-4 ${color}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
          )}
          {change !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${
              change > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            }`}>
              {change > 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
              <span>{Math.abs(change)}%</span>
              <span className="text-gray-500 dark:text-gray-400">vs last period</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-gradient-to-br ${color} bg-opacity-10`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Analytics Dashboard
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive insights into your academic performance
          </p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          {/* Time Range Selector */}
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            {(['7d', '30d', '90d', '1y'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-all',
                  timeRange === range
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                )}
              >
                {range === '7d' ? '7 Days' : 
                 range === '30d' ? '30 Days' :
                 range === '90d' ? '3 Months' : '1 Year'}
              </button>
            ))}
          </div>

          {/* Compare Toggle */}
          <button
            onClick={() => setCompareMode(!compareMode)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-all',
              compareMode
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            )}
          >
            <Activity className="w-4 h-4" />
            Compare
          </button>

          {/* Refresh */}
          <button
            onClick={() => refetch()}
            className="p-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
          >
            <RefreshCw className={cn("w-5 h-5", isLoading && "animate-spin")} />
          </button>

          {/* Export */}
          <div className="relative group">
            <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all">
              <Download className="w-4 h-4" />
              Export
              <ChevronDown className="w-4 h-4" />
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-xl hidden group-hover:block z-10">
              <CSVLink
                data={analytics?.performanceTrends || []}
                filename={`analytics-${format(new Date(), 'yyyy-MM-dd')}.csv`}
                className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
              >
                Export as CSV
              </CSVLink>
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600">
                Export as PDF
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600">
                Export as Excel
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Mentees"
            value={analytics.overview.totalMentees}
            change={12}
            icon={Users}
            color="border-blue-500"
            subtitle={`${analytics.overview.activeMentees} active`}
          />
          <StatCard
            title="Avg Performance"
            value={`${analytics.overview.avgPerformance.toFixed(2)}`}
            change={analytics.overview.performanceChange}
            icon={TrendingUp}
            color="border-green-500"
            subtitle="SGPI"
          />
          <StatCard
            title="Sessions"
            value={analytics.overview.sessionsCompleted}
            change={8}
            icon={Calendar}
            color="border-purple-500"
            subtitle={`${analytics.overview.avgSessionRating.toFixed(1)}★ rating`}
          />
          <StatCard
            title="Research Impact"
            value={analytics.overview.citations}
            change={25}
            icon={BookOpen}
            color="border-orange-500"
            subtitle={`${analytics.overview.researchPapers} papers`}
          />
        </div>
      )}

      {/* Main Analytics Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Performance Trends
            </h3>
            <div className="flex gap-2">
              {['performance', 'engagement', 'research'].map((metric) => (
                <button
                  key={metric}
                  onClick={() => setSelectedMetric(metric as any)}
                  className={cn(
                    'px-3 py-1 text-xs font-medium rounded-lg capitalize transition-colors',
                    selectedMetric === metric
                      ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                  )}
                >
                  {metric}
                </button>
              ))}
            </div>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analytics?.performanceTrends}>
              <defs>
                <linearGradient id="colorPrimary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorSecondary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColors.secondary} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={chartColors.secondary} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 11 }}
                tickFormatter={(value) => format(new Date(value), 'MMM dd')}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {selectedMetric === 'performance' && (
                <>
                  <Area
                    type="monotone"
                    dataKey="avgSGPI"
                    stroke={chartColors.primary}
                    strokeWidth={2}
                    fill="url(#colorPrimary)"
                    name="Avg SGPI"
                  />
                  <Area
                    type="monotone"
                    dataKey="attendance"
                    stroke={chartColors.success}
                    strokeWidth={2}
                    fill="url(#colorSecondary)"
                    name="Attendance %"
                  />
                </>
              )}
              
              {selectedMetric === 'engagement' && (
                <Area
                  type="monotone"
                  dataKey="submissions"
                  stroke={chartColors.info}
                  strokeWidth={2}
                  fill="url(#colorPrimary)"
                  name="Submissions"
                />
              )}
            </AreaChart>
          </ResponsiveContainer>

          {/* Comparison Mode */}
          {compareMode && comparativeData && (
            <div className="mt-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
              <h4 className="text-sm font-medium text-indigo-700 dark:text-indigo-300 mb-3">
                Department Comparison
              </h4>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                    #{comparativeData.departmentRank}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Dept Rank</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    +{comparativeData.aboveAverage}%
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Above Avg</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {comparativeData.percentile}th
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Percentile</p>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        {/* Mentee Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Mentee Distribution
          </h3>
          
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={analytics?.menteeDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="count"
              >
                {analytics?.menteeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={Object.values(chartColors)[index % 6]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>

          <div className="mt-4 space-y-2">
            {analytics?.menteeDistribution.map((item, index) => (
              <div key={item.category} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: Object.values(chartColors)[index % 6] }}
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {item.category}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {item.count} ({item.percentage}%)
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Session Analytics & Research Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Session Analytics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Session Analytics
          </h3>
          
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <Clock className="w-8 h-8 mx-auto mb-2 text-indigo-600 dark:text-indigo-400" />
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analytics?.sessionAnalytics.avgDuration} min
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Avg Duration</p>
            </div>
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <Target className="w-8 h-8 mx-auto mb-2 text-green-600 dark:text-green-400" />
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analytics?.sessionAnalytics.completionRate}%
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Completion Rate</p>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Top Discussion Topics
            </h4>
            <div className="space-y-2">
              {analytics?.sessionAnalytics.topicsDiscussed.slice(0, 5).map((topic, index) => (
                <div key={topic.topic} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {index + 1}. {topic.topic}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="h-2 bg-indigo-500 rounded-full"
                        style={{ width: `${(topic.frequency / 100) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {topic.frequency}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Research Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Research Impact
          </h3>
          
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={150}>
              <RadarChart data={[
                { metric: 'Papers', value: analytics?.researchMetrics.papers || 0 },
                { metric: 'Citations', value: Math.min(analytics?.researchMetrics.citations || 0, 100) },
                { metric: 'H-Index', value: (analytics?.researchMetrics.hIndex || 0) * 10 },
                { metric: 'Collaborations', value: (analytics?.researchMetrics.collaborations || 0) * 5 },
                { metric: 'Impact', value: (analytics?.researchMetrics.impactFactor || 0) * 20 }
              ]}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar
                  name="Research Metrics"
                  dataKey="value"
                  stroke={chartColors.primary}
                  fill={chartColors.primary}
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                H-Index
              </span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {analytics?.researchMetrics.hIndex}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Impact Factor
              </span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {analytics?.researchMetrics.impactFactor.toFixed(2)}
              </span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Predictions & Insights */}
      {predictions && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg p-6 text-white"
        >
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-6 h-6" />
            <h3 className="text-xl font-semibold">AI-Powered Insights</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <h4 className="font-medium mb-2">Performance Prediction</h4>
              <p className="text-3xl font-bold mb-1">
                {predictions.nextMonthPerformance.toFixed(1)}
              </p>
              <p className="text-sm opacity-90">
                Expected avg SGPI next month
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <h4 className="font-medium mb-2">At-Risk Students</h4>
              <p className="text-3xl font-bold mb-1">
                {predictions.atRiskCount}
              </p>
              <p className="text-sm opacity-90">
                Require immediate attention
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <h4 className="font-medium mb-2">Success Rate</h4>
              <p className="text-3xl font-bold mb-1">
                {predictions.successProbability}%
              </p>
              <p className="text-sm opacity-90">
                Probability of target achievement
              </p>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-white/10 backdrop-blur-sm rounded-lg">
            <h4 className="font-medium mb-3">Recommended Actions</h4>
            <ul className="space-y-2">
              {predictions.recommendations.map((rec: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Engagement Heatmap */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          Weekly Engagement Heatmap
        </h3>
        
        <div className="grid grid-cols-8 gap-1">
          <div></div>
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
            <div key={day} className="text-center text-xs text-gray-600 dark:text-gray-400">
              {day}
            </div>
          ))}
          
          {Array.from({ length: 4 }, (_, weekIndex) => (
            <React.Fragment key={weekIndex}>
              <div className="text-xs text-gray-600 dark:text-gray-400 pr-2 flex items-center justify-end">
                W{weekIndex + 1}
              </div>
              {Array.from({ length: 7 }, (_, dayIndex) => {
                const intensity = Math.random();
                return (
                  <div
                    key={`${weekIndex}-${dayIndex}`}
                    className="aspect-square rounded"
                    style={{
                      backgroundColor: `rgba(99, 102, 241, ${intensity})`,
                    }}
                    title={`Week ${weekIndex + 1}, Day ${dayIndex + 1}: ${Math.round(intensity * 100)}% activity`}
                  />
                );
              })}
            </React.Fragment>
          ))}
        </div>
        
        <div className="flex items-center justify-center gap-4 mt-4">
          <span className="text-xs text-gray-600 dark:text-gray-400">Less</span>
          <div className="flex gap-1">
            {[0.1, 0.3, 0.5, 0.7, 0.9].map(opacity => (
              <div
                key={opacity}
                className="w-4 h-4 rounded"
                style={{ backgroundColor: `rgba(99, 102, 241, ${opacity})` }}
              />
            ))}
          </div>
          <span className="text-xs text-gray-600 dark:text-gray-400">More</span>
        </div>
      </motion.div>
    </div>
  );
};

export default Analytics;