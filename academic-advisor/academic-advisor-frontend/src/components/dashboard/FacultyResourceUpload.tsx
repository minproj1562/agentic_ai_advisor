// academic-advisor-frontend/src/components/dashboard/FacultyResourceUpload.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload, Link2, FileText, Video, BookOpen, Trash2, Plus,
  ExternalLink, Download, Eye, Filter, X, File
} from 'lucide-react';
import apiClient from '../../services/api.service';
import toast from 'react-hot-toast';

const TYPE_ICONS: Record<string, any> = {
  link: Link2, video: Video, pdf: FileText, ppt: FileText,
  doc: FileText, book: BookOpen, other: File,
};

const TYPE_COLORS: Record<string, string> = {
  link: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  video: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
  pdf: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400',
  ppt: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
  doc: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
  book: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
  other: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
};

const SEMESTERS = [0, 1, 2, 3, 4, 5, 6, 7, 8];
const SUBJECTS = [
  'Engineering Mathematics-III', 'Engineering Mathematics-IV',
  'Data Structures & Analysis', 'Database Management System',
  'Computer Network', 'Operating System', 'Software Engineering',
  'Automata Theory', 'Artificial Intelligence', 'Internet of Things',
  'Digital Logic Design & Analysis', 'Computer Organization & Architecture',
  'Microcontroller and Embedded Systems', 'Cryptography & Network Security',
];

const FacultyResourceUpload: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formMode, setFormMode] = useState<'link' | 'upload'>('link');
  const [filterSem, setFilterSem] = useState<number | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [resourceType, setResourceType] = useState('link');
  const [url, setUrl] = useState('');
  const [semester, setSemester] = useState(0);
  const [subject, setSubject] = useState('');
  const [tags, setTags] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['faculty-resources-my'],
    queryFn: async () => {
      const res = await apiClient.get('/faculty/resources/my');
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/faculty/resources', {
        title, description, resource_type: resourceType, url,
        semester, branch: 'IT', subject,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success('Resource added!');
      queryClient.invalidateQueries({ queryKey: ['faculty-resources-my'] });
      resetForm();
    },
    onError: () => toast.error('Failed to add resource'),
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected');
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('description', description);
      formData.append('semester', semester.toString());
      formData.append('branch', 'IT');
      formData.append('subject', subject);
      formData.append('tags', tags);
      const res = await apiClient.post('/faculty/resources/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success('File uploaded!');
      queryClient.invalidateQueries({ queryKey: ['faculty-resources-my'] });
      resetForm();
    },
    onError: () => toast.error('Upload failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/faculty/resources/${id}`);
    },
    onSuccess: () => {
      toast.success('Resource deleted');
      queryClient.invalidateQueries({ queryKey: ['faculty-resources-my'] });
    },
  });

  const resetForm = () => {
    setTitle(''); setDescription(''); setResourceType('link');
    setUrl(''); setSemester(0); setSubject(''); setTags('');
    setFile(null); setShowForm(false);
  };

  const filteredResources = (data?.resources || []).filter((r: any) =>
    filterSem === null || r.semester === filterSem || r.semester === 0
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Learning Resources</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? 'Cancel' : 'Add Resource'}
        </button>
      </div>

      {/* Add Resource Form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg overflow-hidden"
          >
            {/* Mode Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setFormMode('link')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${formMode === 'link' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}
              >
                <Link2 className="w-4 h-4" /> Add Link
              </button>
              <button
                onClick={() => setFormMode('upload')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${formMode === 'upload' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}
              >
                <Upload className="w-4 h-4" /> Upload File
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Title *</label>
                <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Resource title"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Subject</label>
                <select value={subject} onChange={e => setSubject(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm">
                  <option value="">All Subjects</option>
                  {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
                <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>

              {formMode === 'link' ? (
                <>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">URL *</label>
                    <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://..."
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
                    <select value={resourceType} onChange={e => setResourceType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm">
                      {['link', 'video', 'book', 'other'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                    </select>
                  </div>
                </>
              ) : (
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-gray-500 mb-1">File (PDF, PPT, DOC) *</label>
                  <input type="file" accept=".pdf,.ppt,.pptx,.doc,.docx"
                    onChange={e => setFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm" />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Semester</label>
                <select value={semester} onChange={e => setSemester(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm">
                  <option value={0}>All Semesters</option>
                  {[3, 4, 5, 6, 7, 8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Tags (comma-separated)</label>
                <input value={tags} onChange={e => setTags(e.target.value)} placeholder="notes, important"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => formMode === 'link' ? createMutation.mutate() : uploadMutation.mutate()}
                disabled={!title || (formMode === 'link' ? !url : !file) || createMutation.isPending || uploadMutation.isPending}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:bg-gray-400 transition-colors"
              >
                {(createMutation.isPending || uploadMutation.isPending) ? 'Saving...' : formMode === 'link' ? 'Add Link' : 'Upload File'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filter */}
      <div className="flex gap-1 flex-wrap">
        <button onClick={() => setFilterSem(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filterSem === null ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>
          All
        </button>
        {[3, 4, 5, 6, 7].map(s => (
          <button key={s} onClick={() => setFilterSem(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filterSem === s ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>
            Sem {s}
          </button>
        ))}
      </div>

      {/* Resource List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />)}
        </div>
      ) : filteredResources.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <BookOpen className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>No resources yet. Add your first resource!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredResources.map((r: any, i: number) => {
            const Icon = TYPE_ICONS[r.resource_type] || File;
            const colorCls = TYPE_COLORS[r.resource_type] || TYPE_COLORS.other;
            return (
              <motion.div
                key={r._id || i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 flex items-center gap-4"
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${colorCls}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm truncate">{r.title}</h4>
                  <p className="text-xs text-gray-500 truncate">{r.subject || 'General'} • Sem {r.semester === 0 ? 'All' : r.semester}</p>
                </div>
                <div className="flex items-center gap-2">
                  {(r.url || r.file_url) && (
                    <a href={r.url || r.file_url} target="_blank" rel="noopener noreferrer"
                      className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                      <ExternalLink className="w-4 h-4 text-gray-500" />
                    </a>
                  )}
                  <button onClick={() => { if (confirm('Delete this resource?')) deleteMutation.mutate(r._id); }}
                    className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg">
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FacultyResourceUpload;
