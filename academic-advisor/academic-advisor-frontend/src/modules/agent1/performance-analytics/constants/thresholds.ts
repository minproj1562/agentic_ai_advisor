// modules/agent1/performance-analytics/constants/thresholds.ts
/**
 * Performance thresholds and constants
 */
export const PERFORMANCE_THRESHOLDS = {
  EXCELLENT: 90,
  GOOD: 80,
  AVERAGE: 70,
  POOR: 60,
  CRITICAL: 50,
  GPA: {
    DEANS_LIST: 3.5,
    HONORS: 3.0,
    MINIMUM: 2.0,
    PROBATION: 1.5
  }
} as const;

/**
 * Weakness detection thresholds
 */
export const WEAKNESS_THRESHOLDS = {
  DEFAULT: 60,
  STRICT: 70,
  LENIENT: 50,
  CLASS_AVERAGE_FACTOR: 0.85, // 85% of class average
  IMPROVEMENT_NEEDED: 0.2, // 20% improvement needed
  CRITICAL_GAP: 30 // 30 points below target
} as const;

/**
 * Trend analysis thresholds
 */
export const TREND_THRESHOLDS = {
  IMPROVEMENT: 0.01, // Slope threshold for improvement
  SIGNIFICANT_CHANGE: 0.05,
  PLATEAU: 0.005,
  ACCELERATION: 0.02,
  MIN_DATA_POINTS: 5,
  CONFIDENCE_HIGH: 0.8,
  CONFIDENCE_MEDIUM: 0.6,
  CONFIDENCE_LOW: 0.4
} as const;

/**
 * Prediction model configurations
 */
export const PREDICTION_MODELS = {
  LINEAR: {
    name: 'Linear Regression',
    minDataPoints: 3,
    defaultHorizon: 90,
    confidence: 0.75
  },
  POLYNOMIAL: {
    name: 'Polynomial Regression',
    minDataPoints: 5,
    defaultDegree: 2,
    defaultHorizon: 90,
    confidence: 0.70
  },
  EXPONENTIAL: {
    name: 'Exponential Smoothing',
    minDataPoints: 5,
    alpha: 0.3,
    beta: 0.2,
    defaultHorizon: 90,
    confidence: 0.75
  },
  ML: {
    name: 'Machine Learning',
    minDataPoints: 20,
    epochs: 50,
    batchSize: 32,
    learningRate: 0.001,
    defaultHorizon: 180,
    confidence: 0.85
  }
} as const;

/**
 * Confidence level thresholds
 */
export const CONFIDENCE_THRESHOLDS = {
  DEFAULT: 0.95,
  HIGH: 0.99,
  MEDIUM: 0.90,
  LOW: 0.80,
  Z_SCORES: {
    0.80: 1.282,
    0.90: 1.645,
    0.95: 1.96,
    0.99: 2.576
  }
} as const;

/**
 * API endpoints
 */
export const ANALYTICS_ENDPOINTS = {
  BASE: '/api/analytics',
  PERFORMANCE_TRENDS: '/api/analytics/performance',
  WEAKNESS_ANALYSIS: '/api/analytics/weakness',
  SUBJECT_PERFORMANCE: '/api/analytics/subjects',
  PREDICTIONS: '/api/analytics/predictions',
  TRACK_IMPROVEMENT: '/api/analytics/improvement',
  GENERATE_REPORT: '/api/analytics/report'
} as const;

export const TREND_ENDPOINTS = {
  ANALYZE: '/api/trends/analyze',
  PREDICT: '/api/trends/predict',
  ANOMALIES: '/api/trends/anomalies'
} as const;

export const PREDICTION_ENDPOINTS = {
  GENERATE: '/api/predictions/generate',
  VALIDATE: '/api/predictions/validate',
  SCENARIOS: '/api/predictions/scenarios'
} as const;

/**
 * Cache configuration
 */
export const CACHE_KEYS = {
  PERFORMANCE_TRENDS: 'performance-trends',
  WEAKNESS_ANALYSIS: 'weakness-analysis',
  SUBJECT_PERFORMANCE: 'subject-performance',
  PREDICTIONS: 'predictions',
  RECOMMENDATIONS: 'recommendations'
} as const;

export const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Refresh intervals
 */
export const REFRESH_INTERVALS = {
  PERFORMANCE_DATA: 30 * 60 * 1000, // 30 minutes
  PREDICTIONS: 60 * 60 * 1000, // 1 hour
  WEAKNESS_ANALYSIS: 30 * 60 * 1000, // 30 minutes
  REALTIME_SYNC: 5 * 1000 // 5 seconds
} as const;

/**
 * Calculation constants
 */
export const CALCULATION_CONSTANTS = {
  SMOOTHING_ALPHA: 0.3,
  SMOOTHING_WINDOW: 3,
  OUTLIER_THRESHOLD: 2, // Standard deviations
  MIN_SAMPLE_SIZE: 5,
  WEAKNESS_THRESHOLD: 60,
  CLASS_AVG_THRESHOLD: 0.85,
  GRADE_WEIGHTS: {
    QUIZ: 0.2,
    ASSIGNMENT: 0.3,
    MIDTERM: 0.2,
    FINAL: 0.3
  }
} as const;

/**
 * Improvement strategies
 */
