// StudentDashboard.tsx
import React, { useState, useEffect } from 'react';
import StudentMeetingRequest from '../../components/meetings/StudentMeetingRequest';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Award,
  BookOpen,
  Users,
  FileText,
  Bell,
  Calendar,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Brain,
  Briefcase,
  Star,
  Activity,
  BarChart3,
  PieChart,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Search,
  Filter,
  RefreshCw,
  Download,
  Info,
  Sparkles,
  AlertCircle,
  GraduationCap,
  Lightbulb,
  ExternalLink,
  Code,
  FolderOpen,
  ChevronLeft,
  Loader2,
  Heart
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import PerformanceChart from '../../components/dashboard/PerformanceChart';
import StatCard from '../../components/common/StatCard';
import { analyticsService } from '../../services/analytics.service';
import { StudentProjectsList } from '../../components/dashboard/sections/StudentProjectsList';
import { StudentProjectsUpload } from '../../components/dashboard/sections/StudentProjectsUpload';
import { studentProjectsService } from '../../services/student_projects_cloudinary.service';
import { getStudentAnalysisService } from '../../services/student_analysis.service';
import { mlIntegrationService } from '../../modules/agent1/student-analysis/services/ml-integration.service';
import { realtimeSyncService } from '../../modules/agent1/student-analysis/services/realtime-sync.service';
import { DetailedAnalysis, PredictionResult, WeaknessData } from '../../modules/agent1/student-analysis/types/student-analysis.types';
import TrendAnalyzer from '../../modules/agent1/performance-analytics/components/TrendAnalyzer';
import SubjectPerformance from '../../modules/agent1/performance-analytics/components/SubjectPerformance';
import { ElectiveRecommender, WeaknessAnalyzer, StudyResources } from '../../components/dashboard/EngineeringGuidance';
import toast from 'react-hot-toast';
import { AcademicDataEntry } from '../../components/dashboard/AcademicDataEntry';
import { InterestManagement } from '../../components/dashboard/InterestManagement';
import { AcademicInsights } from '../../components/dashboard/AcademicInsights';
import { auth } from '../../services/firebase.config';

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Add localStorage persistence for user profile data
const PROFILE_STORAGE_KEY = 'academic_advisor_profile';

const saveProfileToStorage = (profile: any) => {
  if (profile) {
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify({
      ...profile,
      timestamp: Date.now()
    }));
  }
};

const loadProfileFromStorage = (): any => {
  try {
    const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      if (Date.now() - data.timestamp < 3600000) { // 1 hour cache
        return data;
      }
    }
  } catch (error) {
    console.error('Error loading profile from storage:', error);
  }
  return null;
};

// Define user type for better TypeScript support
interface AuthUser {
  uid: string;
  displayName?: string;
  email?: string;
  getIdToken?: () => Promise<string>;
}

// Extended types to include missing properties
interface ExtendedDetailedAnalysis {
  weaknesses?: WeaknessData[];
  performance_data?: {
    sgpa_trend?: Array<{
      semester: number;
      sgpa: number;
      credits: number;
    }>;
  };
  improvement_trend?: 'improving' | 'declining' | 'stable';
  department?: string;
  current_semester?: number;
  latest_sgpa?: number;
  cgpa?: number;
  weakness_count?: number;
  metadata?: {
    total_credits?: number;
  };
  risk_level?: 'low' | 'medium' | 'high';
  attendance?: number;
  batch?: number;
  profile_completeness?: number;
}

interface ExtendedWeaknessData {
  subject: string;
  topic?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  gap?: number;
}

interface ExtendedPredictionResult {
  failure_risk?: 'low' | 'medium' | 'high';
  next_semester_sgpa?: number;
  confidence_score?: number;
  expected_graduation_cgpa?: number;
}

// Define DashboardStats type
interface DashboardStats {
  currentSGPI: number;
  previousSGPI: number;
  averageSGPI: number;
  bestSGPI: number;
  totalCredits: number;
  currentSemester: number;
  rank: string;
  totalStudents: string;
  department: string;
  completedCourses: number;
  trend: string;
  percentageChange: number;
  cgpa?: number;
}

// Helper functions for data transformation
const transformWeaknessData = (weakness: WeaknessData): ExtendedWeaknessData => {
  return {
    subject: weakness.subject,
    topic: Array.isArray(weakness.topic) ? weakness.topic.join(', ') : weakness.topic,
    severity: (weakness as any).severity || 'low',
    gap: (weakness as any).gap || 0
  };
};

const transformStudentData = (studentDetails: any): ExtendedDetailedAnalysis => {
  return {
    weaknesses: studentDetails.weaknesses || [],
    performance_data: (studentDetails as any).performance_data || {},
    improvement_trend: (studentDetails as any).improvement_trend || 'stable',
    department: (studentDetails as any).department || 'Unknown',
    current_semester: (studentDetails as any).current_semester || 1,
    latest_sgpa: (studentDetails as any).latest_sgpa || 0,
    cgpa: (studentDetails as any).cgpa || 0,
    weakness_count: (studentDetails as any).weakness_count || 0,
    metadata: (studentDetails as any).metadata || {},
    risk_level: (studentDetails as any).risk_level || 'low',
    attendance: (studentDetails as any).attendance || 0,
    batch: (studentDetails as any).batch || 2020,
    profile_completeness: (studentDetails as any).profile_completeness || 0
  };
};

