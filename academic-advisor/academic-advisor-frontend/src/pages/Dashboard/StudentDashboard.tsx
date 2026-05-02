// src/pages/Dashboard/StudentDashboard.tsx
// ENHANCED VERSION - All improvements implemented
// Changes marked with ✅ NEW or ✅ ENHANCED

import React, { useState, useEffect, useCallback, useRef, useMemo, Component, ErrorInfo, Suspense, lazy } from 'react';
import StudentMeetingRequest from '../../components/meetings/StudentMeetingRequest';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

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
  Zap,
  MessageSquare,
  Bot,
  Minimize2,
  Maximize2,
  TrendingUp as TrendUp,
  Shield,
  Rocket,
  Home,
  Inbox,
  HelpCircle,
  RotateCcw,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import PerformanceChart from '../../components/dashboard/PerformanceChart';
import { analyticsService, extendedAnalyticsService } from '../../services/analytics.service';
import { StudentProjectsList } from '../../components/dashboard/sections/StudentProjectsList';
import { StudentProjectsUpload } from '../../components/dashboard/sections/StudentProjectsUpload';
import { ProjectAnalysisResults } from '../../components/dashboard/sections/ProjectAnalysisResults';
import { studentProjectsService } from '../../services/student_projects_cloudinary.service';
import { getStudentAnalysisService } from '../../services/student_analysis.service';
import { mlIntegrationService } from '../../modules/agent1/student-analysis/services/ml-integration.service';
import { realtimeSyncService } from '../../modules/agent1/student-analysis/services/realtime-sync.service';
import {
  DetailedAnalysis,
  PredictionResult,
  WeaknessData,
} from '../../modules/agent1/student-analysis/types/student-analysis.types';
// ✅ LAZY-LOADED heavy components for faster initial dashboard render
const TrendAnalyzer = lazy(() => import('../../modules/agent1/performance-analytics/components/TrendAnalyzer'));
const SubjectPerformance = lazy(() => import('../../modules/agent1/performance-analytics/components/SubjectPerformance'));
const MLRecommendations = lazy(() => import('../../components/dashboard/MLRecommendations'));
const AcademicChatbot = lazy(() => import('../../components/dashboard/AcademicChatbot'));
const MeetingsCalendar = lazy(() => import('../../components/meetings/MeetingsCalendar'));
const ReadinessIndicator = lazy(() => import('../../components/dashboard/ReadinessIndicator'));
import {
  WeaknessAnalyzer,
  StudyResources,
} from '../../components/dashboard/EngineeringGuidance';
import {
  mlService,
  LegacyProjectAnalysisResult,
  ComprehensiveProjectAnalysisResponse,
} from '../../services/ml.service';
import toast from 'react-hot-toast';
import { AcademicDataEntry } from '../../components/dashboard/AcademicDataEntry';
import { InterestManagement } from '../../components/dashboard/InterestManagement';
import { AcademicInsights } from '../../components/dashboard/AcademicInsights';
import { auth } from '../../services/firebase.config';
import { ComprehensiveAnalysis } from '../../services/student_projects_cloudinary.service';
import { ReadinessAnalysis } from '../../components/dashboard/ReadinessAnalysis';
import { useStudentInterests, useSyncInterests } from '../../hooks/useEngineeringGuidance';
import { getWeaknessService } from '../../services/weakness.service';
// import ImprovementHub from '../../components/dashboard/ImprovementHub'; // COMMENTED OUT — Game Hub disabled
const PersonalizedRoadmap = lazy(() => import('../../components/dashboard/PersonalizedRoadmap'));

// ✅ Suspense fallback for lazy-loaded tabs
const TabLoader = () => (
  <div className="flex items-center justify-center py-16">
    <div className="flex flex-col items-center gap-3">
      <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      <p className="text-sm text-gray-500">Loading section...</p>
    </div>
  </div>
);

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

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  onRetry?: () => void;
}

// ==================== Constants ====================

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const PROFILE_STORAGE_KEY = 'academic_advisor_profile';

// ✅ NEW: Interests persistence key
const INTERESTS_STORAGE_KEY = 'academic_advisor_interests';

// ==================== Animation Variants (✅ ENHANCED) ====================

const animationVariants = {
  container: {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1,
      },
    },
  },
  item: {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 24,
      },
    },
  },
  // ✅ ENHANCED: Better hover lift and shadow
  card: {
    rest: {
      scale: 1,
      y: 0,
      boxShadow: '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px -1px rgba(0,0,0,0.1)',
    },
    hover: {
      scale: 1.025,
      y: -6,
      boxShadow: '0 20px 25px -5px rgba(0,0,0,0.08), 0 8px 10px -6px rgba(0,0,0,0.06)',
      transition: {
        type: 'spring',
        stiffness: 400,
        damping: 17,
      },
    },
    tap: { scale: 0.98 },
  },
  fadeIn: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },
  slideIn: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
  },
  // ✅ NEW: Nav item hover
  navItem: {
    rest: { x: 0 },
    hover: { x: 4, transition: { type: 'spring', stiffness: 400, damping: 20 } },
  },
};

// ==================== Error Boundary Component ====================

class DashboardErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Dashboard Error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center bg-white p-8 rounded-2xl shadow-xl max-w-md w-full"
          >
            <div className="h-20 w-20 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
              <AlertTriangle className="h-10 w-10 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-500 mb-2">
              We encountered an unexpected error while loading the dashboard.
            </p>
            {this.state.error && (
              <p className="text-xs text-gray-400 mb-6 font-mono bg-gray-50 p-2 rounded">
                {this.state.error.message}
              </p>
            )}
            <div className="space-y-3">
              <button
                onClick={this.handleRetry}
                className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center justify-center space-x-2"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Try Again</span>
              </button>
              <button
                onClick={() => window.location.reload()}
                className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Refresh Page</span>
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="w-full px-4 py-3 text-gray-500 hover:text-gray-700 transition-colors flex items-center justify-center space-x-2"
              >
                <Home className="h-4 w-4" />
                <span>Go to Home</span>
              </button>
            </div>
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

// ==================== Skeleton Loading Component ====================

const DashboardSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="flex h-screen">
        <div className="hidden lg:block w-72 bg-white border-r border-gray-200">
          <div className="animate-pulse p-5">
            <div className="flex items-center space-x-3 mb-6 p-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl">
              <div className="h-11 w-11 bg-gray-300 rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-300 rounded w-1/2" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-3 bg-gray-100 rounded-lg">
                  <div className="h-5 bg-gray-200 rounded w-full mb-1" />
                  <div className="h-3 bg-gray-200 rounded w-2/3 mx-auto" />
                </div>
              ))}
            </div>
            {[1, 2, 3, 4].map((section) => (
              <div key={section} className="mb-6">
                <div className="h-3 bg-gray-200 rounded w-20 mb-3" />
                {[1, 2, 3].map((item) => (
                  <div key={item} className="flex items-center space-x-3 p-3 mb-1">
                    <div className="h-8 w-8 bg-gray-200 rounded-lg" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                    </div>
                    <div className="h-5 w-8 bg-gray-200 rounded-full" />
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
            <div className="animate-pulse flex items-center space-x-4">
              <div className="h-10 w-10 bg-gray-200 rounded-lg" />
              <div className="hidden sm:flex items-center space-x-2">
                <div className="h-4 w-20 bg-gray-200 rounded" />
                <div className="h-4 w-4 bg-gray-200 rounded" />
                <div className="h-5 w-24 bg-gray-200 rounded" />
              </div>
            </div>
            <div className="animate-pulse flex items-center space-x-4">
              <div className="h-8 w-20 bg-gray-200 rounded-full hidden md:block" />
              <div className="h-8 w-8 bg-gray-200 rounded-full" />
              <div className="h-8 w-20 bg-gray-200 rounded-lg hidden sm:block" />
              <div className="pl-4 border-l border-gray-200 flex items-center space-x-3">
                <div className="hidden sm:block text-right">
                  <div className="h-4 w-24 bg-gray-200 rounded mb-1" />
                  <div className="h-3 w-16 bg-gray-200 rounded" />
                </div>
                <div className="h-9 w-9 bg-gray-200 rounded-full" />
              </div>
            </div>
          </div>

          <div className="flex-1 p-6 overflow-auto">
            <div className="animate-pulse space-y-6 max-w-7xl mx-auto">
              <div className="h-36 bg-gradient-to-r from-blue-200 to-purple-200 rounded-xl" />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div className="h-56 bg-gray-200 rounded-xl" />
                <div className="h-56 bg-gray-200 rounded-xl" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-48 bg-gray-200 rounded-xl" />
                ))}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-28 bg-gray-200 rounded-xl" />
                ))}
              </div>
              <div className="h-80 bg-gray-200 rounded-xl" />
            </div>
          </div>
        </div>
      </div>

      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center bg-white p-8 rounded-2xl shadow-2xl max-w-sm mx-4 border border-gray-100"
        >
          <div className="relative mb-6">
            <div className="h-24 w-24 mx-auto">
              <svg className="animate-spin h-24 w-24" viewBox="0 0 100 100">
                <circle
                  className="text-gray-200"
                  strokeWidth="6"
                  stroke="currentColor"
                  fill="transparent"
                  r="42"
                  cx="50"
                  cy="50"
                />
                <circle
                  className="text-blue-600"
                  strokeWidth="6"
                  strokeDasharray="264"
                  strokeDashoffset="66"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                  r="42"
                  cx="50"
                  cy="50"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <GraduationCap className="h-10 w-10 text-blue-600" />
              </div>
            </div>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Loading Your Dashboard</h3>
          <p className="text-gray-500 text-sm mb-4">Analyzing your academic performance...</p>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <motion.div
              className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 h-2 rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: 2.5, ease: 'easeInOut', repeat: Infinity }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-4">This may take a few moments...</p>
        </motion.div>
      </div>
    </div>
  );
};

// ==================== Empty State Component ====================

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void; icon?: React.ReactNode };
  secondaryAction?: { label: string; onClick: () => void };
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className = '',
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}
  >
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
      className="h-20 w-20 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center mb-5 shadow-sm"
    >
      {icon}
    </motion.div>
    <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
    <p className="text-sm text-gray-500 max-w-sm mb-6 leading-relaxed">{description}</p>
    <div className="flex items-center gap-3 flex-wrap justify-center">
      {action && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={action.onClick}
          className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all text-sm flex items-center space-x-2"
        >
          {action.icon}
          <span>{action.label}</span>
        </motion.button>
      )}
      {secondaryAction && (
        <button
          onClick={secondaryAction.onClick}
          className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors text-sm"
        >
          {secondaryAction.label}
        </button>
      )}
    </div>
  </motion.div>
);

// ==================== ✅ NEW: Animated Number Counter ====================

const AnimatedNumber: React.FC<{
  value: number;
  decimals?: number;
  duration?: number;
  suffix?: string;
  prefix?: string;
  className?: string;
}> = ({ value, decimals = 0, duration = 1200, suffix = '', prefix = '', className = '' }) => {
  const [displayValue, setDisplayValue] = useState(0);
  const previousValue = useRef(0);
  const frameRef = useRef<number>();

  useEffect(() => {
    const startValue = previousValue.current;
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutCubic for smooth deceleration
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = startValue + (value - startValue) * eased;
      setDisplayValue(current);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      } else {
        previousValue.current = value;
      }
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [value, duration]);

  return (
    <span className={className}>
      {prefix}
      {displayValue.toFixed(decimals)}
      {suffix}
    </span>
  );
};

