// academic-advisor-frontend/src/components/dashboard/AcademicDataEntry.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GraduationCap, Save, AlertCircle, CheckCircle, Loader2,
  BookOpen, Info, User, Calendar, CreditCard, RefreshCw,
  Hash, School, Mail, ChevronDown, ChevronUp, Eye,
  Award, TrendingUp, BarChart3, ArrowLeft
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { auth } from '../../services/firebase.config';

// ==================== Interfaces ====================

interface ProfileData {
  name: string;
  roll_number: string;
  seat_number: string;
  branch: string;
  admission_year: number;
  email: string;
}

interface SubjectScore {
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

interface SemesterRecord {
  semester_number: number;
  academic_year: string;
  subjects: SubjectScore[];
  sgpa: number;
  total_credits: number;
  credits_earned: number;
  is_complete: boolean;
}

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==================== Component ====================

export const AcademicDataEntry: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [profileExists, setProfileExists] = useState(false);
  const [currentSemester, setCurrentSemester] = useState(1);
  const [academicYear, setAcademicYear] = useState('');
  const [profileLoading, setProfileLoading] = useState(false);
  const [marksSynced, setMarksSynced] = useState(false);

  const [profileForm, setProfileForm] = useState<ProfileData>({
    name: user?.name || '',
    roll_number: '',
    seat_number: '',
    branch: 'IT',
    admission_year: new Date().getFullYear(),
    email: user?.email || ''
  });

  const [semesterRecords, setSemesterRecords] = useState<SemesterRecord[]>([]);
  const [cgpa, setCgpa] = useState(0);
  const [totalCreditsEarned, setTotalCreditsEarned] = useState(0);

  // View semester detail state
  const [selectedSemester, setSelectedSemester] = useState<number | null>(null);
  const [selectedSemesterScores, setSelectedSemesterScores] = useState<SubjectScore[]>([]);
  const [loadingScores, setLoadingScores] = useState(false);
  const [expandedSemester, setExpandedSemester] = useState<number | null>(null);

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

    if (cm >= 7) {
      ay = `${cy}-${(cy + 1).toString().slice(2)}`;
      sem = (cy - year) * 2 + 1;
    } else {
      ay = `${cy - 1}-${cy.toString().slice(2)}`;
      sem = (cy - year) * 2;
    }

