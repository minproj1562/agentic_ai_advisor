// src/pages/Dashboard/StudentDashboard.tsx
// PROFESSIONAL VERSION - All improvements implemented

import React, { useState, useEffect, useCallback, useRef, Component, ErrorInfo } from 'react';
import StudentMeetingRequest from '../../components/meetings/StudentMeetingRequest';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
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
  RotateCcw
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
import AcademicChatbot from '../../components/dashboard/AcademicChatbot';

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

// ==================== Animation Variants ====================

const animationVariants = {
  container: {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1
      }
    }
  },
  item: {
    hidden: { opacity: 0, y: 20 },
    show: { 
      opacity: 1, 
      y: 0,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 24
      }
    }
  },
  card: {
    rest: { scale: 1, y: 0 },
    hover: { 
      scale: 1.02, 
      y: -4,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 17
      }
    },
    tap: { scale: 0.98 }
  },
  fadeIn: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  },
  slideIn: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 }
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 }
  }
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
                onClick={() => window.location.href = '/'}
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
        {/* Sidebar Skeleton */}
        <div className="hidden lg:block w-72 bg-white border-r border-gray-200">
          <div className="animate-pulse p-5">
            {/* Profile Skeleton */}
            <div className="flex items-center space-x-3 mb-6 p-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl">
              <div className="h-11 w-11 bg-gray-300 rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-300 rounded w-1/2" />
              </div>
            </div>
            
            {/* Stats Skeleton */}
            <div className="grid grid-cols-3 gap-2 mb-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-3 bg-gray-100 rounded-lg">
                  <div className="h-5 bg-gray-200 rounded w-full mb-1" />
                  <div className="h-3 bg-gray-200 rounded w-2/3 mx-auto" />
                </div>
              ))}
            </div>
            
            {/* Nav Sections */}
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

        {/* Main Content Skeleton */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header Skeleton */}
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

          {/* Content Skeleton */}
          <div className="flex-1 p-6 overflow-auto">
            <div className="animate-pulse space-y-6 max-w-7xl mx-auto">
              {/* Banner Skeleton */}
              <div className="h-36 bg-gradient-to-r from-blue-200 to-purple-200 rounded-xl" />
              
              {/* Two Column Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div className="h-56 bg-gray-200 rounded-xl" />
                <div className="h-56 bg-gray-200 rounded-xl" />
              </div>
              
              {/* Three Column Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-48 bg-gray-200 rounded-xl" />
                ))}
              </div>
              
              {/* Stats Row */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-28 bg-gray-200 rounded-xl" />
                ))}
              </div>
              
              {/* Chart Skeleton */}
              <div className="h-80 bg-gray-200 rounded-xl" />
            </div>
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
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
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            Loading Your Dashboard
          </h3>
          <p className="text-gray-500 text-sm mb-4">
            Analyzing your academic performance...
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <motion.div
              className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 h-2 rounded-full"
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{ duration: 2.5, ease: "easeInOut", repeat: Infinity }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-4">
            This may take a few moments...
          </p>
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
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({ 
  icon, 
  title, 
  description, 
  action, 
  secondaryAction,
  className = ""
}) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}
  >
    <motion.div 
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
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

