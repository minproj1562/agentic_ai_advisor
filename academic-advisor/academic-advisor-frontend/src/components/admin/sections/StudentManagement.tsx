// academic-advisor/academic-advisor-frontend/src/components/admin/sections/StudentManagement.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Search, ChevronLeft, ChevronRight, Eye, X, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import apiClient from '../../../services/api.service';

const StudentManagement: React.FC = () => {
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [page, setPage] = useState(0);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const pageSize = 15;

  const { data, isLoading } = useQuery({
    queryKey: ['admin-students', search, department, page],
    queryFn: async () => {
      const params: any = { skip: page * pageSize, limit: pageSize };
      if (search) params.search = search;
      if (department) params.department = department;
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
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Student Management</h2>
        <div className="flex gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, roll no..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
          <select
            value={department}
            onChange={(e) => { setDepartment(e.target.value); setPage(0); }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
          >
            <option value="">All Depts</option>
            <option value="IT">IT</option>
            <option value="CS">CS</option>
            <option value="COMP">COMP</option>
            <option value="EXTC">EXTC</option>
            <option value="MECH">MECH</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                {['Name', 'Roll No', 'Branch', 'Sem', 'CGPA', 'SGPA', 'Trend', 'Actions'].map(h => (
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
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded animate-pulse" /></td>
                    ))}
                  </tr>
                ))
              ) : data?.students?.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">No students found</td>
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
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{student.semester}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900 dark:text-white">{student.overall_cgpa?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{student.semester_sgpa?.toFixed(2)}</td>
                    <td className="px-4 py-3">{trendIcon(student.performance_trend)}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedStudent(student)}
                        className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
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
            </p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button onClick={() => setPage(p => p + 1)} disabled={!data.has_more} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Student Detail Modal */}
      <AnimatePresence>
        {selectedStudent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedStudent(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  {studentDetail?.name || selectedStudent.name}
                </h3>
                <button onClick={() => setSelectedStudent(null)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                {detailLoading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="h-6 bg-gray-200 dark:bg-gray-600 rounded animate-pulse" />
                    ))}
                  </div>
                ) : studentDetail ? (
                  <>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="text-gray-500">Email:</span> <span className="font-medium text-gray-900 dark:text-white">{studentDetail.email}</span></div>
                      <div><span className="text-gray-500">Roll:</span> <span className="font-medium text-gray-900 dark:text-white">{studentDetail.roll_number}</span></div>
                      <div><span className="text-gray-500">Branch:</span> <span className="font-medium text-gray-900 dark:text-white">{studentDetail.branch}</span></div>
                      <div><span className="text-gray-500">Semester:</span> <span className="font-medium text-gray-900 dark:text-white">{studentDetail.semester}</span></div>
                      <div><span className="text-gray-500">CGPA:</span> <span className="font-bold text-lg text-gray-900 dark:text-white">{studentDetail.overall_cgpa?.toFixed(2)}</span></div>
                      <div><span className="text-gray-500">Credits:</span> <span className="font-medium text-gray-900 dark:text-white">{studentDetail.completed_credits}/{studentDetail.total_credits}</span></div>
                    </div>

                    {studentDetail.interests?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Interests</h4>
                        <div className="flex flex-wrap gap-2">
                          {studentDetail.interests.map((i: string) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs">{i}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {studentDetail.subjects?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Subjects</h4>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {studentDetail.subjects.map((s: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded-lg text-xs">
                              <span className="font-medium text-gray-900 dark:text-white">{s.name}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-gray-500">{s.score}</span>
                                {trendIcon(s.trend)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {studentDetail.projects?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Projects ({studentDetail.projects.length})</h4>
                        <div className="space-y-2">
                          {studentDetail.projects.map((p: any) => (
                            <div key={p.id} className="p-2 bg-gray-50 dark:bg-gray-700 rounded-lg text-xs">
                              <p className="font-medium text-gray-900 dark:text-white">{p.title}</p>
                              {p.technologies?.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {p.technologies.map((t: string) => (
                                    <span key={t} className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-[10px]">{t}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-gray-500">No data available</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default StudentManagement;