    return { semester: Math.min(Math.max(sem, 1), 8), academicYear: ay };
  };

  const extractErrorMessage = (err: any, defaultMessage: string): string => {
    if (!err) return defaultMessage;
    if (err.detail && Array.isArray(err.detail)) {
      const messages = err.detail
        .map((e: any) => (typeof e === 'string' ? e : e?.msg || null))
        .filter(Boolean);
      return messages.length > 0 ? messages.join(', ') : defaultMessage;
    }
    if (typeof err.detail === 'string') return err.detail;
    if (typeof err.message === 'string') return err.message;
    return defaultMessage;
  };

  const getGradeColor = (grade: string): string => {
    const map: Record<string, string> = {
      'O': 'text-emerald-700 bg-emerald-50 border-emerald-200',
      'A+': 'text-green-700 bg-green-50 border-green-200',
      'A': 'text-blue-700 bg-blue-50 border-blue-200',
      'B+': 'text-sky-700 bg-sky-50 border-sky-200',
      'B': 'text-yellow-700 bg-yellow-50 border-yellow-200',
      'C': 'text-orange-700 bg-orange-50 border-orange-200',
      'P': 'text-amber-700 bg-amber-50 border-amber-200',
      'F': 'text-red-700 bg-red-50 border-red-200',
    };
    return map[grade] || 'text-gray-700 bg-gray-50 border-gray-200';
  };

  const getGradeBadgeColor = (grade: string): string => {
    const map: Record<string, string> = {
      'O': 'bg-emerald-500', 'A+': 'bg-green-500', 'A': 'bg-blue-500',
      'B+': 'bg-sky-500', 'B': 'bg-yellow-500', 'C': 'bg-orange-500',
      'P': 'bg-amber-500', 'F': 'bg-red-500',
    };
    return map[grade] || 'bg-gray-500';
  };

  const getSGPAColor = (sgpa: number): string => {
    if (sgpa >= 9.0) return 'text-emerald-600';
    if (sgpa >= 8.0) return 'text-green-600';
    if (sgpa >= 7.0) return 'text-blue-600';
    if (sgpa >= 6.0) return 'text-yellow-600';
    if (sgpa >= 5.0) return 'text-orange-600';
    return 'text-red-600';
  };

  const getSGPABg = (sgpa: number): string => {
    if (sgpa >= 9.0) return 'from-emerald-50 to-green-50 border-emerald-200';
    if (sgpa >= 8.0) return 'from-green-50 to-teal-50 border-green-200';
    if (sgpa >= 7.0) return 'from-blue-50 to-sky-50 border-blue-200';
    if (sgpa >= 6.0) return 'from-yellow-50 to-amber-50 border-yellow-200';
    if (sgpa >= 5.0) return 'from-orange-50 to-amber-50 border-orange-200';
    return 'from-red-50 to-orange-50 border-red-200';
  };

  const getSubjectTypeBadge = (score: SubjectScore) => {
    if (score.is_elective) {
      return (
        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
          Elective
        </span>
      );
    }
    if (score.is_practical) {
      return (
        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
          Practical
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
        Theory
      </span>
    );
  };

  const getPercentage = (total: number, max: number): number => {
    return max > 0 ? Math.round((total / max) * 100) : 0;
  };

  // ==================== API Calls ====================

  const checkProfile = async () => {
    if (!user) return;
    try {
      setProfileLoading(true);
      const token = await getToken();
      if (!token) return;

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/profile`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.ok) {
        const data = await res.json();
        const profile = data.profile;

        setProfileExists(true);
        setCurrentSemester(profile.current_semester);
        setAcademicYear(profile.current_academic_year);
        setProfileForm({
          name: profile.name || '',
          roll_number: profile.roll_number || '',
          seat_number: profile.seat_number || '',
          branch: profile.branch || 'IT',
          admission_year: profile.admission_year || new Date().getFullYear(),
          email: profile.email || ''
        });
        setCgpa(profile.cgpa || 0);
        setTotalCreditsEarned(profile.total_credits_earned || 0);
        setMarksSynced(profile.marks_synced || false);

        await fetchSemesterRecords();
      } else if (res.status === 404) {
        setProfileExists(false);
        const ad = calcAcademicDetails(profileForm.admission_year);
        setCurrentSemester(ad.semester);
        setAcademicYear(ad.academicYear);
      }
    } catch (e) {
      console.error(e);
      setProfileExists(false);
    } finally {
      setProfileLoading(false);
    }
  };

  const fetchSemesterRecords = async () => {
    if (!user) return;
    try {
      const token = await getToken();
      if (!token) return;

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/semesters`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.ok) {
        const data = await res.json();
        setSemesterRecords(data.semesters || []);
        if (data.semesters && data.semesters.length > 0) {
          setMarksSynced(true);
        }
      }
    } catch (e) {
      console.error('Error fetching semesters:', e);
    }
  };

  const fetchSemesterScores = async (semesterNumber: number) => {
    if (!user) return;
    try {
      setLoadingScores(true);
      const token = await getToken();
      if (!token) return;

      const res = await fetch(
        `${BACKEND_URL}/api/v1/academic/scores?semester_number=${semesterNumber}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (res.ok) {
        const data = await res.json();
        setSelectedSemesterScores(data.scores || []);
        setSelectedSemester(semesterNumber);
      } else {
        toast.error('Failed to load semester scores');
      }
    } catch (e) {
      console.error('Error fetching scores:', e);
      toast.error('Error loading scores');
    } finally {
      setLoadingScores(false);
    }
  };

  const toggleSemesterDetail = async (semesterNumber: number) => {
    if (expandedSemester === semesterNumber) {
      // Collapse
      setExpandedSemester(null);
      setSelectedSemester(null);
      setSelectedSemesterScores([]);
    } else {
      // Expand and fetch scores
      setExpandedSemester(semesterNumber);
      await fetchSemesterScores(semesterNumber);
    }
  };

  const saveProfile = async () => {
    if (!user) return;
    if (!profileForm.name.trim() || !profileForm.roll_number.trim()) {
      toast.error('Please fill required fields');
      return;
    }

    if (profileForm.seat_number && profileForm.seat_number.length !== 5) {
      toast.error('Seat number must be exactly 5 digits');
      return;
    }

    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;

      const payload: any = {
        name: profileForm.name,
        roll_number: profileForm.roll_number,
        branch: profileForm.branch,
        admission_year: profileForm.admission_year,
        email: profileForm.email,
      };

      if (profileForm.seat_number && profileForm.seat_number.length === 5) {
        payload.seat_number = profileForm.seat_number;
      }

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/profile/create`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const d = await res.json();
        setProfileExists(true);
        setCurrentSemester(d.current_semester);
        setAcademicYear(d.current_academic_year);
        toast.success('Profile saved!');

        if (d.marks_synced) {
          setMarksSynced(true);
          await fetchSemesterRecords();
          toast.success('Marks automatically synced!');
        }

        window.dispatchEvent(new Event('profileUpdated'));
        window.dispatchEvent(new CustomEvent('profileSaved', { detail: d }));
      } else {
        const err = await res.json();
        toast.error(extractErrorMessage(err, 'Failed to save profile'));
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Error saving profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updateSeatNumber = async () => {
    if (!user || !profileForm.seat_number) {
      toast.error('Please enter a seat number');
      return;
    }

    if (profileForm.seat_number.length !== 5) {
      toast.error('Seat number must be exactly 5 digits');
      return;
    }

    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/profile/seat-number`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          seat_number: profileForm.seat_number,
          semester: currentSemester
        })
      });

      if (res.ok) {
        const d = await res.json();
        toast.success('Seat number updated!');

        if (d.marks_synced) {
          setMarksSynced(true);
          await fetchSemesterRecords();
          toast.success('New marks found and synced!');
        }
      } else {
        const err = await res.json();
        toast.error(extractErrorMessage(err, 'Failed to update seat number'));
      }
    } catch (error) {
      console.error('Error updating seat number:', error);
      toast.error('Error updating seat number. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // ==================== Effects ====================

  useEffect(() => {
    if (user) {
      checkProfile();
    }
  }, [user]);

  useEffect(() => {
    const ad = calcAcademicDetails(profileForm.admission_year);
    setCurrentSemester(ad.semester);
    setAcademicYear(ad.academicYear);
  }, [profileForm.admission_year]);

  // ==================== Sub-Components ====================

  // In AcademicDataEntry.tsx, add this function:

const forceSync = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;

      const res = await fetch(`${BACKEND_URL}/api/v1/academic/profile/force-sync`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        // Reload everything
        await checkProfile();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Sync failed');
      }
    } catch (e) {
      toast.error('Sync failed');
    } finally {
      setLoading(false);
    }
  };

  const SemesterScoresTable: React.FC<{
    scores: SubjectScore[];
    semRecord: SemesterRecord;
  }> = ({ scores, semRecord }) => {
    const totalMaxMarks = scores.reduce(
      (sum, s) => {
        // Approximate max marks from grade points logic
        // Internal + External maxes aren't stored in scores, so calculate from context
        return sum + s.total_marks;
      },
      0
    );

    // Count grades
    const gradeCount: Record<string, number> = {};
    scores.forEach(s => {
      gradeCount[s.grade] = (gradeCount[s.grade] || 0) + 1;
    });

    return (
      <div className="space-y-4">
        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <p className="text-xs text-blue-600 font-medium">SGPA</p>
            <p className={`text-2xl font-bold ${getSGPAColor(semRecord.sgpa)}`}>
              {semRecord.sgpa.toFixed(2)}
            </p>
          </div>
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <p className="text-xs text-green-600 font-medium">Credits Earned</p>
            <p className="text-2xl font-bold text-green-700">
              {semRecord.credits_earned}
              <span className="text-sm text-green-500">/{semRecord.total_credits}</span>
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <p className="text-xs text-purple-600 font-medium">Subjects</p>
            <p className="text-2xl font-bold text-purple-700">{scores.length}</p>
          </div>
          <div className="bg-amber-50 rounded-lg p-3 text-center">
            <p className="text-xs text-amber-600 font-medium">Result</p>
            <p className={`text-2xl font-bold ${
              scores.some(s => s.grade === 'F') ? 'text-red-600' : 'text-green-600'
            }`}>
              {scores.some(s => s.grade === 'F') ? 'ATKT' : 'PASS'}
            </p>
          </div>
        </div>

        {/* Grade distribution mini bar */}
        {Object.keys(gradeCount).length > 0 && (
          <div className="flex items-center gap-2 px-1">
            <span className="text-xs text-gray-500 w-16 flex-shrink-0">Grades:</span>
            <div className="flex gap-1 flex-wrap">
              {['O', 'A+', 'A', 'B+', 'B', 'C', 'P', 'F']
                .filter(g => gradeCount[g])
                .map(g => (
                  <span
                    key={g}
                    className={`px-2 py-0.5 rounded text-xs font-bold text-white ${getGradeBadgeColor(g)}`}
                  >
                    {g} × {gradeCount[g]}
                  </span>
                ))}
            </div>
          </div>
        )}

        {/* Scores table */}
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Subject
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Credits
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Internal
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  External
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Grade
                </th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  GP
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {scores.map((score, idx) => {
                const maxMarks = score.internal_marks + score.external_marks > 0
                  ? score.total_marks
                  : 0;

                return (
                  <tr
                    key={idx}
                    className={`hover:bg-gray-50 transition-colors ${
                      score.grade === 'F' ? 'bg-red-50/50' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900 text-sm">
                          {score.subject_name}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {score.subject_code}
                        </p>
                      </div>
                    </td>
                    <td className="px-3 py-3 text-center">
                      {getSubjectTypeBadge(score)}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="font-semibold text-gray-700 text-sm">
                        {score.credits}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center text-sm text-gray-700">
                      {score.internal_marks}
                    </td>
                    <td className="px-3 py-3 text-center text-sm text-gray-700">
                      {score.external_marks}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="font-bold text-gray-900 text-sm">
                        {score.total_marks}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span
                        className={`inline-flex items-center justify-center w-10 h-7 rounded-md text-xs font-bold border ${getGradeColor(score.grade)}`}
                      >
                        {score.grade}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="font-semibold text-gray-700 text-sm">
                        {score.grade_points}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {/* Footer totals */}
            <tfoot>
              <tr className="bg-gray-50 border-t-2 border-gray-200">
                <td className="px-4 py-3 font-semibold text-gray-700 text-sm" colSpan={2}>
                  Total
                </td>
                <td className="px-3 py-3 text-center font-bold text-gray-800 text-sm">
                  {scores.reduce((s, sc) => s + sc.credits, 0)}
                </td>
                <td className="px-3 py-3 text-center font-semibold text-gray-700 text-sm">
                  {scores.reduce((s, sc) => s + sc.internal_marks, 0).toFixed(1)}
                </td>
                <td className="px-3 py-3 text-center font-semibold text-gray-700 text-sm">
                  {scores.reduce((s, sc) => s + sc.external_marks, 0).toFixed(1)}
                </td>
                <td className="px-3 py-3 text-center font-bold text-gray-900 text-sm">
                  {scores.reduce((s, sc) => s + sc.total_marks, 0).toFixed(1)}
                </td>
                <td className="px-3 py-3 text-center" colSpan={2}>
                  <span className={`text-lg font-bold ${getSGPAColor(semRecord.sgpa)}`}>
                    SGPA: {semRecord.sgpa.toFixed(2)}
                  </span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    );
  };

  // ==================== Render ====================

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Academic Profile</h1>
            <p className="text-purple-100">
              {profileExists
                ? 'View your academic records and track your progress'
                : 'Set up your profile to access your academic records'
              }
            </p>
          </div>
          <button
            onClick={checkProfile}
            disabled={profileLoading}
            className="px-4 py-2 bg-white/20 backdrop-blur rounded-lg hover:bg-white/30 transition flex items-center gap-2"
          >
            {profileLoading
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <RefreshCw className="w-4 h-4" />
            }
            {profileLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
        {/* Add this button next to the Refresh button in the header */}
<button
  onClick={forceSync}
  disabled={loading}
  className="px-4 py-2 bg-green-500/20 backdrop-blur rounded-lg hover:bg-green-500/30 transition flex items-center gap-2"
>
  {loading
    ? <Loader2 className="w-4 h-4 animate-spin" />
    : <RefreshCw className="w-4 h-4" />
  }
  Force Sync Marks
</button>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            Semester: {currentSemester}
          </span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            Year: {academicYear || 'N/A'}
          </span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            {profileExists ? '✅ Profile Complete' : '⏳ Profile Pending'}
          </span>
          {marksSynced && (
            <span className="px-3 py-1 bg-green-400/30 rounded-full text-sm">
              ✅ Marks Synced
            </span>
          )}
          {profileExists && cgpa > 0 && (
            <span className="px-3 py-1 bg-yellow-400/30 rounded-full text-sm font-semibold">
              CGPA: {cgpa.toFixed(2)}
            </span>
          )}
        </div>
      </div>

      {/* Profile Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border p-6"
      >
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <User className="w-5 h-5 mr-2 text-purple-600" />
          {profileExists ? 'Your Profile' : 'Student Profile Setup'}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <User className="w-3 h-3" /> Full Name *
            </label>
            <input
              type="text"
              value={profileForm.name}
              onChange={e => setProfileForm({ ...profileForm, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-50 disabled:text-gray-600"
              placeholder="John Doe"
              disabled={profileExists}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <CreditCard className="w-3 h-3" /> Roll Number *
            </label>
            <input
              type="text"
              value={profileForm.roll_number}
              onChange={e => setProfileForm({ ...profileForm, roll_number: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-50 disabled:text-gray-600"
              placeholder="5023152"
              disabled={profileExists}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Hash className="w-3 h-3" /> Seat Number (5 digits)
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <input
                  type="text"
                  value={profileForm.seat_number}
                  onChange={e => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 5);
                    setProfileForm({ ...profileForm, seat_number: value });
                  }}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 ${
                    profileForm.seat_number &&
                    profileForm.seat_number.length !== 5 &&
                    profileForm.seat_number.length > 0
                      ? 'border-red-300 focus:ring-red-500'
                      : ''
                  }`}
                  placeholder="69261"
                  maxLength={5}
                />
                {profileForm.seat_number && profileForm.seat_number.length > 0 && profileForm.seat_number.length !== 5 && (
                  <p className="text-xs text-red-500 mt-1">
                    Must be exactly 5 digits ({profileForm.seat_number.length}/5)
                  </p>
                )}
                {profileForm.seat_number && profileForm.seat_number.length === 5 && (
                  <p className="text-xs text-green-500 mt-1">✓ Valid seat number</p>
                )}
                {!profileForm.seat_number && (
                  <p className="text-xs text-gray-500 mt-1">Optional — changes each semester</p>
                )}
              </div>
              {profileExists && (
                <button
                  onClick={updateSeatNumber}
                  disabled={loading || profileForm.seat_number.length !== 5}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Update
                </button>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <School className="w-3 h-3" /> Branch *
            </label>
            <select
              value={profileForm.branch}
              onChange={e => setProfileForm({ ...profileForm, branch: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-50"
              disabled={profileExists}
            >
              {branches.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3" /> Admission Year *
            </label>
            <input
              type="number"
              value={profileForm.admission_year}
              onChange={e => {
                const y = parseInt(e.target.value) || new Date().getFullYear();
                setProfileForm({ ...profileForm, admission_year: y });
              }}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-50 disabled:text-gray-600"
              min={2018}
              max={new Date().getFullYear()}
              disabled={profileExists}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Mail className="w-3 h-3" /> Email
            </label>
            <input
              type="email"
              value={profileForm.email}
              onChange={e => setProfileForm({ ...profileForm, email: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-50 disabled:text-gray-600"
              disabled={profileExists}
            />
          </div>
        </div>

        {!profileExists && (
          <button
            onClick={saveProfile}
            disabled={loading || !profileForm.name.trim() || !profileForm.roll_number.trim()}
            className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        )}
      </motion.div>

      {/* Academic Records Section */}
      {profileExists && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm border p-6"
        >
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
            Academic Records
          </h2>

          {semesterRecords.length > 0 ? (
            <div className="space-y-4">
              {/* CGPA Overview Card */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-5 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="h-14 w-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-md">
                      <Award className="h-7 w-7 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 font-medium">
                        Cumulative Grade Point Average
                      </p>
                      <p className="text-4xl font-bold text-blue-700">{cgpa.toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="text-right space-y-1">
                    <div>
                      <p className="text-xs text-gray-500">Semesters</p>
                      <p className="text-2xl font-bold text-purple-700">
                        {semesterRecords.length}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Credits Earned</p>
                      <p className="text-lg font-semibold text-green-700">
                        {totalCreditsEarned}
                      </p>
                    </div>
                  </div>
                </div>

                {/* SGPA trend mini bar */}
                {semesterRecords.length > 1 && (
                  <div className="mt-4 pt-3 border-t border-blue-200/50">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                      <span className="text-xs font-medium text-blue-700">SGPA Trend</span>
                    </div>
                    <div className="flex items-end gap-1 h-12">
                      {semesterRecords
                        .sort((a, b) => a.semester_number - b.semester_number)
                        .map((sem, idx) => {
                          const height = Math.max(10, (sem.sgpa / 10) * 100);
                          return (
                            <div
                              key={idx}
                              className="flex-1 flex flex-col items-center gap-0.5"
                            >
                              <span className="text-[10px] text-gray-500 font-medium">
                                {sem.sgpa.toFixed(1)}
                              </span>
                              <div
                                className={`w-full rounded-t-sm transition-all ${
                                  sem.sgpa >= 8 ? 'bg-green-400' :
                                  sem.sgpa >= 6 ? 'bg-blue-400' :
                                  sem.sgpa >= 4 ? 'bg-yellow-400' : 'bg-red-400'
                                }`}
                                style={{ height: `${height}%` }}
                              />
                              <span className="text-[9px] text-gray-400">S{sem.semester_number}</span>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>

              {/* Semester Cards — clickable to expand */}
              <div className="space-y-3">
                {semesterRecords
                  .sort((a, b) => a.semester_number - b.semester_number)
                  .map(sem => {
                    const isExpanded = expandedSemester === sem.semester_number;
                    const passRate = sem.credits_earned / sem.total_credits;

                    return (
                      <div
                        key={sem.semester_number}
                        className={`border rounded-xl overflow-hidden transition-all ${
                          isExpanded ? 'ring-2 ring-blue-300 shadow-md' : 'hover:shadow-sm'
                        }`}
                      >
                        {/* Semester header — click to toggle */}
                        <button
                          onClick={() => toggleSemesterDetail(sem.semester_number)}
                          className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition"
                        >
                          <div className="flex items-center gap-4">
                            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                              sem.sgpa >= 8 ? 'bg-green-100' :
                              sem.sgpa >= 6 ? 'bg-blue-100' :
                              sem.sgpa >= 4 ? 'bg-yellow-100' : 'bg-red-100'
                            }`}>
                              <span className={`text-sm font-bold ${getSGPAColor(sem.sgpa)}`}>
                                S{sem.semester_number}
                              </span>
                            </div>
                            <div className="text-left">
                              <p className="font-semibold text-gray-900">
                                Semester {sem.semester_number}
                              </p>
                              <p className="text-sm text-gray-500">{sem.academic_year}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-6">
                            <div className="text-right hidden sm:block">
                              <p className={`text-lg font-bold ${getSGPAColor(sem.sgpa)}`}>
                                {sem.sgpa.toFixed(2)}
                              </p>
                              <p className="text-xs text-gray-500">SGPA</p>
                            </div>
                            <div className="text-right hidden sm:block">
                              <p className="text-sm font-semibold text-gray-700">
                                {sem.credits_earned}/{sem.total_credits}
                              </p>
                              <p className="text-xs text-gray-500">Credits</p>
                            </div>
                            <div className="hidden sm:block">
                              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                                passRate >= 1 ? 'bg-green-100 text-green-700' :
                                passRate >= 0.5 ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {passRate >= 1 ? 'PASS' : 'ATKT'}
                              </span>
                            </div>

                            {/* Mobile SGPA */}
                            <div className="sm:hidden text-right">
                              <p className={`font-bold ${getSGPAColor(sem.sgpa)}`}>
                                {sem.sgpa.toFixed(2)}
                              </p>
                            </div>

                            <div className="text-gray-400">
                              {isExpanded
                                ? <ChevronUp className="w-5 h-5" />
                                : <ChevronDown className="w-5 h-5" />
                              }
                            </div>
                          </div>
                        </button>

                        {/* Expanded detail */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.3, ease: 'easeInOut' }}
                              className="overflow-hidden"
                            >
                              <div className="px-4 pb-4 border-t bg-gray-50/50">
                                {loadingScores && expandedSemester === sem.semester_number ? (
                                  <div className="flex items-center justify-center py-8">
                                    <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                                    <span className="ml-2 text-gray-600">Loading scores...</span>
                                  </div>
                                ) : selectedSemesterScores.length > 0 && selectedSemester === sem.semester_number ? (
                                  <div className="pt-4">
                                    <SemesterScoresTable
                                      scores={selectedSemesterScores}
                                      semRecord={sem}
                                    />
                                  </div>
                                ) : (
                                  <div className="text-center py-8 text-gray-500">
                                    <BarChart3 className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                                    <p className="text-sm">No detailed scores available</p>
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  })}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-yellow-100 flex items-center justify-center">
                <AlertCircle className="h-8 w-8 text-yellow-600" />
              </div>
              <p className="text-gray-600 mb-2 font-medium">No academic records found</p>
              <p className="text-sm text-gray-500 mb-4">
                Your marks will appear here once uploaded by the administration
              </p>
              {profileForm.seat_number && profileForm.seat_number.length === 5 && (
                <button
                  onClick={updateSeatNumber}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto transition"
                >
                  {loading
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <RefreshCw className="w-4 h-4" />
                  }
                  {loading ? 'Checking...' : 'Check for Marks'}
                </button>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium text-blue-900">How it works</p>
            <ul className="mt-2 text-sm text-blue-700 space-y-1">
              <li>• Create your profile with roll number and seat number (5 digits)</li>
              <li>• Marks are automatically fetched when uploaded by administration</li>
              <li>• Click on any semester to view detailed subject-wise marks</li>
              <li>• Update your seat number each semester to sync new marks</li>
              <li>• Your CGPA is automatically calculated from all semester records</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};