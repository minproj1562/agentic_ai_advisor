// academic-advisor-frontend/src/components/dashboard/AcademicDataEntry.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  GraduationCap, Save, AlertCircle, CheckCircle, Loader2,
  BookOpen, Info, Eye, Edit3, Sparkles, BarChart3, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { auth } from '../../services/firebase.config';

// ==================== Interfaces ====================

interface SubjectDefinition {
  subject_code: string;
  subject_name: string;
  credits: number;
  course_type: string;
  internal_max: number;
  external_max: number;
  is_elective: boolean;
  is_practical: boolean;
  elective_group?: string;
}

interface SubjectEntry extends SubjectDefinition {
  internal_marks: number;
  external_marks: number;
  selected_elective_code?: string;
  selected_elective_name?: string;
}

interface ElectiveOption { code: string; name: string; }

interface CurriculumData {
  semester: number;
  admission_year: number;
  curriculum_type: string;
  theory_subjects: SubjectDefinition[];
  lab_subjects: SubjectDefinition[];
  project_subjects: SubjectDefinition[];
  elective_groups: {
    [key: string]: {
      group_name: string;
      subject_template: SubjectDefinition;
      options: ElectiveOption[];
    };
  };
}

interface SavedScore {
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

interface ProfileData {
  name: string;
  roll_number: string;
  branch: string;
  admission_year: number;
  email: string;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==================== Component ====================

export const AcademicDataEntry: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [profileExists, setProfileExists] = useState(false);
  const [currentSemester, setCurrentSemester] = useState(1);
  const [academicYear, setAcademicYear] = useState('');
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);

  const [availableSubjects, setAvailableSubjects] = useState<CurriculumData | null>(null);
  const [loadingSubjects, setLoadingSubjects] = useState(false);

  const [profileForm, setProfileForm] = useState<ProfileData>({
    name: user?.name || '', roll_number: '', branch: 'IT',
    admission_year: new Date().getFullYear(), email: user?.email || ''
  });

  const [subjects, setSubjects] = useState<SubjectEntry[]>([]);
  const [selectedSemester, setSelectedSemester] = useState(1);

  // Study hours — per semester, asked at score entry time
  const [studyHours, setStudyHours] = useState(4);

  // View/Edit state
  const [savedScores, setSavedScores] = useState<SavedScore[]>([]);
  const [hasSavedData, setHasSavedData] = useState(false);
  const [viewMode, setViewMode] = useState<'view' | 'edit'>('edit');
  const [loadingSavedData, setLoadingSavedData] = useState(false);
  const [semesterSGPA, setSemesterSGPA] = useState<number | null>(null);

  const branches = ['IT', 'COMP', 'EXTC', 'MECH', 'ELEC'];

  // ==================== Helpers ====================

  const getToken = async (): Promise<string | null> => {
    const u = auth.currentUser;
    return u ? u.getIdToken(true) : null;
  };

  const calcAcademicDetails = (year: number) => {
    const now = new Date();
    const cy = now.getFullYear();
    const cm = now.getMonth() + 1;
    let sem: number, ay: string;
    if (cm >= 7) { ay = `${cy}-${(cy + 1).toString().slice(2)}`; sem = (cy - year) * 2 + 1; }
    else { ay = `${cy - 1}-${cy.toString().slice(2)}`; sem = (cy - year) * 2; }
    return { semester: Math.min(Math.max(sem, 1), 8), academicYear: ay };
  };

  const calcGrade = (total: number, max: number) => {
    const pct = max > 0 ? (total / max) * 100 : 0;
    if (pct >= 90) return { grade: 'O', points: 10, color: 'text-green-600' };
    if (pct >= 80) return { grade: 'A+', points: 9, color: 'text-green-500' };
    if (pct >= 70) return { grade: 'A', points: 8, color: 'text-blue-600' };
    if (pct >= 60) return { grade: 'B+', points: 7, color: 'text-blue-500' };
    if (pct >= 50) return { grade: 'B', points: 6, color: 'text-yellow-600' };
    if (pct >= 45) return { grade: 'C', points: 5, color: 'text-yellow-500' };
    if (pct >= 40) return { grade: 'P', points: 4, color: 'text-orange-500' };
    return { grade: 'F', points: 0, color: 'text-red-600' };
  };

