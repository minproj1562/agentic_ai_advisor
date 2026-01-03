// useMLPredictions.ts - COMPLETE FIXED VERSION
import { useState, useEffect, useCallback } from 'react';
import { collection, query, where, getDocs } from 'firebase/firestore';
import { firebaseApp } from '../../../../core/integrations/firebase/config';

// Define proper TypeScript interfaces
interface StudentSubject {
  subject_code: string;
  subject_name: string;
  credits: number;
  current_grade: string;
  attendance: number;
  assignments_completed?: number;
  total_assignments?: number;
  midterm_score?: number;
  final_score?: number;
}

interface Weakness {
  subject: string;
  severity: string;
  reason: string;
  improvement_suggestions?: string[];
  affected_subjects?: string[];
}

interface Strength {
  subject: string;
  severity: string;
  evidence: string[];
}

interface Prediction {
  next_semester_sgpa: number;
  expected_graduation_cgpa: number;
  failure_risk: string;
  key_factors: string[];
  improvement_recommendations: string[];
  confidence_score: number;
  career_recommendations?: string[];
  last_updated?: string;
}

interface FirebaseStudentData {
  student_id: string;
  email: string;
  name: string;
  department: string;
  semester: number;
  latest_sgpa: number;
  cumulative_cgpa: number;
  attendance_percentage: number;
  improvement_trend: string;
  class_rank?: number;
  total_students?: number;
  enrollment_year?: number;
  current_subjects: StudentSubject[];
  performance_history: any[];
  weaknesses: Weakness[];
  strengths: Strength[];
  predictions: Prediction;
  analytics?: any;
  extracurriculars?: any[];
  achievements?: string[];
}

interface ImprovementPotential {
  current: number;
  potential_max: number;
  time_to_achieve: string;
  focus_areas: string[];
  recommended_focus_areas?: string[];
  estimated_effort_hours?: number;
}

interface PredictionsData {
  student_info: {
    name: string;
    email: string;
    department: string;
    semester: number;
    enrollment_year?: number;
    class_rank?: number;
    total_students?: number;
  };
  academic_performance: {
    latest_sgpa: number;
    cumulative_cgpa: number;
    improvement_trend: string;
    attendance_percentage: number;
  };
  predicted_sgpa: number;
  confidence: number;
  trend: string;
  risk_factors: Array<{
    factor: string;
    severity: string;
  }>;
  improvement_potential: ImprovementPotential;
  current_subjects: StudentSubject[];
  weaknesses: Weakness[];
  strengths: Strength[];
  analytics_scores?: any;
  career_recommendations?: string[];
  _source?: string;
  _raw?: any;
}

/**
 * Main hook for fetching student predictions from Firebase
 */
