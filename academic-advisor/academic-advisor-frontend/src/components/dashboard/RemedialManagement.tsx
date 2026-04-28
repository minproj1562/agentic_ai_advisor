// academic-advisor-frontend/src/components/dashboard/RemedialManagement.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle, Plus, CheckCircle, Clock, TrendingUp,
  MessageSquare, X, User, BookOpen, ChevronDown
} from 'lucide-react';
import apiClient from '../../services/api.service';
import toast from 'react-hot-toast';

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  active: { label: 'Active', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', icon: AlertTriangle },
  improving: { label: 'Improving', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400', icon: TrendingUp },
  resolved: { label: 'Resolved', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', icon: CheckCircle },
};

const RemedialManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [noteModal, setNoteModal] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  const [marksChange, setMarksChange] = useState('');

  // Add form state
  const [studentId, setStudentId] = useState('');
  const [studentName, setStudentName] = useState('');
  const [studentRoll, setStudentRoll] = useState('');
  const [semester, setSemester] = useState(5);
  const [subject, setSubject] = useState('');
  const [reason, setReason] = useState('');
  const [initialMarks, setInitialMarks] = useState('');
  const [targetMarks, setTargetMarks] = useState('50');

  const { data, isLoading } = useQuery({
    queryKey: ['remedial-entries', statusFilter],
    queryFn: async () => {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.get('/faculty/remedial', { params });
      return res.data;
    },
  });

  const addMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/faculty/remedial', {
        student_id: studentId, student_name: studentName, student_roll: studentRoll,
        semester, subject, reason,
        initial_marks: initialMarks ? parseFloat(initialMarks) : null,
        target_marks: targetMarks ? parseFloat(targetMarks) : null,
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success('Student added to remedial');
      queryClient.invalidateQueries({ queryKey: ['remedial-entries'] });
      setShowAddForm(false);
      setStudentId(''); setStudentName(''); setStudentRoll('');
      setSubject(''); setReason(''); setInitialMarks('');
    },
    onError: () => toast.error('Failed to add'),
  });

  const addNoteMutation = useMutation({
    mutationFn: async (entryId: string) => {
      const res = await apiClient.put(`/faculty/remedial/${entryId}/progress`, {
        note: noteText,
        marks_change: marksChange ? parseFloat(marksChange) : null,
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success('Progress note added');
      queryClient.invalidateQueries({ queryKey: ['remedial-entries'] });
      setNoteModal(null); setNoteText(''); setMarksChange('');
    },
  });

  const resolveMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.put(`/faculty/remedial/${id}/resolve`);
      return res.data;
    },
    onSuccess: () => {
      toast.success('Marked as resolved!');
      queryClient.invalidateQueries({ queryKey: ['remedial-entries'] });
    },
  });

  const entries = data?.entries || [];
  const activeCount = entries.filter((e: any) => e.status === 'active').length;
  const improvingCount = entries.filter((e: any) => e.status === 'improving').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Remedial Students</h2>
          <p className="text-sm text-gray-500">{activeCount} active, {improvingCount} improving</p>
        </div>
        <button onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors">
          {showAddForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showAddForm ? 'Cancel' : 'Add Student'}
        </button>
      </div>

      {/* Add Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg overflow-hidden">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Add Remedial Student</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Student Name *</label>
                <input value={studentName} onChange={e => setStudentName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Roll Number</label>
                <input value={studentRoll} onChange={e => setStudentRoll(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Student ID (Firebase UID)</label>
                <input value={studentId} onChange={e => setStudentId(e.target.value)} placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Subject *</label>
                <select value={subject} onChange={e => setSubject(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm">
                  <option value="">Select subject</option>
                  {['Engineering Mathematics-III', 'Engineering Mathematics-IV', 'Data Structures & Analysis',
                    'Database Management System', 'Computer Network', 'Operating System', 'Software Engineering',
                    'Automata Theory', 'Artificial Intelligence', 'Internet of Things',
                  ].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Current Marks</label>
                <input type="number" value={initialMarks} onChange={e => setInitialMarks(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Target Marks</label>
                <input type="number" value={targetMarks} onChange={e => setTargetMarks(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div className="md:col-span-3">
                <label className="block text-xs font-medium text-gray-500 mb-1">Reason</label>
                <textarea value={reason} onChange={e => setReason(e.target.value)} rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
            </div>
            <div className="mt-4 flex justify-end">
              <button onClick={() => addMutation.mutate()}
                disabled={!studentName || !subject || addMutation.isPending}
                className="px-6 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:bg-gray-400 transition-colors">
                {addMutation.isPending ? 'Adding...' : 'Add to Remedial'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status Filter */}
      <div className="flex gap-2">
        {[null, 'active', 'improving', 'resolved'].map(s => (
          <button key={s || 'all'} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${statusFilter === s ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>
            {s ? STATUS_CONFIG[s].label : 'All'} {s === null ? `(${entries.length})` : ''}
          </button>
        ))}
      </div>

      {/* Entries List */}
      {isLoading ? (
        <div className="space-y-3">{[1, 2, 3].map(i => <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />)}</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-20" />
          <p>No remedial students found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {entries.map((entry: any, i: number) => {
            const statusConf = STATUS_CONFIG[entry.status] || STATUS_CONFIG.active;
            const StatusIcon = statusConf.icon;
            return (
              <motion.div key={entry._id || i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                      <User className="w-5 h-5 text-gray-500" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{entry.student_name || 'Unknown'}</h4>
                      <p className="text-xs text-gray-500">{entry.student_roll} • {entry.subject}</p>
                      {entry.reason && <p className="text-xs text-gray-400 mt-1">{entry.reason}</p>}
                      <div className="flex items-center gap-3 mt-2">
                        {entry.initial_marks != null && (
                          <span className="text-xs text-gray-500">Initial: <strong>{entry.initial_marks}</strong></span>
                        )}
                        {entry.current_marks != null && (
                          <span className="text-xs text-gray-500">Current: <strong className={entry.current_marks > (entry.initial_marks || 0) ? 'text-green-600' : 'text-red-600'}>{entry.current_marks}</strong></span>
                        )}
                        {entry.target_marks != null && (
                          <span className="text-xs text-gray-500">Target: <strong>{entry.target_marks}</strong></span>
                        )}
                      </div>
                      {/* Progress Notes */}
                      {entry.progress_notes?.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {entry.progress_notes.slice(-2).map((n: any, ni: number) => (
                            <div key={ni} className="text-xs text-gray-400 flex items-start gap-1">
                              <MessageSquare className="w-3 h-3 mt-0.5 flex-shrink-0" />
                              <span>{n.note} {n.marks_change ? `(${n.marks_change > 0 ? '+' : ''}${n.marks_change})` : ''}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-lg text-xs font-medium ${statusConf.color}`}>
                      {statusConf.label}
                    </span>
                    {entry.status !== 'resolved' && (
                      <>
                        <button onClick={() => { setNoteModal(entry._id); setNoteText(''); setMarksChange(''); }}
                          className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg" title="Add note">
                          <MessageSquare className="w-4 h-4 text-gray-500" />
                        </button>
                        <button onClick={() => { if (confirm('Mark as resolved?')) resolveMutation.mutate(entry._id); }}
                          className="p-1.5 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg" title="Resolve">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Add Note Modal */}
      <AnimatePresence>
        {noteModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setNoteModal(null)}>
            <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
              onClick={e => e.stopPropagation()}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-2xl">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Add Progress Note</h3>
              <div className="space-y-3">
                <textarea value={noteText} onChange={e => setNoteText(e.target.value)} rows={3} placeholder="Progress update..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
                <input type="number" value={marksChange} onChange={e => setMarksChange(e.target.value)} placeholder="Marks change (e.g., +5)"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div className="mt-4 flex justify-end gap-2">
                <button onClick={() => setNoteModal(null)} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
                <button onClick={() => addNoteMutation.mutate(noteModal)} disabled={!noteText || addNoteMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:bg-gray-400">
                  {addNoteMutation.isPending ? 'Saving...' : 'Save Note'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RemedialManagement;