  const getGradeColor = (grade: string) => {
    const map: Record<string, string> = {
      'O': 'text-green-600 bg-green-50', 'A+': 'text-green-600 bg-green-50',
      'A': 'text-blue-600 bg-blue-50', 'B+': 'text-blue-500 bg-blue-50',
      'B': 'text-yellow-600 bg-yellow-50', 'C': 'text-yellow-500 bg-yellow-50',
      'P': 'text-orange-600 bg-orange-50', 'F': 'text-red-600 bg-red-50'
    };
    return map[grade] || 'text-gray-600 bg-gray-50';
  };

  const getBadge = (ct: string) => {
    const m: Record<string, { bg: string; text: string; label: string }> = {
      PCC: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Core' },
      PEC: { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Elective' },
      LBC: { bg: 'bg-green-100', text: 'text-green-700', label: 'Lab' },
      SBL: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Skill Lab' },
      MNP: { bg: 'bg-pink-100', text: 'text-pink-700', label: 'Mini Project' },
      MJP: { bg: 'bg-red-100', text: 'text-red-700', label: 'Major Project' },
      INT: { bg: 'bg-indigo-100', text: 'text-indigo-700', label: 'Internship' },
      BSC: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Basic Science' },
      ESC: { bg: 'bg-teal-100', text: 'text-teal-700', label: 'Engg Science' },
      AEC: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Ability' },
      OEC: { bg: 'bg-cyan-100', text: 'text-cyan-700', label: 'Open Elective' }
    };
    const b = m[ct] || { bg: 'bg-gray-100', text: 'text-gray-700', label: ct };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${b.bg} ${b.text}`}>{b.label}</span>;
  };

  // ==================== API Calls ====================

  const checkProfile = async () => {
    if (!user) return;
    try {
      setProfileLoading(true);
      const token = await getToken();
      if (!token) return;
      const res = await fetch(`${BACKEND_URL}/api/v1/student-profile/profile`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        const d = await res.json();
        setProfileExists(true);
        setCurrentSemester(d.current_semester);
        setAcademicYear(d.current_academic_year);
        setSelectedSemester(d.current_semester);
        setProfileForm({
          name: d.name || '', roll_number: d.roll_number || '', branch: d.branch || 'IT',
          admission_year: d.admission_year || new Date().getFullYear(), email: d.email || ''
        });
        // Load study hours from profile if available
        if (d.study_hours !== undefined && d.study_hours !== null) {
          setStudyHours(d.study_hours);
        }
      } else if (res.status === 404) {
        setProfileExists(false);
        const ad = calcAcademicDetails(profileForm.admission_year);
        setCurrentSemester(ad.semester); setAcademicYear(ad.academicYear); setSelectedSemester(ad.semester);
      }
    } catch (e) { console.error(e); setProfileExists(false); }
    finally { setProfileLoading(false); }
  };

  const fetchSubjects = async (sem: number) => {
    if (!user || !profileExists) return;
    try {
      setLoadingSubjects(true);
      const token = await getToken(); if (!token) return;
      const res = await fetch(`${BACKEND_URL}/api/v1/academic/subjects/available/${sem}`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        const d = await res.json();
        setAvailableSubjects(d);
        const entries: SubjectEntry[] = [];
        d.theory_subjects?.forEach((s: SubjectDefinition) => entries.push({ ...s, internal_marks: 0, external_marks: 0 }));
        d.lab_subjects?.forEach((s: SubjectDefinition) => entries.push({ ...s, internal_marks: 0, external_marks: 0 }));
        d.project_subjects?.forEach((s: SubjectDefinition) => entries.push({ ...s, internal_marks: 0, external_marks: 0 }));
        Object.values(d.elective_groups || {}).forEach((g: any) => {
          entries.push({ ...g.subject_template, internal_marks: 0, external_marks: 0, selected_elective_code: '', selected_elective_name: '' });
        });
        setSubjects(entries);
      } else {
        const err = await res.json(); toast.error(err.detail || 'Failed to load subjects');
      }
    } catch { toast.error('Error loading subjects'); }
    finally { setLoadingSubjects(false); }
  };

  const fetchExistingScores = async (sem: number) => {
    if (!user || !profileExists) return;
    try {
      setLoadingSavedData(true);
      const token = await getToken(); if (!token) return;

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/scores?semester_number=${sem}`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
      });