export const useMLPredictions = (studentEmail: string) => {
  const [predictions, setPredictions] = useState<PredictionsData | null>(null);
  const [studentData, setStudentData] = useState<FirebaseStudentData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<'firebase' | 'mock' | null>(null);

  const fetchPredictions = useCallback(async () => {
    if (!studentEmail) return;

    setLoading(true);
    setError(null);
    setDataSource(null);
    
    console.log('🔍 [DEBUG] ========== HOOK EXECUTING ==========');
    console.log('🔍 [DEBUG] Email being searched:', studentEmail);

    try {
      console.log('🔍 [DEBUG] Initializing Firebase...');
      firebaseApp.initialize();
      const firestore = firebaseApp.getFirestore();
      
      console.log('🔍 [DEBUG] Creating Firebase query...');
      const studentsQuery = query(
        collection(firestore, 'students'),
        where('email', '==', studentEmail.toLowerCase())
      );
      
      console.log('🔍 [DEBUG] Executing query...');
      const querySnapshot = await getDocs(studentsQuery);
      
      console.log('🔍 [DEBUG] Query result - documents found:', querySnapshot.size);
      
      if (!querySnapshot.empty) {
        console.log('🔍 [DEBUG] ✅ STUDENT FOUND IN FIREBASE');
        const studentDoc = querySnapshot.docs[0];
        const firebaseData = studentDoc.data() as FirebaseStudentData;
        
        console.log('🔍 [DEBUG] Student name:', firebaseData.name);
        console.log('🔍 [DEBUG] SGPA:', firebaseData.latest_sgpa);
        console.log('🔍 [DEBUG] Department:', firebaseData.department);
        console.log('🔍 [DEBUG] Subjects:', firebaseData.current_subjects);
        console.log('🔍 [DEBUG] Full Firebase data:', firebaseData);
        
        setStudentData(firebaseData);
        setDataSource('firebase');
        
        // Transform Firebase data to predictions format
        const predictionsData: PredictionsData = {
          // Student Info
          student_info: {
            name: firebaseData.name,
            email: firebaseData.email,
            department: firebaseData.department,
            semester: firebaseData.semester,
            enrollment_year: firebaseData.enrollment_year,
            class_rank: firebaseData.class_rank,
            total_students: firebaseData.total_students
          },
          
          // Academic Performance
          academic_performance: {
            latest_sgpa: firebaseData.latest_sgpa,
            cumulative_cgpa: firebaseData.cumulative_cgpa,
            improvement_trend: firebaseData.improvement_trend,
            attendance_percentage: firebaseData.attendance_percentage
          },
          
          // Predictions
          predicted_sgpa: firebaseData.predictions?.next_semester_sgpa || 0,
          confidence: firebaseData.predictions?.confidence_score || 0,
          trend: firebaseData.improvement_trend || 'stable',
          
          // Risk Analysis
          risk_factors: firebaseData.predictions?.key_factors?.map((factor: string) => ({
            factor,
            severity: getSeverity(factor, firebaseData)
          })) || [],
          
          // Improvement Potential
          improvement_potential: {
            current: firebaseData.latest_sgpa,
            potential_max: Math.min(10, firebaseData.latest_sgpa + 1.5),
            recommended_focus_areas: firebaseData.predictions?.improvement_recommendations || ['General Studies'],
            estimated_effort_hours: calculateEstimatedEffort(firebaseData.predictions?.failure_risk || 'medium'),
            time_to_achieve: getTimeToAchieve(firebaseData.improvement_trend),
            focus_areas: firebaseData.weaknesses?.map((w: Weakness) => w.subject) || ['General Studies']
          },
          
          // Current Subjects
          current_subjects: firebaseData.current_subjects || [],
          
          // Weaknesses & Strengths
          weaknesses: firebaseData.weaknesses || [],
          strengths: firebaseData.strengths || [],
          
          // Analytics
          analytics_scores: firebaseData.analytics || {},
          
          // Career Guidance
          career_recommendations: firebaseData.predictions?.career_recommendations || ['Software Developer', 'Data Analyst'],
          
          // Raw data for debugging
          _raw: firebaseData,
          _source: 'firebase'
        };
        
        console.log('🔍 [DEBUG] ✅ TRANSFORMED DATA:', predictionsData);
        setPredictions(predictionsData);
        
      } else {
        console.log('🔍 [DEBUG] ❌ STUDENT NOT FOUND IN FIREBASE - using mock data');
        setDataSource('mock');
        // Fallback to mock data
        const mockData = getMockPredictions(studentEmail);
        console.log('🔍 [DEBUG] 🎭 USING MOCK DATA:', mockData);
        setPredictions(mockData);
      }

    } catch (err) {
      console.error('🔍 [DEBUG] 💥 ERROR FETCHING FROM FIREBASE:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch student data');
      
      // Fallback to mock data
      console.log('🔍 [DEBUG] 🎭 FALLING BACK TO MOCK DATA DUE TO ERROR');
      setDataSource('mock');
      const mockData = getMockPredictions(studentEmail);
      setPredictions(mockData);
    } finally {
      setLoading(false);
      console.log('🔍 [DEBUG] ========== HOOK COMPLETED ==========');
    }
  }, [studentEmail]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  return {
    predictions,
    studentData, // Full student data from Firebase
    loading,
    error,
    dataSource, // 'firebase' or 'mock'
    refetch: fetchPredictions
  };
};

/**
 * Hook for calculating improvement potential
 * This hook depends on useMLPredictions data
 */
export const useImprovementPotential = (studentEmail: string) => {
  const [potential, setPotential] = useState<ImprovementPotential | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use the main predictions hook
  const { predictions, loading: predictionsLoading, error: predictionsError } = useMLPredictions(studentEmail);

  useEffect(() => {
    console.log('🔍 [DEBUG] ImprovementPotential - predictions changed:', predictions);
    if (predictions?.improvement_potential) {
      console.log('🔍 [DEBUG] ImprovementPotential - setting potential from predictions');
      setPotential(predictions.improvement_potential);
    }
  }, [predictions]);

  const calculatePotential = useCallback(async () => {
    if (!studentEmail) return;

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 [DEBUG] ImprovementPotential - calculating...');
      // If we have predictions data, use it
      if (predictions?.improvement_potential) {
        console.log('🔍 [DEBUG] ImprovementPotential - using predictions data');
        setPotential(predictions.improvement_potential);
      } else {
        console.log('🔍 [DEBUG] ImprovementPotential - using fallback calculation');
        // Fallback calculation based on email
        const fallbackPotential: ImprovementPotential = {
          current: 8.2,
          potential_max: 9.4,
          time_to_achieve: '2 semesters',
          focus_areas: ['Mathematics', 'Research Projects'],
          estimated_effort_hours: 12
        };
        setPotential(fallbackPotential);
      }
    } catch (err) {
      console.error('🔍 [DEBUG] ImprovementPotential - error:', err);
      setError(err instanceof Error ? err.message : 'Failed to calculate improvement potential');
    } finally {
      setLoading(false);
    }
  }, [studentEmail, predictions]);

  useEffect(() => {
    calculatePotential();
  }, [calculatePotential]);

  return {
    potential,
    loading: loading || predictionsLoading,
    error: error || predictionsError,
    recalculate: calculatePotential
  };
};

