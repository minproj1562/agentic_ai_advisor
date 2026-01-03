// modules/agent1/performance-analytics/components/TrendAnalyzer/index.tsx
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, AlertCircle, ChevronDown } from 'lucide-react';
import TrendChart from './TrendChart';
import { usePerformanceTrends } from '../../hooks/usePerformanceTrends';
import { PerformanceTrend, TrendAnalysis, TimeRange } from '../../types/analytics.types';
import { calculateTrendMetrics, detectAnomalies } from '../../utils/calculations';
import LoadingSpinner from '../../../../../components/common/LoadingSpinner';
import { ErrorBoundary } from '../../../../../components/ErrorBoundary';

// Add these missing utility functions locally since the formatters module is missing
const formatGPA = (value: number | undefined | null): string => {
  if (value === undefined || value === null) return 'N/A';
  return value.toFixed(2);
};

const formatPercentage = (value: number | undefined | null, decimals: number = 1): string => {
  if (value === undefined || value === null) return 'N/A';
  return `${value.toFixed(decimals)}%`;
};

interface TrendAnalyzerProps {
  studentId: string;
  subjectId?: string;
  onTrendChange?: (trend: TrendAnalysis) => void;
  className?: string;
}

const timeRanges: TimeRange[] = [
  { label: 'Last Month', value: '1m', days: 30 },
  { label: 'Last 3 Months', value: '3m', days: 90 },
  { label: 'Last 6 Months', value: '6m', days: 180 },
  { label: 'Last Year', value: '1y', days: 365 },
  { label: 'All Time', value: 'all', days: -1 }
];