      if (res.ok) {
        const d = await res.json();
        if (d.scores?.length > 0) {
          setSavedScores(d.scores);
          setHasSavedData(true);
          setViewMode('view');

          // Load saved study hours for this semester
          if (d.study_hours !== undefined && d.study_hours !== null) {
            setStudyHours(d.study_hours);
          }

          // Get SGPA
          const semRes = await fetch(`${BACKEND_URL}/api/v1/academic/semesters`, {
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
          });
          if (semRes.ok) {
            const semData = await semRes.json();
            const match = semData.semesters?.find((s: any) => s.semester_number === sem);
            setSemesterSGPA(match?.sgpa ?? null);
          }

          // Pre-fill subjects with saved data for edit mode
          setSubjects(prev => prev.map(sub => {
            const m = d.scores.find((s: SavedScore) =>
              s.subject_code === sub.subject_code || s.subject_code === sub.selected_elective_code
            );
            if (m) {
              return {
                ...sub, internal_marks: m.internal_marks, external_marks: m.external_marks,
                ...(m.is_elective ? { selected_elective_code: m.subject_code, selected_elective_name: m.subject_name, subject_code: m.subject_code, subject_name: m.subject_name } : {})
              };
            }
            return sub;
          }));
        } else {
          setSavedScores([]); setHasSavedData(false); setViewMode('edit'); setSemesterSGPA(null);
        }
      }
    } catch (e) { console.error(e); }
    finally { setLoadingSavedData(false); }
  };

  // ==================== Effects ====================

  useEffect(() => {
    if (user) {
      (async () => {
        try { const r = await fetch(`${BACKEND_URL}/health`); setBackendAvailable(r.ok); } catch { setBackendAvailable(false); }
        if (backendAvailable) await checkProfile();
      })();
    }
  }, [user]);

  useEffect(() => {
    if (profileExists && selectedSemester) {
      fetchSubjects(selectedSemester).then(() => fetchExistingScores(selectedSemester));
    }
  }, [selectedSemester, profileExists]);

  // ==================== Handlers ====================

  const updateSubject = (index: number, field: 'internal_marks' | 'external_marks' | 'selected_elective_code', value: any) => {
    setSubjects(prev => {
      const updated = [...prev];
      if (field === 'selected_elective_code' && availableSubjects) {
        const sub = updated[index];
        const group = availableSubjects.elective_groups[sub.elective_group || ''];
        const opt = group?.options.find(o => o.code === value);
        if (opt) {
          updated[index] = { ...sub, selected_elective_code: opt.code, selected_elective_name: opt.name, subject_code: opt.code, subject_name: opt.name };
        }
      } else {
        updated[index] = { ...updated[index], [field]: value };
      }
      return updated;
    });
  };

  const saveProfile = async () => {
    if (!user) return;
    if (!profileForm.name.trim() || !profileForm.roll_number.trim()) { toast.error('Please fill required fields'); return; }
    try {
      setLoading(true);
      const token = await getToken(); if (!token) return;
      const res = await fetch(`${BACKEND_URL}/api/v1/student-profile/profile/create`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm)
      });
      if (res.ok) {
        const d = await res.json();
        setProfileExists(true); setCurrentSemester(d.current_semester); setAcademicYear(d.current_academic_year);
        toast.success('Profile saved!');
        window.dispatchEvent(new Event('profileUpdated'));
        window.dispatchEvent(new CustomEvent('profileSaved', { detail: d }));
      } else { const err = await res.json(); toast.error(err.detail || 'Failed'); }
    } catch { toast.error('Error saving profile'); }
    finally { setLoading(false); }
  };

  const saveSubjects = async () => {
    if (!user || !profileExists) return;
    const invalid = subjects.filter(s => {
      if (s.is_elective && !s.selected_elective_code) return true;
      if (s.internal_marks < 0 || s.internal_marks > s.internal_max) return true;
      if (s.external_marks < 0 || s.external_marks > s.external_max) return true;
      return false;
    });
    if (invalid.length) { toast.error('Fix invalid entries'); return; }

    try {
      setLoading(true);
      const token = await getToken(); if (!token) return;
      const body = {
        semester_number: selectedSemester,
        academic_year: academicYear,
        study_hours: studyHours,
        subjects: subjects.map(s => {
          const total = s.internal_marks + s.external_marks;
          const max = s.internal_max + s.external_max;
          const g = calcGrade(total, max);
          return {
            subject_code: s.selected_elective_code || s.subject_code,
            subject_name: s.selected_elective_name || s.subject_name,
            credits: s.credits, internal_marks: s.internal_marks, external_marks: s.external_marks,
            internal_max: s.internal_max, external_max: s.external_max,
            total_marks: total, grade: g.grade, grade_points: g.points,
            is_elective: s.is_elective, is_practical: s.is_practical
          };
        })
      };

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/scores/add`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        const d = await res.json();
        toast.success(`Saved! SGPA: ${d.semester_sgpa?.toFixed(2) || 'N/A'} | CGPA: ${d.updated_cgpa?.toFixed(2) || 'N/A'}`);
        setSemesterSGPA(d.semester_sgpa);
        await fetchExistingScores(selectedSemester);
        setViewMode('view');

        // Notify dashboard
        window.dispatchEvent(new CustomEvent('academicDataUpdated'));
        window.dispatchEvent(new Event('profileUpdated'));
      } else { const err = await res.json(); toast.error(err.detail || 'Failed'); }
    } catch { toast.error('Error saving'); }
    finally { setLoading(false); }
  };

  // ==================== Study Hours Helper ====================

  const getStudyHoursLabel = (hours: number): string => {
    if (hours <= 1) return 'Minimal';
    if (hours <= 3) return 'Light';
    if (hours <= 5) return 'Moderate';
    if (hours <= 8) return 'Dedicated';
    return 'Intensive';
  };

  const getStudyHoursColor = (hours: number): string => {
    if (hours <= 1) return 'text-red-600';
    if (hours <= 3) return 'text-orange-600';
    if (hours <= 5) return 'text-blue-600';
    if (hours <= 8) return 'text-green-600';
    return 'text-purple-600';
  };

  // ==================== Render ====================

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Academic Data Entry</h1>
            <p className="text-purple-100">Add your academic scores to get personalized AI recommendations</p>
          </div>
          <button onClick={checkProfile} disabled={profileLoading}
            className="px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 flex items-center gap-2">
            {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            {profileLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Semester: {currentSemester}</span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Year: {academicYear || 'N/A'}</span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">{profileExists ? '✅ Profile Complete' : '⏳ Profile Pending'}</span>
          {availableSubjects && <span className="px-3 py-1 bg-white/20 rounded-full text-sm">{availableSubjects.curriculum_type}</span>}
        </div>
      </div>

      {!backendAvailable && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-yellow-600" />
          <p className="text-yellow-800">Backend server not available.</p>
        </div>
      )}

      {/* Profile Section */}
      {!profileExists && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <GraduationCap className="w-5 h-5 mr-2 text-purple-600" /> Student Profile Setup
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
              <input type="text" value={profileForm.name} onChange={e => setProfileForm({ ...profileForm, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" placeholder="John Doe" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Roll Number *</label>
              <input type="text" value={profileForm.roll_number} onChange={e => setProfileForm({ ...profileForm, roll_number: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Branch *</label>
              <select value={profileForm.branch} onChange={e => setProfileForm({ ...profileForm, branch: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500">
                {branches.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Admission Year *</label>
              <input type="number" value={profileForm.admission_year}
                onChange={e => {
                  const y = parseInt(e.target.value) || new Date().getFullYear();
                  setProfileForm({ ...profileForm, admission_year: y });
                  const ad = calcAcademicDetails(y);
                  setCurrentSemester(ad.semester); setAcademicYear(ad.academicYear); setSelectedSemester(ad.semester);
                }}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" min={2018} max={new Date().getFullYear()} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={profileForm.email} onChange={e => setProfileForm({ ...profileForm, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" />
            </div>
          </div>
          <button onClick={saveProfile} disabled={loading || !profileForm.name.trim() || !profileForm.roll_number.trim()}
            className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        </motion.div>
      )}

      {/* Semester Scores Section */}
      {profileExists && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border p-6">
          {/* Header with semester selector */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
              Semester {selectedSemester} Scores
              {availableSubjects && <span className="ml-2 text-sm text-gray-500">({availableSubjects.curriculum_type})</span>}
            </h2>
            <div className="flex items-center gap-3">
              <select value={selectedSemester} onChange={e => setSelectedSemester(parseInt(e.target.value))}
                className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                {[1, 2, 3, 4, 5, 6, 7, 8].map(i => <option key={i} value={i}>Semester {i}</option>)}
              </select>
              {hasSavedData && (
                <div className="flex rounded-lg border overflow-hidden">
                  <button onClick={() => setViewMode('view')}
                    className={`px-3 py-2 text-sm flex items-center gap-1 ${viewMode === 'view' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>
                    <Eye className="w-4 h-4" /> View
                  </button>
                  <button onClick={() => setViewMode('edit')}
                    className={`px-3 py-2 text-sm flex items-center gap-1 ${viewMode === 'edit' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>
                    <Edit3 className="w-4 h-4" /> Edit
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* SGPA Badge */}
          {hasSavedData && semesterSGPA !== null && (
            <div className="mb-4 p-4 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-green-600" />
                <div>
                  <p className="font-semibold text-green-900">Semester {selectedSemester} — Data Saved</p>
                  <p className="text-sm text-green-700">{savedScores.length} subjects recorded</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-green-700">{semesterSGPA.toFixed(2)}</p>
                <p className="text-xs text-green-600">SGPA</p>
              </div>
            </div>
          )}

          {loadingSubjects || loadingSavedData ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">Loading...</span>
            </div>
          ) : (
            <>
              {/* ===== VIEW MODE ===== */}
              {viewMode === 'view' && hasSavedData && (
                <div className="space-y-4">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Credits</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Internal</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">External</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Total</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Grade</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {savedScores.map((s, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-4 py-3">
                              <p className="font-medium text-gray-900">{s.subject_name}</p>
                              <p className="text-xs text-gray-500">{s.subject_code}</p>
                            </td>
                            <td className="px-4 py-3">
                              {s.is_elective && <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">Elective</span>}
                              {s.is_practical && <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full ml-1">Practical</span>}
                              {!s.is_elective && !s.is_practical && <span className="text-xs text-gray-500">Theory</span>}
                            </td>
                            <td className="px-4 py-3 text-center font-medium">{s.credits}</td>
                            <td className="px-4 py-3 text-center">{s.internal_marks}</td>
                            <td className="px-4 py-3 text-center">{s.external_marks}</td>
                            <td className="px-4 py-3 text-center font-bold">{s.total_marks}</td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-3 py-1 rounded-full text-sm font-bold ${getGradeColor(s.grade)}`}>{s.grade}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Study hours display in view mode */}
                  <div className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <BookOpen className="w-4 h-4" />
                      <span>Study hours recorded for this semester:</span>
                    </div>
                    <span className={`font-bold ${getStudyHoursColor(studyHours)}`}>
                      {studyHours} hrs/day ({getStudyHoursLabel(studyHours)})
                    </span>
                  </div>
                </div>
              )}

              {/* ===== EDIT MODE ===== */}
              {viewMode === 'edit' && subjects.length > 0 && (
                <div className="space-y-4">
                  {subjects.map((subject, index) => {
                    const total = subject.internal_marks + subject.external_marks;
                    const max = subject.internal_max + subject.external_max;
                    const gradeInfo = calcGrade(total, max);

                    return (
                      <div key={index} className="p-4 border rounded-lg bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getBadge(subject.course_type)}
                            <span className="text-sm font-medium text-gray-700">{subject.credits} Credits</span>
                            {subject.is_elective && <span className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-full">Elective</span>}
                          </div>
                          <div className="text-xs text-gray-500">Max: {subject.internal_max} + {subject.external_max} = {max}</div>
                        </div>

                        {/* Elective selector */}
                        {subject.is_elective && subject.elective_group && availableSubjects?.elective_groups[subject.elective_group] ? (
                          <div className="mb-3">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Select {subject.elective_group} *</label>
                            <select value={subject.selected_elective_code || ''}
                              onChange={e => updateSubject(index, 'selected_elective_code', e.target.value)}
                              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500">
                              <option value="">-- Select Elective --</option>
                              {availableSubjects.elective_groups[subject.elective_group].options.map(o => (
                                <option key={o.code} value={o.code}>{o.code} - {o.name}</option>
                              ))}
                            </select>
                          </div>
                        ) : (
                          <p className="font-medium text-gray-800 mb-3">{subject.subject_code} - {subject.subject_name}</p>
                        )}

                        {/* Marks inputs */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                          <div>
                            <label className="block text-xs text-gray-600 mb-1">Internal (max {subject.internal_max})</label>
                            <input type="number" value={subject.internal_marks}
                              onChange={e => updateSubject(index, 'internal_marks', parseFloat(e.target.value) || 0)}
                              className="w-full px-3 py-2 border rounded-lg text-sm" min={0} max={subject.internal_max} step="0.5" />
                          </div>
                          <div>
                            <label className="block text-xs text-gray-600 mb-1">External (max {subject.external_max})</label>
                            <input type="number" value={subject.external_marks}
                              onChange={e => updateSubject(index, 'external_marks', parseFloat(e.target.value) || 0)}
                              className="w-full px-3 py-2 border rounded-lg text-sm" min={0} max={subject.external_max} step="0.5"
                              disabled={subject.external_max === 0} />
                          </div>
                          <div className="flex items-center gap-4 bg-white rounded-lg p-2 md:col-span-2">
                            <div><span className="text-xs text-gray-600">Total</span><p className="font-bold">{total}/{max}</p></div>
                            <div><span className="text-xs text-gray-600">%</span><p className="font-bold">{max > 0 ? ((total / max) * 100).toFixed(1) : 0}%</p></div>
                            <div><span className="text-xs text-gray-600">Grade</span><p className={`font-bold ${gradeInfo.color}`}>{gradeInfo.grade}</p></div>
                            <div><span className="text-xs text-gray-600">Points</span><p className="font-bold">{gradeInfo.points}</p></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  {/* ===== STUDY HOURS SECTION ===== */}
                  <div className="p-5 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 bg-purple-100 rounded-lg flex-shrink-0">
                        <BookOpen className="w-5 h-5 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-sm font-semibold text-purple-900">
                            Average Daily Study Hours — Semester {selectedSemester}
                          </label>
                          <span className={`text-sm font-bold ${getStudyHoursColor(studyHours)}`}>
                            {getStudyHoursLabel(studyHours)}
                          </span>
                        </div>
                        <p className="text-xs text-purple-600 mb-3">
                          How many hours did you typically study outside of class this semester?
                          This helps our AI predict your next semester performance.
                        </p>

                        {/* Slider */}
                        <div className="flex items-center gap-4">
                          <input
                            type="range"
                            min={0}
                            max={12}
                            step={0.5}
                            value={studyHours}
                            onChange={e => setStudyHours(parseFloat(e.target.value))}
                            className="flex-1 h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                          />
                          <div className="flex items-center gap-1 bg-white px-4 py-2 rounded-lg border border-purple-200 min-w-[90px] justify-center shadow-sm">
                            <span className="text-xl font-bold text-purple-700">{studyHours}</span>
                            <span className="text-xs text-purple-500">hrs/day</span>
                          </div>
                        </div>

                        {/* Scale labels */}
                        <div className="flex justify-between text-xs text-purple-400 mt-1.5 px-1">
                          <span>0</span>
                          <span>2</span>
                          <span>4</span>
                          <span>6</span>
                          <span>8</span>
                          <span>10</span>
                          <span>12</span>
                        </div>

                        {/* Contextual hint */}
                        <div className="mt-3 text-xs text-purple-500 flex items-center gap-1">
                          <Info className="w-3 h-3" />
                          {studyHours <= 1 && "Very low study hours — consider increasing for better results"}
                          {studyHours > 1 && studyHours <= 3 && "Light study schedule — sufficient for revision, may need more for tough subjects"}
                          {studyHours > 3 && studyHours <= 6 && "Good study routine — this is the recommended range for most students"}
                          {studyHours > 6 && studyHours <= 9 && "Strong dedication — make sure to include breaks and rest"}
                          {studyHours > 9 && "Intensive schedule — ensure quality over quantity and avoid burnout"}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {viewMode === 'edit' && subjects.length === 0 && !loadingSubjects && (
                <div className="text-center py-12 text-gray-500">
                  <Info className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No subjects available for Semester {selectedSemester}.</p>
                </div>
              )}

              {/* Action buttons */}
              {viewMode === 'edit' && subjects.length > 0 && (
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {subjects.length} subjects • Semester {selectedSemester} • {studyHours} hrs/day study
                    {hasSavedData && <span className="ml-2 text-orange-600 font-medium">⚠ Saving will overwrite existing data</span>}
                  </span>
                  <div className="flex gap-3">
                    {hasSavedData && (
                      <button onClick={() => setViewMode('view')}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
                        <X className="w-4 h-4" /> Cancel
                      </button>
                    )}
                    <button onClick={saveSubjects} disabled={loading || !backendAvailable}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                      {loading ? 'Saving...' : (hasSavedData ? 'Update Data' : 'Save Semester Data')}
                    </button>
                  </div>
                </div>
              )}

              {/* Generate Recommendations Button */}
              {hasSavedData && viewMode === 'view' && (
                <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Sparkles className="w-6 h-6 text-purple-600" />
                      <div>
                        <p className="font-semibold text-purple-900">Get AI Recommendations</p>
                        <p className="text-sm text-purple-700">Based on your marks, get elective, honours & career path suggestions</p>
                      </div>
                    </div>
                    <button onClick={async () => {
                      try {
                        const token = await getToken(); if (!token) return;
                        toast.loading('Generating recommendations...');
                        const res = await fetch(`${BACKEND_URL}/api/v1/ml-insights/academic-recommendations`, {
                          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
                        });
                        toast.dismiss();
                        if (res.ok) toast.success('Recommendations ready! Check the Elective Recommendations tab.');
                        else toast.error('Add more academic data first.');
                      } catch { toast.dismiss(); toast.error('Error generating recommendations'); }
                    }} className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg flex items-center gap-2">
                      <Sparkles className="w-4 h-4" /> Generate
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">Curriculum-Based Entry System</p>
            <ul className="mt-2 text-sm text-blue-700 space-y-1">
              <li>• Subjects load automatically based on admission year & semester</li>
              <li>• Saved data is shown in View mode — switch to Edit to modify</li>
              <li>• Grades are calculated using percentage-based scale</li>
              <li>• Study hours are saved per semester for AI performance predictions</li>
              <li>• After saving, click "Generate Recommendations" for AI-powered insights</li>
              <li>• Your CGPA is automatically recalculated from all semester records</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};