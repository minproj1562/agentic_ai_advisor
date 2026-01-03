// modules/agent1/performance-analytics/components/SubjectPerformance/index.tsx
import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

import SubjectRadar from './SubjectRadar';
import { usePerformanceTrends } from '../../hooks/usePerformanceTrends';
import { SubjectData } from '../../types/analytics.types';
import { calculateSubjectMetrics, identifyWeakAreas } from '../../utils/calculations';
import LoadingSpinner from '../../../../../components/common/LoadingSpinner';
// Import the formatters from the actual file now that it exists
import { formatGPA, formatPercentage } from '../../utils/formatters';

interface SubjectPerformanceProps {
  studentId: string;
  semesterId?: string;
  onSubjectSelect?: (subject: SubjectData) => void;
  className?: string;
}

const SubjectPerformance: React.FC<SubjectPerformanceProps> = ({
  studentId,
  semesterId,
  onSubjectSelect,
  className = ''
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'performance' | 'credits' | 'name'>('performance');
  const [showOnlyWeak, setShowOnlyWeak] = useState(false);
  const [expandedSubject, setExpandedSubject] = useState<string | null>(null);

  const {
    trends: performanceData,
    loading,
    error,
    refetch
  } = usePerformanceTrends(studentId, {
    semesterId,
    groupBySubject: true
  });

  const subjects = useMemo(() => {
    if (!performanceData?.subjects) return [];
    
    let filtered = [...performanceData.subjects];
    
    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(s => s.category === selectedCategory);
    }
    
    // Apply weak areas filter
    if (showOnlyWeak) {
      const weakAreas = identifyWeakAreas(filtered);
      filtered = filtered.filter(s => weakAreas.includes(s.id));
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'performance':
          return b.currentGrade - a.currentGrade;
        case 'credits':
          return b.credits - a.credits;
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [performanceData, selectedCategory, showOnlyWeak, sortBy]);

  const metrics = useMemo(() => {
    if (!subjects.length) return null;
    return calculateSubjectMetrics(subjects);
  }, [subjects]);

  const categories = useMemo(() => {
    if (!performanceData?.subjects) return [];
    const cats = new Set(performanceData.subjects.map(s => s.category));
    return Array.from(cats);
  }, [performanceData]);

  const getSubjectStatus = useCallback((subject: SubjectData) => {
    if (subject.currentGrade >= 85) return { color: 'green', label: 'Excellent' };
    if (subject.currentGrade >= 70) return { color: 'blue', label: 'Good' };
    if (subject.currentGrade >= 50) return { color: 'yellow', label: 'Average' };
    return { color: 'red', label: 'Needs Improvement' };
  }, []);

  const handleExport = useCallback(() => {
    const data = subjects.map(s => ({
      Subject: s.name,
      Category: s.category,
      Credits: s.credits,
      'Current Grade': s.currentGrade,
      'Class Average': s.classAverage || 'N/A',
      Status: getSubjectStatus(s).label
    }));
    
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `subject-performance-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [subjects, getSubjectStatus]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        {/* FIXED: Removed invalid size prop */}
        <LoadingSpinner />
        <div className="ml-3">Loading subject performance...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-red-50 rounded-lg">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-red-700 font-medium">Failed to load subject data</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!performanceData?.subjects || performanceData.subjects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-gray-50 rounded-lg">
        <BookOpen className="w-16 h-16 text-gray-400 mb-4" />
        <p className="text-gray-700 font-medium text-lg mb-2">No Subject Data Available</p>
        <p className="text-gray-500 text-center">
          Subject performance data will appear here once available.
        </p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Subject Performance</h2>
          <p className="text-gray-600 mt-1">
            Detailed analysis of your performance across all subjects
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh data"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          <button
            onClick={handleExport}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Export data"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="performance">Sort by Performance</option>
          <option value="credits">Sort by Credits</option>
          <option value="name">Sort by Name</option>
        </select>
        
        <button
          onClick={() => setShowOnlyWeak(!showOnlyWeak)}
          className={`px-4 py-2 rounded-lg transition-colors border ${
            showOnlyWeak
              ? 'bg-red-100 text-red-700 border-red-300'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
          }`}
        >
          <Filter className="w-4 h-4 inline mr-2" />
          {showOnlyWeak ? 'Showing Weak Areas' : 'Show Weak Areas'}
        </button>
      </div>

      {/* Overall Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-600 font-medium">Overall GPA</p>
            <p className="text-2xl font-bold text-blue-900">{formatGPA(metrics.overallGPA)}</p>
            <p className="text-xs text-blue-700 mt-1">
              {metrics.gpaChange >= 0 ? '+' : ''}{formatPercentage(metrics.gpaChange)} from last sem
            </p>
          </div>
          
          <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
            <p className="text-sm text-green-600 font-medium">Strong Subjects</p>
            <p className="text-2xl font-bold text-green-900">{metrics.strongSubjects}</p>
            <p className="text-xs text-green-700 mt-1">Grade ≥ 85%</p>
          </div>
          
          <div className="p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-600 font-medium">Needs Attention</p>
            <p className="text-2xl font-bold text-yellow-900">{metrics.needsAttention}</p>
            <p className="text-xs text-yellow-700 mt-1">Grade &lt; 60%</p>
          </div>
          
          <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
            <p className="text-sm text-purple-600 font-medium">Total Credits</p>
            <p className="text-2xl font-bold text-purple-900">{metrics.totalCredits}</p>
            <p className="text-xs text-purple-700 mt-1">This semester</p>
          </div>
        </div>
      )}

      {/* Radar Chart */}
      <div className="mb-6">
        <SubjectRadar subjects={subjects} height={350} />
      </div>

      {/* Subject List */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Subject Details</h3>
        
        {subjects.map((subject, index) => {
          const status = getSubjectStatus(subject);
          const isExpanded = expandedSubject === subject.id;
          
          // FIXED: Use explicit color mapping instead of template literals
          const getStatusColorClass = (color: string) => {
            switch (color) {
              case 'green': return 'text-green-500';
              case 'blue': return 'text-blue-500';
              case 'yellow': return 'text-yellow-500';
              case 'red': return 'text-red-500';
              default: return 'text-gray-500';
            }
          };
          
          const statusColorClass = getStatusColorClass(status.color);
          
          return (
            <motion.div
              key={subject.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
            >
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => {
                  setExpandedSubject(isExpanded ? null : subject.id);
                  onSubjectSelect?.(subject);
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BookOpen className={`w-5 h-5 ${statusColorClass}`} />
                    <div>
                      <h4 className="font-semibold text-gray-900">{subject.name}</h4>
                      <p className="text-sm text-gray-600">
                        {subject.category} • {subject.credits} credits
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">
                        {subject.currentGrade}%
                      </p>
                      <p className={`text-sm font-medium ${statusColorClass}`}>
                        {status.label}
                      </p>
                    </div>
                    
                    {/* FIXED: Added null checks for trend property */}
                    {subject.trend && subject.trend > 0 ? (
                      <TrendingUp className="w-5 h-5 text-green-500" />
                    ) : subject.trend && subject.trend < 0 ? (
                      <TrendingDown className="w-5 h-5 text-red-500" />
                    ) : null}
                  </div>
                </div>
              </div>
              
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-gray-200 bg-gray-50 overflow-hidden"
                  >
                    <div className="p-4 space-y-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Class Average</p>
                          <p className="font-semibold">{subject.classAverage || 'N/A'}%</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Your Rank</p>
                          <p className="font-semibold">
                            {subject.rank && subject.totalStudents 
                              ? `#${subject.rank}/${subject.totalStudents}`
                              : 'N/A'
                            }
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Attendance</p>
                          <p className="font-semibold">{subject.attendance || 'N/A'}%</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Assignments</p>
                          <p className="font-semibold">
                            {subject.completedAssignments && subject.totalAssignments
                              ? `${subject.completedAssignments}/${subject.totalAssignments}`
                              : 'N/A'
                            }
                          </p>
                        </div>
                      </div>
                      
                      {subject.weakTopics && subject.weakTopics.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">Areas for Improvement:</p>
                          <div className="flex flex-wrap gap-2">
                            {subject.weakTopics.map((topic, topicIndex) => (
                              <span
                                key={topicIndex}
                                className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
                              >
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {subject.recommendation && (
                        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="text-sm text-blue-900">
                            <strong>Recommendation:</strong> {subject.recommendation}
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default SubjectPerformance;