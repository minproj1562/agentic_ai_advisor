// academic-advisor-frontend/src/components/dashboard/AcademicDataEntry.tsx

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GraduationCap,
  Plus,
  Save,
  AlertCircle,
  CheckCircle,
  Upload,
  FileSpreadsheet,
  BookOpen,
  X,
  Loader2,
  Book,
  ChevronDown,
  Info,
  TrendingUp,
  Award,
  Calendar
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { auth } from '../../services/firebase.config';

interface SubjectDefinition {
  subject_code: string;
  subject_name: string;
  credits: number;
  course_type: 'PCC' | 'PEC' | 'LBC' | 'SBL' | 'MNP' | 'MJP' | 'INT' | 'BSC' | 'ESC' | 'AEC' | 'OEC';
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

interface ElectiveOption {
  code: string;
  name: string;
}

interface CurriculumData {
  semester: number;
  admission_year: number;
  curriculum_type: 'Pre-Autonomy' | 'Autonomy';
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

interface ProfileData {
  name: string;
  roll_number: string;
  branch: string;
  admission_year: number;
  email: string;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const AcademicDataEntry: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [profileExists, setProfileExists] = useState(false);
  const [currentSemester, setCurrentSemester] = useState(1);
  const [academicYear, setAcademicYear] = useState('');
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  
  // Available subjects from backend
  const [availableSubjects, setAvailableSubjects] = useState<CurriculumData | null>(null);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  
  // Profile form
  const [profileForm, setProfileForm] = useState<ProfileData>({
    name: user?.name || '',
    roll_number: '',
    branch: 'IT',
    admission_year: new Date().getFullYear(),
    email: user?.email || ''
  });
  
  // Subjects form - now dynamically populated
  const [subjects, setSubjects] = useState<SubjectEntry[]>([]);
  
  const [selectedSemester, setSelectedSemester] = useState(1);
  
  // Branch options for FCRIT
  const branches = ['IT', 'COMP', 'EXTC', 'MECH', 'ELEC'];
  
  // Calculate current semester and academic year based on admission year
  const calculateAcademicDetails = (admissionYear: number) => {
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1;
    
    let semester = 1;
    let calculatedAcademicYear = '';
    
    if (currentMonth >= 7) {
      calculatedAcademicYear = `${currentYear}-${(currentYear + 1).toString().slice(2)}`;
      semester = (currentYear - admissionYear) * 2 + 1;
    } else {
      calculatedAcademicYear = `${currentYear - 1}-${currentYear.toString().slice(2)}`;
      semester = (currentYear - admissionYear) * 2;
    }
    
    semester = Math.min(Math.max(semester, 1), 8);
    
    return { semester, academicYear: calculatedAcademicYear };
  };
  
  // Backend health check
  const isBackendRunning = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${BACKEND_URL}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  };
  