// ✅ NEW: Helper to render animated values for StatCard
const renderAnimatedValue = (value: string): React.ReactNode => {
  // Pure number like "7.16" or "6"
  if (/^\d+\.?\d*$/.test(value.trim())) {
    const num = parseFloat(value);
    const dec = value.includes('.') ? (value.split('.')[1]?.length || 0) : 0;
    return <AnimatedNumber value={num} decimals={dec} />;
  }
  // Format "X/Y" like "0/166"
  const slashMatch = value.match(/^(\d+)\/(\d+)$/);
  if (slashMatch) {
    return (
      <>
        <AnimatedNumber value={parseInt(slashMatch[1])} />/{slashMatch[2]}
      </>
    );
  }
  return value;
};

// ==================== ✅ NEW: Enhanced SGPI Chart Component ====================

const EnhancedSGPIChart: React.FC<{
  performanceData: any;
  studentData: ExtendedDetailedAnalysis | null;
}> = ({ performanceData, studentData }) => {
  const chartData = useMemo(() => {
    if (studentData?.performance_data?.sgpa_trend?.length) {
      return studentData.performance_data.sgpa_trend.map((item) => ({
        semester: `Sem ${item.semester}`,
        sgpi: item.sgpa,
        credits: item.credits || 0,
      }));
    }
    if (performanceData?.semesterWiseData?.length) {
      return performanceData.semesterWiseData.map((item: any) => ({
        semester: `Sem ${item.semester}`,
        sgpi: item.sgpi || item.sgpa || 0,
        credits: item.credits || 0,
      }));
    }
    return [
      { semester: 'Sem 1', sgpi: 5.75, credits: 20 },
      { semester: 'Sem 2', sgpi: 7.16, credits: 22 },
    ];
  }, [performanceData, studentData]);

  const currentSGPI = chartData[chartData.length - 1]?.sgpi || 0;
  const previousSGPI =
    chartData.length > 1 ? chartData[chartData.length - 2]?.sgpi : currentSGPI;
  const percentChange = previousSGPI
    ? ((currentSGPI - previousSGPI) / previousSGPI) * 100
    : 0;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white px-4 py-3 rounded-xl shadow-xl border border-gray-100"
        >
          <p className="text-xs font-semibold text-gray-500 mb-1">{label}</p>
          <p className="text-lg font-bold text-indigo-600">
            SGPI: {payload[0].value.toFixed(2)}
          </p>
          {payload[0].payload.credits > 0 && (
            <p className="text-xs text-gray-400 mt-1">
              Credits: {payload[0].payload.credits}
            </p>
          )}
        </motion.div>
      );
    }
    return null;
  };

  const CustomDot = (props: any) => {
    const { cx, cy, index } = props;
    const isLast = index === chartData.length - 1;
    return (
      <g>
        {isLast && (
          <circle cx={cx} cy={cy} r={12} fill="#4F46E5" opacity={0.15}>
            <animate
              attributeName="r"
              values="8;14;8"
              dur="2s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="0.2;0.05;0.2"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
        )}
        <circle
          cx={cx}
          cy={cy}
          r={isLast ? 6 : 5}
          fill="#4F46E5"
          stroke="#fff"
          strokeWidth={isLast ? 3 : 2}
          className="drop-shadow-sm"
        />
      </g>
    );
  };

  return (
    <div>
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            Performance Trend
            {percentChange !== 0 && (
              <span
                className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${
                  percentChange >= 0
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}
              >
                {percentChange >= 0 ? (
                  <TrendingUp className="h-3 w-3 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1" />
                )}
                {Math.abs(percentChange).toFixed(2)}%
              </span>
            )}
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">SGPI across semesters</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900">
            <AnimatedNumber value={currentSGPI} decimals={2} />
          </p>
          <p className="text-xs text-gray-500">Current SGPI</p>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="sgpiGradientFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.25} />
              <stop offset="50%" stopColor="#7C3AED" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#4F46E5" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="sgpiStrokeGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#4F46E5" />
              <stop offset="100%" stopColor="#7C3AED" />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis
            dataKey="semester"
            tick={{ fontSize: 12, fill: '#6B7280' }}
            axisLine={{ stroke: '#E5E7EB' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 10]}
            ticks={[0, 2.5, 5.0, 7.5, 10.0]}
            tick={{ fontSize: 12, fill: '#6B7280' }}
            axisLine={{ stroke: '#E5E7EB' }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#E5E7EB', strokeDasharray: '4 4' }} />
          <ReferenceLine y={7.5} stroke="#10B981" strokeDasharray="3 3" strokeOpacity={0.4} />
          <Area
            type="monotone"
            dataKey="sgpi"
            stroke="url(#sgpiStrokeGradient)"
            strokeWidth={3}
            fill="url(#sgpiGradientFill)"
            dot={<CustomDot />}
            activeDot={{
              r: 8,
              fill: '#4F46E5',
              stroke: '#fff',
              strokeWidth: 3,
              className: 'drop-shadow-md',
            }}
            animationDuration={1800}
            animationEasing="ease-in-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// ==================== ✅ NEW: Readiness Breakdown Component ====================

const ReadinessBreakdown: React.FC<{
  readinessData: any;
  projectCount: number;
  studentData: ExtendedDetailedAnalysis | null;
  studentInterests: string[];
  userProfile: any;
}> = ({ readinessData, projectCount, studentData, studentInterests, userProfile }) => {
  const factors = useMemo(() => {
    const projectScore = Math.min(projectCount * 15, 100);
    const academicScore = studentData?.cgpa
      ? Math.min((studentData.cgpa / 10) * 100, 100)
      : 0;
    const interestsScore = Math.min(studentInterests.length * 11, 100);
    const profileScore = userProfile
      ? studentData?.profile_completeness || 50
      : 0;

    return [
      {
        label: 'Projects',
        score: projectScore,
        color: 'from-green-500 to-emerald-500',
        bgColor: 'bg-green-50',
        textColor: 'text-green-700',
        icon: Code,
      },
      {
        label: 'Academics',
        score: academicScore,
        color: 'from-blue-500 to-indigo-500',
        bgColor: 'bg-blue-50',
        textColor: 'text-blue-700',
        icon: GraduationCap,
      },
      {
        label: 'Interests',
        score: interestsScore,
        color: 'from-pink-500 to-rose-500',
        bgColor: 'bg-pink-50',
        textColor: 'text-pink-700',
        icon: Heart,
      },
      {
        label: 'Profile',
        score: profileScore,
        color: 'from-purple-500 to-violet-500',
        bgColor: 'bg-purple-50',
        textColor: 'text-purple-700',
        icon: User,
      },
    ];
  }, [projectCount, studentData, studentInterests, userProfile]);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-purple-200/50">
      {factors.map((factor, idx) => (
        <motion.div
          key={factor.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
          className={`${factor.bgColor} rounded-xl p-3`}
        >
          <div className="flex items-center gap-2 mb-2">
            <factor.icon className={`h-3.5 w-3.5 ${factor.textColor}`} />
            <span className="text-xs font-medium text-gray-700">{factor.label}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-white/60 rounded-full h-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${factor.score}%` }}
                transition={{ duration: 1, delay: 0.3 + idx * 0.15, ease: 'easeOut' }}
                className={`h-2 rounded-full bg-gradient-to-r ${factor.color}`}
              />
            </div>
            <span className={`text-xs font-bold ${factor.textColor} min-w-[32px] text-right`}>
              {Math.round(factor.score)}%
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

// ==================== Enhanced StatCard Component (✅ ENHANCED with AnimatedNumber) ====================

interface StatCardProps {
  title: string;
  value: string;
  change?: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'orange' | 'purple' | 'indigo' | 'pink' | 'yellow';
  onClick?: () => void;
  subtitle?: string;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  icon,
  color,
  onClick,
  subtitle,
  loading = false,
}) => {
  const colorConfig = {
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-600', gradient: 'from-blue-500 to-blue-600' },
    green: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-600', gradient: 'from-green-500 to-green-600' },
    orange: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-600', gradient: 'from-orange-500 to-orange-600' },
    purple: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-600', gradient: 'from-purple-500 to-purple-600' },
    indigo: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-600', gradient: 'from-indigo-500 to-indigo-600' },
    pink: { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-600', gradient: 'from-pink-500 to-pink-600' },
    yellow: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-600', gradient: 'from-yellow-500 to-yellow-600' },
  };
  const config = colorConfig[color];

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse">
        <div className="flex items-start justify-between mb-3">
          <div className="h-10 w-10 bg-gray-200 rounded-lg" />
          <div className="h-5 w-12 bg-gray-200 rounded" />
        </div>
        <div className="h-7 w-16 bg-gray-200 rounded mb-1" />
        <div className="h-4 w-20 bg-gray-200 rounded" />
      </div>
    );
  }

  return (
    <motion.div
      variants={animationVariants.card}
      initial="rest"
      whileHover="hover"
      whileTap="tap"
      onClick={onClick}
      className={`relative overflow-hidden bg-white rounded-xl shadow-sm border ${config.border} p-4 ${
        onClick ? 'cursor-pointer' : ''
      } transition-all duration-200`}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      aria-label={`${title}: ${value}`}
    >
      <div className={`absolute top-0 right-0 w-24 h-24 ${config.bg} rounded-full -mr-12 -mt-12 opacity-60`} />

      <div className="relative">
        <div className="flex items-start justify-between mb-3">
          <div className={`p-2.5 rounded-xl ${config.bg} transition-transform duration-200 group-hover:scale-110`}>
            {icon}
          </div>
          {change !== undefined && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className={`flex items-center space-x-1 text-xs font-semibold px-2 py-1 rounded-full ${
                change >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}
            >
              {change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              <span>{Math.abs(change).toFixed(1)}%</span>
            </motion.div>
          )}
        </div>

        {/* ✅ ENHANCED: Animated value */}
        <p className="text-2xl font-bold text-gray-900 mb-0.5">{renderAnimatedValue(value)}</p>
        <p className="text-xs text-gray-500 font-medium">{title}</p>
        {subtitle && <p className="text-[10px] text-gray-400 mt-1">{subtitle}</p>}
      </div>

      {onClick && (
        <div className="absolute bottom-3 right-3">
          <ChevronRight className={`h-4 w-4 ${config.text} opacity-50`} />
        </div>
      )}
    </motion.div>
  );
};

// ==================== Custom Toast Functions ====================

const showToast = {
  success: (message: string) => {
    toast.custom(
      (t) => (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          className={`flex items-center space-x-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-green-200 max-w-sm ${
            t.visible ? '' : 'pointer-events-none'
          }`}
        >
          <div className="flex-shrink-0 p-1.5 bg-green-100 rounded-full">
            <CheckCircle className="h-4 w-4 text-green-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="flex-shrink-0 p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </motion.div>
      ),
      { duration: 3000 }
    );
  },
  error: (message: string) => {
    toast.custom(
      (t) => (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          className={`flex items-center space-x-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-red-200 max-w-sm ${
            t.visible ? '' : 'pointer-events-none'
          }`}
        >
          <div className="flex-shrink-0 p-1.5 bg-red-100 rounded-full">
            <AlertCircle className="h-4 w-4 text-red-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="flex-shrink-0 p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </motion.div>
      ),
      { duration: 4000 }
    );
  },
  loading: (message: string) => {
    return toast.custom(
      () => (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          className="flex items-center space-x-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-blue-200 max-w-sm"
        >
          <Loader2 className="h-5 w-5 text-blue-600 animate-spin flex-shrink-0" />
          <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
        </motion.div>
      ),
      { duration: Infinity }
    );
  },
  info: (message: string) => {
    toast.custom(
      (t) => (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          className={`flex items-center space-x-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-blue-200 max-w-sm ${
            t.visible ? '' : 'pointer-events-none'
          }`}
        >
          <div className="flex-shrink-0 p-1.5 bg-blue-100 rounded-full">
            <Info className="h-4 w-4 text-blue-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="flex-shrink-0 p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </motion.div>
      ),
      { duration: 3000 }
    );
  },
};

// ==================== Helper Functions ====================

const saveProfileToStorage = (profile: any) => {
  if (profile) {
    localStorage.setItem(
      PROFILE_STORAGE_KEY,
      JSON.stringify({ ...profile, timestamp: Date.now() })
    );
  }
};

const loadProfileFromStorage = (): any => {
  try {
    const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      if (Date.now() - data.timestamp < 3600000) return data;
    }
  } catch (error) {
    console.error('Error loading profile from storage:', error);
  }
  return null;
};

// ✅ NEW: Interests persistence helpers
const saveInterestsToStorage = (interests: string[], electives: string[], honours: string[]) => {
  try {
    localStorage.setItem(
      INTERESTS_STORAGE_KEY,
      JSON.stringify({ interests, electives, honours, timestamp: Date.now() })
    );
  } catch (error) {
    console.error('Error saving interests to storage:', error);
  }
};

const loadInterestsFromStorage = (): {
  interests: string[];
  electives: string[];
  honours: string[];
} => {
  try {
    const stored = localStorage.getItem(INTERESTS_STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      // Expire after 24 hours
      if (Date.now() - (data.timestamp || 0) < 86400000) {
        return {
          interests: data.interests || [],
          electives: data.electives || [],
          honours: data.honours || [],
        };
      }
    }
  } catch (error) {
    console.error('Error loading interests from storage:', error);
  }
  return { interests: [], electives: [], honours: [] };
};

const transformWeaknessData = (weakness: WeaknessData): ExtendedWeaknessData => {
  return {
    subject: weakness.subject,
    topic: Array.isArray(weakness.topic) ? weakness.topic.join(', ') : weakness.topic,
    severity: (weakness as any).severity || 'low',
    gap: (weakness as any).gap || 0,
  };
};

// Performance metrics hook
const usePerformanceMetrics = () => {
  const [metrics] = useState({
    studentInfo: {
      year: 'Third Year',
      semester: 'Semester 5',
      branch: 'Information Technology',
      rollNumber: 'IT/2022/045',
    },
    subjects: [] as SubjectData[],
    overallCGPA: 0,
    semesterSGPA: 0,
    strongSubjects: [] as string[],
    weakSubjects: [] as string[],
    completedCredits: 0,
    totalCredits: 166,
    interests: [] as string[],
    careerGoals: [] as string[],
  });
  return metrics;
};

// ==================== Main Dashboard Component ====================

const StudentDashboardContent: React.FC = () => {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();

  // ==================== State ====================

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<
    | 'overview'
    | 'performance'
    | 'electives'
    | 'weaknesses'
    | 'resources'
    | 'projects'
    | 'academic'
    | 'interests'
    | 'meetings'
    | 'readiness'
    | 'chatbot'
    | 'notifications'
    // | 'roadmap'
    // | 'improvement' // COMMENTED OUT — Game Hub disabled
  >('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [projectsView, setProjectsView] = useState<'list' | 'upload'>('list');
  const [projectCount, setProjectCount] = useState(0);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [showProjectAnalysis, setShowProjectAnalysis] = useState(false);
  const [projectAnalysisResult, setProjectAnalysisResult] =
    useState<LegacyProjectAnalysisResult | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [meetingsView, setMeetingsView] = useState<'requests' | 'calendar'>('requests');
  const [recommendationStats, setRecommendationStats] = useState({
    careerPaths: 0,
    honoursProgramsMatch: 0,
    electivesRecommended: 0,
  });
  const [readinessData, setReadinessData] = useState<any>(null);
  const [loadingReadiness, setLoadingReadiness] = useState(false);

  // ✅ ENHANCED: Initialize interests from localStorage
    // ✅ FIXED: Use shared persistence utility for consistent initialization
  const [studentInterests, setStudentInterests] = useState<string[]>(
    () => loadInterestsFromStorage().interests
  );
  const [studentElectives, setStudentElectives] = useState<string[]>(
    () => loadInterestsFromStorage().electives
  );
  const [studentHonours, setStudentHonours] = useState<string[]>(
    () => loadInterestsFromStorage().honours
  );

  const [studentData, setStudentData] = useState<ExtendedDetailedAnalysis | null>(null);
  const [predictions, setPredictions] = useState<ExtendedPredictionResult | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [userProfile, setUserProfile] = useState<any>(null);
  const [showFloatingChatbot, setShowFloatingChatbot] = useState(false);

  const engineeringMetrics = usePerformanceMetrics();
  const userDisplayName = user?.name || user?.rollNumber || user?.email?.split('@')[0] || 'Student';

  // ==================== Refs ====================

  const initialFetchDone = useRef(false);
  const projectCountFetchedFor = useRef<string | null>(null);
  const interestsSyncedFor = useRef<string | null>(null);
  const readinessFetchingRef = useRef(false);

  // ==================== Tab Configuration ====================

  const tabConfig = {
    overview: { label: 'Overview', description: 'Dashboard summary' },
    chatbot: { label: 'AI Assistant', description: 'Ask anything' },
    performance: { label: 'Performance', description: 'Analytics & trends' },
    projects: { label: 'Projects', description: 'Your portfolio' },
    academic: { label: 'Academic Data', description: 'Profile setup' },
    interests: { label: 'Interests', description: 'Career goals' },
    electives: { label: 'Recommendations', description: 'AI suggestions' },
    weaknesses: { label: 'Weaknesses', description: 'Areas to improve' },
    resources: { label: 'Resources', description: 'Study materials' },
    meetings: { label: 'Meetings', description: 'Faculty sessions' },
    readiness: { label: 'Readiness', description: 'Career readiness' },
    notifications: { label: 'Notifications', description: 'Activity updates' },
    roadmap: { label: 'AI Roadmap', description: 'Personalized learning path' },
    // improvement: { label: 'Game Hub', description: 'Games, roadmaps & badges' }, // COMMENTED OUT
  };

  // ==================== ✅ NEW: Persist interests to localStorage ====================

  useEffect(() => {
    saveInterestsToStorage(studentInterests, studentElectives, studentHonours);
  }, [studentInterests, studentElectives, studentHonours]);

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
        honoursProgramsMatch:
          data.honours?.filter((h: any) => h.eligibility)?.length || 0,
        electivesRecommended: data.electives?.length || 0,
      });
    } catch (error) {
      console.error('Error fetching recommendation stats:', error);
    }
  }, []);

  const fetchReadiness = useCallback(async () => {
    if (!user?.uid) return;
    if (readinessFetchingRef.current) return;
    readinessFetchingRef.current = true;
    setLoadingReadiness(true);
    try {
      const service = getWeaknessService();
      const data = await service.getReadiness(
        user.uid,
        studentInterests.length > 0 ? studentInterests : undefined,
        studentElectives.length > 0 ? studentElectives : undefined,
        studentHonours.length > 0 ? studentHonours : undefined
      );
      setReadinessData(data);
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
        percentageChange: 0,
      }),
      currentSGPI: profile.cgpa || 0,
      cgpa: profile.cgpa,
      totalCredits: profile.total_credits,
      currentSemester: profile.semester,
      department: profile.branch,
    }));
  }, []);

  const fetchProjectCount = useCallback(async () => {
    if (!user?.uid) return;
    if (projectCountFetchedFor.current === user.uid) return;
    projectCountFetchedFor.current = user.uid;
    try {
      setProjectsLoading(true);
      const projects = await studentProjectsService.getUserProjects();
      setProjectCount(projects.length);
    } catch (error) {
      console.error('Error fetching project count:', error);
      setProjectCount(0);
    } finally {
      setProjectsLoading(false);
    }
  }, [user?.uid]);

  const refetchProjectCount = useCallback(async () => {
    if (!user?.uid) return;
    projectCountFetchedFor.current = null;
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
      let token: string | null = null;
      if (currentUser) {
        token = await currentUser.getIdToken(true);
      } else {
        // Student users: use stored JWT
        token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
      }
      if (!token) return;

      let response = await fetch(`${BACKEND_URL}/api/v1/student-profile/me`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 404) {
        response = await fetch(`${BACKEND_URL}/api/v1/student-profile/profile`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
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
          career_goals: data.career_goals || [],
        };
        setUserProfile(profile);
        saveProfileToStorage(profile);
        updateDashboardWithProfile(profile);
        localStorage.setItem('userBranch', profile.branch);
        localStorage.setItem('userSemester', profile.semester.toString());
        window.dispatchEvent(new CustomEvent('profileLoaded', { detail: profile }));
      } else if (response.status === 404) {
        localStorage.removeItem(PROFILE_STORAGE_KEY);
        setUserProfile(null);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      if (!userProfile && cachedProfile) showToast.info('Using cached profile data');
    }
  }, [user?.uid, updateDashboardWithProfile]);

  const fetchDashboardData = useCallback(
    async (showLoader = true) => {
      if (!user?.uid) {
        setLoading(false);
        return;
      }
      try {
        if (showLoader) setLoading(true);
        const [chartData, stats, metrics] = await Promise.all([
          extendedAnalyticsService.getPerformanceChartData(user.uid),
          extendedAnalyticsService.getDashboardStats(user.uid),
          extendedAnalyticsService.getPerformanceMetrics(user.uid),
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
            profile_completeness: fullData.completion_percentage,
          });
        }
        setLastUpdated(new Date());
      } catch (error) {
        console.error('Dashboard fetch error:', error);
        showToast.error('Failed to load dashboard data');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [user?.uid]
  );

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    invalidateAllCaches();
    projectCountFetchedFor.current = null;
    interestsSyncedFor.current = null;
    readinessFetchingRef.current = false;
    await Promise.all([
      fetchDashboardData(false),
      fetchRecommendationStats(),
      fetchReadiness(),
      refetchProjectCount(),
    ]);
    setLastUpdated(new Date());
    showToast.success('Dashboard refreshed!');
  }, [
    invalidateAllCaches,
    fetchDashboardData,
    fetchRecommendationStats,
    fetchReadiness,
    refetchProjectCount,
  ]);

  const handleProjectAnalyzed = useCallback(
    async (analysisResponse: ComprehensiveAnalysis) => {
      try {
        const legacyFormat: LegacyProjectAnalysisResult = {
          inferred_interests: analysisResponse.inferred_interests.map((i) => ({
            domain: i.domain,
            confidence: i.confidence,
            keywords: i.keywords || [],
            relatedSkills: i.relatedSkills || [],
            careerPaths: i.careerPaths || [],
            industryRelevance: i.industryRelevance || i.confidence * 0.9,
          })),
          elective_recommendations: analysisResponse.elective_recommendations.map((e) => ({
            elective: e.elective,
            code: '',
            match_score: e.match_score,
            reasons: e.reasons,
            skills_to_gain: e.skills_to_gain,
            career_relevance: e.career_relevance,
            difficulty_level: e.difficulty_level,
          })),
          honours_minor_recommendations: analysisResponse.honours_minor_recommendations.map(
            (h) => ({
              program: h.program,
              type: h.type,
              match_score: h.match_score,
              courses: h.courses,
              career_paths: h.career_paths,
              credits: h.credits,
              semester_commitment: h.semester_commitment,
              reasons: h.reasons,
            })
          ),
          career_paths: analysisResponse.career_paths.map((c) => ({
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
                  (resources as string[]).map((r) => ({ platform: 'Online', course: r })),
                ]
              )
            ),
            completeness_percentage: 70,
            estimated_learning_time:
              analysisResponse.skill_gap_analysis.estimated_learning_time,
          },
          next_steps: analysisResponse.next_steps.map((s) => ({
            action: s.action,
            category: s.category,
            priority: s.priority,
            deadline: s.deadline,
            details: s.details,
          })),
          metadata: {
            analysis_date:
              analysisResponse.metadata?.analysis_date || new Date().toISOString(),
            confidence_score: analysisResponse.metadata?.confidence_score || 0.75,
            model_version: '2.0.0',
            data_sources: ['projects'],
          },
        };
        setProjectAnalysisResult(legacyFormat);
        setShowProjectAnalysis(true);
        setRecommendationStats({
          careerPaths: analysisResponse.career_paths?.length || 0,
          honoursProgramsMatch:
            analysisResponse.honours_minor_recommendations?.filter(
              (h) => h.eligibility_met
            )?.length || 0,
          electivesRecommended: analysisResponse.elective_recommendations?.length || 0,
        });
        showToast.success('Project analyzed! View your personalized recommendations.');
      } catch (error) {
        console.error('Error processing analysis:', error);
        showToast.error('Failed to process analysis results');
      }
    },
    []
  );

  const handleDownloadReport = useCallback(() => {
    const reportData = {
      student: userDisplayName,
      date: new Date().toLocaleDateString(),
      studentId: user?.uid,
      department:
        userProfile?.branch || studentData?.department || engineeringMetrics.studentInfo.branch,
      currentSemester: userProfile?.semester
        ? `Semester ${userProfile.semester}`
        : studentData?.current_semester
        ? `Semester ${studentData.current_semester}`
        : engineeringMetrics.studentInfo.semester,
      currentSGPI: dashboardStats?.currentSGPI,
      cgpa: studentData?.cgpa || engineeringMetrics.overallCGPA,
      trend: dashboardStats?.trend,
      performanceHistory:
        studentData?.performance_data?.sgpa_trend || performanceData?.semesterWiseData,
      weaknesses: studentData?.weaknesses || [],
      predictions,
      insights,
      recommendationStats,
      readiness: readinessData
        ? {
            score: readinessData.overall_readiness_score,
            level: readinessData.readiness_level,
            recommendation: readinessData.primary_recommendation,
          }
        : null,
      lastUpdated: lastUpdated.toISOString(),
    };
    const dataStr = JSON.stringify(reportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `academic_report_${new Date().toISOString().split('T')[0]}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    showToast.success('Report downloaded!');
  }, [
    userDisplayName,
    user?.uid,
    userProfile,
    studentData,
    dashboardStats,
    performanceData,
    predictions,
    insights,
    recommendationStats,
    readinessData,
    lastUpdated,
    engineeringMetrics,
  ]);

  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId as any);
    if (tabId === 'chatbot') setShowFloatingChatbot(false);
    if (window.innerWidth < 1024) setSidebarOpen(false);
    analyticsService.trackEvent('tab_switched', { tab: tabId });
  }, []);

  // ==================== Effects ====================

  useEffect(() => {
    const handleProfileSaved = (event: Event) => {
      const detail = (event as CustomEvent).detail;
      setUserProfile(detail);
      saveProfileToStorage(detail);
      updateDashboardWithProfile(detail);
      showToast.success('Profile data updated!');
    };

    const handleProfileUpdated = async () => {
      extendedAnalyticsService.clearCache();
      await fetchUserProfile();
      await fetchDashboardData(false);
    };

    const handleAcademicDataUpdated = async () => {
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
      showToast.success('Dashboard updated with new academic data!');
    };

    // ✅ ENHANCED: Also persist interests from events
        // ✅ FIXED: Handle interestsUpdated event with ALL correct field names
    const handleInterestsUpdated = async (event: Event) => {
      const detail = (event as CustomEvent).detail;

      // Update interests (AI, Web Dev, etc.)
      if (detail?.interests && Array.isArray(detail.interests)) {
        setStudentInterests(detail.interests);
        console.log('📥 Dashboard received interests:', detail.interests.length);
      }

      // Update electives (preferred course electives — separate from careerGoals)
      if (detail?.electives && Array.isArray(detail.electives)) {
        setStudentElectives(detail.electives);
        console.log('📥 Dashboard received electives:', detail.electives.length);
      }

      // Update honours (honours/minor programs)
      if (detail?.honours && Array.isArray(detail.honours)) {
        setStudentHonours(detail.honours);
        console.log('📥 Dashboard received honours:', detail.honours.length);
      }

      // Log career goals and skills (available for future use)
      if (detail?.careerGoals && Array.isArray(detail.careerGoals)) {
        console.log('📥 Dashboard received careerGoals:', detail.careerGoals.length);
      }
      if (detail?.skills && Array.isArray(detail.skills)) {
        console.log('📥 Dashboard received skills:', detail.skills.length);
      }

      // ✅ FIX: Also persist to dashboard's localStorage
      // (interestPersistence.ts already saved from InterestManagement,
      //  but this ensures dashboard state stays in sync)

      invalidateAllCaches();
      setReadinessData(null);
      readinessFetchingRef.current = false;

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
  }, [
    user?.uid,
    queryClient,
    fetchUserProfile,
    fetchDashboardData,
    fetchRecommendationStats,
    fetchReadiness,
    invalidateAllCaches,
    updateDashboardWithProfile,
    handleProjectAnalyzed,
  ]);

  useEffect(() => {
    const fetchAndSyncInterests = async () => {
      if (!user?.uid) return;
      if (interestsSyncedFor.current === user.uid) return;
      interestsSyncedFor.current = user.uid;

      // ✅ ENHANCED: Check localStorage first before API calls
      const cached = loadInterestsFromStorage();
      if (cached.interests.length > 0) {
        setStudentInterests(cached.interests);
        if (cached.electives.length) setStudentElectives(cached.electives);
        if (cached.honours.length) setStudentHonours(cached.honours);
      }

      try {
        const service = getWeaknessService();
        try {
          const interestProfile = await service.getInterests(user.uid);
          if (interestProfile.interests?.length) {
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

        try {
          const syncResult = await service.syncInterests(user.uid);
          if (syncResult.status === 'success' && syncResult.interests?.length) {
            setStudentInterests(syncResult.interests);
            return;
          }
        } catch (e) {
          console.warn('Sync failed:', e);
        }

        if (userProfile?.interests?.length) {
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
  }, [user?.uid]);

  useEffect(() => {
    if (studentInterests.length === 0 && userProfile?.interests?.length > 0) {
      setStudentInterests(userProfile.interests);
    }
  }, [userProfile?.interests, studentInterests.length]);

  const interestsKey = studentInterests.join(',');
  const electivesKey = studentElectives.join(',');
  const honoursKey = studentHonours.join(',');

  useEffect(() => {
    if (user?.uid && (interestsKey || electivesKey || honoursKey)) {
      readinessFetchingRef.current = false;
      fetchReadiness();
    }
  }, [user?.uid, interestsKey, electivesKey, honoursKey, fetchReadiness]);

  useEffect(() => {
    const handleProjectUploaded = async () => {
      await refetchProjectCount();
      try {
        const freshRecs = await mlService.getRecommendations(true, true, true, true);
        setRecommendationStats({
          careerPaths: freshRecs.careers?.length || 0,
          honoursProgramsMatch: freshRecs.honours?.filter(
            (h: any) => h.eligibility !== false
          )?.length || 0,
          electivesRecommended: freshRecs.electives?.length || 0,
        });
      } catch (e) {
        console.warn('Recommendation refresh after upload (non-critical):', e);
        await fetchRecommendationStats();
      }
      if (studentInterests.length > 0) {
        readinessFetchingRef.current = false;
        fetchReadiness();
      }
    };
    window.addEventListener('projectUploaded', handleProjectUploaded);
    return () => window.removeEventListener('projectUploaded', handleProjectUploaded);
  }, [refetchProjectCount, fetchRecommendationStats, fetchReadiness, studentInterests.length]);

  useEffect(() => {
    if (user && !initialFetchDone.current) {
      initialFetchDone.current = true;
      fetchUserProfile();
      fetchDashboardData();
      fetchProjectCount();
      fetchRecommendationStats();
    } else if (!user) {
      setLoading(false);
    }
  }, [user, fetchUserProfile, fetchDashboardData, fetchProjectCount, fetchRecommendationStats]);

  useEffect(() => {
    if (activeTab === 'projects' && projectCount === 0 && !projectsLoading) {
      projectCountFetchedFor.current = null;
      fetchProjectCount();
    }
  }, [activeTab, projectCount, projectsLoading, fetchProjectCount]);

  useEffect(() => {
    if (!user?.uid) return;
    const unsubscribe = extendedAnalyticsService.subscribeToMetrics(
      user.uid,
      (metrics: any[]) => {
        if (metrics && metrics.length > 0) {
          const stats = {
            currentSGPI: metrics[0].sgpi,
            previousSGPI: metrics[1]?.sgpi || metrics[0].sgpi,
            trend: metrics[0].sgpi > (metrics[1]?.sgpi || 0) ? 'up' : 'down',
            percentageChange: metrics[1]
              ? ((metrics[0].sgpi - metrics[1].sgpi) / metrics[1].sgpi) * 100
              : 0,
          };
          const chartData = {
            ...stats,
            semesterWiseData: metrics.map((m: any) => ({
              semester: m.semester,
              sgpi: m.sgpi,
              credits: m.credits,
              courses: m.courses,
            })),
          };
          setPerformanceData(chartData);
        }
      }
    );

    let subscriptionId: string | null = null;
    try {
      subscriptionId = realtimeSyncService.subscribeToStudentUpdates(
        user.uid,
        (update) => {
          if (update.data) {
            showToast.info('Performance data updated!');
            fetchDashboardData(false);
          }
        }
      );
    } catch (err) {
      console.warn('Realtime sync subscription failed:', err);
    }

    return () => {
      unsubscribe();
      if (subscriptionId) {
        try {
          realtimeSyncService.unsubscribe(subscriptionId);
        } catch {}
      }
    };
  }, [user?.uid, fetchDashboardData]);

  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      fetchDashboardData(false);
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [user, fetchDashboardData]);

  // ==================== Loading State ====================

  if (loading) {
    return <DashboardSkeleton />;
  }

    // ==================== Main Render ====================
  // (Continues from Part 1)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
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
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* ==================== LAYOUT CONTAINER ==================== */}
      <div className="flex h-screen overflow-hidden">
        {/* ==================== ENHANCED SIDEBAR (✅ ENHANCED with nav animations) ==================== */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-50 lg:z-0
            w-72 flex-shrink-0
            bg-white shadow-xl lg:shadow-sm border-r border-gray-200
            transform transition-all duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            ${!sidebarOpen && 'lg:w-0 lg:overflow-hidden lg:border-0'}
          `}
          role="navigation"
          aria-label="Main navigation"
        >
          <div className="h-full flex flex-col overflow-hidden">
            {/* Sidebar Header */}
            <div className="p-5 border-b bg-gradient-to-r from-blue-600 to-purple-600 flex-shrink-0">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="h-11 w-11 rounded-full bg-white/20 backdrop-blur flex items-center justify-center ring-2 ring-white/30">
                    <User className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-white text-sm leading-tight">{userDisplayName}</p>
                    <p className="text-xs text-white/70">{userProfile?.branch || 'IT'} • {engineeringMetrics.studentInfo.year}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="lg:hidden p-1.5 rounded-lg hover:bg-white/20 transition-colors focus:outline-none focus:ring-2 focus:ring-white/50"
                  aria-label="Close sidebar"
                >
                  <X className="h-5 w-5 text-white" />
                </button>
              </div>

              {/* Quick Stats - ✅ ENHANCED with animated numbers */}
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-white/10 backdrop-blur rounded-lg">
                  <p className="text-lg font-bold text-white">
                    <AnimatedNumber value={studentData?.cgpa || 0} decimals={1} />
                  </p>
                  <p className="text-[10px] text-white/70 uppercase tracking-wide">CGPA</p>
                </div>
                <div className="text-center p-2 bg-white/10 backdrop-blur rounded-lg">
                  <p className="text-lg font-bold text-white">
                    <AnimatedNumber value={userProfile?.semester || 5} />
                  </p>
                  <p className="text-[10px] text-white/70 uppercase tracking-wide">Sem</p>
                </div>
                <div className="text-center p-2 bg-white/10 backdrop-blur rounded-lg">
                  <p className="text-lg font-bold text-white">
                    <AnimatedNumber value={projectCount} />
                  </p>
                  <p className="text-[10px] text-white/70 uppercase tracking-wide">Projects</p>
                </div>
              </div>
            </div>

            {/* Navigation - ✅ ENHANCED with animated active indicator */}
            <nav className="flex-1 p-4 overflow-y-auto" aria-label="Dashboard navigation">
              {/* Main Navigation */}
              <div className="mb-6">
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                  Main Menu
                </p>
                <ul className="space-y-1" role="list">
                  {[
                    { id: 'overview', icon: BarChart3, label: 'Overview', description: 'Dashboard summary' },
                    { id: 'chatbot', icon: Bot, label: 'AI Assistant', badge: 'AI', badgeColor: 'bg-gradient-to-r from-blue-500 to-purple-500', description: 'Ask anything' },
                    { id: 'performance', icon: Activity, label: 'Performance', showTrend: studentData?.improvement_trend === 'improving', description: 'Analytics & trends' },
                  ].map((item) => (
                    <li key={item.id}>
                      <motion.button
                        variants={animationVariants.navItem}
                        initial="rest"
                        whileHover="hover"
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all group focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 relative overflow-hidden ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        {/* ✅ NEW: Animated active indicator bar */}
                        {activeTab === item.id && (
                          <motion.div
                            layoutId="activeNavIndicator"
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-r-full"
                            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                          />
                        )}
                        <div className="flex items-center space-x-3">
                          <div className={`p-1.5 rounded-lg transition-all duration-200 ${
                            activeTab === item.id 
                              ? 'bg-blue-100' 
                              : 'bg-gray-100 group-hover:bg-gray-200 group-hover:scale-110'
                          }`}>
                            <item.icon className="h-4 w-4" />
                          </div>
                          <div className="text-left">
                            <span className="font-medium text-sm block">{item.label}</span>
                            <span className="text-[10px] text-gray-400">{item.description}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-1">
                          {item.showTrend && <TrendingUp className="h-3 w-3 text-green-500" />}
                          {item.badge && (
                            <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                              {item.badge}
                            </span>
                          )}
                        </div>
                      </motion.button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Academic Section */}
              <div className="mb-6">
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                  Academic
                </p>
                <ul className="space-y-1" role="list">
                  {[
                    { id: 'projects', icon: FolderOpen, label: 'My Projects', badge: projectCount > 0 ? projectCount.toString() : 'Add', badgeColor: projectCount > 0 ? 'bg-green-500' : 'bg-yellow-500' },
                    { id: 'academic', icon: GraduationCap, label: 'Academic Data', badge: userProfile ? '✓' : 'Setup', badgeColor: userProfile ? 'bg-green-500' : 'bg-yellow-500' },
                    { id: 'interests', icon: Heart, label: 'My Interests', badge: studentInterests.length > 0 ? studentInterests.length.toString() : 'Setup', badgeColor: studentInterests.length > 0 ? 'bg-pink-500' : 'bg-yellow-500' },
                  ].map((item) => (
                    <li key={item.id}>
                      <motion.button
                        variants={animationVariants.navItem}
                        initial="rest"
                        whileHover="hover"
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 relative overflow-hidden ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        {activeTab === item.id && (
                          <motion.div
                            layoutId="activeNavIndicator"
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-r-full"
                            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                          />
                        )}
                        <div className="flex items-center space-x-3">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </motion.button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* AI Features Section */}
              <div className="mb-6">
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                  AI Features
                </p>
                <ul className="space-y-1" role="list">
                  {[
                    { id: 'electives', icon: Sparkles, label: 'AI Recommendations', badge: recommendationStats.electivesRecommended.toString(), badgeColor: 'bg-purple-500' },
                    { id: 'weaknesses', icon: AlertCircle, label: 'Weakness Analysis', badge: studentData?.weakness_count?.toString() || '0', badgeColor: 'bg-orange-500' },
                    { id: 'readiness', icon: Target, label: 'Readiness Score', badge: readinessData ? `${Math.round(readinessData.overall_readiness_score)}%` : '-', badgeColor: 'bg-indigo-500' },
                  ].map((item) => (
                    <li key={item.id}>
                      <motion.button
                        variants={animationVariants.navItem}
                        initial="rest"
                        whileHover="hover"
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 relative overflow-hidden ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        {activeTab === item.id && (
                          <motion.div
                            layoutId="activeNavIndicator"
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-r-full"
                            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                          />
                        )}
                        <div className="flex items-center space-x-3">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </motion.button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Growth Section — Game Learning Hub — COMMENTED OUT */}
              {/* <div className="mb-6">
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                  Growth
                </p>
                <ul className="space-y-1" role="list">
                  {[
                    { id: 'improvement', icon: Rocket, label: 'Game Hub', badge: 'XP', badgeColor: 'bg-gradient-to-r from-amber-500 to-orange-500', description: 'Games, roadmaps & badges' },
                  ].map((item) => (
                    <li key={item.id}>
                      <motion.button
                        variants={animationVariants.navItem}
                        initial="rest"
                        whileHover="hover"
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all group focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 relative overflow-hidden ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        {activeTab === item.id && (
                          <motion.div
                            layoutId="activeNavIndicator"
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-r-full"
                            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                          />
                        )}
                        <div className="flex items-center space-x-3">
                          <div className={`p-1.5 rounded-lg transition-all duration-200 ${
                            activeTab === item.id
                              ? 'bg-blue-100'
                              : 'bg-gray-100 group-hover:bg-gray-200 group-hover:scale-110'
                          }`}>
                            <item.icon className="h-4 w-4" />
                          </div>
                          <div className="text-left">
                            <span className="font-medium text-sm block">{item.label}</span>
                            <span className="text-[10px] text-gray-400">{item.description}</span>
                          </div>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </motion.button>
                    </li>
                  ))}
                </ul>
              </div> */}

              {/* Resources Section */}
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                  Resources
                </p>
                <ul className="space-y-1" role="list">
                  {[
                    { id: 'resources', icon: BookOpen, label: 'Study Resources', badge: 'New', badgeColor: 'bg-green-500' },
                    { id: 'meetings', icon: Calendar, label: 'Faculty Meetings', badge: 'Book', badgeColor: 'bg-indigo-500' },
                    { id: 'notifications', icon: Bell, label: 'Notifications', badge: '•', badgeColor: 'bg-red-500' },
                    // { id: 'roadmap', icon: Rocket, label: 'AI Roadmap', badge: 'AI', badgeColor: 'bg-violet-500' },
                  ].map((item) => (
                    <li key={item.id}>
                      <motion.button
                        variants={animationVariants.navItem}
                        initial="rest"
                        whileHover="hover"
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 relative overflow-hidden ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        {activeTab === item.id && (
                          <motion.div
                            layoutId="activeNavIndicator"
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-r-full"
                            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                          />
                        )}
                        <div className="flex items-center space-x-3">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </motion.button>
                    </li>
                  ))}
                </ul>
              </div>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t bg-gray-50 flex-shrink-0 space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="flex items-center justify-center space-x-1.5 px-3 py-2 bg-white rounded-lg hover:bg-gray-100 text-gray-700 transition-colors text-xs font-medium border border-gray-200 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Refresh dashboard"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleDownloadReport}
                  className="flex items-center justify-center space-x-1.5 px-3 py-2 bg-white rounded-lg hover:bg-gray-100 text-gray-700 transition-colors text-xs font-medium border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Download report"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Export</span>
                </motion.button>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={logout}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl hover:from-red-600 hover:to-pink-600 transition-all shadow-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </motion.button>

              <p className="text-[10px] text-gray-400 text-center">
                AI Academic Advisor v2.0 • {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        </aside>

        {/* ==================== MAIN CONTENT ==================== */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* ==================== ENHANCED HEADER (✅ "Live" replaced with "Data Synced") ==================== */}
          <header className="bg-white shadow-sm border-b flex-shrink-0 z-30" role="banner">
            <div className="px-4 lg:px-6">
              <div className="flex items-center justify-between h-16">
                {/* Left Section */}
                <div className="flex items-center space-x-4">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label="Toggle sidebar"
                    aria-expanded={sidebarOpen}
                  >
                    <Menu className="h-5 w-5 text-gray-600" />
                  </motion.button>

                  {/* Breadcrumb */}
                  <nav className="hidden sm:flex items-center space-x-2 text-sm" aria-label="Breadcrumb">
                    <span className="text-gray-400">Dashboard</span>
                    <ChevronRight className="h-4 w-4 text-gray-300" aria-hidden="true" />
                    <span className="font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      {tabConfig[activeTab]?.label || 'Overview'}
                    </span>
                  </nav>

                  {/* Mobile Title */}
                  <h1 className="sm:hidden text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {tabConfig[activeTab]?.label || 'Overview'}
                  </h1>
                </div>

                {/* Right Section */}
                <div className="flex items-center space-x-2 sm:space-x-4">
                  {/* ✅ REPLACED: "Live" badge → "Data Synced" / "Updated Recently" indicator */}
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="hidden md:flex items-center space-x-2 px-3 py-1.5 bg-blue-50 rounded-full border border-blue-200"
                  >
                    <CheckCircle className="h-3.5 w-3.5 text-blue-600" aria-hidden="true" />
                    <span className="text-xs font-medium text-blue-700">Data Synced</span>
                  </motion.div>

                  {/* Last Updated */}
                  <div className="hidden lg:flex items-center space-x-1 text-xs text-gray-500">
                    <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>

                  {/* Notification Bell */}
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setActiveTab('notifications')}
                    className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                    title="Notifications"
                    aria-label="View notifications"
                  >
                    <Bell className="h-4 w-4 text-gray-600" />
                  </motion.button>

                  {/* Refresh Button */}
                  <motion.button
                    whileHover={{ scale: 1.1, rotate: 15 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    title="Refresh Dashboard"
                    aria-label="Refresh dashboard"
                  >
                    <RefreshCw className={`h-4 w-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
                  </motion.button>

                  {/* Download Report */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleDownloadReport}
                    className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label="Export report"
                  >
                    <Download className="h-4 w-4" />
                    <span className="hidden md:inline">Export</span>
                  </motion.button>

                  {/* Profile Section */}
                  <div className="flex items-center space-x-3 pl-3 border-l border-gray-200">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm font-semibold text-gray-900 leading-tight">{userDisplayName}</p>
                      <p className="text-xs text-gray-500 leading-tight">
                        {userProfile?.branch || 'IT'} • Sem {userProfile?.semester || '5'}
                      </p>
                    </div>
                    <div className="relative">
                      <div className="h-9 w-9 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center ring-2 ring-white shadow-sm">
                        <User className="h-4 w-4 text-white" />
                      </div>
                      <span className="absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full bg-green-500 ring-2 ring-white" aria-hidden="true" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress Bar for Refreshing */}
            <AnimatePresence>
              {refreshing && (
                <motion.div
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-0.5 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 origin-left"
                  transition={{ duration: 2, ease: 'easeInOut' }}
                />
              )}
            </AnimatePresence>
          </header>

          {/* ==================== PAGE CONTENT ==================== */}
          <main className="flex-1 overflow-y-auto p-4 lg:p-6 scroll-smooth" role="main">
            {/* ✅ NEW: Wrap nav items in LayoutGroup for animated indicator */}
            <LayoutGroup>
            <AnimatePresence mode="wait">

              {/* ==================== OVERVIEW TAB (✅ ENHANCED) ==================== */}
              {activeTab === 'overview' && (
                <motion.div
                  key="overview"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="space-y-6 max-w-7xl mx-auto"
                >
                  {/* ROW 1: AI ASSISTANT BANNER */}
                  <motion.div
                    variants={animationVariants.item}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-5 text-white shadow-lg"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                      <div className="flex items-center space-x-4">
                        <motion.div
                          animate={{ rotate: [0, 5, -5, 0] }}
                          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                          className="h-12 w-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center flex-shrink-0"
                        >
                          <Bot className="h-7 w-7 text-white" />
                        </motion.div>
                        <div>
                          <h2 className="text-lg font-bold">AI Academic Assistant</h2>
                          <p className="text-white/80 text-sm">
                            Get instant help with syllabus, faculty info, performance analysis & career guidance
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => setShowFloatingChatbot(true)}
                          className="px-3 py-2 bg-white/20 backdrop-blur hover:bg-white/30 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-white/50"
                        >
                          <MessageSquare className="h-4 w-4" />
                          Quick Chat
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleTabChange('chatbot')}
                          className="px-3 py-2 bg-white text-blue-600 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-white"
                        >
                          Open Full Assistant
                          <ChevronRight className="h-4 w-4" />
                        </motion.button>
                      </div>
                    </div>

                    {/* Quick Suggestions */}
                    <div className="mt-4 pt-4 border-t border-white/20">
                      <div className="flex flex-wrap gap-2">
                        {['Explain deadlock in OS', 'Who teaches DBMS?', 'Show my performance', 'Recommend electives'].map((suggestion, idx) => (
                          <motion.button
                            key={idx}
                            whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.2)' }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleTabChange('chatbot')}
                            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-full text-xs transition-colors focus:outline-none focus:ring-2 focus:ring-white/50"
                          >
                            {suggestion}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  </motion.div>

                  {/* ROW 2: AI INSIGHTS + AI RECOMMENDATIONS SUMMARY */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* AI Insights & Recommendations */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      className="bg-gradient-to-br from-blue-50 to-purple-50 border border-purple-200 rounded-2xl p-5"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold text-gray-900 flex items-center">
                          <Brain className="h-5 w-5 mr-2 text-purple-600" />
                          AI Insights & Recommendations
                        </h3>
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                          Personalized
                        </span>
                      </div>
                      {insights?.recommendations && insights.recommendations.length > 0 ? (
                        <div className="space-y-3">
                          {insights.recommendations.slice(0, 3).map((rec: any, index: number) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="flex items-start space-x-3 bg-white p-3 rounded-xl shadow-sm hover:shadow-md transition-shadow"
                            >
                              <div className={`mt-0.5 h-2.5 w-2.5 rounded-full flex-shrink-0 ${
                                rec.type === 'success' ? 'bg-green-500' :
                                rec.type === 'warning' ? 'bg-yellow-500' :
                                rec.type === 'alert' ? 'bg-orange-500' : 'bg-blue-500'
                              }`} />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-700 font-medium line-clamp-2">{rec.message}</p>
                                <div className="flex items-center justify-between mt-2">
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    rec.priority === 'high' ? 'bg-red-100 text-red-600' :
                                    rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                                    'bg-green-100 text-green-600'
                                  }`}>
                                    {rec.priority}
                                  </span>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      ) : (
                        <EmptyState
                          icon={<Lightbulb className="h-8 w-8 text-purple-400" />}
                          title="No Insights Yet"
                          description="Complete your profile to get personalized AI insights and recommendations."
                          action={{
                            label: 'Complete Profile',
                            onClick: () => handleTabChange('academic'),
                            icon: <GraduationCap className="h-4 w-4" />,
                          }}
                          className="py-6"
                        />
                      )}
                    </motion.div>

                    {/* AI Recommendation Summary */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-2xl p-5"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold text-gray-900 flex items-center">
                          <Sparkles className="h-5 w-5 mr-2 text-pink-600" />
                          AI Recommendations
                        </h3>
                        <button
                          onClick={() => handleTabChange('electives')}
                          className="text-xs text-purple-600 hover:text-purple-700 flex items-center font-medium focus:outline-none"
                        >
                          View All <ChevronRight className="w-3 h-3" />
                        </button>
                      </div>

                      {/* ✅ ENHANCED: Animated recommendation numbers */}
                      <div className="grid grid-cols-3 gap-3 mb-4">
                        <motion.div
                          whileHover={{ scale: 1.08, y: -2 }}
                          className="text-center p-4 bg-white rounded-xl shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                          onClick={() => handleTabChange('electives')}
                        >
                          <Briefcase className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                          <p className="text-3xl font-bold text-purple-700">
                            <AnimatedNumber value={recommendationStats.careerPaths} />
                          </p>
                          <p className="text-xs text-gray-600 mt-1">Careers</p>
                        </motion.div>
                        <motion.div
                          whileHover={{ scale: 1.08, y: -2 }}
                          className="text-center p-4 bg-white rounded-xl shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                          onClick={() => handleTabChange('electives')}
                        >
                          <Award className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                          <p className="text-3xl font-bold text-blue-700">
                            <AnimatedNumber value={recommendationStats.honoursProgramsMatch} />
                          </p>
                          <p className="text-xs text-gray-600 mt-1">Honours</p>
                        </motion.div>
                        <motion.div
                          whileHover={{ scale: 1.08, y: -2 }}
                          className="text-center p-4 bg-white rounded-xl shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                          onClick={() => handleTabChange('electives')}
                        >
                          <BookOpen className="w-6 h-6 text-green-600 mx-auto mb-2" />
                          <p className="text-3xl font-bold text-green-700">
                            <AnimatedNumber value={recommendationStats.electivesRecommended} />
                          </p>
                          <p className="text-xs text-gray-600 mt-1">Electives</p>
                        </motion.div>
                      </div>

                      <p className="text-xs text-gray-500 text-center bg-white rounded-lg p-2">
                        Based on your performance, interests & uploaded projects
                      </p>
                    </motion.div>
                  </div>

                  {/* ROW 3: Three Primary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    {/* My Projects Card */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-5 cursor-pointer flex flex-col"
                      onClick={() => handleTabChange('projects')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('projects')}
                      aria-label="View my projects"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-2">
                          <FolderOpen className="h-5 w-5 text-green-600" />
                          <h3 className="font-semibold text-green-900">My Projects</h3>
                        </div>
                        <p className="text-3xl font-bold text-green-700">
                          {projectsLoading ? (
                            <Loader2 className="w-6 h-6 animate-spin" />
                          ) : (
                            <AnimatedNumber value={projectCount} />
                          )}
                        </p>
                      </div>
                      <p className="text-sm text-green-700 mb-4 flex-grow">
                        Upload projects to discover AI-powered career interests and recommendations
                      </p>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="w-full py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all flex items-center justify-center gap-2"
                      >
                        <Code className="h-4 w-4" />
                        {projectCount > 0 ? 'View Projects' : 'Add Project'}
                      </motion.button>
                    </motion.div>

                    {/* Academic Information Card */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl p-5 flex flex-col"
                    >
                      <div className="flex items-center space-x-2 mb-4">
                        <GraduationCap className="h-5 w-5 text-indigo-600" />
                        <h3 className="font-semibold text-indigo-900">Academic Info</h3>
                      </div>
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                          <p className="text-xs text-indigo-600 mb-1">CGPA</p>
                          <p className="text-2xl font-bold text-indigo-700">
                            <AnimatedNumber
                              value={studentData?.cgpa || engineeringMetrics.overallCGPA}
                              decimals={2}
                            />
                          </p>
                        </div>
                        <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                          <p className="text-xs text-green-600 mb-1">SGPA</p>
                          <p className="text-2xl font-bold text-green-700">
                            <AnimatedNumber
                              value={studentData?.latest_sgpa || engineeringMetrics.semesterSGPA}
                              decimals={2}
                            />
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center text-xs mt-auto">
                        <div className="bg-white p-2 rounded-lg">
                          <p className="text-gray-500 mb-0.5">Branch</p>
                          <p className="font-semibold text-gray-800">{userProfile?.branch || 'IT'}</p>
                        </div>
                        <div className="bg-white p-2 rounded-lg">
                          <p className="text-gray-500 mb-0.5">Sem</p>
                          <p className="font-semibold text-gray-800">
                            {userProfile?.semester || studentData?.current_semester || 5}
                          </p>
                        </div>
                        <div className="bg-white p-2 rounded-lg">
                          <p className="text-gray-500 mb-0.5">Year</p>
                          <p className="font-semibold text-gray-800">{engineeringMetrics.studentInfo.year}</p>
                        </div>
                      </div>
                    </motion.div>

                    {/* Honours & Minor Programs */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-5 cursor-pointer flex flex-col"
                      onClick={() => handleTabChange('electives')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('electives')}
                      aria-label="View honours and minor programs"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-2">
                          <Shield className="h-5 w-5 text-blue-600" />
                          <h3 className="font-semibold text-blue-900">Honours & Minors</h3>
                        </div>
                        <span className="text-3xl font-bold text-blue-700">
                          <AnimatedNumber value={recommendationStats.honoursProgramsMatch} />
                        </span>
                      </div>
                      <p className="text-sm text-blue-700 mb-4 flex-grow">
                        Eligible programs based on your academic performance and interests
                      </p>
                      <div className="flex items-center justify-between mt-auto">
                        <div className="flex space-x-2">
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">AI Matched</span>
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">Eligible</span>
                        </div>
                        <ChevronRight className="h-5 w-5 text-blue-600" />
                      </div>
                    </motion.div>
                  </div>

                  {/* ROW 4: Performance Metrics */}
                  <motion.div
                    variants={animationVariants.container}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4"
                  >
                    <StatCard
                      title="Current SGPI"
                      value={dashboardStats?.currentSGPI?.toFixed(2) || studentData?.latest_sgpa?.toFixed(2) || '0.00'}
                      change={dashboardStats?.percentageChange}
                      icon={<TrendingUp className="h-5 w-5 text-blue-600" />}
                      color="blue"
                      onClick={() => handleTabChange('performance')}
                    />
                    <StatCard
                      title="Weak Subjects"
                      value={studentData?.weakness_count?.toString() || '0'}
                      icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
                      color="orange"
                      onClick={() => handleTabChange('weaknesses')}
                    />
                    <StatCard
                      title="Strong Subjects"
                      value={engineeringMetrics.strongSubjects.length.toString()}
                      icon={<Star className="h-5 w-5 text-green-600" />}
                      color="green"
                    />
                    <StatCard
                      title="Credits"
                      value={`${engineeringMetrics.completedCredits}/${engineeringMetrics.totalCredits}`}
                      icon={<Award className="h-5 w-5 text-purple-600" />}
                      color="purple"
                    />
                    <StatCard
                      title="AI Recs"
                      value={recommendationStats.electivesRecommended.toString()}
                      icon={<Brain className="h-5 w-5 text-indigo-600" />}
                      color="indigo"
                      onClick={() => handleTabChange('electives')}
                    />
                  </motion.div>

                  {/* ROW 5: ✅ ENHANCED SGPI Trend Analysis with new chart */}
                  <motion.div
                    variants={animationVariants.card}
                    initial="rest"
                    whileHover="hover"
                    className="bg-white rounded-2xl shadow-sm border p-6"
                  >
                    <div className="flex items-center justify-between mb-5">
                      <h2 className="text-lg font-bold text-gray-900 flex items-center">
                        <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                        SGPI Trend Analysis
                      </h2>
                      <button
                        onClick={() => handleTabChange('performance')}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center focus:outline-none hover:underline"
                      >
                        View Detailed Analysis <ChevronRight className="h-4 w-4 ml-1" />
                      </button>
                    </div>
                    {/* ✅ ENHANCED: Use new chart component */}
                    <EnhancedSGPIChart
                      performanceData={performanceData}
                      studentData={studentData}
                    />
                  </motion.div>

                  {/* ROW 6: Three Equal Columns */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    {/* Areas to Improve */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      className="bg-white rounded-2xl shadow-sm border p-5 flex flex-col"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-gray-900 flex items-center">
                          <AlertCircle className="h-5 w-5 mr-2 text-orange-600" />
                          Areas to Improve
                        </h3>
                        <button
                          onClick={() => handleTabChange('weaknesses')}
                          className="text-xs text-orange-600 hover:text-orange-700 flex items-center focus:outline-none"
                        >
                          View All <ChevronRight className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="space-y-3 flex-grow">
                        {studentData?.weaknesses && studentData.weaknesses.length > 0 ? (
                          studentData.weaknesses.slice(0, 4).map((weakness, idx) => (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: idx * 0.1 }}
                              className="flex items-center justify-between p-3 bg-orange-50 rounded-xl hover:bg-orange-100 transition-colors"
                            >
                              <div className="flex items-center space-x-3">
                                <div className="w-2 h-2 rounded-full bg-orange-500 flex-shrink-0" />
                                <span className="text-sm text-gray-700">{weakness.subject}</span>
                              </div>
                              <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded-full whitespace-nowrap">
                                Focus
                              </span>
                            </motion.div>
                          ))
                        ) : (
                          <EmptyState
                            icon={<AlertCircle className="h-8 w-8 text-orange-300" />}
                            title="No Weaknesses Found"
                            description={
                              studentInterests.length > 0
                                ? 'Analyzing your performance...'
                                : 'Set your interests to see analysis'
                            }
                            className="py-4"
                          />
                        )}
                      </div>
                    </motion.div>

                    {/* Immediate Actions */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      className="bg-white rounded-2xl shadow-sm border p-5 flex flex-col"
                    >
                      <h3 className="font-semibold text-gray-900 flex items-center mb-4">
                        <Zap className="h-5 w-5 mr-2 text-yellow-600" />
                        Immediate Actions
                      </h3>
                      <div className="space-y-3 flex-grow">
                        {!userProfile && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center justify-between p-3 bg-yellow-50 rounded-xl border border-yellow-200 hover:shadow-sm transition-shadow"
                          >
                            <div className="flex items-center space-x-3">
                              <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                              <span className="text-sm text-yellow-800">Complete academic profile</span>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={(e) => { e.stopPropagation(); handleTabChange('academic'); }}
                              className="text-xs px-3 py-1.5 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-yellow-500"
                            >
                              Setup
                            </motion.button>
                          </motion.div>
                        )}
                        {studentInterests.length === 0 && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="flex items-center justify-between p-3 bg-pink-50 rounded-xl border border-pink-200 hover:shadow-sm transition-shadow"
                          >
                            <div className="flex items-center space-x-3">
                              <Heart className="h-5 w-5 text-pink-600 flex-shrink-0" />
                              <span className="text-sm text-pink-800">Set career interests</span>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={(e) => { e.stopPropagation(); handleTabChange('interests'); }}
                              className="text-xs px-3 py-1.5 bg-pink-600 text-white rounded-lg hover:bg-pink-700 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-pink-500"
                            >
                              Add
                            </motion.button>
                          </motion.div>
                        )}
                        {projectCount === 0 && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="flex items-center justify-between p-3 bg-green-50 rounded-xl border border-green-200 hover:shadow-sm transition-shadow"
                          >
                            <div className="flex items-center space-x-3">
                              <Code className="h-5 w-5 text-green-600 flex-shrink-0" />
                              <span className="text-sm text-green-800">Upload first project</span>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={(e) => { e.stopPropagation(); handleTabChange('projects'); }}
                              className="text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-green-500"
                            >
                              Upload
                            </motion.button>
                          </motion.div>
                        )}
                        {userProfile && studentInterests.length > 0 && projectCount > 0 && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex items-center p-3 bg-green-50 rounded-xl border border-green-200"
                          >
                            <CheckCircle className="h-5 w-5 text-green-600 mr-3 flex-shrink-0" />
                            <span className="text-sm text-green-800">All setup complete!</span>
                          </motion.div>
                        )}
                      </div>
                    </motion.div>

                    {/* Portfolio Building */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-gradient-to-br from-green-50 to-teal-50 border border-green-200 rounded-2xl p-5 cursor-pointer flex flex-col"
                      onClick={() => handleTabChange('projects')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('projects')}
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-green-900 flex items-center">
                          <Code className="h-5 w-5 mr-2 text-green-600" />
                          Portfolio Building
                        </h3>
                        <span className="text-2xl font-bold text-green-700">
                          <AnimatedNumber value={projectCount} />
                        </span>
                      </div>
                      <p className="text-sm text-green-700 mb-4 flex-grow">
                        Build your portfolio with projects for AI-powered analysis and career matching
                      </p>
                      <div className="flex items-center justify-between mt-auto">
                        <div className="flex space-x-2">
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">AI Analysis</span>
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">Career Match</span>
                        </div>
                        <ChevronRight className="h-5 w-5 text-green-600" />
                      </div>
                    </motion.div>
                  </div>

                  {/* ROW 7: Four Quick Access Cards */}
                  <motion.div
                    variants={animationVariants.container}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5"
                  >
                    {/* AI Career Insights */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer group"
                      onClick={() => handleTabChange('electives')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('electives')}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="p-2.5 bg-purple-100 rounded-xl group-hover:scale-110 transition-transform">
                          <Rocket className="h-6 w-6 text-purple-600" />
                        </div>
                        <span className="text-3xl font-bold text-purple-700">
                          <AnimatedNumber value={recommendationStats.careerPaths} />
                        </span>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-1">AI Career Insights</h3>
                      <p className="text-sm text-gray-600 mb-3">Personalized career paths</p>
                      <div className="flex items-center text-purple-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                        Explore <ChevronRight className="h-4 w-4 ml-1" />
                      </div>
                    </motion.div>

                    {/* Academic Insights */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer group"
                      onClick={() => handleTabChange('electives')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('electives')}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="p-2.5 bg-amber-100 rounded-xl group-hover:scale-110 transition-transform">
                          <Lightbulb className="h-6 w-6 text-amber-600" />
                        </div>
                        <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-semibold">Tips</span>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-1">Academic Insights</h3>
                      <p className="text-sm text-gray-600 mb-3">Course & semester planning</p>
                      <div className="flex items-center text-amber-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                        View <ChevronRight className="h-4 w-4 ml-1" />
                      </div>
                    </motion.div>

                    {/* Study Resources */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer group"
                      onClick={() => handleTabChange('resources')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('resources')}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="p-2.5 bg-blue-100 rounded-xl group-hover:scale-110 transition-transform">
                          <BookOpen className="h-6 w-6 text-blue-600" />
                        </div>
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-semibold">New</span>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-1">Study Resources</h3>
                      <p className="text-sm text-gray-600 mb-3">Videos, notes & materials</p>
                      <div className="flex items-center text-blue-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                        Browse <ChevronRight className="h-4 w-4 ml-1" />
                      </div>
                    </motion.div>

                    {/* Faculty Meetings */}
                    <motion.div
                      variants={animationVariants.card}
                      initial="rest"
                      whileHover="hover"
                      whileTap="tap"
                      className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer group"
                      onClick={() => handleTabChange('meetings')}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleTabChange('meetings')}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="p-2.5 bg-indigo-100 rounded-xl group-hover:scale-110 transition-transform">
                          <Calendar className="h-6 w-6 text-indigo-600" />
                        </div>
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded font-semibold">Faculty</span>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-1">Meeting Requests</h3>
                      <p className="text-sm text-gray-600 mb-3">Schedule faculty meetings</p>
                      <div className="flex items-center text-indigo-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                        View <ChevronRight className="h-4 w-4 ml-1" />
                      </div>
                    </motion.div>
                  </motion.div>

                  {/* ROW 8: ✅ ENHANCED Readiness Score with Breakdown */}
                  <motion.div
                    variants={animationVariants.card}
                    initial="rest"
                    whileHover="hover"
                    className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-2xl p-5 cursor-pointer"
                    onClick={() => handleTabChange('readiness')}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && handleTabChange('readiness')}
                  >
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                      <div className="flex items-center space-x-4">
                        <motion.div
                          animate={{ scale: [1, 1.05, 1] }}
                          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                          className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0"
                        >
                          <Target className="h-6 w-6 text-white" />
                        </motion.div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-bold text-purple-900">Readiness Score</h3>
                            {readinessData && (
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                readinessData.overall_readiness_score >= 75
                                  ? 'bg-green-100 text-green-700'
                                  : readinessData.overall_readiness_score >= 50
                                  ? 'bg-yellow-100 text-yellow-700'
                                  : 'bg-red-100 text-red-700'
                              }`}>
                                {readinessData.readiness_level}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">
                            {readinessData
                              ? readinessData.primary_recommendation
                              : studentInterests.length === 0
                              ? 'Set your interests to calculate readiness'
                              : 'Click to analyze your career readiness'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {readinessData ? (
                          <>
                            <div className="text-center">
                              <span className="text-3xl font-bold text-purple-700">
                                <AnimatedNumber
                                  value={readinessData.overall_readiness_score}
                                  decimals={0}
                                  suffix="%"
                                />
                              </span>
                            </div>
                            <div className="w-24 hidden sm:block">
                              <div className="w-full bg-gray-200 rounded-full h-2.5">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${readinessData.overall_readiness_score}%` }}
                                  transition={{ duration: 1, ease: 'easeOut' }}
                                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2.5 rounded-full"
                                />
                              </div>
                            </div>
                          </>
                        ) : loadingReadiness ? (
                          <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
                        ) : (
                          <span className="text-sm text-purple-600 font-medium">Analyze Now</span>
                        )}
                        <ChevronRight className="h-5 w-5 text-purple-400" />
                      </div>
                    </div>

                    {/* ✅ NEW: Readiness Breakdown Section */}
                    <ReadinessBreakdown
                      readinessData={readinessData}
                      projectCount={projectCount}
                      studentData={studentData}
                      studentInterests={studentInterests}
                      userProfile={userProfile}
                    />
                  </motion.div>
                </motion.div>
              )}

              {/* ==================== CHATBOT TAB ==================== */}
              {activeTab === 'chatbot' && (
                <motion.div
                  key="chatbot"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="h-[calc(100vh-140px)] max-w-7xl mx-auto"
                >
                  <div className="bg-white rounded-2xl shadow-lg overflow-hidden h-full">
                    <Suspense fallback={<TabLoader />}>
                      <AcademicChatbot isFloating={false} defaultOpen={true} className="h-full" />
                    </Suspense>
                  </div>
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
                    onTrendChange={(trend) => console.log('Trend analysis updated:', trend)}
                  />
                  <SubjectPerformance
                    studentId={user?.uid || 'student-123'}
                    className="bg-white rounded-xl shadow-sm border p-6"
                    onSubjectSelect={(subject) => console.log('Subject selected:', subject)}
                  />
                  <div className="bg-white rounded-xl shadow-sm border p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-bold text-gray-900">Detailed Performance Analysis</h2>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleDownloadReport}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                      >
                        <Download className="h-4 w-4" />
                        <span>Export Data</span>
                      </motion.button>
                    </div>
                    {/* ✅ ENHANCED: Use new chart in performance tab too */}
                    <EnhancedSGPIChart performanceData={performanceData} studentData={studentData} />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <StatCard
                      title="Current Semester"
                      value={
                        userProfile?.semester
                          ? `Semester ${userProfile.semester}`
                          : studentData?.current_semester
                          ? `${studentData.current_semester}th`
                          : '-'
                      }
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
                  </div>

                  <motion.div
                    variants={animationVariants.card}
                    initial="rest"
                    whileHover="hover"
                    className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <Brain className="h-5 w-5 mr-2 text-purple-600" />
                      AI-Generated Insights
                    </h3>
                    {insights?.recommendations && insights.recommendations.length > 0 ? (
                      <div className="space-y-3">
                        {insights.recommendations.map((rec: any, index: number) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="flex items-start space-x-3"
                          >
                            <div className={`mt-1 h-2 w-2 rounded-full flex-shrink-0 ${
                              rec.type === 'success' ? 'bg-green-500' :
                              rec.type === 'warning' ? 'bg-yellow-500' :
                              rec.type === 'alert' ? 'bg-orange-500' : 'bg-blue-500'
                            }`} />
                            <div>
                              <p className="text-sm text-gray-700">{rec.message}</p>
                              <span className={`text-xs ${
                                rec.priority === 'high' ? 'text-red-600' :
                                rec.priority === 'medium' ? 'text-yellow-600' : 'text-green-600'
                              }`}>
                                {rec.priority} priority
                              </span>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600">No specific recommendations at this time.</p>
                    )}
                  </motion.div>
                </motion.div>
              )}

              {/* ==================== PROJECTS TAB ==================== */}
              {activeTab === 'projects' && (
                <motion.div
                  key="projects"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  {projectsView === 'list' ? (
                    <StudentProjectsList onAddProject={() => setProjectsView('upload')} />
                  ) : (
                    <div className="space-y-4">
                      <button
                        onClick={() => {
                          setProjectsView('list');
                          refetchProjectCount();
                        }}
                        className="flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium focus:outline-none"
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
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  <AcademicDataEntry />
                </motion.div>
              )}

              {/* ==================== INTERESTS TAB ==================== */}
              {activeTab === 'interests' && (
                <motion.div
                  key="interests"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
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
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  <MLRecommendations />
                </motion.div>
              )}

              {/* ==================== WEAKNESSES TAB ==================== */}
              {activeTab === 'weaknesses' && (
                <motion.div
                  key="weaknesses"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  <WeaknessAnalyzer interests={studentInterests} electives={studentElectives} dashboardWeaknesses={studentData?.weaknesses} />
                </motion.div>
              )}

              {/* ==================== RESOURCES TAB ==================== */}
              {activeTab === 'resources' && (
                <motion.div
                  key="resources"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  <StudyResources />
                </motion.div>
              )}

              {/* ==================== MEETINGS TAB ==================== */}
              {activeTab === 'meetings' && (
                <motion.div
                  key="meetings"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="space-y-4 max-w-7xl mx-auto"
                >
                  <div className="flex gap-1 border-b border-gray-200 bg-white rounded-t-2xl px-2 pt-2">
                    <button
                      onClick={() => setMeetingsView('requests')}
                      className={`px-4 py-2.5 font-medium text-sm transition-all relative rounded-t-xl focus:outline-none ${
                        meetingsView === 'requests'
                          ? 'text-indigo-600 bg-indigo-50'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                      aria-selected={meetingsView === 'requests'}
                      role="tab"
                    >
                      <span className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Requests
                      </span>
                    </button>
                    <button
                      onClick={() => setMeetingsView('calendar')}
                      className={`px-4 py-2.5 font-medium text-sm transition-all relative rounded-t-xl focus:outline-none ${
                        meetingsView === 'calendar'
                          ? 'text-indigo-600 bg-indigo-50'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                      aria-selected={meetingsView === 'calendar'}
                      role="tab"
                    >
                      <span className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        Calendar
                      </span>
                    </button>
                  </div>
                  <AnimatePresence mode="wait">
                    {meetingsView === 'requests' ? (
                      <motion.div
                        key="requests-view"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                      >
                        <StudentMeetingRequest />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="calendar-view"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                      >
                        <Suspense fallback={<TabLoader />}>
                          <MeetingsCalendar />
                        </Suspense>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* ==================== READINESS TAB ==================== */}
              {activeTab === 'readiness' && (
                <motion.div
                  key="readiness"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  {loadingReadiness ? (
                    <div className="bg-white rounded-2xl shadow-sm border p-12 text-center">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                      >
                        <Loader2 className="w-12 h-12 text-purple-600 mx-auto mb-4" />
                      </motion.div>
                      <p className="text-gray-600 font-medium">Analyzing your academic readiness...</p>
                      <p className="text-gray-400 text-sm mt-2">This may take a few moments</p>
                    </div>
                  ) : readinessData ? (
                    <ReadinessAnalysis
                      studentId={user?.uid}
                      interests={studentInterests}
                      electives={studentElectives}
                      honours={studentHonours}
                      onAnalysisComplete={(data) => {
                        setReadinessData(data);
                        showToast.success('Readiness analysis updated!');
                      }}
                    />
                  ) : (
                    <div className="bg-white rounded-2xl shadow-sm border p-12">
                      <EmptyState
                        icon={<Target className="h-12 w-12 text-purple-400" />}
                        title="No Readiness Data"
                        description={
                          studentInterests.length === 0
                            ? 'Set your interests first in the "My Interests" tab to get a personalized readiness analysis.'
                            : 'Run an analysis to see how ready you are for your career goals.'
                        }
                        action={
                          studentInterests.length === 0
                            ? {
                                label: 'Set Interests',
                                onClick: () => handleTabChange('interests'),
                                icon: <Heart className="h-4 w-4" />,
                              }
                            : {
                                label: 'Run Analysis',
                                onClick: () => {
                                  readinessFetchingRef.current = false;
                                  fetchReadiness();
                                },
                                icon: <Zap className="h-4 w-4" />,
                              }
                        }
                        secondaryAction={
                          studentInterests.length > 0
                            ? {
                                label: 'Set More Interests',
                                onClick: () => handleTabChange('interests'),
                              }
                            : undefined
                        }
                      />
                    </div>
                  )}
                </motion.div>
              )}

              {/* ==================== NOTIFICATIONS TAB ==================== */}
              {activeTab === 'notifications' && (
                <motion.div
                  key="notifications"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-4xl mx-auto space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Notifications</h2>
                      <p className="text-sm text-gray-500 mt-1">Stay updated with your academic activities</p>
                    </div>
                  </div>

                  {/* Notification Cards */}
                  <div className="space-y-3">
                    {/* Marks Update Notification */}
                    {studentData && (studentData.cgpa ?? 0) > 0 && (
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-white border border-blue-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                            <BarChart3 className="w-5 h-5 text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">Academic Performance Updated</p>
                            <p className="text-sm text-gray-500 mt-0.5">
                              Your CGPA has been updated to <span className="font-semibold text-blue-600">{studentData.cgpa?.toFixed(2)}</span>.
                              {studentData.improvement_trend === 'improving' && ' Great progress! Keep it up! 🎉'}
                              {studentData.improvement_trend === 'declining' && ' Consider focusing on weak subjects.'}
                            </p>
                            <p className="text-xs text-gray-400 mt-1.5">Academic Records</p>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Weakness Alert */}
                    {studentData && (studentData.weakness_count || 0) > 0 && (
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white border border-orange-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
                            <AlertCircle className="w-5 h-5 text-orange-600" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">Weakness Areas Detected</p>
                            <p className="text-sm text-gray-500 mt-0.5">
                              AI analysis found {studentData.weakness_count} areas that need attention. 
                              <button onClick={() => handleTabChange('weaknesses')} className="text-orange-600 font-medium ml-1 hover:underline">
                                View Analysis →
                              </button>
                            </p>
                            <p className="text-xs text-gray-400 mt-1.5">AI Insights</p>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Elective Recommendations */}
                    {recommendationStats.electivesRecommended > 0 && (
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="bg-white border border-purple-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                            <Sparkles className="w-5 h-5 text-purple-600" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">New Elective Recommendations</p>
                            <p className="text-sm text-gray-500 mt-0.5">
                              {recommendationStats.electivesRecommended} electives recommended based on your interests and performance.
                              <button onClick={() => handleTabChange('electives')} className="text-purple-600 font-medium ml-1 hover:underline">
                                Explore →
                              </button>
                            </p>
                            <p className="text-xs text-gray-400 mt-1.5">AI Recommendations</p>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Profile Completeness */}
                    {studentInterests.length === 0 && (
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="bg-white border border-yellow-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center flex-shrink-0">
                            <Heart className="w-5 h-5 text-yellow-600" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">Complete Your Profile</p>
                            <p className="text-sm text-gray-500 mt-0.5">
                              Add your interests to unlock personalized elective and career recommendations.
                              <button onClick={() => handleTabChange('interests')} className="text-yellow-600 font-medium ml-1 hover:underline">
                                Add Interests →
                              </button>
                            </p>
                            <p className="text-xs text-gray-400 mt-1.5">Profile Setup</p>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Welcome Notification (always shown) */}
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 }}
                      className="bg-white border border-green-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                          <Bot className="w-5 h-5 text-green-600" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">AI Assistant Available</p>
                          <p className="text-sm text-gray-500 mt-0.5">
                            Need help with syllabus, faculty info, or career guidance?
                            <button onClick={() => handleTabChange('chatbot')} className="text-green-600 font-medium ml-1 hover:underline">
                              Start a chat →
                            </button>
                          </p>
                          <p className="text-xs text-gray-400 mt-1.5">System</p>
                        </div>
                      </div>
                    </motion.div>
                  </div>
                </motion.div>
              )}

              {/* ==================== AI ROADMAP TAB ==================== */}
              {/* {activeTab === 'roadmap' && (
                <motion.div
                  key="roadmap"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  <Suspense fallback={<TabLoader />}>
                    <PersonalizedRoadmap />
                  </Suspense>
                </motion.div>
              )} */}

              {/* ==================== GAME LEARNING HUB TAB — COMMENTED OUT ==================== */}
              {/* {activeTab === 'improvement' && (
                <motion.div
                  key="improvement"
                  variants={animationVariants.fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="max-w-7xl mx-auto"
                >
                  <ImprovementHub />
                </motion.div>
              )} */}

            </AnimatePresence>
            </LayoutGroup>
          </main>
        </div>
      </div>

      {/* ==================== FLOATING CHATBOT ==================== */}
      {activeTab !== 'chatbot' && (
        <Suspense fallback={null}>
          <AcademicChatbot isFloating={true} defaultOpen={showFloatingChatbot} className="" />
        </Suspense>
      )}
    </div>
  );
};

// ==================== Main Export with Error Boundary ====================

const StudentDashboard: React.FC = () => {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <DashboardErrorBoundary onRetry={handleRetry}>
      <StudentDashboardContent />
    </DashboardErrorBoundary>
  );
};

export default StudentDashboard;