// ==================== Enhanced StatCard Component ====================

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
  loading = false
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
      className={`relative overflow-hidden bg-white rounded-xl shadow-sm border ${config.border} p-4 ${onClick ? 'cursor-pointer' : ''} transition-shadow hover:shadow-md`}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      aria-label={`${title}: ${value}`}
    >
      {/* Background Decoration */}
      <div className={`absolute top-0 right-0 w-24 h-24 ${config.bg} rounded-full -mr-12 -mt-12 opacity-60`} />
      
      <div className="relative">
        <div className="flex items-start justify-between mb-3">
          <div className={`p-2.5 rounded-xl ${config.bg}`}>
            {icon}
          </div>
          {change !== undefined && (
            <div className={`flex items-center space-x-1 text-xs font-semibold px-2 py-1 rounded-full ${
              change >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {change >= 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span>{Math.abs(change).toFixed(1)}%</span>
            </div>
          )}
        </div>
        
        <p className="text-2xl font-bold text-gray-900 mb-0.5">{value}</p>
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
    toast.custom((t) => (
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
    ), { duration: 3000 });
  },
  error: (message: string) => {
    toast.custom((t) => (
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
    ), { duration: 4000 });
  },
  loading: (message: string) => {
    return toast.custom((t) => (
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        className="flex items-center space-x-3 px-4 py-3 bg-white rounded-xl shadow-lg border border-blue-200 max-w-sm"
      >
        <Loader2 className="h-5 w-5 text-blue-600 animate-spin flex-shrink-0" />
        <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
      </motion.div>
    ), { duration: Infinity });
  },
  info: (message: string) => {
    toast.custom((t) => (
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
    ), { duration: 3000 });
  }
};

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

// ==================== Main Dashboard Component ====================

const StudentDashboardContent: React.FC = () => {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();

  // ==================== State ====================

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'performance' | 'electives' | 'weaknesses' | 'resources' | 'projects' | 'academic' | 'interests' | 'meetings' | 'readiness' | 'chatbot'
  >('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);
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

  // Floating Chatbot State
  const [showFloatingChatbot, setShowFloatingChatbot] = useState(false);

  // Get performance metrics for engineering guidance
  const engineeringMetrics = usePerformanceMetrics();

  // Type-safe user display name
  const userDisplayName = (user as AuthUser)?.displayName || 'Student';

  // ==================== Refs to prevent duplicate fetches ====================

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
    readiness: { label: 'Readiness', description: 'Career readiness' }
  };

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
    if (readinessFetchingRef.current) return;

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
        showToast.info('Using cached profile data');
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
      showToast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.uid]);

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
    showToast.success('Dashboard refreshed!');
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

      showToast.success('Project analyzed! View your personalized recommendations.');
    } catch (error) {
      console.error('Error processing analysis:', error);
      showToast.error('Failed to process analysis results');
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

    showToast.success('Report downloaded!');
  }, [userDisplayName, user?.uid, userProfile, studentData, dashboardStats, performanceData, predictions, insights, recommendationStats, readinessData, lastUpdated, engineeringMetrics]);

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

    const handleInterestsUpdated = async (event: Event) => {
      const detail = (event as CustomEvent).detail;

      if (detail?.interests) {
        setStudentInterests(detail.interests);
      }

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
  }, [user?.uid, queryClient, fetchUserProfile, fetchDashboardData, fetchRecommendationStats, fetchReadiness, invalidateAllCaches, updateDashboardWithProfile, handleProjectAnalyzed]);

  useEffect(() => {
    const fetchAndSyncInterests = async () => {
      if (!user?.uid) return;
      if (interestsSyncedFor.current === user.uid) return;
      interestsSyncedFor.current = user.uid;

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
    return () => {
      window.removeEventListener('projectUploaded', handleProjectUploaded);
    };
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
          showToast.info('Performance data updated!');
          fetchDashboardData(false);
        }
      });
    } catch (err) {
      console.warn('Realtime sync subscription failed:', err);
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
        {/* ==================== ENHANCED SIDEBAR ==================== */}
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

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-white/10 backdrop-blur rounded-lg">
                  <p className="text-lg font-bold text-white">
                    {studentData?.cgpa?.toFixed(1) || '0.0'}
                  </p>
                  <p className="text-[10px] text-white/70 uppercase tracking-wide">CGPA</p>
                </div>
                <div className="text-center p-2 bg-white/10 backdrop-blur rounded-lg">
                  <p className="text-lg font-bold text-white">
                    {userProfile?.semester || '5'}
                  </p>
                  <p className="text-[10px] text-white/70 uppercase tracking-wide">Sem</p>
                </div>
                <div className="text-center p-2 bg-white/10 backdrop-blur rounded-lg">
                  <p className="text-lg font-bold text-white">
                    {projectCount}
                  </p>
                  <p className="text-[10px] text-white/70 uppercase tracking-wide">Projects</p>
                </div>
              </div>
            </div>

            {/* Navigation */}
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
                      <button
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all group focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        <div className="flex items-center space-x-3">
                          <div className={`p-1.5 rounded-lg ${activeTab === item.id ? 'bg-blue-100' : 'bg-gray-100 group-hover:bg-gray-200'}`}>
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
                      </button>
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
                      <button
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        <div className="flex items-center space-x-3">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </button>
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
                      <button
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        <div className="flex items-center space-x-3">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Resources Section */}
              <div>
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
                  Resources
                </p>
                <ul className="space-y-1" role="list">
                  {[
                    { id: 'resources', icon: BookOpen, label: 'Study Resources', badge: 'New', badgeColor: 'bg-green-500' },
                    { id: 'meetings', icon: Calendar, label: 'Faculty Meetings', badge: 'Book', badgeColor: 'bg-indigo-500' },
                  ].map((item) => (
                    <li key={item.id}>
                      <button
                        onClick={() => handleTabChange(item.id)}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          activeTab === item.id
                            ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-sm border border-blue-100'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                        aria-current={activeTab === item.id ? 'page' : undefined}
                      >
                        <div className="flex items-center space-x-3">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className={`${item.badgeColor} text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold`}>
                          {item.badge}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t bg-gray-50 flex-shrink-0 space-y-3">
              {/* Quick Actions */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="flex items-center justify-center space-x-1.5 px-3 py-2 bg-white rounded-lg hover:bg-gray-100 text-gray-700 transition-colors text-xs font-medium border border-gray-200 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Refresh dashboard"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
                <button
                  onClick={handleDownloadReport}
                  className="flex items-center justify-center space-x-1.5 px-3 py-2 bg-white rounded-lg hover:bg-gray-100 text-gray-700 transition-colors text-xs font-medium border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Download report"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Export</span>
                </button>
              </div>
              
              {/* Logout Button */}
              <button
                onClick={logout}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl hover:from-red-600 hover:to-pink-600 transition-all shadow-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
              
              {/* Version Info */}
              <p className="text-[10px] text-gray-400 text-center">
                AI Academic Advisor v2.0 • {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        </aside>

        {/* ==================== MAIN CONTENT ==================== */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* ==================== ENHANCED HEADER ==================== */}
          <header className="bg-white shadow-sm border-b flex-shrink-0 z-30" role="banner">
            <div className="px-4 lg:px-6">
              <div className="flex items-center justify-between h-16">
                {/* Left Section */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label="Toggle sidebar"
                    aria-expanded={sidebarOpen}
                  >
                    <Menu className="h-5 w-5 text-gray-600" />
                  </button>
                  
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
                  {/* Live Status Indicator */}
                  <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 bg-green-50 rounded-full border border-green-200">
                    <span className="relative flex h-2 w-2" aria-hidden="true">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span className="text-xs font-medium text-green-700">Live</span>
                  </div>

                  {/* Last Updated */}
                  <div className="hidden lg:flex items-center space-x-1 text-xs text-gray-500">
                    <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>

                  {/* Refresh Button */}
                  <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    title="Refresh Dashboard"
                    aria-label="Refresh dashboard"
                  >
                    <RefreshCw className={`h-4 w-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
                  </button>

                  {/* Download Report */}
                  <button
                    onClick={handleDownloadReport}
                    className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label="Export report"
                  >
                    <Download className="h-4 w-4" />
                    <span className="hidden md:inline">Export</span>
                  </button>

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
                      {/* Online Indicator */}
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
                  transition={{ duration: 2, ease: "easeInOut" }}
                />
              )}
            </AnimatePresence>
          </header>

          {/* ==================== PAGE CONTENT ==================== */}
          <main className="flex-1 overflow-y-auto p-4 lg:p-6 scroll-smooth" role="main">
            <AnimatePresence mode="wait">

              {/* ==================== OVERVIEW TAB ==================== */}
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
          <div className="h-12 w-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center flex-shrink-0">
            <Bot className="h-7 w-7 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold">AI Academic Assistant</h2>
            <p className="text-white/80 text-sm">
              Get instant help with syllabus, faculty info, performance analysis & career guidance
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowFloatingChatbot(true)}
            className="px-3 py-2 bg-white/20 backdrop-blur hover:bg-white/30 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-white/50"
          >
            <MessageSquare className="h-4 w-4" />
            Quick Chat
          </button>
          <button
            onClick={() => handleTabChange('chatbot')}
            className="px-3 py-2 bg-white text-blue-600 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-white"
          >
            Open Full Assistant
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      
      {/* Quick Suggestions */}
      <div className="mt-4 pt-4 border-t border-white/20">
        <div className="flex flex-wrap gap-2">
          {["Explain deadlock in OS", "Who teaches DBMS?", "Show my performance", "Recommend electives"].map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => handleTabChange('chatbot')}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-full text-xs transition-colors focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </motion.div>

    {/* ROW 2: AI INSIGHTS + AI RECOMMENDATIONS SUMMARY */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* AI Insights & Recommendations */}
      <motion.div
        variants={animationVariants.item}
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
                className="flex items-start space-x-3 bg-white p-3 rounded-xl shadow-sm"
              >
                <div className={`mt-0.5 h-2.5 w-2.5 rounded-full flex-shrink-0 ${
                  rec.type === 'success' ? 'bg-green-500' :
                  rec.type === 'warning' ? 'bg-yellow-500' :
                  rec.type === 'alert' ? 'bg-orange-500' :
                  'bg-blue-500'
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
              label: "Complete Profile",
              onClick: () => handleTabChange('academic'),
              icon: <GraduationCap className="h-4 w-4" />
            }}
            className="py-6"
          />
        )}
      </motion.div>

      {/* AI Recommendation Summary */}
      <motion.div
        variants={animationVariants.item}
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

        <div className="grid grid-cols-3 gap-3 mb-4">
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="text-center p-4 bg-white rounded-xl shadow-sm cursor-pointer"
            onClick={() => handleTabChange('electives')}
          >
            <Briefcase className="w-6 h-6 text-purple-600 mx-auto mb-2" />
            <p className="text-3xl font-bold text-purple-700">{recommendationStats.careerPaths}</p>
            <p className="text-xs text-gray-600 mt-1">Careers</p>
          </motion.div>
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="text-center p-4 bg-white rounded-xl shadow-sm cursor-pointer"
            onClick={() => handleTabChange('electives')}
          >
            <Award className="w-6 h-6 text-blue-600 mx-auto mb-2" />
            <p className="text-3xl font-bold text-blue-700">{recommendationStats.honoursProgramsMatch}</p>
            <p className="text-xs text-gray-600 mt-1">Honours</p>
          </motion.div>
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="text-center p-4 bg-white rounded-xl shadow-sm cursor-pointer"
            onClick={() => handleTabChange('electives')}
          >
            <BookOpen className="w-6 h-6 text-green-600 mx-auto mb-2" />
            <p className="text-3xl font-bold text-green-700">{recommendationStats.electivesRecommended}</p>
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
            {projectsLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : projectCount}
          </p>
        </div>
        <p className="text-sm text-green-700 mb-4 flex-grow">
          Upload projects to discover AI-powered career interests and recommendations
        </p>
        <button className="w-full py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all flex items-center justify-center gap-2">
          <Code className="h-4 w-4" />
          {projectCount > 0 ? 'View Projects' : 'Add Project'}
        </button>
      </motion.div>

      {/* Academic Information Card */}
      <motion.div
        variants={animationVariants.item}
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
              {studentData?.cgpa?.toFixed(2) || engineeringMetrics.overallCGPA.toFixed(2)}
            </p>
          </div>
          <div className="text-center p-3 bg-white rounded-xl shadow-sm">
            <p className="text-xs text-green-600 mb-1">SGPA</p>
            <p className="text-2xl font-bold text-green-700">
              {studentData?.latest_sgpa?.toFixed(2) || engineeringMetrics.semesterSGPA.toFixed(2)}
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
            <p className="font-semibold text-gray-800">{userProfile?.semester || studentData?.current_semester || 5}</p>
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
            {recommendationStats.honoursProgramsMatch}
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

    {/* ROW 5: SGPI Trend Analysis */}
    <motion.div
      variants={animationVariants.item}
      className="bg-white rounded-2xl shadow-sm border p-6"
    >
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-bold text-gray-900 flex items-center">
          <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
          SGPI Trend Analysis
        </h2>
        <button
          onClick={() => handleTabChange('performance')}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center focus:outline-none"
        >
          View Detailed Analysis <ChevronRight className="h-4 w-4 ml-1" />
        </button>
      </div>
      <div className="h-72">
        <PerformanceChart data={performanceData} />
      </div>
    </motion.div>

    {/* ROW 6: Three Equal Columns */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {/* Areas to Improve */}
      <motion.div
        variants={animationVariants.item}
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
                className="flex items-center justify-between p-3 bg-orange-50 rounded-xl"
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
              description={studentInterests.length > 0 ? 'Analyzing your performance...' : 'Set your interests to see analysis'}
              className="py-4"
            />
          )}
        </div>
      </motion.div>

      {/* Immediate Actions */}
      <motion.div
        variants={animationVariants.item}
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
              className="flex items-center justify-between p-3 bg-yellow-50 rounded-xl border border-yellow-200"
            >
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                <span className="text-sm text-yellow-800">Complete academic profile</span>
              </div>
              <button
                onClick={() => handleTabChange('academic')}
                className="text-xs px-3 py-1.5 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-yellow-500"
              >
                Setup
              </button>
            </motion.div>
          )}
          {studentInterests.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="flex items-center justify-between p-3 bg-pink-50 rounded-xl border border-pink-200"
            >
              <div className="flex items-center space-x-3">
                <Heart className="h-5 w-5 text-pink-600 flex-shrink-0" />
                <span className="text-sm text-pink-800">Set career interests</span>
              </div>
              <button
                onClick={() => handleTabChange('interests')}
                className="text-xs px-3 py-1.5 bg-pink-600 text-white rounded-lg hover:bg-pink-700 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-pink-500"
              >
                Add
              </button>
            </motion.div>
          )}
          {projectCount === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex items-center justify-between p-3 bg-green-50 rounded-xl border border-green-200"
            >
              <div className="flex items-center space-x-3">
                <Code className="h-5 w-5 text-green-600 flex-shrink-0" />
                <span className="text-sm text-green-800">Upload first project</span>
              </div>
              <button
                onClick={() => handleTabChange('projects')}
                className="text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Upload
              </button>
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
          <span className="text-2xl font-bold text-green-700">{projectCount}</span>
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
        className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer"
        onClick={() => handleTabChange('electives')}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleTabChange('electives')}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="p-2.5 bg-purple-100 rounded-xl">
            <Rocket className="h-6 w-6 text-purple-600" />
          </div>
          <span className="text-3xl font-bold text-purple-700">{recommendationStats.careerPaths}</span>
        </div>
        <h3 className="font-semibold text-gray-900 mb-1">AI Career Insights</h3>
        <p className="text-sm text-gray-600 mb-3">Personalized career paths</p>
        <div className="flex items-center text-purple-600 text-sm font-medium">
          Explore <ChevronRight className="h-4 w-4 ml-1" />
        </div>
      </motion.div>

      {/* Academic Insights */}
      <motion.div
        variants={animationVariants.card}
        initial="rest"
        whileHover="hover"
        whileTap="tap"
        className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer"
        onClick={() => handleTabChange('electives')}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleTabChange('electives')}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="p-2.5 bg-amber-100 rounded-xl">
            <Lightbulb className="h-6 w-6 text-amber-600" />
          </div>
          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-semibold">Tips</span>
        </div>
        <h3 className="font-semibold text-gray-900 mb-1">Academic Insights</h3>
        <p className="text-sm text-gray-600 mb-3">Course & semester planning</p>
        <div className="flex items-center text-amber-600 text-sm font-medium">
          View <ChevronRight className="h-4 w-4 ml-1" />
        </div>
      </motion.div>

      {/* Study Resources */}
      <motion.div
        variants={animationVariants.card}
        initial="rest"
        whileHover="hover"
        whileTap="tap"
        className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer"
        onClick={() => handleTabChange('resources')}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleTabChange('resources')}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="p-2.5 bg-blue-100 rounded-xl">
            <BookOpen className="h-6 w-6 text-blue-600" />
          </div>
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-semibold">New</span>
        </div>
        <h3 className="font-semibold text-gray-900 mb-1">Study Resources</h3>
        <p className="text-sm text-gray-600 mb-3">Videos, notes & materials</p>
        <div className="flex items-center text-blue-600 text-sm font-medium">
          Browse <ChevronRight className="h-4 w-4 ml-1" />
        </div>
      </motion.div>

      {/* Faculty Meetings */}
      <motion.div
        variants={animationVariants.card}
        initial="rest"
        whileHover="hover"
        whileTap="tap"
        className="bg-white rounded-2xl shadow-sm border p-5 cursor-pointer"
        onClick={() => handleTabChange('meetings')}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleTabChange('meetings')}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="p-2.5 bg-indigo-100 rounded-xl">
            <Calendar className="h-6 w-6 text-indigo-600" />
          </div>
          <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded font-semibold">Faculty</span>
        </div>
        <h3 className="font-semibold text-gray-900 mb-1">Meeting Requests</h3>
        <p className="text-sm text-gray-600 mb-3">Schedule faculty meetings</p>
        <div className="flex items-center text-indigo-600 text-sm font-medium">
          View <ChevronRight className="h-4 w-4 ml-1" />
        </div>
      </motion.div>
    </motion.div>

    {/* ROW 8: Readiness Score - LOW PRIORITY */}
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
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
            <Target className="h-6 w-6 text-white" />
          </div>
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
                  {Math.round(readinessData.overall_readiness_score)}%
                </span>
              </div>
              <div className="w-24 hidden sm:block">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${readinessData.overall_readiness_score}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2.5 rounded-full"
                  />
                </div>
              </div>
            </>
          ) : (
            loadingReadiness ? (
              <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
            ) : (
              <span className="text-sm text-purple-600 font-medium">Analyze Now</span>
            )
          )}
          <ChevronRight className="h-5 w-5 text-purple-400" />
        </div>
      </div>
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
                    <AcademicChatbot 
                      isFloating={false} 
                      defaultOpen={true}
                      className="h-full"
                    />
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

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                        onClick={() => { setProjectsView('list'); refetchProjectCount(); }}
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
                  <WeaknessAnalyzer interests={studentInterests} electives={studentElectives} />
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
                      className={`px-4 py-2.5 font-medium text-sm transition-colors relative rounded-t-xl focus:outline-none ${
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
                      className={`px-4 py-2.5 font-medium text-sm transition-colors relative rounded-t-xl focus:outline-none ${
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
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
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
                                label: "Set Interests",
                                onClick: () => handleTabChange('interests'),
                                icon: <Heart className="h-4 w-4" />
                              }
                            : {
                                label: "Run Analysis",
                                onClick: () => { readinessFetchingRef.current = false; fetchReadiness(); },
                                icon: <Zap className="h-4 w-4" />
                              }
                        }
                        secondaryAction={
                          studentInterests.length > 0
                            ? {
                                label: "Set More Interests",
                                onClick: () => handleTabChange('interests')
                              }
                            : undefined
                        }
                      />
                    </div>
                  )}
                </motion.div>
              )}

            </AnimatePresence>
                    </main>
        </div>
      </div>

      {/* ==================== FLOATING CHATBOT ==================== */}
      {activeTab !== 'chatbot' && (
        <AcademicChatbot 
          isFloating={true} 
          defaultOpen={showFloatingChatbot}
          className=""
        />
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