const TrendAnalyzer: React.FC<TrendAnalyzerProps> = ({
  studentId,
  subjectId,
  onTrendChange,
  className = ''
}) => {
  const [selectedRange, setSelectedRange] = useState<TimeRange>(timeRanges[1]);
  const [showDetails, setShowDetails] = useState(false);
  const [activeMetric, setActiveMetric] = useState<'gpa' | 'percentile' | 'improvement'>('gpa');

  const {
    trends,
    loading,
    error,
    refetch,
    isValidating
  } = usePerformanceTrends(studentId, {
    subjectId,
    timeRange: selectedRange.value,
    includeProjections: true
  });

  const trendAnalysis = useMemo(() => {
    if (!trends?.dataPoints) return null;
    return calculateTrendMetrics(trends.dataPoints, selectedRange.days);
  }, [trends, selectedRange]);

  const anomalies = useMemo(() => {
    if (!trends?.dataPoints) return [];
    return detectAnomalies(trends.dataPoints);
  }, [trends]);

  useEffect(() => {
    if (trendAnalysis && onTrendChange) {
      onTrendChange(trendAnalysis);
    }
  }, [trendAnalysis, onTrendChange]);

  const handleRangeChange = useCallback((range: TimeRange) => {
    setSelectedRange(range);
  }, []);

  const getTrendIcon = useCallback((value: number) => {
    if (value > 5) return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (value < -5) return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Activity className="w-5 h-5 text-yellow-500" />;
  }, []);

  const getTrendColor = useCallback((value: number) => {
    if (value > 5) return 'text-green-600 bg-green-50 border-green-200';
    if (value < -5) return 'text-red-600 bg-red-50 border-red-200';
    return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-red-50 rounded-lg">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-red-700 font-medium">Failed to load performance trends</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (loading && !trends) {
    return (
      <div className="flex items-center justify-center p-12">
        {/* FIXED: Removed the size prop entirely */}
        <LoadingSpinner />
        <div className="ml-3">Analyzing performance trends...</div>
      </div>
    );
  }

  if (!trends?.dataPoints || trends.dataPoints.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-gray-50 rounded-lg">
        <Activity className="w-16 h-16 text-gray-400 mb-4" />
        <p className="text-gray-700 font-medium text-lg mb-2">No Trend Data Available</p>
        <p className="text-gray-500 text-center mb-4">
          Performance trend data will appear here once you have enough historical data.
        </p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh Data
        </button>
      </div>
    );
  }

  return (
    // FIXED: Using named import for ErrorBoundary
    <ErrorBoundary>
      <div className={`bg-white rounded-xl shadow-lg p-6 ${className}`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Performance Trends</h2>
            <p className="text-gray-600 mt-1">
              Track your academic progress over time
            </p>
          </div>
          
          {/* Time Range Selector */}
          <div className="relative">
            <button
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              onClick={() => setShowDetails(!showDetails)}
            >
              <span className="font-medium">{selectedRange.label}</span>
              <ChevronDown className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`} />
            </button>
            
            <AnimatePresence>
              {showDetails && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10"
                >
                  {timeRanges.map((range) => (
                    <button
                      key={range.value}
                      onClick={() => {
                        handleRangeChange(range);
                        setShowDetails(false);
                      }}
                      className={`w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                        selectedRange.value === range.value ? 'bg-blue-50 text-blue-600' : ''
                      }`}
                    >
                      {range.label}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Key Metrics */}
        {trendAnalysis && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                activeMetric === 'gpa' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
              onClick={() => setActiveMetric('gpa')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Current GPA</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatGPA(trendAnalysis.currentGPA)}
                  </p>
                </div>
                {getTrendIcon(trendAnalysis.gpaChange || 0)}
              </div>
              <div className="mt-2">
                <span className={`text-sm font-medium ${
                  (trendAnalysis.gpaChange || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(trendAnalysis.gpaChange || 0) >= 0 ? '+' : ''}{formatPercentage(trendAnalysis.gpaChange || 0)}
                </span>
                <span className="text-xs text-gray-500 ml-1">vs last period</span>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                activeMetric === 'percentile' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
              onClick={() => setActiveMetric('percentile')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Class Percentile</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {trendAnalysis.percentile}th
                  </p>
                </div>
                {getTrendIcon(trendAnalysis.percentileChange || 0)}
              </div>
              <div className="mt-2">
                <span className={`text-sm font-medium ${
                  (trendAnalysis.percentileChange || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(trendAnalysis.percentileChange || 0) >= 0 ? '+' : ''}{trendAnalysis.percentileChange}
                </span>
                <span className="text-xs text-gray-500 ml-1">positions</span>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                activeMetric === 'improvement' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
              onClick={() => setActiveMetric('improvement')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Improvement Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatPercentage(trendAnalysis.improvementRate || 0)}
                  </p>
                </div>
                {getTrendIcon(trendAnalysis.improvementRate || 0)}
              </div>
              <div className="mt-2">
                <span className="text-xs text-gray-500">
                  Based on {trendAnalysis.dataPointsCount} assessments
                </span>
              </div>
            </motion.div>
          </div>
        )}

        {/* Trend Chart */}
        {trends && (
          <TrendChart
            data={trends}
            activeMetric={activeMetric}
            timeRange={selectedRange}
            anomalies={anomalies}
            isLoading={isValidating}
          />
        )}

        {/* Anomaly Alerts */}
        {anomalies.length > 0 && (
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-yellow-900">Performance Anomalies Detected</h4>
                <ul className="mt-2 space-y-1">
                  {anomalies.slice(0, 3).map((anomaly, index) => (
                    <li key={index} className="text-sm text-yellow-800">
                      • {anomaly.description}
                    </li>
                  ))}
                </ul>
                {anomalies.length > 3 && (
                  <p className="text-xs text-yellow-700 mt-2">
                    ...and {anomalies.length - 3} more anomalies
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Insights */}
        {trendAnalysis && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Trend Summary</h4>
              <p className="text-sm text-gray-600">
                Your performance is{' '}
                <span className={`font-medium ${
                  trendAnalysis.trend === 'improving' ? 'text-green-600' :
                  trendAnalysis.trend === 'declining' ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {trendAnalysis.trend}
                </span>
                {' '}with a confidence of {formatPercentage(trendAnalysis.confidence)}.
                {trendAnalysis.insights && trendAnalysis.insights.length > 0 && (
                  <span className="block mt-1">{trendAnalysis.insights[0]}</span>
                )}
              </p>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Projection</h4>
              <p className="text-sm text-gray-600">
                At current rate, expected GPA next semester:{' '}
                <span className="font-medium text-blue-600">
                  {formatGPA(trendAnalysis.projectedGPA)}
                </span>
              </p>
              {trendAnalysis.patterns && trendAnalysis.patterns.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  Pattern: {trendAnalysis.patterns.join(', ')}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Data Quality Notice */}
        {trendAnalysis && trendAnalysis.dataPointsCount < 5 && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> For more accurate trend analysis, additional data points are recommended. 
              Currently analyzing {trendAnalysis.dataPointsCount} data points.
            </p>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default TrendAnalyzer;