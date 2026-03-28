// academic-advisor-frontend/src/components/admin/sections/BulkMarksUpload.tsx
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Download, FileSpreadsheet, CheckCircle2, XCircle,
  AlertTriangle, Loader2, Eye, Save, RefreshCw, FileText,
  Users, BookOpen, ArrowRight, ChevronDown, ChevronUp, Info,
  UserPlus, FolderDown, Package, Trash2, Search, Edit3, 
  PenTool, Check, X
} from 'lucide-react';
import toast from 'react-hot-toast';
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
  created_students: number;
  failed_updates: number;
  skipped_students: number;
  matched_details: MatchedStudent[];
  unmatched_roll_numbers: string[];
  errors: { roll_number: string; errors?: string[]; error?: string }[];
  warnings: string[];
  csv_data: string;
  semester: number;
  branch: string;
  academic_year: string;
}

interface StudentSummaryGroup {
  branch: string;
  admission_year: number;
  count: number;
  students: { roll_number: string; name: string; current_semester: number; cgpa: number }[];
}

interface NewStudent {
  roll_number: string;
  name: string;
  seat_number: string;
  email: string;
}

interface SubjectMarks {
  subject_code: string;
  subject_name: string;
  credits: number;
  internal_marks: number;
  external_marks: number;
  total_marks: number;
  grade: string;
  grade_points: number;
  is_elective: boolean;
  is_practical: boolean;
}

interface SemesterMarksStudent {
  roll_number: string;
  name: string;
  user_id: string;
  is_placeholder: boolean;
  has_marks: boolean;
  semester_data: {
    semester_number: number;
    academic_year: string;
    sgpa: number;
    total_credits: number;
    credits_earned: number;
    is_complete: boolean;
    subjects: SubjectMarks[];
  } | null;
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
  const [prefillStudents, setPrefillStudents] = useState(true);
  const [studentCount, setStudentCount] = useState<number | null>(null);

  // ── Tab state ──
  const [activeTab, setActiveTab] = useState<'upload' | 'templates' | 'students' | 'edit'>('upload');

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

  // ── Student management state ──
  const [studentSummary, setStudentSummary] = useState<{ total_students: number; groups: StudentSummaryGroup[] } | null>(null);
  const [newStudents, setNewStudents] = useState<NewStudent[]>([{ roll_number: '', name: '', seat_number: '', email: '' }]);
  const [addingStudents, setAddingStudents] = useState(false);

  // ── Template batch state ──
  const [selectedSemesters, setSelectedSemesters] = useState<number[]>([1, 2, 3, 4, 5]);
  const [downloadingBatch, setDownloadingBatch] = useState(false);

  // ── Edit Marks state ──
  const [semesterMarks, setSemesterMarks] = useState<SemesterMarksStudent[]>([]);
  const [loadingMarks, setLoadingMarks] = useState(false);
  const [editingStudent, setEditingStudent] = useState<string | null>(null);
  const [editSubjects, setEditSubjects] = useState<SubjectMarks[]>([]);
  const [savingEdit, setSavingEdit] = useState(false);
  const [expandedEditRows, setExpandedEditRows] = useState<Set<string>>(new Set());

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

