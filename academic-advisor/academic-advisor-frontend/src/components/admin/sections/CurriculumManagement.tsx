// academic-advisor/academic-advisor-frontend/src/components/admin/sections/CurriculumManagement.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Edit3, Save, X, Plus, Trash2 } from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

const CurriculumManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [admissionYear, setAdmissionYear] = useState<number>(2024);
  const [editingElective, setEditingElective] = useState<any>(null);
  const [tab, setTab] = useState<'curriculum' | 'electives'>('curriculum');

  const { data: curriculumData, isLoading: currLoading } = useQuery({
    queryKey: ['admin-curriculum', selectedSemester, admissionYear],
    queryFn: async () => {
      const res = await apiClient.get('/admin/curriculum', {
        params: { semester: selectedSemester, admission_year: admissionYear },
      });
      return res.data;
    },
  });

  const { data: electivesData, isLoading: electivesLoading } = useQuery({
    queryKey: ['admin-electives'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/curriculum/electives');
      return res.data;
    },
    enabled: tab === 'electives',
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const res = await apiClient.put(`/admin/curriculum/electives/${id}`, data);
      return res.data;
    },
    onSuccess: () => {
      toast.success('Elective updated');
      queryClient.invalidateQueries({ queryKey: ['admin-electives'] });
      setEditingElective(null);
    },
    onError: () => toast.error('Update failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/admin/curriculum/electives/${id}`);
    },
    onSuccess: () => {
      toast.success('Elective deleted');
      queryClient.invalidateQueries({ queryKey: ['admin-electives'] });
    },
    onError: () => toast.error('Delete failed'),
  });

  const subjects = curriculumData?.curriculum?.[`semester_${selectedSemester}`] || [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Curriculum Management</h2>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setTab('curriculum')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'curriculum' ? 'bg-red-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        >
          Semester Subjects
        </button>
        <button
          onClick={() => setTab('electives')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'electives' ? 'bg-red-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        >
          Elective Courses
        </button>
      </div>

      {tab === 'curriculum' && (
        <div className="space-y-4">
          <div className="flex gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Semester</label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
                  <button
                    key={sem}
                    onClick={() => setSelectedSemester(sem)}
                    className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${selectedSemester === sem ? 'bg-red-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'}`}
                  >
                    {sem}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Admission Year</label>
              <select
                value={admissionYear}
                onChange={(e) => setAdmissionYear(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
              >
                {[2022, 2023, 2024, 2025].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          {curriculumData?.curriculum_type && (
            <p className="text-xs text-gray-500">
              Curriculum type: <span className="font-medium capitalize">{curriculumData.curriculum_type}</span>
            </p>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  {['Code', 'Subject', 'Credits', 'Type', 'Internal', 'External', 'Elective'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {currLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>{Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-600 rounded animate-pulse" /></td>
                    ))}</tr>
                  ))
                ) : subjects.length === 0 ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No subjects for this semester</td></tr>
                ) : (
                  subjects.map((s: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-900 dark:text-white">{s.subject_code}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{s.subject_name}</td>
                      <td className="px-4 py-3 text-center">{s.credits}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">{s.course_type}</span>
                      </td>
                      <td className="px-4 py-3 text-center">{s.internal_max}</td>
                      <td className="px-4 py-3 text-center">{s.external_max}</td>
                      <td className="px-4 py-3 text-center">{s.is_elective ? '✅' : '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'electives' && (
        <div className="space-y-4">
          {electivesLoading ? (
            <div className="animate-pulse space-y-3">
              {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-20 bg-gray-200 dark:bg-gray-600 rounded-xl" />)}
            </div>
          ) : (
            <>
              {/* Static Elective Groups */}
              {electivesData?.static_elective_groups && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Elective Groups (Curriculum)</h3>
                  <div className="space-y-4">
                    {Object.entries(electivesData.static_elective_groups).map(([group, options]) => (
                      <div key={group} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">{group}</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {(options as any[]).map((opt: any) => (
                            <div key={opt.code} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs">
                              <span className="font-mono text-gray-500">{opt.code}</span>
                              <span className="text-gray-900 dark:text-white">{opt.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* DB Electives (Editable) */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Database Electives (Editable)</h3>
                {electivesData?.db_electives?.length === 0 ? (
                  <p className="text-gray-500 text-sm">No electives in database yet.</p>
                ) : (
                  <div className="space-y-3">
                    {electivesData?.db_electives?.map((e: any) => (
                      <div key={e.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{e.name}</p>
                          <p className="text-xs text-gray-500">{e.code} · Sem {e.semester} · {e.credits} credits · {e.category}</p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingElective(e)}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                          >
                            <Edit3 className="w-4 h-4 text-gray-500" />
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`Delete ${e.name}?`)) deleteMutation.mutate(e.id);
                            }}
                            className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default CurriculumManagement;