const transformPredictionData = (mlPredictions: any): ExtendedPredictionResult => {
  return {
    failure_risk: (mlPredictions as any).failure_risk || 'low',
    next_semester_sgpa: (mlPredictions as any).next_semester_sgpa || 0,
    confidence_score: (mlPredictions as any).confidence_score || 0,
    expected_graduation_cgpa: (mlPredictions as any).expected_graduation_cgpa || 0
  };
};

// hooks/usePerformanceMetrics.ts
const usePerformanceMetrics = () => {
  return {
    studentInfo: {
      year: 'Third Year',
      semester: 'Semester 5',
      branch: 'Computer Science & Information Technology',
      rollNumber: 'CSIT/2022/045'
    },
    subjects: [
      { name: 'Data Structures & Algorithms', score: 78, credits: 4, trend: 'up', weakness: ['Trees', 'Graph Algorithms'] },
      { name: 'Operating Systems', score: 85, credits: 4, trend: 'stable', weakness: [] },
      { name: 'Database Management Systems', score: 65, credits: 4, trend: 'down', weakness: ['Normalization', 'Query Optimization', 'Indexing'] },
      { name: 'Computer Networks', score: 92, credits: 3, trend: 'up', weakness: [] },
      { name: 'Software Engineering', score: 88, credits: 3, trend: 'up', weakness: [] },
      { name: 'Theory of Computation', score: 71, credits: 3, trend: 'stable', weakness: ['Turing Machines'] }
    ],
    overallCGPA: 7.8,
    semesterSGPA: 8.1,
    strongSubjects: ['Computer Networks', 'Software Engineering'],
    weakSubjects: ['Database Management Systems'],
    completedCredits: 95,
    totalCredits: 160,
    interests: ['Web Development', 'Cloud Computing', 'AI/ML'],
    careerGoals: ['Software Engineer', 'Full Stack Developer', 'Cloud Architect']
  };
};

const StudentDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'performance' | 'electives' | 'weaknesses' | 'resources' | 'projects' | 'academic' | 'interests'| 'meetings'
  >('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [projectsView, setProjectsView] = useState<'list' | 'upload'>('list');
  const [projectCount, setProjectCount] = useState(0);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [useMockData, setUseMockData] = useState(false);
  
  // Integrated dashboard data with proper typing
  const [studentData, setStudentData] = useState<ExtendedDetailedAnalysis | null>(null);
  const [predictions, setPredictions] = useState<ExtendedPredictionResult | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Add user profile state
  const [userProfile, setUserProfile] = useState<any>(null);

  // Get performance metrics for engineering guidance
  const engineeringMetrics = usePerformanceMetrics();

  // Type-safe user display name
  const userDisplayName = (user as AuthUser)?.displayName || 'Student';

  // Event listeners for profile and academic data updates
  useEffect(() => {
    const handleProfileSaved = (event: CustomEvent) => {
      console.log('Profile saved event received:', event.detail);
      setUserProfile(event.detail);
      saveProfileToStorage(event.detail);
      updateDashboardWithProfile(event.detail);
      toast.success('Profile data updated!');
    };

    const handleProfileUpdated = () => {
      fetchUserProfile();
      fetchDashboardData();
    };

    const handleAcademicDataUpdated = () => {
      fetchUserProfile();
      fetchDashboardData();
      toast.success('Academic data refreshed!');
    };

    // Add event listeners
    window.addEventListener('profileSaved', handleProfileSaved as EventListener);
    window.addEventListener('profileUpdated', handleProfileUpdated);
    window.addEventListener('academicDataUpdated', handleAcademicDataUpdated);

    return () => {
      window.removeEventListener('profileSaved', handleProfileSaved as EventListener);
      window.removeEventListener('profileUpdated', handleProfileUpdated);
      window.removeEventListener('academicDataUpdated', handleAcademicDataUpdated);
    };
  }, [user]);

const fetchUserProfile = async () => {
  if (!user?.uid) return;
  
  // Try cache first
  const cachedProfile = loadProfileFromStorage();
  if (cachedProfile) {
    setUserProfile(cachedProfile);
    updateDashboardWithProfile(cachedProfile);
  }
  
  try {
    // FIXED: Get token from Firebase Auth directly
    const currentUser = auth.currentUser;
    if (!currentUser) {
      console.error('No authenticated user found');
      return;
    }
    
    const token = await currentUser.getIdToken(true); // force refresh
    
    if (!token) {
      console.error('Failed to get auth token');
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
      
      const profile = {
        name: data.name,
        branch: data.branch,
        semester: data.current_semester,
        cgpa: data.cgpa,
        admission_year: data.admission_year,
        academic_year: data.current_academic_year,
        total_credits: data.total_credits_earned,
        roll_number: data.roll_number
      };
      
      setUserProfile(profile);
      saveProfileToStorage(profile);
      updateDashboardWithProfile(profile);
      
      localStorage.setItem('userBranch', profile.branch);
      localStorage.setItem('userSemester', profile.semester.toString());
      
      // Notify other components
      window.dispatchEvent(new CustomEvent('profileLoaded', { detail: profile }));
      
    } else if (response.status === 404) {
      console.log('Profile not found - user needs to create profile');
      localStorage.removeItem(PROFILE_STORAGE_KEY);
    } else {
      const errorData = await response.json().catch(() => ({}));
      console.error('Failed to fetch profile:', response.status, errorData);
    }
  } catch (error) {
    console.error('Error fetching profile:', error);
    // If error but we have cached data, still use it
    if (!userProfile && cachedProfile) {
      // FIXED: Use toast() instead of toast.info()
      toast('Using cached profile data');
    }
  }
};

  // Helper function to update dashboard with profile data
  const updateDashboardWithProfile = (profile: any) => {
    setDashboardStats((prev: DashboardStats | null) => ({
      ...(prev || {
        currentSGPI: 0,
        previousSGPI: 0,
        averageSGPI: 0,
        bestSGPI: 0,
        totalCredits: 0,
        currentSemester: 1,
        rank: '0/0',
        totalStudents: '0',
        department: '',
        completedCourses: 0,
        trend: 'stable',
        percentageChange: 0
      }),
      currentSGPI: profile.cgpa || 0,
      cgpa: profile.cgpa,
      totalCredits: profile.total_credits,
      currentSemester: profile.semester,
      department: profile.branch
    }));
  };

  // Helper functions
  const calculatePercentageChange = (studentData: ExtendedDetailedAnalysis): number => {
    const sgpaTrend = studentData.performance_data?.sgpa_trend;
    if (!sgpaTrend || sgpaTrend.length < 2) return 0;
    
    const current = sgpaTrend[sgpaTrend.length - 1].sgpa;
    const previous = sgpaTrend[sgpaTrend.length - 2].sgpa;
    return previous ? ((current - previous) / previous) * 100 : 0;
  };

  const calculateAverageSGPA = (sgpaTrend: any[]): number => {
    if (!sgpaTrend || sgpaTrend.length === 0) return 0;
    return sgpaTrend.reduce((sum, semester) => sum + semester.sgpa, 0) / sgpaTrend.length;
  };

  const generateRealInsights = (studentData: ExtendedDetailedAnalysis, predictions: ExtendedPredictionResult) => {
    const weaknesses = studentData.weaknesses || [];
    const performanceTrend = studentData.improvement_trend;
    
    const recommendations = [];
    
    // Weakness-based recommendations
    weaknesses.forEach((weakness) => {
      const extendedWeakness = transformWeaknessData(weakness);
      if (extendedWeakness.severity === 'high' || extendedWeakness.severity === 'critical') {
        recommendations.push({
          message: `Focus on ${extendedWeakness.subject}: ${extendedWeakness.topic || 'key concepts'} (${extendedWeakness.gap || 0}% gap)`,
          priority: 'high',
          type: 'alert'
        });
      } else if (extendedWeakness.severity === 'medium') {
        recommendations.push({
          message: `Practice ${extendedWeakness.subject} to improve ${extendedWeakness.gap || 0}% gap`,
          priority: 'medium',
          type: 'warning'
        });
      }
    });

    // Trend-based recommendations
    if (performanceTrend === 'declining') {
      recommendations.push({
        message: 'Performance trend declining. Review study strategies and seek guidance',
        priority: 'high',
        type: 'warning'
      });
    } else if (performanceTrend === 'improving') {
      recommendations.push({
        message: 'Great improvement trend! Maintain your current study approach',
        priority: 'low',
        type: 'success'
      });
    }

    // Prediction-based insights
    if (predictions.failure_risk === 'high') {
      recommendations.push({
        message: 'High failure risk detected. Consider additional support and resources',
        priority: 'high',
        type: 'alert'
      });
    }

    // Add general recommendations if none specific
    if (recommendations.length === 0) {
      recommendations.push({
        message: 'Good performance! Focus on maintaining consistency and exploring advanced topics',
        priority: 'low',
        type: 'success'
      });
    }

    const riskFactors = weaknesses
      .map(w => transformWeaknessData(w))
      .filter(w => w.severity === 'high' || w.severity === 'critical')
      .map(w => ({
        factor: `${w.subject} - ${w.topic || 'Overall'}`,
        severity: w.severity
      }));

    return {
      recommendations,
      trends: {
        overall: performanceTrend,
        confidence: 0.85,
        averageChange: calculatePercentageChange(studentData)
      },
      predictions: {
        nextSGPI: predictions.next_semester_sgpa,
        confidence: predictions.confidence_score && predictions.confidence_score > 0.8 ? 'high' : 
                   predictions.confidence_score && predictions.confidence_score > 0.6 ? 'medium' : 'low',
        rSquared: 0.76
      },
      riskFactors
    };
  };

  // Add function to fetch project count
  const fetchProjectCount = async () => {
    if (!user) return;
    
    try {
      setProjectsLoading(true);
      console.log('Fetching project count for user:', user.uid);
      const projects = await studentProjectsService.getUserProjects();
      console.log('Projects fetched:', projects);
      setProjectCount(projects.length);
    } catch (error) {
      console.error('Error fetching project count:', error);
      setProjectCount(0);
    } finally {
      setProjectsLoading(false);
    }
  };

  // Fetch dashboard data
  const fetchDashboardData = async (showLoader = true) => {
    if (!user?.uid) {
      setLoading(false);
      return;
    }

    try {
      if (showLoader) setLoading(true);
      
      const studentService = getStudentAnalysisService();
      
      // Fetch real student data from backend
      const [studentDetails, mlPredictions, metrics, stats, insightsData] = await Promise.all([
        studentService.getStudentDetails(user.uid),
        mlIntegrationService.getPredictions(user.uid),
        analyticsService.getPerformanceMetrics(user.uid),
        analyticsService.getDashboardStats(user.uid),
        analyticsService.generateInsights(await analyticsService.getPerformanceMetrics(user.uid))
      ]);

      // Transform data to extended types
      const extendedStudentDetails = transformStudentData(studentDetails);
      const extendedMlPredictions = transformPredictionData(mlPredictions);

      setStudentData(extendedStudentDetails);
      setPredictions(extendedMlPredictions);

      // Transform data for dashboard display
      const sgpaTrend = extendedStudentDetails.performance_data?.sgpa_trend || [];
      const chartData = {
        currentSGPI: extendedStudentDetails.latest_sgpa || stats.currentSGPI,
        previousSGPI: sgpaTrend.length > 1 ? sgpaTrend[sgpaTrend.length - 2].sgpa : (extendedStudentDetails.latest_sgpa || stats.previousSGPI),
        trend: extendedStudentDetails.improvement_trend || stats.trend,
        percentageChange: calculatePercentageChange(extendedStudentDetails) || stats.percentageChange,
        semesterWiseData: sgpaTrend.length > 0 ? sgpaTrend.map((semester: any) => ({
          semester: semester.semester,
          sgpi: semester.sgpa,
          credits: semester.credits,
          courses: []
        })) : metrics.map((m: any) => ({
          semester: m.semester,
          sgpi: m.sgpi,
          credits: m.credits,
          courses: m.courses
        }))
      };

      const combinedStats: DashboardStats = {
        currentSGPI: extendedStudentDetails.latest_sgpa || stats.currentSGPI,
        previousSGPI: chartData.previousSGPI,
        averageSGPI: calculateAverageSGPA(sgpaTrend) || stats.averageSGPI,
        bestSGPI: Math.max(...(sgpaTrend.map((s: any) => s.sgpa) || [stats.bestSGPI || 0])),
        totalCredits: extendedStudentDetails.metadata?.total_credits || stats.totalCredits,
        currentSemester: extendedStudentDetails.current_semester || stats.currentSemester,
        // FIXED: Ensure rank and totalStudents are strings
        rank: String(stats.rank || `${(extendedStudentDetails.current_semester || 1) * 15}/120`),
        totalStudents: String(stats.totalStudents || '120'),
        department: extendedStudentDetails.department || stats.department,
        completedCourses: stats.completedCourses || (extendedStudentDetails.current_semester || 1) * 6,
        trend: extendedStudentDetails.improvement_trend || stats.trend,
        percentageChange: chartData.percentageChange
      };

      const combinedInsights = generateRealInsights(extendedStudentDetails, extendedMlPredictions) || insightsData;

      setPerformanceData(chartData);
      setDashboardStats(combinedStats);
      setInsights(combinedInsights);
      setLastUpdated(new Date());

      // Track dashboard view
      await analyticsService.trackEvent('dashboard_viewed', {
        userId: user.uid,
        role: 'student',
        tab: activeTab,
        timestamp: new Date().toISOString()
      });

      // Show recommendations if any
      const highPriorityRecs = combinedInsights.recommendations?.filter((r: any) => r.priority === 'high') || [];
      if (highPriorityRecs.length > 0) {
        toast(highPriorityRecs[0].message, {
          icon: '⚠️',
          duration: 5000
        });
      }

    } catch (error) {
      console.error('Dashboard fetch error:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Event listener for project uploads
  useEffect(() => {
    const handleProjectUploaded = () => {
      console.log('Project uploaded event received');
      fetchProjectCount();
      //setProjectsView('list');
    };

    window.addEventListener('projectUploaded', handleProjectUploaded);
    
    return () => {
      window.removeEventListener('projectUploaded', handleProjectUploaded);
    };
  }, []);

  // Initial data fetch when user is available
  useEffect(() => {
    if (user) {
      fetchUserProfile();
      fetchDashboardData();
      fetchProjectCount();
    } else {
      setLoading(false);
    }
  }, [user]);

  // Also refresh project count when switching tabs
  useEffect(() => {
    if (activeTab === 'projects' || activeTab === 'overview') {
      fetchProjectCount();
    }
  }, [activeTab]);

  // Set up real-time subscription
  useEffect(() => {
    if (!user?.uid) return;

    const unsubscribe = analyticsService.subscribeToMetrics(user.uid, (metrics: any[]) => {
      if (metrics && metrics.length > 0) {
        const stats = {
          currentSGPI: metrics[0].sgpi,
          previousSGPI: metrics[1]?.sgpi || metrics[0].sgpi,
          trend: metrics[0].sgpi > (metrics[1]?.sgpi || 0) ? 'up' : 'down',
          percentageChange: metrics[1] ? ((metrics[0].sgpi - metrics[1].sgpi) / metrics[1].sgpi) * 100 : 0
        };

        const chartData = {
          ...stats,
          semesterWiseData: metrics.map((m: any) => ({
            semester: m.semester,
            sgpi: m.sgpi,
            credits: m.credits,
            courses: m.courses
          }))
        };

        setPerformanceData(chartData);
      }
    });

    // Additional real-time subscription for ML data
    const subscriptionId = realtimeSyncService.subscribeToStudentUpdates(user.uid, (update) => {
      if (update.data) {
        toast.success('Performance data updated!', { duration: 2000 });
        fetchDashboardData(false);
      }
    });

    return () => {
      unsubscribe();
      realtimeSyncService.unsubscribe(subscriptionId);
    };
  }, [user]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(() => {
      fetchDashboardData(false);
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user]);

  // Manual refresh
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData(false);
    toast.success('Dashboard refreshed!');
  };

  // Download report
  const handleDownloadReport = () => {
    const reportData = {
      student: userDisplayName,
      date: new Date().toLocaleDateString(),
      studentId: user?.uid,
      department: userProfile?.branch || studentData?.department || engineeringMetrics.studentInfo.branch,
      currentSemester: userProfile?.semester ? `Semester ${userProfile.semester}` : (studentData?.current_semester ? `Semester ${studentData.current_semester}` : engineeringMetrics.studentInfo.semester),
      currentSGPI: dashboardStats?.currentSGPI,
      cgpa: studentData?.cgpa || engineeringMetrics.overallCGPA,
      trend: dashboardStats?.trend,
      performanceHistory: studentData?.performance_data?.sgpa_trend || performanceData?.semesterWiseData,
      weaknesses: studentData?.weaknesses || [],
      predictions: predictions,
      insights: insights,
      lastUpdated: lastUpdated.toISOString()
    };

    const dataStr = JSON.stringify(reportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `academic_report_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast.success('Report downloaded!');
  };

  // Loading state with skeleton
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="relative">
            <div className="h-24 w-24 mx-auto">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 rounded-full border-4 border-blue-200"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 rounded-full border-4 border-t-blue-600 border-r-transparent border-b-transparent border-l-transparent"
              />
            </div>
          </div>
          <p className="mt-6 text-lg font-medium text-gray-700">
            Loading your personalized dashboard...
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Analyzing your academic performance
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: "spring", damping: 25 }}
            className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-2xl lg:relative lg:shadow-none"
          >
            <div className="h-full flex flex-col">
              {/* Sidebar Header */}
              <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-purple-600">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="h-12 w-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center">
                      <User className="h-7 w-7 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">{userDisplayName}</p>
                      <p className="text-xs text-white/80">{engineeringMetrics.studentInfo.year}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="lg:hidden p-1 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <X className="h-5 w-5 text-white" />
                  </button>
                </div>

                {/* Quick Stats in Sidebar */}
                <div className="space-y-3 bg-white/10 backdrop-blur rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/80">Current CGPA</span>
                    <span className="font-bold text-lg text-white">
                      {studentData?.cgpa?.toFixed(2) || engineeringMetrics.overallCGPA.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/80">Semester</span>
                    <span className="font-bold text-white">
                      {userProfile?.semester ? `Semester ${userProfile.semester}` : (studentData?.current_semester ? `Semester ${studentData.current_semester}` : engineeringMetrics.studentInfo.semester)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/80">Branch</span>
                    <span className="font-bold text-white">
                      {userProfile?.branch || studentData?.department || engineeringMetrics.studentInfo.branch}
                    </span>
                  </div>
                </div>
              </div>

              {/* Navigation */}
              <nav className="flex-1 p-4">
                <ul className="space-y-2">
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('overview');
                        analyticsService.trackEvent('tab_switched', { tab: 'overview' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'overview'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <BarChart3 className="h-5 w-5" />
                      <span className="font-medium">Overview</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('performance');
                        analyticsService.trackEvent('tab_switched', { tab: 'performance' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'performance'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Activity className="h-5 w-5" />
                      <span className="font-medium">Performance Analysis</span>
                      {studentData?.improvement_trend === 'improving' && (
                        <TrendingUp className="h-4 w-4 text-green-500 ml-auto" />
                      )}
                    </button>
                  </li>
                  
                  {/* PROJECTS TAB */}
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('projects');
                        analyticsService.trackEvent('tab_switched', { tab: 'projects' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'projects'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <FolderOpen className="h-5 w-5" />
                      <span className="font-medium">My Projects</span>
                      <span className="ml-auto bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full font-semibold">
                        AI Insights
                      </span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('academic');
                        analyticsService.trackEvent('tab_switched', { tab: 'academic' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'academic'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <GraduationCap className="h-5 w-5" />
                      <span className="font-medium">Academic Data Entry</span>
                      <span className="ml-auto bg-yellow-100 text-yellow-700 text-xs px-2 py-1 rounded-full">
                        Setup
                      </span>
                    </button>
                  </li>

                  <li>
  <button
    onClick={() => {
      setActiveTab('meetings');
      analyticsService.trackEvent('tab_switched', { tab: 'meetings' });
    }}
    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
      activeTab === 'meetings'
        ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
        : 'hover:bg-gray-50 text-gray-700'
    }`}
  >
    <Calendar className="h-5 w-5" />
    <span className="font-medium">Meeting Requests</span>
    <span className="ml-auto bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full">
      Faculty
    </span>
  </button>
</li>


                  {/* INTERESTS TAB - Added */}
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('interests');
                        analyticsService.trackEvent('tab_switched', { tab: 'interests' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'interests'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Heart className="h-5 w-5" />
                      <span className="font-medium">My Interests</span>
                      <span className="ml-auto bg-pink-100 text-pink-700 text-xs px-2 py-1 rounded-full">
                        Setup
                      </span>
                    </button>
                  </li>

                  {/* Engineering Guidance Tabs */}
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('electives');
                        analyticsService.trackEvent('tab_switched', { tab: 'electives' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'electives'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Sparkles className="h-5 w-5" />
                      <span className="font-medium">Elective Recommendations</span>
                      <span className="ml-auto bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full font-semibold">
                        AI
                      </span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('weaknesses');
                        analyticsService.trackEvent('tab_switched', { tab: 'weaknesses' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'weaknesses'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <AlertCircle className="h-5 w-5" />
                      <span className="font-medium">Weakness Analysis</span>
                      {engineeringMetrics.weakSubjects.length > 0 && (
                        <span className="ml-auto bg-orange-100 text-orange-700 text-xs px-2 py-1 rounded-full">
                          {engineeringMetrics.weakSubjects.length}
                        </span>
                      )}
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => {
                        setActiveTab('resources');
                        analyticsService.trackEvent('tab_switched', { tab: 'resources' });
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'resources'
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <GraduationCap className="h-5 w-5" />
                      <span className="font-medium">Study Resources</span>
                      <span className="ml-auto bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                        New
                      </span>
                    </button>
                  </li>
                </ul>

                <div className="mt-8 pt-8 border-t">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Quick Actions</p>
                  <ul className="space-y-2">
                    <li>
                      <button 
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-50 text-gray-700 transition-colors"
                      >
                        <RefreshCw className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
                        <span className="font-medium">Refresh Data</span>
                      </button>
                    </li>
                    <li>
                      <button 
                        onClick={handleDownloadReport}
                        className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-50 text-gray-700 transition-colors"
                      >
                        <Download className="h-5 w-5" />
                        <span className="font-medium">Download Report</span>
                      </button>
                    </li>
                  </ul>
                </div>

                {/* Development Mode Toggle */}
                <div className="mt-8 pt-8 border-t">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Development Mode</p>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-gray-500">Use Mock Data</span>
                    <button
                      onClick={() => setUseMockData(!useMockData)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        useMockData ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          useMockData ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 text-center">
                    {useMockData ? 'Using Mock Data' : 'Using API Data'}
                  </p>
                </div>
              </nav>

              {/* Last Updated */}
              <div className="p-4 border-t">
                <p className="text-xs text-gray-500 text-center">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </p>
              </div>

              {/* Logout */}
              <div className="p-4 border-t">
                <button
                  onClick={logout}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-lg hover:from-red-600 hover:to-pink-600 transition-all shadow-md"
                >
                  <LogOut className="h-5 w-5" />
                  <span className="font-medium">Logout</span>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className={`flex-1 ${sidebarOpen ? 'lg:ml-72' : ''}`}>
        {/* Top Navigation */}
        <header className="bg-white shadow-sm border-b sticky top-0 z-40">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <Menu className="h-6 w-6 text-gray-600" />
                </button>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  {activeTab === 'overview' && 'Dashboard Overview'}
                  {activeTab === 'performance' && 'Performance Analysis'}
                  {activeTab === 'projects' && 'My Projects & AI Interests'}
                  {activeTab === 'academic' && 'Academic Data Entry'}
                  {activeTab === 'interests' && 'My Interests'}
                  {activeTab === 'electives' && 'AI Elective Recommendations'}
                  {activeTab === 'weaknesses' && 'Weakness Analysis & Improvement'}
                  {activeTab === 'resources' && 'Smart Study Resources'}
                  {activeTab === 'meetings' && (
  <motion.div
    key="meetings"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.3 }}
  >
    <StudentMeetingRequest />
  </motion.div>
)}
                </h1>
              </div>

              <div className="flex items-center space-x-4">
                {/* Data Source Indicator */}
                <span className={`text-xs px-2 py-1 rounded-full ${
                  useMockData ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                }`}>
                  {useMockData ? 'Using Mock Data' : 'Live Data'}
                </span>

                {/* Refresh Button */}
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  title="Refresh Dashboard"
                >
                  <RefreshCw className={`h-5 w-5 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
                </button>

                {/* User Menu */}
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{userDisplayName}</p>
                    <p className="text-xs text-gray-500">{userProfile?.branch || studentData?.department || engineeringMetrics.studentInfo.branch}</p>
                  </div>
                  <div className="h-10 w-10 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                    <User className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <AnimatePresence mode="wait">
            {activeTab === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                {/* Projects Preview Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <FolderOpen className="h-6 w-6 text-green-600" />
                      <div>
                        <p className="font-semibold text-green-900">My Projects</p>
                        <p className="text-sm text-green-700">
                          Upload projects to discover your AI-powered career interests
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-xs text-green-600">Projects</p>
                        <p className="text-xl font-bold text-green-700">
                          {projectsLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                          ) : (
                            projectCount
                          )}
                        </p>
                      </div>
                      <button
                        onClick={() => setActiveTab('projects')}
                        className="px-4 py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg text-sm hover:shadow-lg transition-shadow"
                      >
                        {projectCount > 0 ? 'View Projects' : 'Add Project'}
                      </button>
                    </div>
                  </div>
                </motion.div>

                {/* AI Analysis Summary Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center">
                      <Brain className="w-5 h-5 mr-2 text-purple-600" />
                      Latest AI Analysis
                    </h3>
                    <button
                      onClick={() => setActiveTab('projects')}
                      className="text-sm text-purple-600 hover:text-purple-700"
                    >
                      View All
                    </button>
                  </div>
                  
                  {/* Show latest analysis summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-700">3</p>
                      <p className="text-xs text-gray-600">Career Paths Identified</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-700">2</p>
                      <p className="text-xs text-gray-600">Honours Programs Match</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-700">4</p>
                      <p className="text-xs text-gray-600">Electives Recommended</p>
                    </div>
                  </div>
                </motion.div>

                {/* Engineering Student Info Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <GraduationCap className="h-6 w-6 text-purple-600" />
                      <div>
                        <p className="font-semibold text-purple-900">{userProfile?.branch || studentData?.department || engineeringMetrics.studentInfo.branch}</p>
                        <p className="text-sm text-purple-700">
                          {engineeringMetrics.studentInfo.year} • {userProfile?.semester ? `Semester ${userProfile.semester}` : (studentData?.current_semester ? `Semester ${studentData.current_semester}` : engineeringMetrics.studentInfo.semester)} • Roll: {engineeringMetrics.studentInfo.rollNumber}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-xs text-purple-600">CGPA</p>
                        <p className="text-xl font-bold text-purple-700">{studentData?.cgpa?.toFixed(2) || engineeringMetrics.overallCGPA}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-green-600">SGPA</p>
                        <p className="text-xl font-bold text-green-700">{studentData?.latest_sgpa?.toFixed(2) || engineeringMetrics.semesterSGPA}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
                
                {/* Academic Details Setup Alert */}
                {!userProfile && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-300 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <AlertCircle className="h-6 w-6 text-yellow-600" />
                        <div>
                          <p className="font-semibold text-yellow-900">Setup Required</p>
                          <p className="text-sm text-yellow-700">
                            Add your academic details to get personalized AI recommendations
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => setActiveTab('academic')}
                        className="px-4 py-2 bg-yellow-600 text-white rounded-lg text-sm hover:bg-yellow-700"
                      >
                        Setup Now
                      </button>
                    </div>
                  </motion.div>
                )}

                {/* Academic Insights Component */}
                <AcademicInsights 
                  onViewElectives={() => setActiveTab('electives')}
                  onViewWeaknesses={() => setActiveTab('weaknesses')}
                />

                {/* Insights Alert */}
                {insights?.recommendations && insights.recommendations.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4"
                  >
                    <div className="flex items-start space-x-3">
                      <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium text-blue-900">AI Insights</p>
                        <p className="text-sm text-blue-700 mt-1">
                          {insights.recommendations[0].message}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Dynamic Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                  <StatCard
                    title="Current SGPI"
                    value={dashboardStats?.currentSGPI?.toFixed(2) || studentData?.latest_sgpa?.toFixed(2) || engineeringMetrics.semesterSGPA.toFixed(2)}
                    change={dashboardStats?.percentageChange}
                    icon={<TrendingUp className="h-6 w-6 text-blue-600" />}
                    color="blue"
                    onClick={() => setActiveTab('performance')}
                  />
                  
                  <StatCard
                    title="Weak Subjects"
                    value={studentData?.weakness_count?.toString() || engineeringMetrics.weakSubjects.length.toString()}
                    icon={<AlertTriangle className="h-6 w-6 text-orange-600" />}
                    color="orange"
                    onClick={() => setActiveTab('weaknesses')}
                  />
                  
                  <StatCard
                    title="Strong Subjects"
                    value={engineeringMetrics.strongSubjects.length.toString()}
                    icon={<Star className="h-6 w-6 text-green-600" />}
                    color="green"
                  />
                  
                  <StatCard
                    title="Credits Progress"
                    value={`${engineeringMetrics.completedCredits}/${engineeringMetrics.totalCredits}`}
                    icon={<Award className="h-6 w-6 text-purple-600" />}
                    color="purple"
                  />
                  
                  <StatCard
                    title="AI Interests"
                    value={engineeringMetrics.interests.length.toString()}
                    icon={<Brain className="h-6 w-6 text-indigo-600" />}
                    color="indigo"
                    onClick={() => setActiveTab('projects')}
                  />
                </div>

                {/* Performance Chart */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white rounded-xl shadow-sm border p-6"
                >
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900">SGPI Trend Analysis</h2>
                    <button
                      onClick={() => setActiveTab('performance')}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center space-x-1"
                    >
                      <span>View Details</span>
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                  <PerformanceChart data={performanceData} />
                </motion.div>

                {/* Quick Access Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  {/* Projects Preview Card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-white rounded-xl shadow-sm border p-6 cursor-pointer"
                    onClick={() => setActiveTab('projects')}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Code className="h-5 w-5 mr-2 text-green-600" />
                      Upload New Project
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">AI Career Insights</span>
                        <span className="text-green-600 font-medium">Discover Now</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Portfolio Building</span>
                        <span className="text-green-600 font-medium">Boost CGPA</span>
                      </div>
                    </div>
                    <button className="mt-4 w-full text-sm text-green-600 hover:text-green-700 font-medium flex items-center justify-center">
                      <FolderOpen className="h-4 w-4 mr-1" />
                      Start Uploading
                    </button>
                  </motion.div>

                  {/* Electives Preview */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-white rounded-xl shadow-sm border p-6 cursor-pointer"
                    onClick={() => setActiveTab('electives')}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Sparkles className="h-5 w-5 mr-2 text-purple-600" />
                      Recommended Electives
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Cloud Computing</span>
                        <span className="text-purple-600 font-medium">92% match</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Machine Learning</span>
                        <span className="text-purple-600 font-medium">85% match</span>
                      </div>
                    </div>
                    <button className="mt-4 text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center">
                      View all recommendations
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </button>
                  </motion.div>

                  {/* Weakness Preview */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-white rounded-xl shadow-sm border p-6 cursor-pointer"
                    onClick={() => setActiveTab('weaknesses')}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <AlertCircle className="h-5 w-5 mr-2 text-orange-600" />
                      Areas to Improve
                    </h3>
                    <div className="space-y-2">
                      {engineeringMetrics.weakSubjects.map((subject, idx) => (
                        <div key={idx} className="flex justify-between items-center text-sm">
                          <span className="text-gray-600">{subject}</span>
                          <span className="text-orange-600 font-medium">Needs focus</span>
                        </div>
                      ))}
                    </div>
                    <button className="mt-4 text-sm text-orange-600 hover:text-orange-700 font-medium flex items-center">
                      View improvement plan
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </button>
                  </motion.div>

                  {/* Resources Preview */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-white rounded-xl shadow-sm border p-6 cursor-pointer"
                    onClick={() => setActiveTab('resources')}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <BookOpen className="h-5 w-5 mr-2 text-green-600" />
                      Study Resources
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm text-gray-600">
                        <span className="mr-2">🎥</span>
                        <span>6 recommended videos</span>
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <span className="mr-2">📚</span>
                        <span>4 study materials</span>
                      </div>
                    </div>
                    <button className="mt-4 text-sm text-green-600 hover:text-green-700 font-medium flex items-center">
                      Browse resources
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </button>
                  </motion.div>
                </div>
              </motion.div>
            )}

            {activeTab === 'performance' && (
              <motion.div
                key="performance"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                
                {/* Data Source Indicator */}
                <div className="flex justify-end">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    useMockData ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {useMockData ? 'Using Mock Data' : 'Live Data'}
                  </span>
                </div>

                <TrendAnalyzer 
                  studentId={user?.uid || 'student-123'} 
                  className="bg-white rounded-xl shadow-sm border p-6"
                  onTrendChange={(trend) => {
                    console.log('Trend analysis updated:', trend);
                  }}
                />
                
                <SubjectPerformance 
                  studentId={user?.uid || 'student-123'}
                  className="bg-white rounded-xl shadow-sm border p-6"
                  onSubjectSelect={(subject) => {
                    console.log('Subject selected:', subject);
                  }}
                />

                {/* Detailed Performance Chart */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Detailed Performance Analysis</h2>
                    <div className="flex items-center space-x-2">
                      <button 
                        onClick={handleDownloadReport}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                      >
                        <Download className="h-4 w-4" />
                        <span>Export Data</span>
                      </button>
                    </div>
                  </div>
                  <PerformanceChart data={performanceData} />
                </div>

                {/* Subject-wise Performance */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Subject-wise Performance</h3>
                  <div className="space-y-3">
                    {engineeringMetrics.subjects.map((subject, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`h-2 w-2 rounded-full ${
                            subject.trend === 'up' ? 'bg-green-500' :
                            subject.trend === 'down' ? 'bg-red-500' :
                            'bg-gray-500'
                          }`} />
                          <span className="font-medium text-gray-700">{subject.name}</span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm text-gray-600">{subject.credits} credits</span>
                          <span className={`font-bold ${
                            subject.score >= 80 ? 'text-green-600' :
                            subject.score >= 60 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {subject.score}%
                          </span>
                          {subject.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                          {subject.trend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Performance Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <StatCard
                    title="Current Semester"
                    value={userProfile?.semester ? `Semester ${userProfile.semester}` : (studentData?.current_semester ? `${studentData.current_semester}th` : '-')}
                    icon={<Calendar className="h-6 w-6 text-blue-600" />}
                    color="blue"
                  />
                  <StatCard
                    title="Department"
                    value={userProfile?.branch || studentData?.department || '-'}
                    icon={<Users className="h-6 w-6 text-green-600" />}
                    color="green"
                  />
                  <StatCard
                    title="Batch"
                    value={studentData?.batch?.toString() || '-'}
                    icon={<BookOpen className="h-6 w-6 text-yellow-600" />}
                    color="yellow"
                  />
                  <StatCard
                    title="Profile Complete"
                    value={`${studentData?.profile_completeness || 0}%`}
                    icon={<CheckCircle className="h-6 w-6 text-purple-600" />}
                    color="purple"
                  />
                </div>

                {/* AI Insights Panel */}
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Brain className="h-5 w-5 mr-2 text-purple-600" />
                    AI-Generated Insights
                  </h3>
                  
                  {insights?.recommendations && insights.recommendations.length > 0 ? (
                    <div className="space-y-3">
                      {insights.recommendations.map((rec: any, index: number) => (
                        <div key={index} className="flex items-start space-x-3">
                          <div className={`mt-1 h-2 w-2 rounded-full flex-shrink-0 ${
                            rec.type === 'success' ? 'bg-green-500' :
                            rec.type === 'warning' ? 'bg-yellow-500' :
                            rec.type === 'alert' ? 'bg-orange-500' :
                            'bg-blue-500'
                          }`} />
                          <div>
                            <p className="text-sm text-gray-700">{rec.message}</p>
                            <span className={`text-xs ${
                              rec.priority === 'high' ? 'text-red-600' :
                              rec.priority === 'medium' ? 'text-yellow-600' :
                              'text-green-600'
                            }`}>
                              {rec.priority} priority
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600">No specific recommendations at this time.</p>
                  )}
                </div>
              </motion.div>
            )}

            {/* PROJECTS TAB CONTENT */}
            {activeTab === 'projects' && (
              <motion.div
                key="projects"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                {projectsView === 'list' ? (
                  <StudentProjectsList 
                    onAddProject={() => setProjectsView('upload')} 
                  />
                ) : (
                  <div className="space-y-4">
                    <button
                      onClick={() => {
                        setProjectsView('list');
                        fetchProjectCount();
                      }}
                      className="flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
                    >
                      <ChevronLeft className="w-5 h-5" />
                      <span>Back to Projects</span>
                    </button>
                    <StudentProjectsUpload />
                  </div>
                )}
              </motion.div>
            )}

            {/* ACADEMIC TAB CONTENT */}
            {activeTab === 'academic' && (
              <motion.div
                key="academic"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <AcademicDataEntry />
              </motion.div>
            )}

            {/* INTERESTS TAB CONTENT */}
            {activeTab === 'interests' && (
              <motion.div
                key="interests"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <InterestManagement 
                  onInterestsUpdated={() => {
                    fetchDashboardData(false);
                  }}
                />
              </motion.div>
            )}

            {/* Engineering Guidance Tabs */}
            {activeTab === 'electives' && (
              <motion.div
                key="electives"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ElectiveRecommender />
              </motion.div>
            )}

            {activeTab === 'weaknesses' && (
              <motion.div
                key="weaknesses"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <WeaknessAnalyzer />
              </motion.div>
            )}

            {activeTab === 'resources' && (
              <motion.div
                key="resources"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <StudyResources />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default StudentDashboard;