  // ── Fetch student count ──
  const fetchStudentCount = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/students?branch=${branch}&admission_year=${admissionYear}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setStudentCount(data.total);
      }
    } catch (error) {
      console.error('Error fetching student count:', error);
    }
  };

  // ── Fetch student summary ──
  const fetchStudentSummary = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const params = new URLSearchParams();
      if (branch) params.append('branch', branch);
      if (admissionYear) params.append('admission_year', admissionYear.toString());
      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/students/summary?${params}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setStudentSummary(data);
      }
    } catch (error) {
      console.error('Error fetching student summary:', error);
    }
  };

  // ── Fetch semester marks (for edit tab) ──
  const fetchSemesterMarks = async () => {
    try {
      setLoadingMarks(true);
      const token = await getToken();
      if (!token) return;

      const params = new URLSearchParams({
        semester: semester.toString(),
        branch,
        admission_year: admissionYear.toString(),
      });

      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/semester-marks?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (res.ok) {
        const data = await res.json();
        setSemesterMarks(data.students || []);
        toast.success(
          `Loaded ${data.students_with_marks} students with marks, ` +
          `${data.students_without_marks} without`
        );
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to load marks');
      }
    } catch (e) {
      toast.error('Failed to load marks');
    } finally {
      setLoadingMarks(false);
    }
  };

  // ── Save edited marks ──
  const handleSaveEdit = async (rollNumber: string) => {
    try {
      setSavingEdit(true);
      const token = await getToken();
      if (!token) return;

      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/student-marks/${encodeURIComponent(rollNumber)}`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            semester,
            academic_year: academicYear,
            subjects: editSubjects.map(s => ({
              subject_code: s.subject_code,
              internal_marks: s.internal_marks,
              external_marks: s.external_marks,
            })),
          }),
        }
      );

      if (res.ok) {
        const data = await res.json();
        toast.success(
          `Updated ${rollNumber}: SGPA ${data.updated_sgpa}, CGPA ${data.updated_cgpa}`
        );
        setEditingStudent(null);
        setEditSubjects([]);
        await fetchSemesterMarks();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to save');
      }
    } catch (e) {
      toast.error('Save failed');
    } finally {
      setSavingEdit(false);
    }
  };

  // ── Start editing a student ──
  const startEditing = (student: SemesterMarksStudent) => {
    if (!student.semester_data) return;
    setEditingStudent(student.roll_number);
    setEditSubjects(student.semester_data.subjects.map(s => ({ ...s })));
  };

  const cancelEditing = () => {
    setEditingStudent(null);
    setEditSubjects([]);
  };

  const updateEditSubject = (idx: number, field: 'internal_marks' | 'external_marks', value: number) => {
    const updated = [...editSubjects];
    updated[idx][field] = value;
    updated[idx].total_marks = updated[idx].internal_marks + updated[idx].external_marks;
    setEditSubjects(updated);
  };

  useEffect(() => {
    if (branch && admissionYear) fetchStudentCount();
  }, [branch, admissionYear]);

  useEffect(() => {
    if (activeTab === 'students') fetchStudentSummary();
    if (activeTab === 'edit') fetchSemesterMarks();
  }, [activeTab, branch, admissionYear, semester]);

  // ── Download Template ──
  const handleDownloadTemplate = async () => {
    try {
      setDownloading(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }
      const params = new URLSearchParams({
        semester: semester.toString(), branch,
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
      toast.success('Template downloaded!');
    } catch (e) { toast.error('Download failed'); }
    finally { setDownloading(false); }
  };

  // ── Download template with EXISTING marks ──
  const handleDownloadMarksTemplate = async () => {
    try {
      setDownloading(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }
      const params = new URLSearchParams({
        semester: semester.toString(), branch,
        academic_year: academicYear,
        admission_year: admissionYear.toString(),
      });
      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/download-marks-template?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed');
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `marks_edit_sem${semester}_${branch}_${academicYear.replace('-', '_')}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Template with existing marks downloaded! Edit and re-upload.');
    } catch (e) { toast.error('Download failed'); }
    finally { setDownloading(false); }
  };

  // ── Download All Templates (ZIP) ──
  const handleDownloadAllTemplates = async () => {
    try {
      setDownloadingBatch(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }
      const params = new URLSearchParams({
        branch, academic_year: academicYear,
        admission_year: admissionYear.toString(),
      });
      if (selectedSemesters.length > 0) params.append('semesters', selectedSemesters.join(','));
      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/templates/all?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed');
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `marks_templates_${branch}_${admissionYear}_${academicYear.replace('-','_')}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${selectedSemesters.length} semester templates!`);
    } catch (e) { toast.error('Download failed'); }
    finally { setDownloadingBatch(false); }
  };

  // ── Export Students Excel ──
  const handleExportStudents = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }
      const params = new URLSearchParams({ branch });
      if (admissionYear) params.append('admission_year', admissionYear.toString());
      const res = await fetch(
        `http://localhost:8000/api/v1/admin/bulk-marks/students/export?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) { toast.error('Failed to export students'); return; }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `students_${branch}_${admissionYear || 'all'}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Student list exported!');
    } catch (e) { toast.error('Export failed'); }
    finally { setLoading(false); }
  };

  // ── Add New Students ──
  const handleAddStudents = async () => {
    const validStudents = newStudents.filter(s => s.roll_number.trim() && s.name.trim());
    if (validStudents.length === 0) { toast.error('Add at least one student'); return; }
    try {
      setAddingStudents(true);
      const token = await getToken();
      if (!token) { toast.error('Not authenticated'); return; }
      const res = await fetch('http://localhost:8000/api/v1/admin/bulk-marks/students/add', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ students: validStudents, branch, admission_year: admissionYear })
      });
      const data = await res.json();
      if (!res.ok) { toast.error(data.detail || 'Failed'); return; }
      toast.success(`Added ${data.added} students! (${data.skipped} skipped, ${data.errors} errors)`);
      setNewStudents([{ roll_number: '', name: '', seat_number: '', email: '' }]);
      fetchStudentCount();
      fetchStudentSummary();
    } catch (e: any) { toast.error(e.message || 'Failed'); }
    finally { setAddingStudents(false); }
  };

  const addStudentRow = () => setNewStudents([...newStudents, { roll_number: '', name: '', seat_number: '', email: '' }]);
  const removeStudentRow = (i: number) => { if (newStudents.length > 1) setNewStudents(newStudents.filter((_, idx) => idx !== i)); };
  const updateStudentRow = (i: number, field: keyof NewStudent, value: string) => {
    const u = [...newStudents]; u[i][field] = value; setNewStudents(u);
  };

  // ── File Handling ──
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setDragActive(false);
    if (e.dataTransfer.files?.[0]) validateAndSetFile(e.dataTransfer.files[0]);
  }, []);

  const validateAndSetFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['xls', 'xlsx', 'csv'].includes(ext || '')) { toast.error('Only .xlsx/.xls/.csv'); return; }
    if (file.size > 10 * 1024 * 1024) { toast.error('Max 10 MB'); return; }
    setSelectedFile(file); setPreviewData(null); setSaveResult(null); setStep('config');
  };

  // ── Upload & Preview ──
  const handlePreview = async () => {
    if (!selectedFile) { toast.error('Select a file'); return; }
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
        method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd,
      });
      const data: UploadResponse = await res.json();
      if (!res.ok) { toast.error((data as any).detail || 'Preview failed'); return; }
      setPreviewData(data); setStep('preview');
      toast.success(`Parsed ${data.total_rows} — ${data.matched_students} matched`);
    } catch (e: any) { toast.error(e.message || 'Preview failed'); }
    finally { setLoading(false); }
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
        method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd,
      });
      const data: UploadResponse = await res.json();
      if (!res.ok) { toast.error((data as any).detail || 'Save failed'); return; }
      setSaveResult(data); setStep('result');
      toast.success(`✅ ${data.updated_students} updated, ${data.created_students} pending`);
    } catch (e: any) { toast.error(e.message || 'Save failed'); }
    finally { setLoading(false); }
  };

  const handleDownloadCSV = () => {
    const csv = previewData?.csv_data || saveResult?.csv_data;
    if (!csv) return;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `marks_sem${semester}_${branch}_converted.csv`;
    a.click(); URL.revokeObjectURL(url);
    toast.success('CSV downloaded');
  };

  const reset = () => {
    setSelectedFile(null); setPreviewData(null); setSaveResult(null);
    setStep('config'); setExpandedRows(new Set());
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ═══════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <FileSpreadsheet className="w-7 h-7" /> Bulk Marks Management
        </h1>
        <p className="mt-1 text-indigo-100">
          Generate templates, upload marks, edit existing marks, and manage students
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        {[
          { id: 'upload', label: 'Upload Marks', icon: Upload },
          { id: 'edit', label: 'View / Edit Marks', icon: Edit3 },
          { id: 'templates', label: 'Generate Templates', icon: FolderDown },
          { id: 'students', label: 'Manage Students', icon: Users },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-3 flex items-center gap-2 font-medium border-b-2 transition-colors whitespace-nowrap
              ${activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════
          TAB: VIEW / EDIT MARKS
      ═══════════════════════════════════════════════════ */}
      {activeTab === 'edit' && (
        <div className="space-y-6">
          {/* Configuration */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-indigo-600" /> View & Edit Marks
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Semester</label>
                <select value={semester} onChange={e => setSemester(+e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Branch</label>
                <select value={branch} onChange={e => setBranch(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {branches.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admission Year</label>
                <input type="number" value={admissionYear} onChange={e => setAdmissionYear(+e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  min={2018} max={2030} />
              </div>
              <div className="flex items-end gap-2">
                <button onClick={fetchSemesterMarks} disabled={loadingMarks}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2">
                  {loadingMarks ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  Load Marks
                </button>
                <button onClick={handleDownloadMarksTemplate} disabled={downloading}
                  className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 disabled:opacity-50 flex items-center gap-2">
                  {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  Export for Edit
                </button>
              </div>
            </div>
          </div>

          {/* Info box */}
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-amber-600 mt-0.5" />
              <div className="text-sm text-amber-800 dark:text-amber-300">
                <p className="font-semibold mb-1">How to Edit Marks</p>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>Inline edit:</strong> Click the edit icon next to any student to modify marks directly</li>
                  <li><strong>Bulk edit:</strong> Click "Export for Edit" to download an Excel template with existing marks, modify in Excel, then re-upload via the Upload tab with "Overwrite" enabled</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Marks Table */}
          {semesterMarks.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border overflow-hidden">
              <div className="p-4 border-b flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm">
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full font-bold">
                    {semesterMarks.filter(s => s.has_marks).length} with marks
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full font-bold">
                    {semesterMarks.filter(s => !s.has_marks).length} without marks
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Roll Number</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Name</th>
                      <th className="px-3 py-3 text-center font-medium text-gray-600 dark:text-gray-300">SGPA</th>
                      <th className="px-3 py-3 text-center font-medium text-gray-600 dark:text-gray-300">Credits</th>
                      <th className="px-3 py-3 text-center font-medium text-gray-600 dark:text-gray-300">Subjects</th>
                      <th className="px-3 py-3 text-center font-medium text-gray-600 dark:text-gray-300">Status</th>
                      <th className="px-3 py-3 text-center font-medium text-gray-600 dark:text-gray-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y dark:divide-gray-700">
                    {semesterMarks.map(student => {
                      const isEditing = editingStudent === student.roll_number;
                      const isExpanded = expandedEditRows.has(student.roll_number);

                      return (
                        <React.Fragment key={student.roll_number}>
                          <tr className={`hover:bg-gray-50 dark:hover:bg-gray-750 ${!student.has_marks ? 'opacity-60' : ''}`}>
                            <td className="px-4 py-3 font-mono font-bold text-sm">{student.roll_number}</td>
                            <td className="px-4 py-3">
                              <div>
                                <span className="font-medium">{student.name}</span>
                                {student.is_placeholder && (
                                  <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                                    Not registered
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-3 py-3 text-center">
                              {student.semester_data ? (
                                <span className="font-bold text-lg">{student.semester_data.sgpa.toFixed(2)}</span>
                              ) : '—'}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {student.semester_data
                                ? `${student.semester_data.credits_earned}/${student.semester_data.total_credits}`
                                : '—'}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {student.semester_data ? student.semester_data.subjects.length : '—'}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {student.has_marks ? (
                                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-bold">
                                  Has Marks
                                </span>
                              ) : (
                                <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full">
                                  No Marks
                                </span>
                              )}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {student.has_marks && (
                                <div className="flex items-center justify-center gap-1">
                                  <button
                                    onClick={() => {
                                      setExpandedEditRows(prev => {
                                        const n = new Set(prev);
                                        n.has(student.roll_number) ? n.delete(student.roll_number) : n.add(student.roll_number);
                                        return n;
                                      });
                                    }}
                                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                    title="View details"
                                  >
                                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                  </button>
                                  <button
                                    onClick={() => startEditing(student)}
                                    className="p-1.5 text-amber-600 hover:bg-amber-50 rounded"
                                    title="Edit marks"
                                  >
                                    <PenTool className="w-4 h-4" />
                                  </button>
                                </div>
                              )}
                            </td>
                          </tr>

                          {/* Expanded row: view or edit subjects */}
                          {(isExpanded || isEditing) && student.semester_data && (
                            <tr>
                              <td colSpan={7} className="px-4 py-4 bg-gray-50 dark:bg-gray-750">
                                {isEditing ? (
                                  <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                      <h4 className="font-semibold text-amber-700 flex items-center gap-2">
                                        <PenTool className="w-4 h-4" />
                                        Editing marks for {student.roll_number}
                                      </h4>
                                      <div className="flex gap-2">
                                        <button onClick={cancelEditing}
                                          className="px-3 py-1.5 border rounded-lg hover:bg-gray-100 flex items-center gap-1 text-sm">
                                          <X className="w-3 h-3" /> Cancel
                                        </button>
                                        <button
                                          onClick={() => handleSaveEdit(student.roll_number)}
                                          disabled={savingEdit}
                                          className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-1 text-sm"
                                        >
                                          {savingEdit ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                          Save Changes
                                        </button>
                                      </div>
                                    </div>
                                    <table className="w-full text-xs border rounded-lg overflow-hidden">
                                      <thead className="bg-amber-50">
                                        <tr>
                                          <th className="px-3 py-2 text-left">Subject</th>
                                          <th className="px-3 py-2 text-center">Credits</th>
                                          <th className="px-3 py-2 text-center">Internal</th>
                                          <th className="px-3 py-2 text-center">External</th>
                                          <th className="px-3 py-2 text-center">Total</th>
                                          <th className="px-3 py-2 text-center">Grade</th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y">
                                        {editSubjects.map((subj, idx) => (
                                          <tr key={idx}>
                                            <td className="px-3 py-2">
                                              <span className="font-medium">{subj.subject_name}</span>
                                              <span className="text-gray-400 ml-1">({subj.subject_code})</span>
                                            </td>
                                            <td className="px-3 py-2 text-center">{subj.credits}</td>
                                            <td className="px-3 py-2 text-center">
                                              <input
                                                type="number"
                                                value={subj.internal_marks}
                                                onChange={e => updateEditSubject(idx, 'internal_marks', parseFloat(e.target.value) || 0)}
                                                className="w-16 px-2 py-1 border rounded text-center text-sm focus:ring-2 focus:ring-amber-500"
                                                step="0.5" min="0"
                                              />
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                              <input
                                                type="number"
                                                value={subj.external_marks}
                                                onChange={e => updateEditSubject(idx, 'external_marks', parseFloat(e.target.value) || 0)}
                                                className="w-16 px-2 py-1 border rounded text-center text-sm focus:ring-2 focus:ring-amber-500"
                                                step="0.5" min="0"
                                              />
                                            </td>
                                            <td className="px-3 py-2 text-center font-bold">
                                              {subj.total_marks.toFixed(1)}
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${gradeColor(subj.grade)}`}>
                                                {subj.grade}
                                              </span>
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                ) : (
                                  <table className="w-full text-xs border rounded-lg overflow-hidden">
                                    <thead className="bg-blue-50">
                                      <tr>
                                        <th className="px-3 py-2 text-left">Subject</th>
                                        <th className="px-3 py-2 text-center">Credits</th>
                                        <th className="px-3 py-2 text-center">Internal</th>
                                        <th className="px-3 py-2 text-center">External</th>
                                        <th className="px-3 py-2 text-center">Total</th>
                                        <th className="px-3 py-2 text-center">Grade</th>
                                        <th className="px-3 py-2 text-center">GP</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                      {student.semester_data.subjects.map((subj, idx) => (
                                        <tr key={idx} className={subj.grade === 'F' ? 'bg-red-50' : ''}>
                                          <td className="px-3 py-2">
                                            <span className="font-medium">{subj.subject_name}</span>
                                            <span className="text-gray-400 ml-1">({subj.subject_code})</span>
                                          </td>
                                          <td className="px-3 py-2 text-center">{subj.credits}</td>
                                          <td className="px-3 py-2 text-center">{subj.internal_marks}</td>
                                          <td className="px-3 py-2 text-center">{subj.external_marks}</td>
                                          <td className="px-3 py-2 text-center font-bold">{subj.total_marks}</td>
                                          <td className="px-3 py-2 text-center">
                                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${gradeColor(subj.grade)}`}>
                                              {subj.grade}
                                            </span>
                                          </td>
                                          <td className="px-3 py-2 text-center">{subj.grade_points}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                )}
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {semesterMarks.length === 0 && !loadingMarks && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-12 text-center">
              <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="text-gray-500 font-medium">No marks data loaded</p>
              <p className="text-sm text-gray-400 mt-1">Select semester, branch, and click "Load Marks"</p>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          TAB: GENERATE TEMPLATES (unchanged)
      ═══════════════════════════════════════════════════ */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" /> Template Configuration
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Branch *</label>
                <select value={branch} onChange={e => setBranch(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {branches.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Academic Year *</label>
                <input type="text" value={academicYear} onChange={e => setAcademicYear(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white" placeholder="2024-25" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admission Year *</label>
                <input type="number" value={admissionYear} onChange={e => setAdmissionYear(+e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white" min={2018} max={2030} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Students Found</label>
                <div className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg font-bold text-lg">
                  {studentCount !== null ? studentCount : '—'}
                </div>
              </div>
            </div>
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Select Semesters</label>
              <div className="flex flex-wrap gap-2">
                {[1,2,3,4,5,6,7,8].map(sem => (
                  <button key={sem}
                    onClick={() => setSelectedSemesters(prev => prev.includes(sem) ? prev.filter(s => s !== sem) : [...prev, sem].sort())}
                    className={`px-4 py-2 rounded-lg border-2 font-medium transition-all
                      ${selectedSemesters.includes(sem)
                        ? 'border-indigo-600 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30'
                        : 'border-gray-300 text-gray-600 hover:border-indigo-400 dark:border-gray-600 dark:text-gray-400'
                      }`}
                  >Sem {sem}</button>
                ))}
              </div>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={handleDownloadAllTemplates} disabled={downloadingBatch || selectedSemesters.length === 0}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                {downloadingBatch ? <Loader2 className="w-4 h-4 animate-spin" /> : <Package className="w-4 h-4" />}
                Download All Selected (ZIP)
              </button>
              <div className="flex items-center gap-2">
                <select value={semester} onChange={e => setSemester(+e.target.value)}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                  {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                </select>
                <button onClick={handleDownloadTemplate} disabled={downloading}
                  className="px-4 py-2.5 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 disabled:opacity-50 flex items-center gap-2">
                  {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  Download Single
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          TAB: MANAGE STUDENTS (unchanged)
      ═══════════════════════════════════════════════════ */}
      {activeTab === 'students' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-green-600" /> Add New Students
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Branch *</label>
                <select value={branch} onChange={e => setBranch(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {branches.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admission Year *</label>
                <input type="number" value={admissionYear} onChange={e => setAdmissionYear(+e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white" min={2018} max={2030} />
              </div>
            </div>
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">Roll Number *</th>
                    <th className="px-3 py-2 text-left font-medium">Name *</th>
                    <th className="px-3 py-2 text-left font-medium">Seat No</th>
                    <th className="px-3 py-2 text-left font-medium">Email</th>
                    <th className="px-3 py-2 w-12"></th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-gray-700">
                  {newStudents.map((student, idx) => (
                    <tr key={idx}>
                      <td className="px-3 py-2">
                        <input type="text" value={student.roll_number}
                          onChange={e => updateStudentRow(idx, 'roll_number', e.target.value)}
                          className="w-full px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600"
                          placeholder="2022IT001" />
                      </td>
                      <td className="px-3 py-2">
                        <input type="text" value={student.name}
                          onChange={e => updateStudentRow(idx, 'name', e.target.value)}
                          className="w-full px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600"
                          placeholder="John Doe" />
                      </td>
                      <td className="px-3 py-2">
                        <input type="text" value={student.seat_number}
                          onChange={e => updateStudentRow(idx, 'seat_number', e.target.value.replace(/\D/g, '').slice(0, 5))}
                          className="w-full px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600"
                          placeholder="69261" maxLength={5} />
                      </td>
                      <td className="px-3 py-2">
                        <input type="email" value={student.email}
                          onChange={e => updateStudentRow(idx, 'email', e.target.value)}
                          className="w-full px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600"
                          placeholder="john@example.com" />
                      </td>
                      <td className="px-3 py-2">
                        <button onClick={() => removeStudentRow(idx)} disabled={newStudents.length === 1}
                          className="p-1 text-red-500 hover:bg-red-50 rounded disabled:opacity-30">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex gap-3">
              <button onClick={addStudentRow}
                className="px-4 py-2 border border-green-600 text-green-600 rounded-lg hover:bg-green-50 flex items-center gap-2">
                <UserPlus className="w-4 h-4" /> Add Row
              </button>
              <button onClick={handleAddStudents} disabled={addingStudents}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                {addingStudents ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save Students
              </button>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Users className="w-5 h-5 text-indigo-600" /> Student Database
              </h2>
              <div className="flex gap-2">
                <button onClick={fetchStudentSummary}
                  className="px-3 py-1.5 border rounded-lg hover:bg-gray-50 flex items-center gap-1 text-sm">
                  <RefreshCw className="w-4 h-4" /> Refresh
                </button>
                <button onClick={handleExportStudents} disabled={loading}
                  className="px-3 py-1.5 border rounded-lg hover:bg-gray-50 flex items-center gap-1 text-sm">
                  <Download className="w-4 h-4" /> Export
                </button>
              </div>
            </div>
            {studentSummary ? (
              <div className="space-y-4">
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full font-bold text-sm">
                  Total: {studentSummary.total_students} students
                </span>
                {studentSummary.groups.map((group, idx) => (
                  <div key={idx} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-bold">{group.branch}</span>
                        <span className="text-gray-600">Admission {group.admission_year}</span>
                      </div>
                      <span className="text-lg font-bold text-indigo-600">{group.count} students</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {group.students.slice(0, 5).map((s, i) => (
                        <span key={i} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                          {s.roll_number} - {s.name}
                        </span>
                      ))}
                      {group.count > 5 && (
                        <span className="px-2 py-1 bg-gray-200 rounded text-xs">+{group.count - 5} more</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Loading student data...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          TAB: UPLOAD MARKS
      ═══════════════════════════════════════════════════ */}
      {activeTab === 'upload' && (
        <div className="space-y-6">
          {/* Configuration */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" /> Upload Configuration
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Semester *</label>
                <select value={semester} onChange={e => setSemester(+e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Branch *</label>
                <select value={branch} onChange={e => setBranch(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {branches.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Academic Year *</label>
                <input type="text" value={academicYear} onChange={e => setAcademicYear(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white" placeholder="2024-25" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admission Year *</label>
                <input type="number" value={admissionYear} onChange={e => setAdmissionYear(+e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white" min={2018} max={2030} />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={overwrite} onChange={e => setOverwrite(e.target.checked)}
                  className="rounded text-indigo-600" />
                <span className="text-gray-700 dark:text-gray-300">Overwrite existing semester data</span>
              </label>
            </div>
            <div className="mt-4 flex gap-3">
              <button onClick={handleDownloadTemplate} disabled={downloading}
                className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Download Empty Template
              </button>
              <button onClick={handleDownloadMarksTemplate} disabled={downloading}
                className="px-5 py-2.5 border border-amber-600 text-amber-600 rounded-lg hover:bg-amber-50 disabled:opacity-50 flex items-center gap-2 font-medium">
                {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Edit3 className="w-4 h-4" />}
                Download Template with Existing Marks
              </button>
            </div>
          </div>

          {/* File Upload */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-indigo-600" /> Upload Marks File
            </h2>
            <div
              onDragEnter={handleDrag} onDragLeave={handleDrag}
              onDragOver={handleDrag} onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                ${dragActive ? 'border-indigo-500 bg-indigo-50' :
                  selectedFile ? 'border-green-400 bg-green-50' :
                  'border-gray-300 hover:border-indigo-400 hover:bg-gray-50 dark:border-gray-600'}`}
            >
              <input ref={fileInputRef} type="file" accept=".xls,.xlsx,.csv" className="hidden"
                onChange={e => e.target.files?.[0] && validateAndSetFile(e.target.files[0])} />
              {selectedFile ? (
                <div className="flex flex-col items-center gap-2">
                  <FileSpreadsheet className="w-12 h-12 text-green-600" />
                  <p className="font-semibold text-green-700">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                  <button onClick={(e) => { e.stopPropagation(); reset(); }}
                    className="text-sm text-red-600 hover:underline mt-1">Remove</button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="w-12 h-12 text-gray-400" />
                  <p className="font-medium text-gray-600">Drag & drop or click to browse</p>
                  <p className="text-sm text-gray-400">.xlsx, .xls, .csv (max 10 MB)</p>
                </div>
              )}
            </div>
            {selectedFile && step === 'config' && (
              <div className="mt-4">
                <button onClick={handlePreview} disabled={loading}
                  className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
                  Upload & Preview
                </button>
              </div>
            )}
          </div>

          {/* Preview Section */}
          <AnimatePresence>
            {step === 'preview' && previewData && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {[
                    { label: 'Total Rows', value: previewData.total_rows, bg: 'bg-blue-50', color: 'text-blue-700' },
                    { label: 'Matched', value: previewData.matched_students, bg: 'bg-green-50', color: 'text-green-700' },
                    { label: 'Unmatched (Pending)', value: previewData.unmatched_students, bg: 'bg-yellow-50', color: 'text-yellow-700' },
                    { label: 'With Errors', value: previewData.matched_details.filter(d => d.has_errors).length, bg: 'bg-red-50', color: 'text-red-700' },
                    { label: 'Format', value: previewData.metadata.format_detected, bg: 'bg-purple-50', color: 'text-purple-700' },
                  ].map((c, i) => (
                    <div key={i} className={`${c.bg} border rounded-lg p-4`}>
                      <span className="text-sm text-gray-600">{c.label}</span>
                      <p className={`text-2xl font-bold ${c.color} mt-1`}>{c.value}</p>
                    </div>
                  ))}
                </div>

                {previewData.matched_details.some(d => d.has_errors) && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                    <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                      <XCircle className="w-5 h-5" /> Validation Errors
                    </h3>
                    <div className="max-h-60 overflow-y-auto space-y-2">
                      {previewData.matched_details.filter(d => d.has_errors).slice(0, 20).map((detail, idx) => (
                        <div key={idx} className="bg-white rounded-lg p-3 border border-red-100">
                          <p className="font-medium text-sm">{detail.roll_number} — {detail.student_name || detail.profile_name}</p>
                          <ul className="mt-1 space-y-0.5">
                            {detail.errors.map((err, i) => (
                              <li key={i} className="text-xs text-red-600">• {err}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {previewData.unmatched_roll_numbers.length > 0 && (
                  <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                    <h3 className="font-semibold text-orange-800 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" /> Unmatched ({previewData.unmatched_roll_numbers.length})
                    </h3>
                    <p className="text-sm text-orange-700 mb-2">These marks will be saved as "pending" and auto-linked when students register:</p>
                    <div className="flex flex-wrap gap-2">
                      {previewData.unmatched_roll_numbers.map((r, i) => (
                        <span key={i} className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-mono">{r}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-4">
                  <button onClick={reset} className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2">
                    <RefreshCw className="w-4 h-4" /> Start Over
                  </button>
                  <div className="flex items-center gap-3">
                    <button onClick={handleDownloadCSV} className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2">
                      <FileText className="w-4 h-4" /> Download CSV
                    </button>
                    <button onClick={handleSave} disabled={loading || previewData.total_rows === 0}
                      className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                      Confirm & Save All
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Result Section — IMPROVED */}
          <AnimatePresence>
            {step === 'result' && saveResult && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <CheckCircle2 className="w-8 h-8 text-green-600" />
                    <div>
                      <h3 className="text-xl font-bold text-green-800">Upload Complete!</h3>
                      <p className="text-green-700">Processing finished successfully</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                    <div className="bg-white rounded-lg p-3 text-center border">
                      <p className="text-xs text-gray-500 font-medium">Directly Updated</p>
                      <p className="text-2xl font-bold text-green-700">{saveResult.updated_students}</p>
                      <p className="text-xs text-gray-400">Profiles with marks saved</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 text-center border">
                      <p className="text-xs text-gray-500 font-medium">Saved as Pending</p>
                      <p className="text-2xl font-bold text-yellow-700">{saveResult.created_students}</p>
                      <p className="text-xs text-gray-400">Will auto-link on registration</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 text-center border">
                      <p className="text-xs text-gray-500 font-medium">Failed</p>
                      <p className="text-2xl font-bold text-red-700">{saveResult.failed_updates}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 text-center border">
                      <p className="text-xs text-gray-500 font-medium">Skipped</p>
                      <p className="text-2xl font-bold text-gray-700">{saveResult.skipped_students}</p>
                    </div>
                  </div>
                  {saveResult.errors.length > 0 && (
                    <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="font-semibold text-red-700 text-sm mb-1">Errors:</p>
                      {saveResult.errors.slice(0, 10).map((err, i) => (
                        <p key={i} className="text-xs text-red-600">
                          {err.roll_number}: {err.error || err.errors?.join(', ')}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-3">
                  <button onClick={reset}
                    className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
                    <RefreshCw className="w-4 h-4" /> Upload Another
                  </button>
                  <button onClick={() => setActiveTab('edit')}
                    className="px-5 py-2.5 border border-amber-600 text-amber-600 rounded-lg hover:bg-amber-50 flex items-center gap-2">
                    <Edit3 className="w-4 h-4" /> View / Edit Marks
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default BulkMarksUpload;