// Helper functions
function getSeverity(factor: string, studentData: FirebaseStudentData): string {
  if (studentData.predictions?.failure_risk === 'high') return 'high';
  if (studentData.predictions?.failure_risk === 'medium') return 'medium';
  return 'low';
}

function calculateEstimatedEffort(riskLevel: string): number {
  switch (riskLevel) {
    case 'high': return 20;
    case 'medium': return 15;
    case 'low': return 10;
    default: return 12;
  }
}

function getTimeToAchieve(trend: string): string {
  switch (trend) {
    case 'improving': return '1-2 semesters';
    case 'stable': return '2-3 semesters';
    case 'declining': return '3-4 semesters';
    default: return '2 semesters';
  }
}

// Mock data fallback
function getMockPredictions(email: string): PredictionsData {
  console.log('🔍 [DEBUG] 🎭 CREATING MOCK DATA FOR:', email);
  return {
    student_info: {
      name: "Mock Student",
      email: email,
      department: "Computer Science",
      semester: 6
    },
    academic_performance: {
      latest_sgpa: 9.02, // This matches what you're seeing!
      cumulative_cgpa: 8.11,
      improvement_trend: "improving",
      attendance_percentage: 83
    },
    predicted_sgpa: 0.00,
    confidence: 0.2,
    trend: "stable",
    risk_factors: [
      { factor: "Mathematics", severity: "medium" },
      { factor: "Physics", severity: "low" },
      { factor: "Data Structures", severity: "high" }
    ],
    improvement_potential: {
      current: 9.02,
      potential_max: 9.5,
      time_to_achieve: "2 semesters",
      focus_areas: ["Mathematics", "Physics", "Data Structures"],
      recommended_focus_areas: ["Mathematics", "Physics", "Data Structures"],
      estimated_effort_hours: 15
    },
    current_subjects: [
      {
        subject_code: "MATH101",
        subject_name: "Mathematics",
        credits: 4,
        current_grade: "B+",
        attendance: 80
      },
      {
        subject_code: "PHY101",
        subject_name: "Physics",
        credits: 4,
        current_grade: "B",
        attendance: 75
      },
      {
        subject_code: "CHEM101",
        subject_name: "Chemistry",
        credits: 3,
        current_grade: "B-",
        attendance: 70
      }
    ],
    weaknesses: [
      {
        subject: "Mathematics",
        severity: "medium",
        reason: "15% gap in understanding"
      },
      {
        subject: "Data Structures",
        severity: "high", 
        reason: "Trees concept needs improvement"
      }
    ],
    strengths: [
      {
        subject: "Study Consistency",
        severity: "medium",
        evidence: ["Good improvement trend"]
      }
    ],
    career_recommendations: ["Software Engineer", "Data Analyst"],
    _source: 'mock'
  };
}