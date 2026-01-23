import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
  Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { auth } from '../../services/firebase.config';

interface SubjectEntry {
  subject_code: string;
  subject_name: string;
  credits: number;
  internal_marks: number;
  external_marks: number;
  is_elective: boolean;
  is_practical: boolean;
}

interface ProfileData {
  name: string;
  roll_number: string;
  branch: string;
  admission_year: number;
  email: string;
  // Removed current_semester and academic_year - they'll be calculated on backend
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
  
  // Profile form - REMOVED current_semester and academic_year
  const [profileForm, setProfileForm] = useState<ProfileData>({
    name: user?.name || '', // Changed from displayName to name
    roll_number: '',
    branch: 'IT',
    admission_year: new Date().getFullYear(),
    email: user?.email || ''
  });
  
  // Subjects form
  const [subjects, setSubjects] = useState<SubjectEntry[]>([
    {
      subject_code: '',
      subject_name: '',
      credits: 3,
      internal_marks: 0,
      external_marks: 0,
      is_elective: false,
      is_practical: false
    }
  ]);
  
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
      // Odd semester (July-Dec)
      calculatedAcademicYear = `${currentYear}-${(currentYear + 1).toString().slice(2)}`;
      semester = (currentYear - admissionYear) * 2 + 1;
    } else {
      // Even semester (Jan-June)
      calculatedAcademicYear = `${currentYear - 1}-${currentYear.toString().slice(2)}`;
      semester = (currentYear - admissionYear) * 2;
    }
    
    // Cap at 8 semesters
    semester = Math.min(Math.max(semester, 1), 8);
    
    return { semester, academicYear: calculatedAcademicYear };
  };
  
  // Backend health check
  const isBackendRunning = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${BACKEND_URL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  };
  
  // Check if profile exists
  const checkProfile = async () => {
    if (!user) return;
    
    try {
      setProfileLoading(true);
      const token = await auth.currentUser?.getIdToken();
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
        
        // Set current semester and academic year from backend
        setCurrentSemester(data.current_semester);
        setAcademicYear(data.current_academic_year);
        setSelectedSemester(data.current_semester);
        
        // Populate form with existing data
        setProfileForm({
          name: data.name || user.name || '', // Changed from displayName to name
          roll_number: data.roll_number || '',
          branch: data.branch || 'IT',
          admission_year: data.admission_year || new Date().getFullYear(),
          email: data.email || user.email || ''
        });
        
        toast.success('Profile loaded successfully');
      } else if (response.status === 404) {
        setProfileExists(false);
        // Calculate academic details for new profile
        const academicDetails = calculateAcademicDetails(profileForm.admission_year);
        setCurrentSemester(academicDetails.semester);
        setAcademicYear(academicDetails.academicYear);
        setSelectedSemester(academicDetails.semester);
      }
    } catch (error) {
      console.error('Error checking profile:', error);
      setProfileExists(false);
    } finally {
      setProfileLoading(false);
    }
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
  
  // Save profile
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
      
      const token = await auth.currentUser?.getIdToken();
      if (!token) {
        toast.error('Authentication token not available');
        return;
      }
      
      // Prepare profile data - DON'T include current_semester or academic_year
      const profileData = {
        ...profileForm,
        email: profileForm.email || user.email || ''
      };
      
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
        
        // Trigger dashboard refresh
        window.dispatchEvent(new Event('profileUpdated'));
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Failed to save profile');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Failed to save profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Add subject
  const addSubject = () => {
    setSubjects([...subjects, {
      subject_code: '',
      subject_name: '',
      credits: 3,
      internal_marks: 0,
      external_marks: 0,
      is_elective: false,
      is_practical: false
    }]);
  };
  
  // Remove subject
  const removeSubject = (index: number) => {
    if (subjects.length > 1) {
      const newSubjects = [...subjects];
      newSubjects.splice(index, 1);
      setSubjects(newSubjects);
    }
  };
  
  // Update subject
  const updateSubject = (index: number, field: keyof SubjectEntry, value: any) => {
    const updated = [...subjects];
    updated[index] = { ...updated[index], [field]: value };
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
    
    // Validate subjects
    const invalidSubjects = subjects.filter(subject => 
      !subject.subject_code.trim() || 
      !subject.subject_name.trim() || 
      subject.credits <= 0
    );
    
    if (invalidSubjects.length > 0) {
      toast.error('Please fill all subject fields with valid data');
      return;
    }
    
    // Validate marks
    const invalidMarks = subjects.filter(subject => 
      subject.internal_marks < 0 || subject.internal_marks > 20 ||
      subject.external_marks < 0 || subject.external_marks > 80
    );
    
    if (invalidMarks.length > 0) {
      toast.error('Marks must be within valid ranges (Internal: 0-20, External: 0-80)');
      return;
    }
    
    try {
      setLoading(true);
      
      const token = await auth.currentUser?.getIdToken();
      if (!token) {
        toast.error('Authentication token not available');
        return;
      }
      
      const requestData = {
        semester_number: selectedSemester,
        academic_year: academicYear,
        subjects: subjects.map(subject => ({
          ...subject,
          total_marks: calculateTotalMarks(subject),
          grade: calculateGrade(calculateTotalMarks(subject)).grade,
          grade_points: calculateGrade(calculateTotalMarks(subject)).points
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
        
        // Clear form
        setSubjects([{
          subject_code: '',
          subject_name: '',
          credits: 3,
          internal_marks: 0,
          external_marks: 0,
          is_elective: false,
          is_practical: false
        }]);
        
        // Trigger dashboard refresh
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
  
  // Import from CSV
  const handleCSVImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const rows = text.split('\n').filter(row => row.trim());
        
        if (rows.length < 2) {
          toast.error('CSV file is empty or has no data rows');
          return;
        }
        
        const headers = rows[0].split(',').map(h => h.trim().toLowerCase());
        const requiredHeaders = ['subject_code', 'subject_name', 'credits', 'internal_marks', 'external_marks'];
        
        const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
        if (missingHeaders.length > 0) {
          toast.error(`Missing required columns: ${missingHeaders.join(', ')}`);
          return;
        }
        
        const importedSubjects: SubjectEntry[] = [];
        
        for (let i = 1; i < rows.length; i++) {
          const values = rows[i].split(',').map(v => v.trim());
          
          // Skip empty rows
          if (values.every(v => !v)) continue;
          
          const subject: SubjectEntry = {
            subject_code: values[headers.indexOf('subject_code')] || '',
            subject_name: values[headers.indexOf('subject_name')] || '',
            credits: parseInt(values[headers.indexOf('credits')]) || 3,
            internal_marks: parseFloat(values[headers.indexOf('internal_marks')]) || 0,
            external_marks: parseFloat(values[headers.indexOf('external_marks')]) || 0,
            is_elective: values[headers.indexOf('is_elective')]?.toLowerCase() === 'true' || false,
            is_practical: values[headers.indexOf('is_practical')]?.toLowerCase() === 'true' || false
          };
          
          // Validate subject
          if (subject.subject_code && subject.subject_name) {
            importedSubjects.push(subject);
          }
        }
        
        if (importedSubjects.length === 0) {
          toast.error('No valid subjects found in CSV file');
          return;
        }
        
        setSubjects(importedSubjects);
        toast.success(`Imported ${importedSubjects.length} subjects`);
      } catch (error) {
        console.error('CSV import error:', error);
        toast.error('Failed to parse CSV file. Please check the format.');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };
  
  // Download CSV template
  const downloadCSVTemplate = () => {
    const headers = ['subject_code', 'subject_name', 'credits', 'internal_marks', 'external_marks', 'is_elective', 'is_practical'];
    const exampleRow = ['CSIT301', 'Data Structures and Algorithms', '3', '18', '65', 'false', 'false'];
    
    const csvContent = [headers.join(','), exampleRow.join(',')].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'academic_scores_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  // Refresh profile
  const refreshProfile = async () => {
    await checkProfile();
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
            </h2>
            
            <div className="flex items-center gap-3">
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
              
              <div className="flex gap-2">
                <button
                  onClick={downloadCSVTemplate}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2 text-sm"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  Template
                </button>
                
                <label className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 cursor-pointer flex items-center gap-2 text-sm">
                  <Upload className="w-4 h-4" />
                  Import CSV
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleCSVImport}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          </div>
          
          {/* Subject List */}
          <div className="space-y-4">
            {subjects.map((subject, index) => {
              const totalMarks = calculateTotalMarks(subject);
              const gradeInfo = calculateGrade(totalMarks);
              
              return (
                <div key={index} className="p-4 border rounded-lg bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Subject Code</label>
                      <input
                        type="text"
                        placeholder="CSIT301"
                        value={subject.subject_code}
                        onChange={(e) => updateSubject(index, 'subject_code', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg text-sm"
                      />
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-xs text-gray-600 mb-1">Subject Name</label>
                      <input
                        type="text"
                        placeholder="Data Structures and Algorithms"
                        value={subject.subject_name}
                        onChange={(e) => updateSubject(index, 'subject_name', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Credits</label>
                      <input
                        type="number"
                        placeholder="3"
                        value={subject.credits}
                        onChange={(e) => updateSubject(index, 'credits', parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 border rounded-lg text-sm"
                        min={1}
                        max={6}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Internal (20)</label>
                      <input
                        type="number"
                        placeholder="0"
                        value={subject.internal_marks}
                        onChange={(e) => updateSubject(index, 'internal_marks', parseFloat(e.target.value) || 0)}
                        className="w-full px-3 py-2 border rounded-lg text-sm"
                        min={0}
                        max={20}
                        step="0.5"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">External (80)</label>
                      <input
                        type="number"
                        placeholder="0"
                        value={subject.external_marks}
                        onChange={(e) => updateSubject(index, 'external_marks', parseFloat(e.target.value) || 0)}
                        className="w-full px-3 py-2 border rounded-lg text-sm"
                        min={0}
                        max={80}
                        step="0.5"
                      />
                    </div>
                  </div>
                  
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={subject.is_elective}
                          onChange={(e) => updateSubject(index, 'is_elective', e.target.checked)}
                          className="rounded"
                        />
                        Elective
                      </label>
                      
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={subject.is_practical}
                          onChange={(e) => updateSubject(index, 'is_practical', e.target.checked)}
                          className="rounded"
                        />
                        Practical
                      </label>
                      
                      {/* Show calculated grade and total marks */}
                      {totalMarks > 0 && (
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Total:</span>
                            <span className="font-bold text-gray-800">
                              {totalMarks}/100
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Grade:</span>
                            <span className={`font-bold ${gradeInfo.color}`}>
                              {gradeInfo.grade}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Points:</span>
                            <span className="font-bold">
                              {gradeInfo.points}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <button
                      onClick={() => removeSubject(index)}
                      className="p-1 text-red-500 hover:text-red-700"
                      disabled={subjects.length === 1}
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Actions */}
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={addSubject}
              className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Subject
            </button>
            
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">
                {subjects.length} subject{subjects.length !== 1 ? 's' : ''} added
              </span>
              <button
                onClick={saveSubjects}
                disabled={loading || subjects.length === 0 || subjects.some(s => !s.subject_code.trim() || !s.subject_name.trim()) || !backendAvailable}
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
          </div>
        </motion.div>
      )}
      
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">How it works:</p>
            <ul className="mt-2 text-sm text-blue-700 space-y-1">
              <li>• Your semester automatically updates based on your admission year</li>
              <li>• Enter your subject scores at the end of each semester</li>
              <li>• AI analyzes your performance to recommend electives and career paths</li>
              <li>• CGPA is automatically calculated from all your semester records</li>
              <li>• You can import scores from a CSV file for quick entry</li>
              <li>• Download the CSV template to ensure proper formatting</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};