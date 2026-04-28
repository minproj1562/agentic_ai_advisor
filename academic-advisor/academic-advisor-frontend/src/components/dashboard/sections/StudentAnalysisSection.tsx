// src/components/dashboard/sections/StudentAnalysisSection.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Users, Search, TrendingUp, TrendingDown, Minus,
  AlertTriangle, FileText, Eye, RefreshCw, Loader2, Filter, X, Calendar
} from 'lucide-react';
import apiClient from '../../../services/api.service';

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
  const [filterSemester, setFilterSemester] = useState<string>('');
  const [filterBatch, setFilterBatch] = useState<string>('');
  const [viewStudentId, setViewStudentId] = useState<string | null>(null);
  const [viewStudentName, setViewStudentName] = useState('');

  // 🎯 Dynamic semester calculation based on current month
  const availableSemesters = useMemo(() => {
    const currentMonth = new Date().getMonth() + 1; // 1-12
    const currentYear = new Date().getFullYear();
    
    // Determine if we're in odd or even semester period
    const isOddSemesterPeriod = currentMonth >= 7 && currentMonth <= 12; // July-December
    const isEvenSemesterPeriod = currentMonth >= 1 && currentMonth <= 6; // January-June
    
    let semesters: Array<{value: string, label: string, yearLevel: string}> = [];
    
    if (isOddSemesterPeriod) {
      // Odd semester period (July-December)
      semesters = [
        { value: '1', label: 'Semester 1', yearLevel: 'FY' },
        { value: '3', label: 'Semester 3', yearLevel: 'SY' },
        { value: '5', label: 'Semester 5', yearLevel: 'TY' },
        { value: '7', label: 'Semester 7', yearLevel: 'BE' },
      ];
    } else if (isEvenSemesterPeriod) {
      // Even semester period (January-June)
    
      semesters = [
        { value: '2', label: 'Semester 2', yearLevel: 'FY' },
        { value: '4', label: 'Semester 4', yearLevel: 'SY' },
        { value: '6', label: 'Semester 6', yearLevel: 'TY' },
        { value: '8', label: 'Semester 8', yearLevel: 'BE' },
      ];
    }
    
    return {
      semesters,
      isOddPeriod: isOddSemesterPeriod,
      isEvenPeriod: isEvenSemesterPeriod,
      currentAcademicYear: isOddSemesterPeriod ? `${currentYear}-${currentYear + 1}` : `${currentYear - 1}-${currentYear}`,
      periodName: isOddSemesterPeriod ? 'Odd Semester Period' : isEvenSemesterPeriod ? 'Even Semester Period' : 'Academic Break'
    };
  }, []);

  // Calculate current academic year for batch filter
  const currentYear = new Date().getFullYear();
  const batchYears = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['faculty-student-analysis', facultyId, filterRisk, filterDept, filterSemester, filterBatch, searchTerm],
    queryFn: async () => {
      const params: any = { limit: 200 };
      if (filterRisk && filterRisk !== 'all') params.risk_level = filterRisk;
      if (filterDept) params.department = filterDept;
      if (filterSemester) params.semester = parseInt(filterSemester);
      if (filterBatch) params.batch = filterBatch;
      if (searchTerm) params.search = searchTerm;

      const response = await apiClient.get('/student-analysis/list', { params });
      console.log('✅ Student analysis response:', response.data);
      return response.data;
    },
    enabled: !!facultyId,
    staleTime: 2 * 60 * 1000,
  });

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

  const handleClearFilters = () => {
    setSearchTerm('');
    setFilterRisk('all');
    setFilterDept('');
    setFilterSemester('');
    setFilterBatch('');
  };

  const hasActiveFilters = searchTerm || filterRisk !== 'all' || filterDept || filterSemester || filterBatch;

  const summaryAtRisk = students.filter((s) => s.risk_level === 'high').length;
  const summaryImproving = students.filter((s) => s.improvement_trend === 'improving').length;
  const summaryProjects = students.reduce((a: number, s: any) => a + (s.projects_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Student Analysis</h2>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-gray-600 dark:text-gray-400">
              Monitor student performance from MongoDB
            </p>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
              {students.length} students
            </span>
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3 text-indigo-500" />
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                availableSemesters.isOddPeriod 
                  ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              }`}>
                {availableSemesters.periodName}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          <span className="text-sm">Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Filters 
            {availableSemesters.semesters.length > 0 && (
              <span className="ml-2 text-xs text-gray-500">
                • {availableSemesters.periodName} ({availableSemesters.currentAcademicYear})
              </span>
            )}
          </h3>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="ml-auto text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
            >
              Clear all
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative lg:col-span-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search students..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Department */}
          <select
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="">All Departments</option>
            <option value="IT">IT</option>
            <option value="COMP">COMP</option>
            <option value="EXTC">EXTC</option>
            <option value="MECH">MECH</option>
            <option value="ELEC">ELEC</option>
          </select>

          {/* 🎯 Dynamic Semester Filter */}
          <select
            value={filterSemester}
            onChange={(e) => setFilterSemester(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="">All Semesters</option>
            {availableSemesters.semesters.map((sem) => (
              <option key={sem.value} value={sem.value}>
                {sem.label} ({sem.yearLevel})
              </option>
            ))}
          </select>

          {/* Batch/Year */}
          <select
            value={filterBatch}
            onChange={(e) => setFilterBatch(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="">All Batches</option>
            {batchYears.map((year) => (
              <option key={year} value={year}>
                Batch {year}
              </option>
            ))}
          </select>
        </div>

        {/* Risk Level Filter (Secondary Row) */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-gray-400">Risk Level:</span>
          <div className="flex gap-2">
            {['all', 'high', 'medium', 'low'].map((risk) => (
              <button
                key={risk}
                onClick={() => setFilterRisk(risk)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  filterRisk === risk
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {risk === 'all' ? 'All' : risk.charAt(0).toUpperCase() + risk.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Academic Period Info */}
        {availableSemesters.semesters.length === 0 && (
          <div className="mt-3 p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-sm text-amber-700 dark:text-amber-400">
              📚 Academic Break Period - Semester filters will appear during active academic sessions (July-December for odd semesters, January-June for even semesters).
            </p>
          </div>
        )}
      </div>

      {/* Active Filters Badges */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2">
          {searchTerm && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-md text-xs">
              Search: {searchTerm}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setSearchTerm('')} />
            </span>
          )}
          {filterDept && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md text-xs">
              Department: {filterDept}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setFilterDept('')} />
            </span>
          )}
          {filterSemester && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md text-xs">
              Semester: {availableSemesters.semesters.find(s => s.value === filterSemester)?.label || filterSemester}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setFilterSemester('')} />
            </span>
          )}
          {filterBatch && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-md text-xs">
              Batch: {filterBatch}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setFilterBatch('')} />
            </span>
          )}
          {filterRisk !== 'all' && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md text-xs">
              Risk: {filterRisk}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setFilterRisk('all')} />
            </span>
          )}
        </div>
      )}

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
                {['Student', 'Sem', 'Batch', 'CGPA', 'SGPA', 'Trend', 'Risk', 'Weaknesses', 'Projects', 'Actions'].map((h) => (
                  <th key={h} className={`px-4 py-3 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider ${h === 'Actions' ? 'text-right' : 'text-left'}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center">
                    <div className="flex items-center justify-center gap-2 text-gray-500">
                      <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                      Loading students from database...
                    </div>
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                    {data?.total === 0
                      ? 'No student profiles found in the database.'
                      : hasActiveFilters
                      ? 'No students match your filters. Try adjusting your search criteria.'
                      : 'No students found.'}
                    {filterSemester && availableSemesters.semesters.length > 0 && (
                      <p className="mt-1 text-xs text-gray-400">
                        Currently showing {availableSemesters.semesters.find(s => s.value === filterSemester)?.label} students only
                      </p>
                    )}
                  </td>
                </tr>
              ) : (
                students.map((student: any, index: number) => (
                  <motion.tr
  key={`student-${student.student_id || student.id || student.uid || student.email || index}-${index}`}
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

                    {/* Semester */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        (student.current_semester % 2 === 1)
                          ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                      }`}>
                        Sem {student.current_semester || student.semester || 'N/A'}
                      </span>
                    </td>

                    {/* Batch */}
                    <td className="px-4 py-3 whitespace-nowrap text-gray-600 dark:text-gray-400">
                      {student.batch || student.admission_year || 'N/A'}
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
            {filterSemester && (
              <span className="ml-2">
                • {availableSemesters.semesters.find(s => s.value === filterSemester)?.label} only
              </span>
            )}
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