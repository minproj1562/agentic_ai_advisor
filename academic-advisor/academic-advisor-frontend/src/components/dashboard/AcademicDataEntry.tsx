//academic-advisor/academic-advisor-frontend/src/components/dashboard/AcademicDataEntry.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GraduationCap, Save, AlertCircle, CheckCircle, Loader2,
  BookOpen, Info, User, Calendar, CreditCard, RefreshCw,
  AlertTriangle, Hash, School, Mail
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

interface SemesterData {
  semester_number: number;
  sgpa: number;
  credits_earned: number;
  total_credits: number;
  academic_year: string;
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

  const [semesterRecords, setSemesterRecords] = useState<SemesterData[]>([]);
  const [cgpa, setCgpa] = useState(0);

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
      // July onwards - odd semester
      ay = `${cy}-${(cy + 1).toString().slice(2)}`; 
      sem = (cy - year) * 2 + 1; 
    } else { 
      // Before July - even semester
      ay = `${cy - 1}-${cy.toString().slice(2)}`; 
      sem = (cy - year) * 2; 
    }
    
    return { semester: Math.min(Math.max(sem, 1), 8), academicYear: ay };
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
        setMarksSynced(profile.marks_synced || false);
        
        // Fetch semester records
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
      }
    } catch (e) {
      console.error('Error fetching semesters:', e);
    }
  };

// academic-advisor-frontend/src/components/dashboard/AcademicDataEntry.tsx
// Update the saveProfile function to handle validation errors properly

