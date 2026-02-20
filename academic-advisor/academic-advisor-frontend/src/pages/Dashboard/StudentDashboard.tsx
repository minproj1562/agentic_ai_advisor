// src/pages/Dashboard/StudentDashboard.tsx
// COMPLETE FILE — All effect loops, duplicate fetches, and re-render issues fixed

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Heart,
  Zap
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import PerformanceChart from '../../components/dashboard/PerformanceChart';
import StatCard from '../../components/common/StatCard';
import { analyticsService, extendedAnalyticsService } from '../../services/analytics.service';
import { StudentProjectsList } from '../../components/dashboard/sections/StudentProjectsList';
import { StudentProjectsUpload } from '../../components/dashboard/sections/StudentProjectsUpload';
import { ProjectAnalysisResults } from '../../components/dashboard/sections/ProjectAnalysisResults';
import { studentProjectsService } from '../../services/student_projects_cloudinary.service';
import { getStudentAnalysisService } from '../../services/student_analysis.service';
import { mlIntegrationService } from '../../modules/agent1/student-analysis/services/ml-integration.service';
import { realtimeSyncService } from '../../modules/agent1/student-analysis/services/realtime-sync.service';
import { DetailedAnalysis, PredictionResult, WeaknessData } from '../../modules/agent1/student-analysis/types/student-analysis.types';
import TrendAnalyzer from '../../modules/agent1/performance-analytics/components/TrendAnalyzer';
import SubjectPerformance from '../../modules/agent1/performance-analytics/components/SubjectPerformance';
import { WeaknessAnalyzer, StudyResources } from '../../components/dashboard/EngineeringGuidance';
import MLRecommendations from '../../components/dashboard/MLRecommendations';
import { mlService, LegacyProjectAnalysisResult, ComprehensiveProjectAnalysisResponse } from '../../services/ml.service';
import toast from 'react-hot-toast';
import { AcademicDataEntry } from '../../components/dashboard/AcademicDataEntry';
import { InterestManagement } from '../../components/dashboard/InterestManagement';
import { AcademicInsights } from '../../components/dashboard/AcademicInsights';
import { auth } from '../../services/firebase.config';
import MeetingsCalendar from '../../components/meetings/MeetingsCalendar';
import { ComprehensiveAnalysis } from '../../services/student_projects_cloudinary.service';
import { ReadinessAnalysis } from '../../components/dashboard/ReadinessAnalysis';
import { useStudentInterests, useSyncInterests } from '../../hooks/useEngineeringGuidance';
import ReadinessIndicator from '../../components/dashboard/ReadinessIndicator';
import { getWeaknessService } from '../../services/weakness.service';

// ==================== Interfaces ====================

interface SubjectData {
  name: string;
  score: number;
  credits: number;
  trend: 'up' | 'down' | 'stable';
  weakness: string[];
}

interface AuthUser {
  uid: string;
  displayName?: string;
  email?: string;
  getIdToken?: () => Promise<string>;
}

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

// ==================== Constants ====================

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const PROFILE_STORAGE_KEY = 'academic_advisor_profile';

// ==================== Helper Functions ====================

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
      if (Date.now() - data.timestamp < 3600000) {
        return data;
      }
    }
  } catch (error) {
    console.error('Error loading profile from storage:', error);
  }
  return null;
};

const transformWeaknessData = (weakness: WeaknessData): ExtendedWeaknessData => {
  return {
    subject: weakness.subject,
    topic: Array.isArray(weakness.topic) ? weakness.topic.join(', ') : weakness.topic,
    severity: (weakness as any).severity || 'low',
    gap: (weakness as any).gap || 0
  };
};

// Performance metrics hook
const usePerformanceMetrics = () => {
  const [metrics] = useState({
    studentInfo: {
      year: 'Third Year',
      semester: 'Semester 5',
      branch: 'Information Technology',
      rollNumber: 'IT/2022/045'
    },
    subjects: [] as SubjectData[],
    overallCGPA: 0,
    semesterSGPA: 0,
    strongSubjects: [] as string[],
    weakSubjects: [] as string[],
    completedCredits: 0,
    totalCredits: 166,
    interests: [] as string[],
    careerGoals: [] as string[]
  });

  return metrics;
};

// ==================== Main Component ====================

const StudentDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();

  // ==================== State ====================

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'performance' | 'electives' | 'weaknesses' | 'resources' | 'projects' | 'academic' | 'interests' | 'meetings' | 'readiness'
  >('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [projectsView, setProjectsView] = useState<'list' | 'upload'>('list');
  const [projectCount, setProjectCount] = useState(0);
  const [projectsLoading, setProjectsLoading] = useState(false);

  // Project analysis state
  const [showProjectAnalysis, setShowProjectAnalysis] = useState(false);
  const [projectAnalysisResult, setProjectAnalysisResult] = useState<LegacyProjectAnalysisResult | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // Meetings view state
  const [meetingsView, setMeetingsView] = useState<'requests' | 'calendar'>('requests');

  // Recommendation stats for overview
  const [recommendationStats, setRecommendationStats] = useState({
    careerPaths: 0,
    honoursProgramsMatch: 0,
    electivesRecommended: 0
  });

  // Readiness Analysis State
  const [readinessData, setReadinessData] = useState<any>(null);
  const [loadingReadiness, setLoadingReadiness] = useState(false);

  // Student interests/electives/honours
  const [studentInterests, setStudentInterests] = useState<string[]>([]);
  const [studentElectives, setStudentElectives] = useState<string[]>([]);
  const [studentHonours, setStudentHonours] = useState<string[]>([]);

  // Integrated dashboard data
  const [studentData, setStudentData] = useState<ExtendedDetailedAnalysis | null>(null);
  const [predictions, setPredictions] = useState<ExtendedPredictionResult | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // User profile state
  const [userProfile, setUserProfile] = useState<any>(null);

  // Get performance metrics for engineering guidance
  const engineeringMetrics = usePerformanceMetrics();

  // Type-safe user display name
  const userDisplayName = (user as AuthUser)?.displayName || 'Student';

  // ==================== Refs to prevent duplicate fetches ====================

  const initialFetchDone = useRef(false);
  const projectCountFetchedFor = useRef<string | null>(null);
  const interestsSyncedFor = useRef<string | null>(null);
  const readinessFetchingRef = useRef(false);

  // ==================== Stable Callbacks ====================

  const invalidateAllCaches = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['weakness-analysis'] });
    queryClient.invalidateQueries({ queryKey: ['student-interests'] });
    queryClient.invalidateQueries({ queryKey: ['performance-metrics'] });
    queryClient.invalidateQueries({ queryKey: ['study-resources'] });
    queryClient.invalidateQueries({ queryKey: ['elective-recommendations'] });
  }, [queryClient]);

  const fetchRecommendationStats = useCallback(async () => {
    try {
      const data = await mlService.getRecommendations(true, true, true, false);
      setRecommendationStats({
        careerPaths: data.careers?.length || 0,
        honoursProgramsMatch: data.honours?.filter((h: any) => h.eligibility)?.length || 0,
        electivesRecommended: data.electives?.length || 0
      });
    } catch (error) {
      console.error('Error fetching recommendation stats:', error);
    }
  }, []);

  const fetchReadiness = useCallback(async () => {
    if (!user?.uid) return;
    if (readinessFetchingRef.current) return; // FIXED: Prevent concurrent calls

    readinessFetchingRef.current = true;
    setLoadingReadiness(true);
    try {
      const service = getWeaknessService();
      const data = await service.getReadiness(
        user.uid,
        studentInterests.length > 0 ? studentInterests : undefined,
        studentElectives.length > 0 ? studentElectives : undefined,
        studentHonours.length > 0 ? studentHonours : undefined,
      );
      setReadinessData(data);
      console.log('✅ Readiness data loaded:', {
        score: data.overall_readiness_score,
        level: data.readiness_level,
      });
    } catch (error) {
      console.error('Error fetching readiness:', error);
    } finally {
      setLoadingReadiness(false);
      readinessFetchingRef.current = false;
    }
  }, [user?.uid, studentInterests, studentElectives, studentHonours]);

  const updateDashboardWithProfile = useCallback((profile: any) => {
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
  }, []);

  const fetchProjectCount = useCallback(async () => {
    if (!user?.uid) return;
    // FIXED: Prevent duplicate project count fetches
    if (projectCountFetchedFor.current === user.uid) return;
    projectCountFetchedFor.current = user.uid;

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
  }, [user?.uid]);

  // Force refetch project count (used after upload)
  const refetchProjectCount = useCallback(async () => {
    if (!user?.uid) return;
    projectCountFetchedFor.current = null; // Reset guard
    await fetchProjectCount();
  }, [user?.uid, fetchProjectCount]);

  const fetchUserProfile = useCallback(async () => {
    if (!user?.uid) return;

    const cachedProfile = loadProfileFromStorage();
    if (cachedProfile) {
      setUserProfile(cachedProfile);
      updateDashboardWithProfile(cachedProfile);
    }

    try {
      const currentUser = auth.currentUser;
      if (!currentUser) {
        console.error('No authenticated user found');
        return;
      }

      const token = await currentUser.getIdToken(true);
      if (!token) {
        console.error('Failed to get auth token');
        return;
      }

      let response = await fetch(`${BACKEND_URL}/api/v1/student-profile/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.status === 404) {
        response = await fetch(`${BACKEND_URL}/api/v1/student-profile/profile`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }

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
          roll_number: data.roll_number,
          interests: data.interests || [],
          career_goals: data.career_goals || []
        };

        setUserProfile(profile);
        saveProfileToStorage(profile);
        updateDashboardWithProfile(profile);

        localStorage.setItem('userBranch', profile.branch);
        localStorage.setItem('userSemester', profile.semester.toString());

        window.dispatchEvent(new CustomEvent('profileLoaded', { detail: profile }));
      } else if (response.status === 404) {
        console.log('Profile not found - user needs to create profile');
        localStorage.removeItem(PROFILE_STORAGE_KEY);
        setUserProfile(null);
      } else {
        console.error('Failed to fetch profile:', response.status);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      if (!userProfile && cachedProfile) {
        toast('Using cached profile data');
      }
    }
  }, [user?.uid, updateDashboardWithProfile]);

  const fetchDashboardData = useCallback(async (showLoader = true) => {
    if (!user?.uid) { setLoading(false); return; }

    try {
      if (showLoader) setLoading(true);

      const [chartData, stats, metrics] = await Promise.all([
        extendedAnalyticsService.getPerformanceChartData(user.uid),
        extendedAnalyticsService.getDashboardStats(user.uid),
        extendedAnalyticsService.getPerformanceMetrics(user.uid)
      ]);

      const insightsData = await extendedAnalyticsService.generateInsights(metrics);

      setPerformanceData(chartData);
      setDashboardStats(stats as DashboardStats);
      setInsights(insightsData);

      const fullData = await extendedAnalyticsService.fetchFullDashboardData();
      if (fullData) {
        setStudentData({
          weaknesses: fullData.weaknesses || [],
          performance_data: { sgpa_trend: fullData.sgpa_trend || [] },
          improvement_trend: fullData.trend || 'stable',
          department: fullData.branch,
          current_semester: fullData.current_semester,
          latest_sgpa: fullData.latest_sgpa,
          cgpa: fullData.cgpa,
          weakness_count: fullData.weakness_count,
          metadata: { total_credits: fullData.total_credits_earned },
          risk_level: fullData.cgpa < 6 ? 'high' : fullData.cgpa < 7 ? 'medium' : 'low',
          attendance: 0,
          batch: fullData.admission_year,
          profile_completeness: fullData.completion_percentage
        });
      }

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.uid]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    invalidateAllCaches();
    projectCountFetchedFor.current = null; // Allow re-fetch
    interestsSyncedFor.current = null;
    readinessFetchingRef.current = false;

    await Promise.all([
      fetchDashboardData(false),
      fetchRecommendationStats(),
      fetchReadiness(),
      refetchProjectCount(),
    ]);
    toast.success('Dashboard refreshed!');
  }, [invalidateAllCaches, fetchDashboardData, fetchRecommendationStats, fetchReadiness, refetchProjectCount]);

  const handleProjectAnalyzed = useCallback(async (analysisResponse: ComprehensiveAnalysis) => {
    try {
      const legacyFormat: LegacyProjectAnalysisResult = {
        inferred_interests: analysisResponse.inferred_interests.map(i => ({
          domain: i.domain,
          confidence: i.confidence,
          keywords: i.keywords || [],
          relatedSkills: i.relatedSkills || [],
          careerPaths: i.careerPaths || [],
          industryRelevance: i.industryRelevance || i.confidence * 0.9,
        })),
        elective_recommendations: analysisResponse.elective_recommendations.map(e => ({
          elective: e.elective,
          code: '',
          match_score: e.match_score,
          reasons: e.reasons,
          skills_to_gain: e.skills_to_gain,
          career_relevance: e.career_relevance,
          difficulty_level: e.difficulty_level,
        })),
        honours_minor_recommendations: analysisResponse.honours_minor_recommendations.map(h => ({
          program: h.program,
          type: h.type,
          match_score: h.match_score,
          courses: h.courses,
          career_paths: h.career_paths,
          credits: h.credits,
          semester_commitment: h.semester_commitment,
          reasons: h.reasons,
        })),
        career_paths: analysisResponse.career_paths.map(c => ({
          title: c.title,
          match_score: c.match_score,
          salary_range: c.salary_range,
          market_demand: c.market_demand,
          growth_potential: c.growth_potential,
          required_skills: c.required_skills,
          companies_hiring: [],
          honours_program: c.honours_program,
          preparation_path: c.preparation_path,
        })),
        skill_gap_analysis: {
          current_skills: analysisResponse.skill_gap_analysis.current_skills,
          skill_gaps: analysisResponse.skill_gap_analysis.skill_gaps,
          priority_skills: analysisResponse.skill_gap_analysis.priority_skills,
          learning_resources: Object.fromEntries(
            Object.entries(analysisResponse.skill_gap_analysis.learning_resources).map(
              ([skill, resources]) => [
                skill,
                (resources as string[]).map(r => ({ platform: 'Online', course: r }))
              ]
            )
          ),
          completeness_percentage: 70,
          estimated_learning_time: analysisResponse.skill_gap_analysis.estimated_learning_time,
        },
        next_steps: analysisResponse.next_steps.map(s => ({
          action: s.action,
          category: s.category,
          priority: s.priority,
          deadline: s.deadline,
          details: s.details,
        })),
        metadata: {
          analysis_date: analysisResponse.metadata?.analysis_date || new Date().toISOString(),
          confidence_score: analysisResponse.metadata?.confidence_score || 0.75,
          model_version: '2.0.0',
          data_sources: ['projects'],
        },
      };

      setProjectAnalysisResult(legacyFormat);
      setShowProjectAnalysis(true);

      setRecommendationStats({
        careerPaths: analysisResponse.career_paths?.length || 0,
        honoursProgramsMatch: analysisResponse.honours_minor_recommendations?.filter(h => h.eligibility_met)?.length || 0,
        electivesRecommended: analysisResponse.elective_recommendations?.length || 0
      });

      toast.success('Project analyzed! View your personalized recommendations.');
    } catch (error) {
      console.error('Error processing analysis:', error);
      toast.error('Failed to process analysis results');
    }
  }, []);

  const handleDownloadReport = useCallback(() => {
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
      recommendationStats: recommendationStats,
      readiness: readinessData ? {
        score: readinessData.overall_readiness_score,
        level: readinessData.readiness_level,
        recommendation: readinessData.primary_recommendation
      } : null,
      lastUpdated: lastUpdated.toISOString()
    };

    const dataStr = JSON.stringify(reportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `academic_report_${new Date().toISOString().split('T')[0]}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();

    toast.success('Report downloaded!');
  }, [userDisplayName, user?.uid, userProfile, studentData, dashboardStats, performanceData, predictions, insights, recommendationStats, readinessData, lastUpdated, engineeringMetrics]);

  // ==================== Effects ====================

  // Effect 1: Event listeners
  useEffect(() => {
    const handleProfileSaved = (event: Event) => {
      const detail = (event as CustomEvent).detail;
      console.log('Profile saved event received:', detail);
      setUserProfile(detail);
      saveProfileToStorage(detail);
      updateDashboardWithProfile(detail);
      toast.success('Profile data updated!');
    };

    const handleProfileUpdated = async () => {
      extendedAnalyticsService.clearCache();
      await fetchUserProfile();
      await fetchDashboardData(false);
    };

    const handleAcademicDataUpdated = async () => {
      console.log('📊 Academic data updated — refreshing everything');

      extendedAnalyticsService.clearCache();
      invalidateAllCaches();

      setPerformanceData(null);
      setStudentData(null);
      setDashboardStats(null);
      setReadinessData(null);
      readinessFetchingRef.current = false;

      await fetchUserProfile();
      await fetchDashboardData(true);
      await fetchRecommendationStats();
      await fetchReadiness();

      toast.success('Dashboard updated with new academic data!');
    };

    const handleInterestsUpdated = async (event: Event) => {
      const detail = (event as CustomEvent).detail;
      console.log('🎯 Interests updated event received:', detail);

      if (detail?.interests) {
        setStudentInterests(detail.interests);
      }

      invalidateAllCaches();
      setReadinessData(null);
      readinessFetchingRef.current = false;

      // Small delay to let state settle
      setTimeout(async () => {
        await fetchReadiness();
        await fetchRecommendationStats();
      }, 500);
    };

    const handleProjectAnalysisComplete = (event: Event) => {
      const detail = (event as CustomEvent<ComprehensiveAnalysis>).detail;
      handleProjectAnalyzed(detail);
    };

    window.addEventListener('profileSaved', handleProfileSaved);
    window.addEventListener('profileUpdated', handleProfileUpdated);
    window.addEventListener('academicDataUpdated', handleAcademicDataUpdated);
    window.addEventListener('interestsUpdated', handleInterestsUpdated);
    window.addEventListener('projectAnalysisComplete', handleProjectAnalysisComplete);

    return () => {
      window.removeEventListener('profileSaved', handleProfileSaved);
      window.removeEventListener('profileUpdated', handleProfileUpdated);
      window.removeEventListener('academicDataUpdated', handleAcademicDataUpdated);
      window.removeEventListener('interestsUpdated', handleInterestsUpdated);
      window.removeEventListener('projectAnalysisComplete', handleProjectAnalysisComplete);
    };
  }, [user?.uid, queryClient, fetchUserProfile, fetchDashboardData, fetchRecommendationStats, fetchReadiness, invalidateAllCaches, updateDashboardWithProfile, handleProjectAnalyzed]);

  // Effect 2: Fetch and sync interests — ONCE per user
  useEffect(() => {
    const fetchAndSyncInterests = async () => {
      if (!user?.uid) return;
      // FIXED: Prevent duplicate interest sync
      if (interestsSyncedFor.current === user.uid) return;
      interestsSyncedFor.current = user.uid;

      try {
        const service = getWeaknessService();

        try {
          const interestProfile = await service.getInterests(user.uid);
          if (interestProfile.interests?.length) {
            console.log('✅ Found interests in profile:', interestProfile.interests);
            setStudentInterests(interestProfile.interests);
          }
          if (interestProfile.preferred_electives?.length) {
            setStudentElectives(interestProfile.preferred_electives);
          }
          if (interestProfile.honours_minors_interest?.length) {
            setStudentHonours(interestProfile.honours_minors_interest);
          }
          if (interestProfile.interests?.length) return;
        } catch (e) {
          console.warn('Could not fetch interest profile directly:', e);
        }

        console.log('⚠️ No interests found, attempting sync...');
        try {
          const syncResult = await service.syncInterests(user.uid);
          if (syncResult.status === 'success' && syncResult.interests?.length) {
            console.log('✅ Synced interests:', syncResult.interests);
            setStudentInterests(syncResult.interests);
            return;
          }
        } catch (e) {
          console.warn('Sync failed:', e);
        }

        if (userProfile?.interests?.length) {
          console.log('📝 Using interests from userProfile');
          setStudentInterests(userProfile.interests);
        }
      } catch (error) {
        console.error('Error fetching interests:', error);
        if (userProfile?.interests?.length) {
          setStudentInterests(userProfile.interests);
        }
      }
    };

    fetchAndSyncInterests();
    // FIXED: Only depend on user.uid, not userProfile.interests (which changes and causes loops)
  }, [user?.uid]);

  // Effect 2b: If userProfile loads later with interests and we have none, use them
  useEffect(() => {
    if (studentInterests.length === 0 && userProfile?.interests?.length > 0) {
      console.log('📝 Late-loading interests from userProfile');
      setStudentInterests(userProfile.interests);
    }
  }, [userProfile?.interests, studentInterests.length]);

  // Effect 3: Re-fetch readiness when interests/electives/honours change
  // FIXED: Use serialized strings for stable dependency comparison
  const interestsKey = studentInterests.join(',');
  const electivesKey = studentElectives.join(',');
  const honoursKey = studentHonours.join(',');

  useEffect(() => {
    if (user?.uid && (interestsKey || electivesKey || honoursKey)) {
      console.log('📊 Goals changed, re-fetching readiness...');
      readinessFetchingRef.current = false; // Allow new fetch
      fetchReadiness();
    }
  }, [user?.uid, interestsKey, electivesKey, honoursKey, fetchReadiness]);

  // Effect 4: Project uploaded event
  useEffect(() => {
    const handleProjectUploaded = () => {
      console.log('Project uploaded event received');
      refetchProjectCount();
      fetchRecommendationStats();
    };

    window.addEventListener('projectUploaded', handleProjectUploaded);
    return () => {
      window.removeEventListener('projectUploaded', handleProjectUploaded);
    };
  }, [refetchProjectCount, fetchRecommendationStats]);

  // Effect 5: Initial data load — ONCE
  useEffect(() => {
    if (user && !initialFetchDone.current) {
      initialFetchDone.current = true;
      fetchUserProfile();
      fetchDashboardData();
      fetchProjectCount();
      fetchRecommendationStats();
      // Readiness will be fetched by Effect 3 once interests are loaded
    } else if (!user) {
      setLoading(false);
    }
  }, [user, fetchUserProfile, fetchDashboardData, fetchProjectCount, fetchRecommendationStats]);

  // Effect 6: Tab-based data refresh — only fetch what's missing
  useEffect(() => {
    if (activeTab === 'projects' && projectCount === 0 && !projectsLoading) {
      projectCountFetchedFor.current = null; // Allow re-check
      fetchProjectCount();
    }
  }, [activeTab, projectCount, projectsLoading, fetchProjectCount]);

  // Effect 7: Real-time subscriptions
  useEffect(() => {
    if (!user?.uid) return;

    const unsubscribe = extendedAnalyticsService.subscribeToMetrics(user.uid, (metrics: any[]) => {
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

    let subscriptionId: string | null = null;
    try {
      subscriptionId = realtimeSyncService.subscribeToStudentUpdates(user.uid, (update) => {
        if (update.data) {
          toast.success('Performance data updated!', { duration: 2000 });
          fetchDashboardData(false);
        }
      });
    } catch (err) {
      console.warn('Realtime sync subscription failed (RTDB may not be available):', err);
    }

    return () => {
      unsubscribe();
      if (subscriptionId) {
        try {
          realtimeSyncService.unsubscribe(subscriptionId);
        } catch {
          // Ignore cleanup errors
        }
      }
    };
  }, [user?.uid, fetchDashboardData]);

  // Effect 8: Periodic refresh
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(() => {
      fetchDashboardData(false);
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user, fetchDashboardData]);

  // ==================== Loading State ====================

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

  // ==================== Main Render ====================

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex">
      {/* Project Analysis Results Modal */}
      <AnimatePresence>
        {showProjectAnalysis && projectAnalysisResult && (
          <ProjectAnalysisResults
            analysis={projectAnalysisResult}
            onClose={() => {
              setShowProjectAnalysis(false);
              setProjectAnalysisResult(null);
            }}
            studentBranch={userProfile?.branch || studentData?.department || 'IT'}
            studentSemester={userProfile?.semester || studentData?.current_semester || 5}
          />
        )}
      </AnimatePresence>
      {/* Mobile Backdrop Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* ==================== SIDEBAR ==================== */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: "spring", damping: 25 }}
            className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-2xl lg:relative lg:z-auto lg:shadow-none lg:border-r flex-shrink-0"
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
              <nav className="flex-1 p-4 overflow-y-auto">
                <ul className="space-y-2">
                  <li>
                    <button
                      onClick={() => { setActiveTab('overview'); analyticsService.trackEvent('tab_switched', { tab: 'overview' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'overview' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <BarChart3 className="h-5 w-5" />
                      <span className="font-medium">Overview</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('performance'); analyticsService.trackEvent('tab_switched', { tab: 'performance' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'performance' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Activity className="h-5 w-5" />
                      <span className="font-medium">Performance Analysis</span>
                      {studentData?.improvement_trend === 'improving' && (
                        <TrendingUp className="h-4 w-4 text-green-500 ml-auto" />
                      )}
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('projects'); analyticsService.trackEvent('tab_switched', { tab: 'projects' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'projects' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <FolderOpen className="h-5 w-5" />
                      <span className="font-medium">My Projects</span>
                      <span className="ml-auto bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full font-semibold">AI Insights</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('academic'); analyticsService.trackEvent('tab_switched', { tab: 'academic' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'academic' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <GraduationCap className="h-5 w-5" />
                      <span className="font-medium">Academic Data Entry</span>
                      <span className="ml-auto bg-yellow-100 text-yellow-700 text-xs px-2 py-1 rounded-full">Setup</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('meetings'); analyticsService.trackEvent('tab_switched', { tab: 'meetings' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'meetings' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Calendar className="h-5 w-5" />
                      <span className="font-medium">Meeting Requests</span>
                      <span className="ml-auto bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full">Faculty</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('interests'); analyticsService.trackEvent('tab_switched', { tab: 'interests' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'interests' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Heart className="h-5 w-5" />
                      <span className="font-medium">My Interests</span>
                      <span className="ml-auto bg-pink-100 text-pink-700 text-xs px-2 py-1 rounded-full">Setup</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('electives'); analyticsService.trackEvent('tab_switched', { tab: 'electives' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'electives' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Sparkles className="h-5 w-5" />
                      <span className="font-medium">AI Recommendations</span>
                      <span className="ml-auto bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full font-semibold">{recommendationStats.electivesRecommended}</span>
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('weaknesses'); analyticsService.trackEvent('tab_switched', { tab: 'weaknesses' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'weaknesses' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <AlertCircle className="h-5 w-5" />
                      <span className="font-medium">Weakness Analysis</span>
                      {studentData?.weakness_count && studentData.weakness_count > 0 && (
                        <span className="ml-auto bg-orange-100 text-orange-700 text-xs px-2 py-1 rounded-full">{studentData.weakness_count}</span>
                      )}
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('readiness'); analyticsService.trackEvent('tab_switched', { tab: 'readiness' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'readiness' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Target className="h-5 w-5" />
                      <span className="font-medium">Readiness Analysis</span>
                      {readinessData && (
                        <span className="ml-auto bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full">
                          {Math.round(readinessData.overall_readiness_score)}%
                        </span>
                      )}
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => { setActiveTab('resources'); analyticsService.trackEvent('tab_switched', { tab: 'resources' }); }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === 'resources' ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <BookOpen className="h-5 w-5" />
                      <span className="font-medium">Study Resources</span>
                      <span className="ml-auto bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">New</span>
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

      {/* ==================== MAIN CONTENT ==================== */}
      <div className={`flex-1 min-w-0 ${sidebarOpen ? 'lg:ml-72' : ''}`}>
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
                  {activeTab === 'electives' && 'AI-Powered Recommendations'}
                  {activeTab === 'weaknesses' && 'Weakness Analysis & Improvement'}
                  {activeTab === 'resources' && 'Smart Study Resources'}
                  {activeTab === 'meetings' && (meetingsView === 'calendar' ? 'Meeting Calendar' : 'Meeting Requests')}
                  {activeTab === 'readiness' && 'Academic Readiness Analysis'}
                </h1>
              </div>

              <div className="flex items-center space-x-4">
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  title="Refresh Dashboard"
                >
                  <RefreshCw className={`h-5 w-5 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
                </button>

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

        {/* ==================== PAGE CONTENT ==================== */}
        <main className="p-4 sm:p-6 lg:p-8">
          <AnimatePresence mode="wait">

            {/* ==================== OVERVIEW TAB ==================== */}
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
                      AI Recommendation Summary
                    </h3>
                    <button
                      onClick={() => setActiveTab('electives')}
                      className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
                    >
                      View All
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <Briefcase className="w-4 h-4 text-purple-600" />
                        <p className="text-2xl font-bold text-purple-700">{recommendationStats.careerPaths}</p>
                      </div>
                      <p className="text-xs text-gray-600">Career Paths Identified</p>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <Award className="w-4 h-4 text-blue-600" />
                        <p className="text-2xl font-bold text-blue-700">{recommendationStats.honoursProgramsMatch}</p>
                      </div>
                      <p className="text-xs text-gray-600">Honours Programs Match</p>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <Sparkles className="w-4 h-4 text-green-600" />
                        <p className="text-2xl font-bold text-green-700">{recommendationStats.electivesRecommended}</p>
                      </div>
                      <p className="text-xs text-gray-600">Electives Recommended</p>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mt-4 text-center">
                    Based on your academic performance (40%), interests (30%), and projects (30%)
                  </p>
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
                    title="AI Recommendations"
                    value={recommendationStats.electivesRecommended.toString()}
                    icon={<Brain className="h-6 w-6 text-indigo-600" />}
                    color="indigo"
                    onClick={() => setActiveTab('electives')}
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
                  {/* Upload Project Card */}
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

                  {/* Readiness Preview Card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-xl shadow-sm p-6 cursor-pointer"
                    onClick={() => setActiveTab('readiness')}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Target className="h-5 w-5 mr-2 text-purple-600" />
                      Readiness Score
                    </h3>
                    {readinessData ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-3xl font-bold text-purple-700">
                            {Math.round(readinessData.overall_readiness_score)}%
                          </span>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            readinessData.overall_readiness_score >= 75
                              ? 'bg-green-100 text-green-700'
                              : readinessData.overall_readiness_score >= 50
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {readinessData.readiness_level}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {readinessData.primary_recommendation?.substring(0, 80)}...
                        </p>
                        <button className="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center">
                          View full analysis
                          <ChevronRight className="h-4 w-4 ml-1" />
                        </button>
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        {studentInterests.length === 0 ? (
                          <>
                            <Heart className="w-8 h-8 text-purple-300 mx-auto mb-2" />
                            <p className="text-sm text-gray-500">Set interests first</p>
                          </>
                        ) : loadingReadiness ? (
                          <>
                            <Loader2 className="w-8 h-8 animate-spin text-purple-400 mx-auto mb-2" />
                            <p className="text-sm text-gray-500">Loading analysis...</p>
                          </>
                        ) : (
                          <>
                            <Target className="w-8 h-8 text-purple-300 mx-auto mb-2" />
                            <p className="text-sm text-gray-500">Click to run analysis</p>
                          </>
                        )}
                      </div>
                    )}
                  </motion.div>

                  {/* AI Recommendations Card */}
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
                      AI Recommendations
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Electives</span>
                        <span className="text-purple-600 font-medium">{recommendationStats.electivesRecommended} matched</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Honours/Minors</span>
                        <span className="text-purple-600 font-medium">{recommendationStats.honoursProgramsMatch} eligible</span>
                      </div>
                    </div>
                    <button className="mt-4 text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center">
                      View all recommendations
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </button>
                  </motion.div>

                  {/* Areas to Improve Card */}
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
                      {studentData?.weaknesses && studentData.weaknesses.length > 0 ? (
                        studentData.weaknesses.slice(0, 2).map((weakness, idx) => (
                          <div key={idx} className="flex justify-between items-center text-sm">
                            <span className="text-gray-600">{weakness.subject}</span>
                            <span className="text-orange-600 font-medium">Needs focus</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">
                          {studentInterests.length > 0 ? 'Loading weakness analysis...' : 'Set interests to see analysis'}
                        </p>
                      )}
                    </div>
                    <button className="mt-4 text-sm text-orange-600 hover:text-orange-700 font-medium flex items-center">
                      View improvement plan
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </button>
                  </motion.div>
                </div>

                {/* Study Resources Quick Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  whileHover={{ scale: 1.01 }}
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
              </motion.div>
            )}

            {/* ==================== PERFORMANCE TAB ==================== */}
            {activeTab === 'performance' && (
              <motion.div
                key="performance"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
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

            {/* ==================== PROJECTS TAB ==================== */}
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
                        refetchProjectCount();
                      }}
                      className="flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
                    >
                      <ChevronLeft className="w-5 h-5" />
                      <span>Back to Projects</span>
                    </button>
                    <StudentProjectsUpload
                      onAnalysisComplete={(response: ComprehensiveAnalysis) => {
                        handleProjectAnalyzed(response);
                        refetchProjectCount();
                      }}
                    />
                  </div>
                )}
              </motion.div>
            )}

            {/* ==================== ACADEMIC TAB ==================== */}
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

            {/* ==================== INTERESTS TAB ==================== */}
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
                    fetchRecommendationStats();
                  }}
                />
              </motion.div>
            )}

            {/* ==================== ELECTIVES TAB ==================== */}
            {activeTab === 'electives' && (
              <motion.div
                key="electives"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <MLRecommendations />
              </motion.div>
            )}

            {/* ==================== WEAKNESSES TAB ==================== */}
            {activeTab === 'weaknesses' && (
              <motion.div
                key="weaknesses"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <WeaknessAnalyzer
                  interests={studentInterests}
                  electives={studentElectives}
                />
              </motion.div>
            )}

            {/* ==================== RESOURCES TAB ==================== */}
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

            {/* ==================== MEETINGS TAB ==================== */}
            {activeTab === 'meetings' && (
              <motion.div
                key="meetings"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div className="flex gap-1 border-b border-gray-200 bg-white rounded-t-xl px-2 pt-2">
                  <button
                    onClick={() => setMeetingsView('requests')}
                    className={`px-5 py-3 font-medium text-sm transition-colors relative rounded-t-lg ${
                      meetingsView === 'requests'
                        ? 'text-indigo-600 bg-indigo-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Meeting Requests
                    </span>
                    {meetingsView === 'requests' && (
                      <motion.div
                        layoutId="meetingsSubTab"
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600"
                      />
                    )}
                  </button>
                  <button
                    onClick={() => setMeetingsView('calendar')}
                    className={`px-5 py-3 font-medium text-sm transition-colors relative rounded-t-lg ${
                      meetingsView === 'calendar'
                        ? 'text-indigo-600 bg-indigo-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Calendar View
                    </span>
                    {meetingsView === 'calendar' && (
                      <motion.div
                        layoutId="meetingsSubTab"
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600"
                      />
                    )}
                  </button>
                </div>

                <AnimatePresence mode="wait">
                  {meetingsView === 'requests' ? (
                    <motion.div
                      key="requests-view"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                    >
                      <StudentMeetingRequest />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="calendar-view"
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                    >
                      <MeetingsCalendar />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* ==================== READINESS TAB ==================== */}
            {activeTab === 'readiness' && (
              <motion.div
                key="readiness"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                {loadingReadiness ? (
                  <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
                    <Loader2 className="w-12 h-12 animate-spin text-purple-600 mx-auto mb-4" />
                    <p className="text-gray-600">Analyzing your academic readiness...</p>
                    <p className="text-sm text-gray-400 mt-1">
                      Checking {studentInterests.length} interests, {studentElectives.length} electives
                    </p>
                  </div>
                ) : readinessData ? (
                  <ReadinessAnalysis
                    studentId={user?.uid}
                    interests={studentInterests}
                    electives={studentElectives}
                    honours={studentHonours}
                    onAnalysisComplete={(data) => {
                      setReadinessData(data);
                      toast.success('Readiness analysis updated!');
                    }}
                  />
                ) : (
                  <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
                    <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">
                      No Readiness Data
                    </h3>
                    <p className="text-gray-500 mb-6">
                      {studentInterests.length === 0
                        ? 'Set your interests first in the "My Interests" tab, then run analysis.'
                        : 'Run an analysis to see your readiness for electives and honours programs'
                      }
                    </p>
                    <div className="flex gap-3 justify-center">
                      {studentInterests.length === 0 && (
                        <button
                          onClick={() => setActiveTab('interests')}
                          className="px-6 py-3 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-all flex items-center gap-2"
                        >
                          <Heart className="w-5 h-5" />
                          Set Interests First
                        </button>
                      )}
                      <button
                        onClick={() => {
                          readinessFetchingRef.current = false;
                          fetchReadiness();
                        }}
                        className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:shadow-lg transition-all flex items-center gap-2"
                      >
                        <Zap className="w-5 h-5" />
                        Run Readiness Analysis
                      </button>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default StudentDashboard;