  // Check if profile exists - UPDATED VERSION
  const checkProfile = async () => {
    if (!user) return;
    
    try {
      setProfileLoading(true);
      
      // FIXED: Get token from Firebase Auth directly
      const currentUser = auth.currentUser;
      if (!currentUser) {
        console.log('No authenticated user for profile check');
        return;
      }
      
      const token = await currentUser.getIdToken();
      if (!token) {
        toast.error('Authentication token not available');
        return;
      }
      
      const response = await fetch(`${BACKEND_URL}/api/v1/student/profile`, {
        method: 'GET',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfileExists(true);
        setCurrentSemester(data.current_semester);
        setAcademicYear(data.current_academic_year);
        setSelectedSemester(data.current_semester);
        
        setProfileForm({
          name: data.name || user.name || '',
          roll_number: data.roll_number || '',
          branch: data.branch || 'IT',
          admission_year: data.admission_year || new Date().getFullYear(),
          email: data.email || user.email || ''
        });
        
        toast.success('Profile loaded successfully');
      } else if (response.status === 404) {
        setProfileExists(false);
        const academicDetails = calculateAcademicDetails(profileForm.admission_year);
        setCurrentSemester(academicDetails.semester);
        setAcademicYear(academicDetails.academicYear);
        setSelectedSemester(academicDetails.semester);
      } else {
        console.error('Profile check failed:', response.status);
      }
    } catch (error) {
      console.error('Error checking profile:', error);
      setProfileExists(false);
    } finally {
      setProfileLoading(false);
    }
  };
  
  // Fetch available subjects for selected semester
  const fetchAvailableSubjects = async (semester: number) => {
    if (!user || !profileExists) return;
    
    try {
      setLoadingSubjects(true);
      
      // FIXED: Get token from Firebase Auth directly
      const currentUser = auth.currentUser;
      if (!currentUser) {
        toast.error('Not authenticated. Please login again.');
        return;
      }
      
      const token = await currentUser.getIdToken(true);
      if (!token) {
        toast.error('Authentication token not available');
        return;
      }
      
      const response = await fetch(
        `${BACKEND_URL}/api/v1/academic/subjects/available/${semester}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setAvailableSubjects(data);
        
        // Initialize subject entries from available subjects
        initializeSubjectEntries(data);
        
        toast.success(`Subjects loaded for Semester ${semester} (${data.curriculum_type})`);
      } else {
        toast.error('Failed to load subjects');
      }
    } catch (error) {
      console.error('Error fetching subjects:', error);
      toast.error('Error loading subjects');
    } finally {
      setLoadingSubjects(false);
    }
  };
  
  // Initialize subject entries from curriculum data
  const initializeSubjectEntries = (curriculum: CurriculumData) => {
    const entries: SubjectEntry[] = [];
    
    // Add theory subjects
    curriculum.theory_subjects.forEach(subject => {
      entries.push({
        ...subject,
        internal_marks: 0,
        external_marks: 0
      });
    });
    
    // Add lab subjects
    curriculum.lab_subjects.forEach(subject => {
      entries.push({
        ...subject,
        internal_marks: 0,
        external_marks: 0
      });
    });
    
    // Add project subjects
    curriculum.project_subjects.forEach(subject => {
      entries.push({
        ...subject,
        internal_marks: 0,
        external_marks: 0
      });
    });
    
    // Add elective placeholders
    Object.entries(curriculum.elective_groups).forEach(([groupName, groupData]) => {
      entries.push({
        ...groupData.subject_template,
        internal_marks: 0,
        external_marks: 0,
        selected_elective_code: '',
        selected_elective_name: ''
      });
    });
    
    setSubjects(entries);
  };
  
  // Check backend health and profile on component mount
  useEffect(() => {
    const initialize = async () => {
      if (user) {
        const isRunning = await isBackendRunning();
        setBackendAvailable(isRunning);
        
        if (isRunning) {
          await checkProfile();
        } else {
          toast.error('Backend server is not running. Please start the backend server.');
        }
      }
    };
    
    initialize();
  }, [user]);
  
  // Fetch subjects when semester changes
  useEffect(() => {
    if (profileExists && selectedSemester) {
      fetchAvailableSubjects(selectedSemester);
    }
  }, [selectedSemester, profileExists]);
  
  // Save profile - UPDATED VERSION
  const saveProfile = async () => {
    if (!user) {
      toast.error('User not authenticated');
      return;
    }
    
    if (!profileForm.name.trim()) {
      toast.error('Please enter your name');
      return;
    }
    
    if (!profileForm.roll_number.trim()) {
      toast.error('Please enter your roll number');
      return;
    }
    
    try {
      setLoading(true);
      
      // FIXED: Get token from Firebase Auth directly
      const currentUser = auth.currentUser;
      if (!currentUser) {
        toast.error('Not authenticated. Please login again.');
        return;
      }
      
      const token = await currentUser.getIdToken(true);
      if (!token) {
        toast.error('Authentication token not available');
        return;
      }
      
      const profileData = {
        ...profileForm,
        email: profileForm.email || user.email || ''
      };
      
      console.log('Saving profile with token:', token.substring(0, 20) + '...');
      
      const response = await fetch(`${BACKEND_URL}/api/v1/student/profile/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfileExists(true);
        setCurrentSemester(data.current_semester);
        setAcademicYear(data.current_academic_year);
        
        toast.success('Profile saved successfully!');
        
        // Dispatch events for other components
        window.dispatchEvent(new Event('profileUpdated'));
        window.dispatchEvent(new CustomEvent('profileSaved', { 
          detail: {
            name: data.name,
            branch: data.branch,
            semester: data.current_semester,
            cgpa: data.cgpa || 0,
            admission_year: data.admission_year,
            academic_year: data.current_academic_year,
            total_credits: 0,
            roll_number: data.roll_number
          }
        }));
        
        // Fetch subjects for current semester
        await fetchAvailableSubjects(data.current_semester);
      } else {
        const errorData = await response.json();
        console.error('Profile save failed:', errorData);
        toast.error(errorData.detail || 'Failed to save profile');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Failed to save profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Update subject marks
  const updateSubject = (index: number, field: 'internal_marks' | 'external_marks' | 'selected_elective_code', value: any) => {
    const updated = [...subjects];
    
    if (field === 'selected_elective_code' && availableSubjects) {
      // Find elective option and update both code and name
      const subject = updated[index];
      const groupData = availableSubjects.elective_groups[subject.elective_group || ''];
      
      if (groupData) {
        const selectedOption = groupData.options.find(opt => opt.code === value);
        if (selectedOption) {
          updated[index].selected_elective_code = selectedOption.code;
          updated[index].selected_elective_name = selectedOption.name;
          updated[index].subject_code = selectedOption.code;
          updated[index].subject_name = selectedOption.name;
        }
      }
    } else {
      updated[index] = { ...updated[index], [field]: value };
    }
    
    setSubjects(updated);
  };
  
  // Calculate grade from marks
  const calculateGrade = (total: number) => {
    if (total >= 90) return { grade: 'O', points: 10, color: 'text-green-600' };
    if (total >= 80) return { grade: 'A+', points: 9, color: 'text-green-500' };
    if (total >= 70) return { grade: 'A', points: 8, color: 'text-blue-600' };
    if (total >= 60) return { grade: 'B+', points: 7, color: 'text-blue-500' };
    if (total >= 50) return { grade: 'B', points: 6, color: 'text-yellow-600' };
    if (total >= 45) return { grade: 'C', points: 5, color: 'text-yellow-500' };
    if (total >= 40) return { grade: 'P', points: 4, color: 'text-orange-500' };
    return { grade: 'F', points: 0, color: 'text-red-600' };
  };
  
  // Calculate total marks for a subject
  const calculateTotalMarks = (subject: SubjectEntry) => {
    return subject.internal_marks + subject.external_marks;
  };
  
  // Validate subject entry
  const validateSubject = (subject: SubjectEntry): boolean => {
    // Check if elective is selected
    if (subject.is_elective && !subject.selected_elective_code) {
      return false;
    }
    
    // Check marks validity
    if (subject.internal_marks < 0 || subject.internal_marks > subject.internal_max) {
      return false;
    }
    
    if (subject.external_marks < 0 || subject.external_marks > subject.external_max) {
      return false;
    }
    
    return true;
  };
  
  // Save subjects
  const saveSubjects = async () => {
    if (!user) {
      toast.error('User not authenticated');
      return;
    }
    
    if (!profileExists) {
      toast.error('Please create your profile first');
      return;
    }
    
    // Validate all subjects
    const invalidSubjects = subjects.filter(subject => !validateSubject(subject));
    
    if (invalidSubjects.length > 0) {
      toast.error('Please complete all subject entries with valid data');
      return;
    }
    
    // Check if all electives are selected
    const unselectedElectives = subjects.filter(
      subject => subject.is_elective && !subject.selected_elective_code
    );
    
    if (unselectedElectives.length > 0) {
      toast.error('Please select all elective courses');
      return;
    }
    
    try {
      setLoading(true);
      
      // FIXED: Get token from Firebase Auth directly
      const currentUser = auth.currentUser;
      if (!currentUser) {
        toast.error('Not authenticated. Please login again.');
        return;
      }
      
      const token = await currentUser.getIdToken(true);
      if (!token) {
        toast.error('Authentication token not available');
        return;
      }
      
      const requestData = {
        semester_number: selectedSemester,
        academic_year: academicYear,
        subjects: subjects.map(subject => ({
          subject_code: subject.selected_elective_code || subject.subject_code,
          subject_name: subject.selected_elective_name || subject.subject_name,
          credits: subject.credits,
          internal_marks: subject.internal_marks,
          external_marks: subject.external_marks,
          total_marks: calculateTotalMarks(subject),
          grade: calculateGrade(calculateTotalMarks(subject)).grade,
          grade_points: calculateGrade(calculateTotalMarks(subject)).points,
          is_elective: subject.is_elective,
          is_practical: subject.is_practical
        }))
      };
      
      const response = await fetch(`${BACKEND_URL}/api/v1/academic/scores/add`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`Semester ${selectedSemester} data saved! SGPA: ${data.semester_sgpa || 'N/A'}`);
        
        // Clear form - reset to curriculum subjects
        if (availableSubjects) {
          initializeSubjectEntries(availableSubjects);
        }
        
        window.dispatchEvent(new CustomEvent('academicDataUpdated'));
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Failed to save subjects');
      }
    } catch (error) {
      console.error('Error saving subjects:', error);
      toast.error('Failed to save subjects. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Refresh profile
  const refreshProfile = async () => {
    await checkProfile();
  };
  
  // Get course type badge color
  const getCourseTypeBadge = (courseType: string) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      'PCC': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Core' },
      'PEC': { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Elective' },
      'LBC': { bg: 'bg-green-100', text: 'text-green-700', label: 'Lab' },
      'SBL': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Skill Lab' },
      'MNP': { bg: 'bg-pink-100', text: 'text-pink-700', label: 'Mini Project' },
      'MJP': { bg: 'bg-red-100', text: 'text-red-700', label: 'Major Project' },
      'INT': { bg: 'bg-indigo-100', text: 'text-indigo-700', label: 'Internship' },
      'BSC': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Basic Science' },
      'ESC': { bg: 'bg-teal-100', text: 'text-teal-700', label: 'Engg Science' },
      'AEC': { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Ability' },
      'OEC': { bg: 'bg-cyan-100', text: 'text-cyan-700', label: 'Open Elective' }
    };
    
    const badge = badges[courseType] || { bg: 'bg-gray-100', text: 'text-gray-700', label: courseType };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Academic Data Entry</h1>
            <p className="text-purple-100">
              Add your academic scores to get personalized AI recommendations
            </p>
          </div>
          <button
            onClick={refreshProfile}
            disabled={profileLoading}
            className="px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 flex items-center gap-2"
          >
            {profileLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4" />
            )}
            {profileLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
        <div className="mt-4 flex items-center gap-4">
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            Current Semester: {currentSemester}
          </span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            Academic Year: {academicYear || 'Not Set'}
          </span>
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
            Status: {profileExists ? 'Profile Complete' : 'Profile Pending'}
          </span>
          {availableSubjects && (
            <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
              Curriculum: {availableSubjects.curriculum_type}
            </span>
          )}
        </div>
      </div>

      {/* Backend Warning */}
      {!backendAvailable && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            <div>
              <p className="font-medium text-yellow-900">Backend Server Not Available</p>
              <p className="text-sm text-yellow-700">
                The academic data server is not running. Please start the backend server to save your academic data.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Profile Section */}
      {!profileExists && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border p-6"
        >
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <GraduationCap className="w-5 h-5 mr-2 text-purple-600" />
            Student Profile Setup
            {profileLoading && (
              <Loader2 className="w-4 h-4 ml-2 animate-spin" />
            )}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                value={profileForm.name}
                onChange={(e) => setProfileForm({...profileForm, name: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="John Doe"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Roll Number *
              </label>
              <input
                type="text"
                value={profileForm.roll_number}
                onChange={(e) => setProfileForm({...profileForm, roll_number: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="CSIT/2022/045"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Branch *
              </label>
              <select
                value={profileForm.branch}
                onChange={(e) => setProfileForm({...profileForm, branch: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                required
              >
                {branches.map(branch => (
                  <option key={branch} value={branch}>{branch}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Admission Year *
              </label>
              <input
                type="number"
                value={profileForm.admission_year}
                onChange={(e) => {
                  const year = parseInt(e.target.value) || new Date().getFullYear();
                  setProfileForm({...profileForm, admission_year: year});
                  const academicDetails = calculateAcademicDetails(year);
                  setCurrentSemester(academicDetails.semester);
                  setAcademicYear(academicDetails.academicYear);
                  setSelectedSemester(academicDetails.semester);
                }}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                min={2018}
                max={new Date().getFullYear()}
                required
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="john@example.com"
                required
              />
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <CheckCircle className="w-5 h-5 text-blue-600" />
              <p className="font-medium text-blue-900">Calculated Academic Details</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Current Semester:</span>
                <p className="font-medium">{currentSemester}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Academic Year:</span>
                <p className="font-medium">{academicYear}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              * These are calculated automatically based on your admission year
            </p>
          </div>
          
          <button
            onClick={saveProfile}
            disabled={loading || !profileForm.name.trim() || !profileForm.roll_number.trim() || !profileForm.email.trim()}
            className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        </motion.div>
      )}
      
      {/* Subject Entry Section */}
      {profileExists && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
              Add Subject Scores - Semester {selectedSemester}
              {availableSubjects && (
                <span className="ml-3 text-sm text-gray-500">
                  ({availableSubjects.curriculum_type})
                </span>
              )}
            </h2>
            
            <select
              value={selectedSemester}
              onChange={(e) => setSelectedSemester(parseInt(e.target.value))}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {[...Array(8)].map((_, i) => (
                <option key={i+1} value={i+1}>
                  Semester {i+1}
                </option>
              ))}
            </select>
          </div>
          
          {loadingSubjects ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="ml-3 text-gray-600">Loading curriculum subjects...</span>
            </div>
          ) : availableSubjects ? (
            <div className="space-y-4">
              {subjects.map((subject, index) => {
                const totalMarks = calculateTotalMarks(subject);
                const gradeInfo = calculateGrade(totalMarks);
                const maxMarks = subject.internal_max + subject.external_max;
                
                return (
                  <div key={index} className="p-4 border rounded-lg bg-gray-50">
                    {/* Subject Header */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {getCourseTypeBadge(subject.course_type)}
                        <span className="text-sm font-medium text-gray-700">
                          {subject.credits} Credits
                        </span>
                        {subject.is_elective && (
                          <span className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-full">
                            Elective
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Elective Selection */}
                    {subject.is_elective && subject.elective_group && availableSubjects.elective_groups[subject.elective_group] ? (
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Select {subject.elective_group} *
                        </label>
                        <select
                          value={subject.selected_elective_code || ''}
                          onChange={(e) => updateSubject(index, 'selected_elective_code', e.target.value)}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                          required
                        >
                          <option value="">-- Select Elective --</option>
                          {availableSubjects.elective_groups[subject.elective_group].options.map(option => (
                            <option key={option.code} value={option.code}>
                              {option.code} - {option.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <div className="mb-3">
                        <p className="font-medium text-gray-800">
                          {subject.subject_code} - {subject.subject_name}
                        </p>
                      </div>
                    )}
                    
                    {/* Marks Entry */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          Internal Marks ({subject.internal_max})
                        </label>
                        <input
                          type="number"
                          value={subject.internal_marks}
                          onChange={(e) => updateSubject(index, 'internal_marks', parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                          min={0}
                          max={subject.internal_max}
                          step="0.5"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          External Marks ({subject.external_max})
                        </label>
                        <input
                          type="number"
                          value={subject.external_marks}
                          onChange={(e) => updateSubject(index, 'external_marks', parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                          min={0}
                          max={subject.external_max}
                          step="0.5"
                        />
                      </div>
                      
                      {/* Grade Display */}
                      {totalMarks > 0 && (
                        <div className="flex items-center gap-4 bg-white rounded-lg p-2">
                          <div>
                            <span className="text-xs text-gray-600">Total</span>
                            <p className="font-bold text-gray-800">
                              {totalMarks}/{maxMarks}
                            </p>
                          </div>
                          <div>
                            <span className="text-xs text-gray-600">Grade</span>
                            <p className={`font-bold ${gradeInfo.color}`}>
                              {gradeInfo.grade}
                            </p>
                          </div>
                          <div>
                            <span className="text-xs text-gray-600">Points</span>
                            <p className="font-bold">
                              {gradeInfo.points}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Info className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>No subjects available. Please select a semester.</p>
            </div>
          )}
          
          {/* Actions */}
          {availableSubjects && subjects.length > 0 && (
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">
                  {subjects.length} subject{subjects.length !== 1 ? 's' : ''} • 
                  Semester {selectedSemester} • {availableSubjects.curriculum_type}
                </span>
              </div>
              <button
                onClick={saveSubjects}
                disabled={loading || subjects.length === 0 || !backendAvailable}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {loading ? 'Saving...' : 'Save Semester Data'}
              </button>
            </div>
          )}
        </motion.div>
      )}
      
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">Curriculum-Based Entry System</p>
            <ul className="mt-2 text-sm text-blue-700 space-y-1">
              <li>• Subjects are automatically loaded based on your admission year and semester</li>
              <li>• Pre-2024 students: Semesters 1-4 use Pre-Autonomy curriculum</li>
              <li>• 2024+ students: All semesters use new Autonomy curriculum</li>
              <li>• Electives must be selected from the provided dropdown list</li>
              <li>• Marks ranges vary by course type (Theory, Lab, Project)</li>
              <li>• Your CGPA is automatically calculated from all semester records</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};