export const IMPROVEMENT_STRATEGIES = {
  critical: {
    actions: [
      'Schedule immediate tutoring sessions',
      'Meet with professor during office hours',
      'Form or join a study group',
      'Review fundamental concepts',
      'Complete all practice problems'
    ],
    resources: [
      'Tutoring center',
      'Online courses',
      'Textbook review',
      'Past exam papers',
      'Video tutorials'
    ],
    baseEffort: 20 // hours per week
  },
  high: {
    actions: [
      'Increase study time by 50%',
      'Seek help for difficult topics',
      'Practice more problems',
      'Review class notes daily',
      'Attend all review sessions'
    ],
    resources: [
      'Study guides',
      'Practice exams',
      'Office hours',
      'Peer tutoring',
      'Online resources'
    ],
    baseEffort: 15
  },
  medium: {
    actions: [
      'Focus on weak topics',
      'Complete all assignments on time',
      'Review before each class',
      'Participate in discussions',
      'Create summary notes'
    ],
    resources: [
      'Class materials',
      'Study groups',
      'Online quizzes',
      'Reference books'
    ],
    baseEffort: 10
  },
  low: {
    actions: [
      'Maintain current study habits',
      'Focus on consistency',
      'Review periodically',
      'Stay engaged in class'
    ],
    resources: [
      'Class notes',
      'Textbook',
      'Online resources'
    ],
    baseEffort: 5
  }
} as const;

/**
 * Grade mappings
 */
export const GRADE_MAPPINGS = {
  LETTER_TO_GPA: {
    'A+': 4.0,
    'A': 4.0,
    'A-': 3.7,
    'B+': 3.3,
    'B': 3.0,
    'B-': 2.7,
    'C+': 2.3,
    'C': 2.0,
    'C-': 1.7,
    'D+': 1.3,
    'D': 1.0,
    'D-': 0.7,
    'F': 0.0
  },
  PERCENTAGE_TO_LETTER: {
    97: 'A+',
    93: 'A',
    90: 'A-',
    87: 'B+',
    83: 'B',
    80: 'B-',
    77: 'C+',
    73: 'C',
    70: 'C-',
    67: 'D+',
    63: 'D',
    60: 'D-',
    0: 'F'
  }
} as const;

/**
 * Subject categories
 */
export const SUBJECT_CATEGORIES = {
  CORE: 'core',
  ELECTIVE: 'elective',
  MINOR: 'minor',
  MAJOR: 'major',
  GENERAL: 'general',
  LAB: 'lab',
  PROJECT: 'project'
} as const;

/**
 * Time ranges
 */
export const TIME_RANGES = {
  LAST_MONTH: { label: 'Last Month', value: '1m', days: 30 },
  LAST_3_MONTHS: { label: 'Last 3 Months', value: '3m', days: 90 },
  LAST_6_MONTHS: { label: 'Last 6 Months', value: '6m', days: 180 },
  LAST_YEAR: { label: 'Last Year', value: '1y', days: 365 },
  ALL_TIME: { label: 'All Time', value: 'all', days: -1 }
} as const;

/**
 * Chart configurations
 */
export const CHART_CONFIG = {
  COLORS: {
    PRIMARY: '#3B82F6',
    SUCCESS: '#10B981',
    WARNING: '#F59E0B',
    DANGER: '#EF4444',
    NEUTRAL: '#6B7280'
  },
  GRADIENTS: {
    BLUE: ['#3B82F6', '#93C5FD'],
    GREEN: ['#10B981', '#86EFAC'],
    YELLOW: ['#F59E0B', '#FDE047'],
    RED: ['#EF4444', '#FCA5A5']
  },
  DEFAULT_HEIGHT: 400,
  DEFAULT_MARGIN: { top: 10, right: 30, left: 0, bottom: 0 }
} as const;

/**
 * Notification types
 */
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
  INFO: 'info',
  ACHIEVEMENT: 'achievement',
  REMINDER: 'reminder'
} as const;

/**
 * Achievement badges
 */
export const ACHIEVEMENT_BADGES = {
  IMPROVEMENT_10: {
    id: 'improvement_10',
    name: 'Rising Star',
    description: 'Improved GPA by 10%',
    icon: '⭐',
    points: 100
  },
  STREAK_7: {
    id: 'streak_7',
    name: 'Consistent Performer',
    description: '7 days improvement streak',
    icon: '🔥',
    points: 50
  },
  TOP_10: {
    id: 'top_10',
    name: 'Top Performer',
    description: 'Top 10% in class',
    icon: '🏆',
    points: 200
  },
  PERFECT_SCORE: {
    id: 'perfect_score',
    name: 'Perfectionist',
    description: 'Achieved perfect score',
    icon: '💯',
    points: 150
  }
} as const;

/**
 * Error codes
 */
export const ERROR_CODES = {
  INVALID_DATA: 'INVALID_DATA',
  INSUFFICIENT_DATA: 'INSUFFICIENT_DATA',
  PREDICTION_FAILED: 'PREDICTION_FAILED',
  ANALYSIS_FAILED: 'ANALYSIS_FAILED',
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  RATE_LIMITED: 'RATE_LIMITED'
} as const;

/**
 * Feature flags
 */
export const FEATURE_FLAGS = {
  ENABLE_ML_PREDICTIONS: true,
  ENABLE_REALTIME_SYNC: true,
  ENABLE_ACHIEVEMENTS: true,
  ENABLE_PEER_COMPARISON: true,
  ENABLE_NOTIFICATIONS: true,
  ENABLE_CV_ANALYSIS: true,
  ENABLE_CAREER_MAPPING: true,
  ENABLE_STUDY_PLANNER: true
} as const;