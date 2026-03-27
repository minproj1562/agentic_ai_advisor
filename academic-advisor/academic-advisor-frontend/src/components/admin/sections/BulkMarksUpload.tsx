import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Download, FileSpreadsheet, CheckCircle2, XCircle,
  AlertTriangle, Loader2, Eye, Save, RefreshCw, FileText,
  Users, BookOpen, ArrowRight, ChevronDown, ChevronUp, Info
} from 'lucide-react';
import toast from 'react-hot-toast';
import apiClient from '../../../services/api.service';
import { auth } from '../../../services/firebase.config';

// ═══════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════

interface MatchedStudent {
  roll_number: string;
  student_name: string;
  profile_name: string;
  user_id: string;
  branch: string;
  current_cgpa: number;
  preview_sgpa: number;
  credits_earned: number;
  total_credits: number;
  subjects_count: number;
  subjects: any[];
  errors: string[];
  warnings: string[];
  has_errors: boolean;
  has_existing_semester?: boolean;
  updated_cgpa?: number;
  status?: string;
}

interface UploadResponse {
  success: boolean;
  mode: 'preview' | 'save';
  metadata: {
    format_detected: string;
    total_rows: number;
    semester: number;
    branch: string;
    subjects_in_curriculum: number;
  };
  upload_id: string;
  total_rows: number;
  matched_students: number;
  unmatched_students: number;
  updated_students: number;
  created_students: number;  // Added this field
  failed_updates: number;
  skipped_students: number;
  matched_details: MatchedStudent[];
  unmatched_roll_numbers: string[];
  errors: { roll_number: string; errors?: string[]; error?: string }[];
  warnings: string[];
  csv_data: string;
  semester: number;  // Added this field
  branch: string;    // Added this field
  academic_year: string;  // Added this field
}

// ═══════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════