const saveProfile = async () => {
  if (!user) return;
  if (!profileForm.name.trim() || !profileForm.roll_number.trim()) { 
    toast.error('Please fill required fields'); 
    return; 
  }
  
  try {
    setLoading(true);
    const token = await getToken(); 
    if (!token) return;
    
    const res = await fetch(`${BACKEND_URL}/api/v1/academic/profile/create`, {
      method: 'POST',
      headers: { 
        Authorization: `Bearer ${token}`, 
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify(profileForm)
    });
    
    if (res.ok) {
      const d = await res.json();
      setProfileExists(true); 
      setCurrentSemester(d.current_semester); 
      setAcademicYear(d.current_academic_year);
      toast.success('Profile saved!');
      
      // Marks will be auto-fetched in backend
      if (d.marks_synced) {
        setMarksSynced(true);
        await fetchSemesterRecords();
        toast.success('Marks automatically synced!');
      }
      
      window.dispatchEvent(new Event('profileUpdated'));
      window.dispatchEvent(new CustomEvent('profileSaved', { detail: d }));
    } else { 
      const err = await res.json();
      
      // Handle 422 validation errors
      if (res.status === 422 && err.detail && Array.isArray(err.detail)) {
        // Extract the first validation error message
        const firstError = err.detail[0];
        const errorMessage = firstError?.msg || 'Validation failed';
        toast.error(errorMessage);
      } else {
        // Handle other error formats
        toast.error(err.detail || 'Failed to save profile'); 
      }
    }
  } catch (error) { 
    console.error('Error saving profile:', error);
    toast.error('Error saving profile. Please try again.'); 
  } finally { 
    setLoading(false); 
  }
};

const updateSeatNumber = async () => {
  if (!user || !profileForm.seat_number || profileForm.seat_number.length !== 6) return;
  
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
      
      // Handle 422 validation errors
      if (res.status === 422 && err.detail && Array.isArray(err.detail)) {
        const firstError = err.detail[0];
        const errorMessage = firstError?.msg || 'Validation failed';
        toast.error(errorMessage);
      } else {
        toast.error(err.detail || 'Failed to update seat number'); 
      }
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
    // Update semester when admission year changes
    const ad = calcAcademicDetails(profileForm.admission_year);
    setCurrentSemester(ad.semester); 
    setAcademicYear(ad.academicYear);
  }, [profileForm.admission_year]);

  // ==================== Render ====================

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Academic Profile Setup</h1>
            <p className="text-purple-100">
              {profileExists 
                ? "Your academic data is managed by the administration" 
                : "Set up your profile to access your academic records"
              }
            </p>
          </div>
          <button onClick={checkProfile} disabled={profileLoading}
            className="px-4 py-2 bg-white/20 backdrop-blur rounded-lg hover:bg-white/30 flex items-center gap-2">
            {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {profileLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Semester: {currentSemester}</span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Year: {academicYear || 'N/A'}</span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            {profileExists ? '✅ Profile Complete' : '⏳ Profile Pending'}
          </span>
          {marksSynced && (
            <span className="px-3 py-1 bg-green-400/30 rounded-full text-sm">
              ✅ Marks Synced
            </span>
          )}
        </div>
      </div>

      {/* Profile Section */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-sm border p-6">
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
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" 
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
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" 
              placeholder="IT/2022/045"
              disabled={profileExists}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Hash className="w-3 h-3" /> Seat Number (6 digits)
            </label>
            <div className="flex gap-2">
              <input 
                type="text" 
                value={profileForm.seat_number} 
                onChange={e => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setProfileForm({ ...profileForm, seat_number: value });
                }}
                className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" 
                placeholder="692610"
                maxLength={6}
              />
              {profileExists && (
                <button 
                  onClick={updateSeatNumber}
                  disabled={loading || profileForm.seat_number.length !== 6}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  Update
                </button>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">Changes each semester</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <School className="w-3 h-3" /> Branch *
            </label>
            <select 
              value={profileForm.branch} 
              onChange={e => setProfileForm({ ...profileForm, branch: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
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
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" 
              min={2018} 
              max={new Date().getFullYear()} 
              disabled={profileExists}
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Mail className="w-3 h-3" /> Email
            </label>
            <input 
              type="email" 
              value={profileForm.email} 
              onChange={e => setProfileForm({ ...profileForm, email: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" 
              disabled={profileExists}
            />
          </div>
        </div>
        
        {!profileExists && (
          <button 
            onClick={saveProfile} 
            disabled={loading || !profileForm.name.trim() || !profileForm.roll_number.trim()}
            className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        )}
      </motion.div>

      {/* Academic Records Section */}
      {profileExists && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
            Academic Records
          </h2>
          
          {marksSynced ? (
            <div className="space-y-4">
              {/* CGPA Display */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Current CGPA</p>
                    <p className="text-3xl font-bold text-blue-700">{cgpa.toFixed(2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Semesters Completed</p>
                    <p className="text-2xl font-bold text-purple-700">{semesterRecords.length}</p>
                  </div>
                </div>
              </div>
              
              {/* Semester Records */}
              <div className="space-y-3">
                {semesterRecords.map((sem) => (
                  <div key={sem.semester_number} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Semester {sem.semester_number}</p>
                        <p className="text-sm text-gray-500">{sem.academic_year}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-blue-600">SGPA: {sem.sgpa.toFixed(2)}</p>
                        <p className="text-sm text-gray-500">
                          Credits: {sem.credits_earned}/{sem.total_credits}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-yellow-100 flex items-center justify-center">
                <AlertCircle className="h-8 w-8 text-yellow-600" />
              </div>
              <p className="text-gray-600 mb-2">No academic records found</p>
              <p className="text-sm text-gray-500">
                Your marks will appear here once uploaded by the administration
              </p>
              {profileForm.seat_number && profileForm.seat_number.length === 6 && (
                <button
                  onClick={updateSeatNumber}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Check for Marks
                </button>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">How it works</p>
            <ul className="mt-2 text-sm text-blue-700 space-y-1">
              <li>• Create your profile with roll number and seat number</li>
              <li>• Marks are automatically fetched from admin uploads</li>
              <li>• Update your seat number each semester to sync new marks</li>
              <li>• No manual marks entry required</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};