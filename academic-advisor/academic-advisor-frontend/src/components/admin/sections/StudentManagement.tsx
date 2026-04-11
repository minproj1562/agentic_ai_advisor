// academic-advisor/academic-advisor-frontend/src/components/admin/sections/StudentManagement.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Search, ChevronLeft, ChevronRight, Eye, X, TrendingUp, TrendingDown, Minus, Filter, Calendar } from 'lucide-react';
import apiClient from '../../../services/api.service';

const StudentManagement: React.FC = () => {
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [semester, setSemester] = useState('');
  const [batch, setBatch] = useState('');
  const [page, setPage] = useState(0);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const pageSize = 15;

  // 🎯 Dynamic semester calculation based on current month
  const availableSemesters = useMemo(() => {
    const currentMonth = new Date().getMonth() + 1; // 1-12
    const currentYear = new Date().getFullYear();
    
    // Determine if we're in odd or even semester period
    const isOddSemesterPeriod = currentMonth >= 7 && currentMonth <= 12; // July-December
    const isEvenSemesterPeriod = currentMonth >= 1 && currentMonth <= 6; // January-June
    
    let semesters: Array<{value: string, label: string, period: string}> = [];
    
    if (isOddSemesterPeriod) {
      // Odd semester period (July-December)
      semesters = [
        { value: '1', label: 'Semester 1 (First Year)', period: 'FY' },
        { value: '3', label: 'Semester 3 (Second Year)', period: 'SY' },
        { value: '5', label: 'Semester 5 (Third Year)', period: 'TY' },
        { value: '7', label: 'Semester 7 (Final Year)', period: 'BE' },
      ];
    } else if (isEvenSemesterPeriod) {
      // Even semester period (January-June)
      semesters = [
        { value: '2', label: 'Semester 2 (First Year)', period: 'FY' },
        { value: '4', label: 'Semester 4 (Second Year)', period: 'SY' },
        { value: '6', label: 'Semester 6 (Third Year)', period: 'TY' },
        { value: '8', label: 'Semester 8 (Final Year)', period: 'BE' },
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

  const { data, isLoading } = useQuery({
    queryKey: ['admin-students', search, department, semester, batch, page],
    queryFn: async () => {
      const params: any = { skip: page * pageSize, limit: pageSize };
      if (search) params.search = search;
      if (department) params.department = department;
      if (semester) params.semester = parseInt(semester);
      if (batch) params.batch = batch;
      const res = await apiClient.get('/admin/students', { params });
      return res.data;
    },
    staleTime: 30 * 1000,
  });

  const { data: studentDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['admin-student-detail', selectedStudent?.uid],
    queryFn: async () => {
      const res = await apiClient.get(`/admin/students/${selectedStudent.uid}`);
      return res.data;
    },
    enabled: !!selectedStudent?.uid,
  });

  const trendIcon = (trend: string) => {
    if (trend === 'up' || trend === 'improving') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down' || trend === 'declining') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const handleClearFilters = () => {
    setSearch('');
    setDepartment('');
    setSemester('');
    setBatch('');
    setPage(0);
  };

  const hasActiveFilters = search || department || semester || batch;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Student Management</h2>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {data?.total || 0} students
            </p>
            <span className="text-gray-300">•</span>
            <div className="flex items-center gap-1 text-xs">
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
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Filters {availableSemesters.semesters.length > 0 && (
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
              placeholder="Search by name, roll no..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
            />
          </div>

          {/* Department */}
          <select
            value={department}
            onChange={(e) => { setDepartment(e.target.value); setPage(0); }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="">All Departments</option>
            <option value="IT">Information Technology</option>
            <option value="COMP">Computer Engineering</option>
            <option value="EXTC">Electronics & Telecom</option>
            <option value="MECH">Mechanical</option>
            <option value="ELEC">Electrical</option>
          </select>

          {/* 🎯 Dynamic Semester Filter */}
          <select
            value={semester}
            onChange={(e) => { setSemester(e.target.value); setPage(0); }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="">All Semesters</option>
            {availableSemesters.semesters.map((sem) => (
              <option key={sem.value} value={sem.value}>
                {sem.label}
              </option>
            ))}
          </select>

          {/* Batch/Year */}
          <select
            value={batch}
            onChange={(e) => { setBatch(e.target.value); setPage(0); }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="">All Batches</option>
            {batchYears.map((year) => (
              <option key={year} value={year}>
                Batch {year}
              </option>
            ))}
          </select>
        </div>

        {/* Academic Period Info */}
        {availableSemesters.semesters.length === 0 && (
          <div className="mt-3 p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-sm text-amber-700 dark:text-amber-400">
              📚 Academic Break Period - No active semesters. Regular semester filters will appear during academic sessions.
            </p>
          </div>
        )}
      </div>

      {/* Active Filters Badges */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2">
          {search && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-md text-xs">
              Search: {search}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setSearch('')} />
            </span>
          )}
          {department && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md text-xs">
              Department: {department}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setDepartment('')} />
            </span>
          )}
          {semester && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md text-xs">
              Semester: {availableSemesters.semesters.find(s => s.value === semester)?.label || semester}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setSemester('')} />
            </span>
          )}
          {batch && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-md text-xs">
              Batch: {batch}
              <X className="w-3 h-3 cursor-pointer" onClick={() => setBatch('')} />
            </span>
          )}
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                {['Name', 'Roll No', 'Branch', 'Sem', 'Batch', 'CGPA', 'SGPA', 'Trend', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 9 }).map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded animate-pulse" /></td>
                    ))}
                  </tr>
                ))
              ) : data?.students?.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                    {hasActiveFilters ? 'No students match your filters' : 'No students found'}
                    {semester && (
                      <p className="mt-1 text-xs text-gray-400">
                        Try selecting a different semester or clear filters to see all students
                      </p>
                    )}
                  </td>
                </tr>
              ) : (
                data?.students?.map((student: any) => (
                  <motion.tr
                    key={student.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{student.name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{student.roll_number}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs">
                        {student.branch}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        (student.semester % 2 === 1) 
                          ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                      }`}>
                        Sem {student.semester || student.current_semester}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{student.batch || student.admission_year}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900 dark:text-white">{student.overall_cgpa?.toFixed(2) || student.cgpa?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{student.semester_sgpa?.toFixed(2) || student.latest_sgpa?.toFixed(2)}</td>
                    <td className="px-4 py-3">{trendIcon(student.performance_trend || student.improvement_trend)}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedStudent(student)}
                        className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4 text-gray-500" />
                      </button>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, data.total)} of {data.total}
              {semester && (
                <span className="ml-2 text-xs text-gray-500">
                  (Semester {semester} students)
                </span>
              )}
            </p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button onClick={() => setPage(p => p + 1)} disabled={!data.has_more} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Student Detail Modal - Same as before */}
      {/* ... (keep the existing modal code) ... */}
    </div>
  );
};

export default StudentManagement;