const BulkMarksUpload: React.FC = () => {
  // ── Form state ──
  const [semester, setSemester] = useState(5);
  const [branch, setBranch] = useState('IT');
  const [academicYear, setAcademicYear] = useState('2024-25');
  const [admissionYear, setAdmissionYear] = useState(2022);
  const [overwrite, setOverwrite] = useState(true);
  const [templateFormat, setTemplateFormat] = useState<'wide' | 'long'>('wide');
  const [prefillStudents, setPrefillStudents] = useState(true);
  const [studentCount, setStudentCount] = useState<number | null>(null);

  // ── File state ──
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Process state ──
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [previewData, setPreviewData] = useState<UploadResponse | null>(null);
  const [saveResult, setSaveResult] = useState<UploadResponse | null>(null);
  const [step, setStep] = useState<'config' | 'preview' | 'result'>('config');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const branches = ['IT', 'COMP', 'EXTC', 'MECH', 'ELEC', 'CSE'];

  // ── Helpers ──
  const getToken = async () => {
    const u = auth.currentUser;
    return u ? u.getIdToken(true) : null;
  };

  const gradeColor = (grade: string) => {
    const map: Record<string, string> = {
      O: 'text-green-700 bg-green-100', 'A+': 'text-green-600 bg-green-50',
      A: 'text-blue-700 bg-blue-100', 'B+': 'text-blue-600 bg-blue-50',
      B: 'text-yellow-700 bg-yellow-100', C: 'text-yellow-600 bg-yellow-50',
      P: 'text-orange-700 bg-orange-100', F: 'text-red-700 bg-red-100',
    };
    return map[grade] || 'text-gray-600 bg-gray-100';
  };

  const toggleRow = (roll: string) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      next.has(roll) ? next.delete(roll) : next.add(roll);
      return next;
    });
  };

  // ── Download Template ──
  const handleDownloadTemplate = async () => {
    try {
      setDownloading(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }

      const params = new URLSearchParams({
        semester: semester.toString(),
        branch,
        academic_year: academicYear,
        admission_year: admissionYear.toString(),
        prefill_students: prefillStudents.toString(),
      });

      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/template?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to download template');
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `marks_sem${semester}_${branch}_${academicYear.replace('-', '_')}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(prefillStudents 
        ? 'Template downloaded with student data pre-filled!' 
        : 'Template downloaded!'
      );
    } catch (e) {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  // ── Fetch student count for preview ──
  const fetchStudentCount = async () => {
    try {
      const token = await getToken();
      if (!token) {
        console.warn('No auth token available for student count fetch');
        setStudentCount(null);
        return;
      }
      
      const url = `http://localhost:8000/api/v1/admin/bulk-marks/students?branch=${branch}&admission_year=${admissionYear}`;
      console.log('Fetching student count from:', url);
      
      const res = await fetch(url, { 
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        } 
      });
      
      if (res.ok) {
        const data = await res.json();
        setStudentCount(data.total);
      } else {
        const errorText = await res.text();
        console.error('Failed to fetch student count:', res.status, errorText);
        setStudentCount(null);
      }
    } catch (error) {
      console.error('Error fetching student count:', error);
      setStudentCount(null);
    }
  };

  // Add useEffect to fetch student count when branch/admission year changes
  React.useEffect(() => {
    if (branch && admissionYear) {
      fetchStudentCount();
    }
  }, [branch, admissionYear]);

  // ── File Drop / Select ──
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const files = e.dataTransfer.files;
    if (files?.[0]) validateAndSetFile(files[0]);
  }, []);

  const validateAndSetFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['xls', 'xlsx', 'csv'].includes(ext || '')) {
      toast.error('Only .xlsx, .xls, or .csv files allowed');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large (max 10 MB)');
      return;
    }
    setSelectedFile(file);
    setPreviewData(null);
    setSaveResult(null);
    setStep('config');
  };

  // ── Upload & Preview ──
  const handlePreview = async () => {
    if (!selectedFile) { toast.error('Select a file first'); return; }
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }

      const fd = new FormData();
      fd.append('file', selectedFile);
      fd.append('semester', semester.toString());
      fd.append('branch', branch);
      fd.append('academic_year', academicYear);
      fd.append('admission_year', admissionYear.toString());
      fd.append('save', 'false');
      fd.append('overwrite', overwrite.toString());

      const res = await fetch('http://localhost:8000/api/v1/admin/bulk-marks/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });

      const data: UploadResponse = await res.json();
      if (!res.ok) {
        toast.error((data as any).detail || 'Preview failed');
        return;
      }

      setPreviewData(data);
      setStep('preview');
      toast.success(`Parsed ${data.total_rows} students — ${data.matched_students} matched`);
    } catch (e: any) {
      toast.error(e.message || 'Preview failed');
    } finally {
      setLoading(false);
    }
  };

  // ── Confirm & Save ──
  const handleSave = async () => {
    if (!selectedFile) return;
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;

      const fd = new FormData();
      fd.append('file', selectedFile);
      fd.append('semester', semester.toString());
      fd.append('branch', branch);
      fd.append('academic_year', academicYear);
      fd.append('admission_year', admissionYear.toString());
      fd.append('save', 'true');
      fd.append('overwrite', overwrite.toString());

      const res = await fetch('http://localhost:8000/api/v1/admin/bulk-marks/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });

      const data: UploadResponse = await res.json();
      if (!res.ok) {
        toast.error((data as any).detail || 'Save failed');
        return;
      }

      setSaveResult(data);
      setStep('result');
      toast.success(`✅ ${data.updated_students + data.created_students} students processed!`);
    } catch (e: any) {
      toast.error(e.message || 'Save failed');
    } finally {
      setLoading(false);
    }
  };

  // ── Download CSV ──
  const handleDownloadCSV = () => {
    const csv = previewData?.csv_data || saveResult?.csv_data;
    if (!csv) return;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `marks_sem${semester}_${branch}_converted.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('CSV downloaded');
  };

  // ── Reset ──
  const reset = () => {
    setSelectedFile(null);
    setPreviewData(null);
    setSaveResult(null);
    setStep('config');
    setExpandedRows(new Set());
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ═══════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Header ── */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <FileSpreadsheet className="w-7 h-7" /> Bulk Marks Upload
        </h1>
        <p className="mt-1 text-indigo-100">
          Upload an XLS/XLSX/CSV of student marks → auto-match roll numbers → save semester records
        </p>
        <div className="mt-3 flex gap-2 text-sm">
          <span className="px-3 py-1 bg-white/20 rounded-full">
            Step 1: Configure &amp; Download Template
          </span>
          <ArrowRight className="w-4 h-4 mt-1" />
          <span className={`px-3 py-1 rounded-full ${step === 'preview' ? 'bg-white/30 font-bold' : 'bg-white/10'}`}>
            Step 2: Upload &amp; Preview
          </span>
          <ArrowRight className="w-4 h-4 mt-1" />
          <span className={`px-3 py-1 rounded-full ${step === 'result' ? 'bg-white/30 font-bold' : 'bg-white/10'}`}>
            Step 3: Confirm &amp; Save
          </span>
        </div>
      </div>

      {/* ── Configuration ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-600" /> Configuration
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Semester *</label>
            <select value={semester} onChange={e => setSemester(+e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white">
              {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Branch *</label>
            <select value={branch} onChange={e => setBranch(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white">
              {branches.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Academic Year *</label>
            <input type="text" value={academicYear} onChange={e => setAcademicYear(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="2024-25" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admission Year *</label>
            <input type="number" value={admissionYear} onChange={e => setAdmissionYear(+e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              min={2018} max={2030} />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={overwrite} onChange={e => setOverwrite(e.target.checked)}
              className="rounded text-indigo-600" />
            <span className="text-gray-700 dark:text-gray-300">Overwrite existing semester data</span>
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={prefillStudents} onChange={e => setPrefillStudents(e.target.checked)}
              className="rounded text-green-600" />
            <span className="text-gray-700 dark:text-gray-300">
              Pre-fill student roll numbers
              {prefillStudents && studentCount !== null && (
                <span className="ml-1 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-bold">
                  {studentCount} students found
                </span>
              )}
              {prefillStudents && studentCount === 0 && (
                <span className="ml-1 px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-bold">
                  No students found — check branch &amp; admission year
                </span>
              )}
            </span>
          </label>
        </div>

        <div className="mt-4 flex gap-3">
          <button onClick={handleDownloadTemplate} disabled={downloading}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 font-medium">
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Download Template
          </button>
        </div>
      </div>

      {/* ── File Upload ── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-indigo-600" /> Upload Marks File
        </h2>

        <div
          onDragEnter={handleDrag} onDragLeave={handleDrag}
          onDragOver={handleDrag} onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
            ${dragActive
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
              : selectedFile
                ? 'border-green-400 bg-green-50 dark:bg-green-900/20'
                : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700/50'
            }`}
        >
          <input ref={fileInputRef} type="file" accept=".xls,.xlsx,.csv" className="hidden"
            onChange={e => e.target.files?.[0] && validateAndSetFile(e.target.files[0])} />

          {selectedFile ? (
            <div className="flex flex-col items-center gap-2">
              <FileSpreadsheet className="w-12 h-12 text-green-600" />
              <p className="font-semibold text-green-700 dark:text-green-400">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              <button onClick={(e) => { e.stopPropagation(); reset(); }}
                className="text-sm text-red-600 hover:underline mt-1">Remove file</button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Upload className="w-12 h-12 text-gray-400" />
              <p className="font-medium text-gray-600 dark:text-gray-300">
                Drag &amp; drop your marks file here, or click to browse
              </p>
              <p className="text-sm text-gray-400">Supports .xlsx, .xls, .csv (max 10 MB)</p>
            </div>
          )}
        </div>

        {selectedFile && step === 'config' && (
          <div className="mt-4 flex gap-3">
            <button onClick={handlePreview} disabled={loading}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 font-medium">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
              Upload &amp; Preview
            </button>
          </div>
        )}
      </div>

      {/* ── Preview ── */}
      <AnimatePresence>
        {step === 'preview' && previewData && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="space-y-4">

            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { label: 'Total Rows', value: previewData.total_rows, icon: FileText, color: 'blue' },
                { label: 'Matched', value: previewData.matched_students, icon: CheckCircle2, color: 'green' },
                { label: 'Unmatched', value: previewData.unmatched_students, icon: XCircle, color: 'red' },
                { label: 'With Errors', value: previewData.matched_details.filter(d => d.has_errors).length, icon: AlertTriangle, color: 'yellow' },
                { label: 'Format', value: previewData.metadata.format_detected, icon: FileSpreadsheet, color: 'purple' },
              ].map((c, i) => (
                <div key={i} className={`bg-${c.color}-50 dark:bg-${c.color}-900/20 border border-${c.color}-200 dark:border-${c.color}-800 rounded-lg p-4`}>
                  <div className="flex items-center gap-2">
                    <c.icon className={`w-5 h-5 text-${c.color}-600`} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">{c.label}</span>
                  </div>
                  <p className={`text-2xl font-bold text-${c.color}-700 dark:text-${c.color}-400 mt-1`}>{c.value}</p>
                </div>
              ))}
            </div>

            {/* Unmatched warning */}
            {previewData.unmatched_roll_numbers.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <span className="font-semibold text-yellow-800 dark:text-yellow-400">
                    Unregistered Students ({previewData.unmatched_roll_numbers.length})
                  </span>
                </div>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  These students are not registered yet. Their marks will be saved as pending and automatically linked when they register:
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {previewData.unmatched_roll_numbers.map(r => (
                    <span key={r} className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-mono">{r}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Matched students table */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border overflow-hidden">
              <div className="p-4 border-b flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <Users className="w-5 h-5 text-green-600" />
                  Matched Students ({previewData.matched_details.length})
                </h3>
                <button onClick={handleDownloadCSV}
                  className="px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-1">
                  <FileText className="w-4 h-4" /> Download CSV
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      {['Roll No', 'Student', 'Subjects', 'Preview SGPA', 'Current CGPA', 'Credits', 'Status', ''].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y dark:divide-gray-700">
                    {previewData.matched_details.map((stu) => (
                      <React.Fragment key={stu.roll_number}>
                        <tr className={`hover:bg-gray-50 dark:hover:bg-gray-750 ${stu.has_errors ? 'bg-red-50/50 dark:bg-red-900/10' : ''}`}>
                          <td className="px-4 py-3 font-mono font-medium">{stu.roll_number}</td>
                          <td className="px-4 py-3">
                            <p className="font-medium">{stu.profile_name || stu.student_name}</p>
                            <p className="text-xs text-gray-500">{stu.branch}</p>
                          </td>
                          <td className="px-4 py-3">{stu.subjects_count}</td>
                          <td className="px-4 py-3">
                            <span className="text-lg font-bold text-indigo-600">{stu.preview_sgpa.toFixed(2)}</span>
                          </td>
                          <td className="px-4 py-3 text-gray-600">{stu.current_cgpa.toFixed(2)}</td>
                          <td className="px-4 py-3">{stu.credits_earned}/{stu.total_credits}</td>
                          <td className="px-4 py-3">
                            {stu.has_errors ? (
                              <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">Errors</span>
                            ) : stu.has_existing_semester ? (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs">Will Overwrite</span>
                            ) : (
                              <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">Ready</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <button onClick={() => toggleRow(stu.roll_number)}
                              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
                              {expandedRows.has(stu.roll_number) ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </td>
                        </tr>

                        {/* Expanded subjects */}
                        {expandedRows.has(stu.roll_number) && (
                          <tr>
                            <td colSpan={8} className="px-4 py-3 bg-gray-50/70 dark:bg-gray-750">
                              {stu.errors.length > 0 && (
                                <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                                  {stu.errors.map((e, i) => <p key={i}>⚠ {e}</p>)}
                                </div>
                              )}
                              {stu.warnings.length > 0 && (
                                <div className="mb-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
                                  {stu.warnings.map((w, i) => <p key={i}>⚡ {w}</p>)}
                                </div>
                              )}
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="text-gray-500">
                                    {['Code', 'Subject', 'Credits', 'Internal', 'External', 'Total', 'Grade', 'Points'].map(h => (
                                      <th key={h} className="py-1 px-2 text-left">{h}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {stu.subjects.map((s: any, i: number) => (
                                    <tr key={i} className="border-t border-gray-200 dark:border-gray-600">
                                      <td className="py-1 px-2 font-mono">{s.subject_code}</td>
                                      <td className="py-1 px-2">{s.subject_name}</td>
                                      <td className="py-1 px-2 text-center">{s.credits}</td>
                                      <td className="py-1 px-2 text-center">{s.internal_marks}/{s.internal_max}</td>
                                      <td className="py-1 px-2 text-center">{s.external_marks}/{s.external_max}</td>
                                      <td className="py-1 px-2 text-center font-bold">{s.total_marks}</td>
                                      <td className="py-1 px-2 text-center">
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${gradeColor(s.grade)}`}>{s.grade}</span>
                                      </td>
                                      <td className="py-1 px-2 text-center">{s.grade_points}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-4">
              <button onClick={reset}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Start Over
              </button>
              <div className="flex items-center gap-3">
                <p className="text-sm text-gray-500">
                  {previewData.total_rows} students ready to save (including {previewData.unmatched_students} pending)
                </p>
                <button onClick={handleSave} disabled={loading || previewData.total_rows === 0}
                  className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Confirm &amp; Save All
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Save Result ── */}
      <AnimatePresence>
        {step === 'result' && saveResult && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="space-y-4">

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
                <div>
                  <h3 className="text-xl font-bold text-green-800 dark:text-green-400">Upload Complete!</h3>
                  <p className="text-green-700 dark:text-green-300">
                    Semester {saveResult.semester} marks saved for {saveResult.updated_students + saveResult.created_students} students
                  </p>
                </div>
              </div>

              {/* Save Result summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { label: 'Updated', value: saveResult.updated_students, icon: CheckCircle2, color: 'green' },
                  { label: 'Saved (Pending)', value: saveResult.created_students, icon: Users, color: 'blue' },
                  { label: 'Total Processed', value: saveResult.unmatched_students, icon: FileText, color: 'indigo' },
                  { label: 'Failed', value: saveResult.failed_updates, icon: XCircle, color: 'red' },
                  { label: 'Skipped', value: saveResult.skipped_students, icon: AlertTriangle, color: 'yellow' },
                ].map((c, i) => (
                  <div key={i} className={`bg-${c.color}-50 dark:bg-${c.color}-900/20 border border-${c.color}-200 dark:border-${c.color}-800 rounded-lg p-4`}>
                    <div className="flex items-center gap-2">
                      <c.icon className={`w-5 h-5 text-${c.color}-600`} />
                      <span className="text-sm text-gray-600 dark:text-gray-400">{c.label}</span>
                    </div>
                    <p className={`text-2xl font-bold text-${c.color}-700 dark:text-${c.color}-400 mt-1`}>{c.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Add info about pending marks */}
            {saveResult.created_students > 0 && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-blue-800 dark:text-blue-300">
                      {saveResult.created_students} Pending Student Records Created
                    </p>
                    <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                      Marks have been saved for students who haven't registered yet. 
                      When these students create their accounts with matching roll numbers, 
                      their marks will be automatically linked to their profiles.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Updated students details */}
            {saveResult.matched_details.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border overflow-hidden">
                <div className="p-4 border-b">
                  <h3 className="font-semibold">Processed Students</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        {['Roll No', 'Name', 'SGPA', 'Updated CGPA', 'Subjects', 'Credits', 'Status'].map(h => (
                          <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y dark:divide-gray-700">
                      {saveResult.matched_details.map((s, i) => (
                        <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                          <td className="px-4 py-3 font-mono">{s.roll_number}</td>
                          <td className="px-4 py-3 font-medium">{s.student_name}</td>
                          <td className="px-4 py-3">
                            <span className="text-lg font-bold text-indigo-600">{(s as any).sgpa?.toFixed(2) || 'N/A'}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-lg font-bold text-green-600">
                              {(s as any).updated_cgpa?.toFixed(2) || 'Pending'}
                            </span>
                          </td>
                          <td className="px-4 py-3">{s.subjects_count || (s as any).subjects_count || 0}</td>
                          <td className="px-4 py-3">{s.credits_earned || 0}</td>
                          <td className="px-4 py-3">
                            {s.status === 'updated' ? (
                              <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">Updated</span>
                            ) : (
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">Pending</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Errors */}
            {saveResult.errors.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg p-4">
                <h3 className="font-semibold text-red-800 mb-2">Errors ({saveResult.errors.length})</h3>
                {saveResult.errors.map((e, i) => (
                  <p key={i} className="text-sm text-red-700">
                    <strong>{e.roll_number}:</strong> {e.errors?.join(', ') || e.error}
                  </p>
                ))}
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={reset}
                className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Upload Another File
              </button>
              <button onClick={handleDownloadCSV}
                className="px-5 py-2.5 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2">
                <FileText className="w-4 h-4" /> Download CSV
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Info box ── */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-semibold mb-1">How it works</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Select semester, branch, and admission year above</li>
              <li>Download the pre-filled XLSX template (correct subjects auto-loaded from curriculum)</li>
              <li>Fill in roll numbers and marks in the template</li>
              <li>Upload the filled file — it gets converted to CSV internally</li>
              <li>Preview shows matched students with computed grades and SGPA</li>
              <li>Confirm to save — all students processed (registered students updated, unregistered saved as pending)</li>
              <li>Unregistered students' marks will be automatically linked when they create accounts</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkMarksUpload;