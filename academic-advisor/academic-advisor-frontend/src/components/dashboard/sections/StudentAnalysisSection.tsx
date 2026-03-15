// src/components/dashboard/sections/StudentAnalysisSection.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Users, Search, TrendingUp, TrendingDown, Minus,
  AlertTriangle, FileText, Eye, RefreshCw, Loader2
} from 'lucide-react';
import apiClient from '../../../services/api.service';

// Lazy import the modal to avoid issues if file doesn't exist yet
const StudentDashboardViewModal = React.lazy(
  () => import('../cards/StudentDashboardViewModal')
);

interface StudentAnalysisSectionProps {
  facultyId: string;
  facultyData?: any;
}

const StudentAnalysisSection: React.FC<StudentAnalysisSectionProps> = ({ facultyId }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [filterDept, setFilterDept] = useState<string>('');
  const [viewStudentId, setViewStudentId] = useState<string | null>(null);
  const [viewStudentName, setViewStudentName] = useState('');

  // ── Fetch from MongoDB via /student-analysis/list ──
  // Returns { students: [...], total: N, has_more: bool } just like admin
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['faculty-student-analysis', facultyId, filterRisk, filterDept, searchTerm],
    queryFn: async () => {
      const params: any = { limit: 200 };
      if (filterRisk && filterRisk !== 'all') params.risk_level = filterRisk;
      if (filterDept) params.department = filterDept;
      if (searchTerm) params.search = searchTerm;

      const response = await apiClient.get('/student-analysis/list', { params });
      console.log('✅ Student analysis response:', response.data);
      return response.data;
    },
    enabled: !!facultyId,
    staleTime: 2 * 60 * 1000,
  });

  // Extract students array - matching admin pattern: data?.students
  const students: any[] = data?.students || [];

  const getTrendIcon = (trend: string) => {
    if (trend === 'improving') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'declining') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      case 'medium': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'low': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const summaryAtRisk = students.filter((s) => s.risk_level === 'high').length;
  const summaryImproving = students.filter((s) => s.improvement_trend === 'improving').length;
  const summaryProjects = students.reduce((a: number, s: any) => a + (s.projects_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Student Analysis</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor student performance from MongoDB
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
              {students.length} students · Read-only
            </span>
          </p>
        </div>

        <div className="flex gap-3 flex-wrap">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search students..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
          </div>

          <select
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
          >
            <option value="">All Depts</option>
            <option value="IT">IT</option>
            <option value="COMP">COMP</option>
            <option value="EXTC">EXTC</option>
            <option value="MECH">MECH</option>
            <option value="ELEC">ELEC</option>
          </select>

          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
          >
            <option value="all">All Risk</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>

          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{students.length}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Total Students</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryAtRisk}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">At Risk</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryImproving}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Improving</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <FileText className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryProjects}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Total Projects</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                {['Student', 'CGPA', 'SGPA', 'Trend', 'Risk', 'Weaknesses', 'Projects', 'Actions'].map((h) => (
                  <th key={h} className={`px-4 py-3 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider ${h === 'Actions' ? 'text-right' : 'text-left'}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <div className="flex items-center justify-center gap-2 text-gray-500">
                      <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                      Loading students from database...
                    </div>
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                    {data?.total === 0
                      ? 'No student profiles found in the database. Students need to create their profiles first.'
                      : 'No students match your search/filter criteria.'}
                  </td>
                </tr>
              ) : (
                students.map((student: any, index: number) => (
                  <motion.tr
                    key={student.student_id || student.id || index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.03 }}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    {/* Student */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                          {(student.name || student.email || 'S').charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 dark:text-white truncate">
                            {student.name || student.email?.split('@')[0] || 'Unknown'}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {student.roll_number || student.email || ''}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* CGPA */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`text-base font-bold ${
                        student.cgpa >= 8 ? 'text-green-600' : student.cgpa >= 6 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {student.cgpa?.toFixed(2) || '—'}
                      </span>
                    </td>

                    {/* SGPA */}
                    <td className="px-4 py-3 whitespace-nowrap text-gray-600 dark:text-gray-400">
                      {student.latest_sgpa?.toFixed(2) || student.semester_sgpa?.toFixed(2) || '—'}
                    </td>

                    {/* Trend */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        {getTrendIcon(student.improvement_trend || student.performance_trend)}
                        <span className="text-xs text-gray-500 capitalize">
                          {student.improvement_trend || student.performance_trend || 'stable'}
                        </span>
                      </div>
                    </td>

                    {/* Risk */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskBadgeColor(student.risk_level)}`}>
                        {student.risk_level?.toUpperCase() || 'N/A'}
                      </span>
                    </td>

                    {/* Weaknesses */}
                    <td className="px-4 py-3 whitespace-nowrap text-gray-600 dark:text-gray-400 text-xs">
                      {student.weakness_count || 0} identified
                    </td>

                    {/* Projects */}
                    <td className="px-4 py-3 whitespace-nowrap text-gray-600 dark:text-gray-400 text-xs">
                      {student.projects_count || 0} projects
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <button
                        onClick={() => {
                          setViewStudentId(student.student_id || student.id || student.uid);
                          setViewStudentName(student.name || student.email?.split('@')[0] || 'Student');
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 rounded-lg transition-colors"
                        title="View Student Dashboard"
                      >
                        <Eye className="w-4 h-4" />
                        View
                      </button>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer with count */}
        {data && (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400">
            Showing {students.length} of {data.total} students
          </div>
        )}
      </div>

      {/* View Modal */}
      <AnimatePresence>
        {viewStudentId && (
          <React.Suspense fallback={
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <Loader2 className="w-8 h-8 animate-spin text-white" />
            </div>
          }>
            <StudentDashboardViewModal
              studentId={viewStudentId}
              studentName={viewStudentName}
              onClose={() => { setViewStudentId(null); setViewStudentName(''); }}
            />
          </React.Suspense>
        )}
      </AnimatePresence>
    </div>
  );
};

export default StudentAnalysisSection;