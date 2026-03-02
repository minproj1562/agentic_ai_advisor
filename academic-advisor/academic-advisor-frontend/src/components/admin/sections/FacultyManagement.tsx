// academic-advisor/academic-advisor-frontend/src/components/admin/sections/FacultyManagement.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Search, Eye, X, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import apiClient from '../../../services/api.service';

const FacultyManagement: React.FC = () => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedFaculty, setSelectedFaculty] = useState<any>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['admin-faculty', search, statusFilter],
    queryFn: async () => {
      const params: any = { limit: 50 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.get('/admin/faculty', { params });
      return res.data;
    },
    staleTime: 30 * 1000,
  });

  const { data: facultyDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['admin-faculty-detail', selectedFaculty?.user_id],
    queryFn: async () => {
      const res = await apiClient.get(`/admin/faculty/${selectedFaculty.user_id}`);
      return res.data;
    },
    enabled: !!selectedFaculty?.user_id,
  });

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      pending_setup: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      on_leave: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400',
      inactive: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    };
    const icons: Record<string, React.ReactNode> = {
      active: <CheckCircle className="w-3 h-3" />,
      pending_setup: <Clock className="w-3 h-3" />,
      inactive: <AlertCircle className="w-3 h-3" />,
    };
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.inactive}`}>
        {icons[status]}
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Faculty Management</h2>
        <div className="flex gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search faculty..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="pending_setup">Pending Setup</option>
            <option value="on_leave">On Leave</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Faculty Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg animate-pulse">
                <div className="h-12 w-12 bg-gray-200 dark:bg-gray-600 rounded-full mb-4" />
                <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-1/2" />
              </div>
            ))
          : data?.faculty?.map((f: any) => (
              <motion.div
                key={f.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all cursor-pointer"
                onClick={() => setSelectedFaculty(f)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {f.name?.charAt(0) || 'F'}
                  </div>
                  {statusBadge(f.status)}
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{f.name}</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{f.designation}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{f.department}</p>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Mentees: <strong className="text-gray-700 dark:text-gray-300">{f.mentee_count}/{f.max_mentees}</strong></span>
                  <span className="text-gray-500">Profile: <strong className="text-gray-700 dark:text-gray-300">{f.profile_completeness}%</strong></span>
                </div>

                {f.profile_completeness < 100 && (
                  <div className="mt-2 w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-1.5 rounded-full" style={{ width: `${f.profile_completeness}%` }} />
                  </div>
                )}
              </motion.div>
            ))
        }
      </div>

      {data?.faculty?.length === 0 && !isLoading && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">No faculty found</div>
      )}

      {/* Faculty Detail Modal */}
      <AnimatePresence>
        {selectedFaculty && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedFaculty(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">{facultyDetail?.name || selectedFaculty.name}</h3>
                <button onClick={() => setSelectedFaculty(null)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4 text-sm">
                {detailLoading ? (
                  <div className="animate-pulse space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-4 bg-gray-200 dark:bg-gray-600 rounded" />)}
                  </div>
                ) : facultyDetail ? (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <div><span className="text-gray-500">Email:</span><br /><span className="font-medium text-gray-900 dark:text-white">{facultyDetail.email}</span></div>
                      <div><span className="text-gray-500">Department:</span><br /><span className="font-medium text-gray-900 dark:text-white">{facultyDetail.department}</span></div>
                      <div><span className="text-gray-500">Designation:</span><br /><span className="font-medium text-gray-900 dark:text-white">{facultyDetail.designation}</span></div>
                      <div><span className="text-gray-500">Status:</span><br />{statusBadge(facultyDetail.status)}</div>
                      <div><span className="text-gray-500">Mentees:</span><br /><span className="font-medium text-gray-900 dark:text-white">{facultyDetail.mentee_count}</span></div>
                      <div><span className="text-gray-500">Meetings:</span><br /><span className="font-medium text-gray-900 dark:text-white">{facultyDetail.meetings_count}</span></div>
                    </div>
                    {facultyDetail.specializations?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Specializations</h4>
                        <div className="flex flex-wrap gap-1">
                          {facultyDetail.specializations.map((s: string) => (
                            <span key={s} className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {facultyDetail.teaching_subjects?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Teaching</h4>
                        <div className="flex flex-wrap gap-1">
                          {facultyDetail.teaching_subjects.map((s: string) => (
                            <span key={s} className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : <p className="text-gray-500">No data</p>}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FacultyManagement;