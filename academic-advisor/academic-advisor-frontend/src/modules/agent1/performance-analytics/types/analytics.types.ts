// modules/agent1/performance-analytics/types/analytics.types.ts
// Core Data Types
export interface DataPoint {
  date: string;
  gpa: number;
  percentile?: number;
  improvement?: number;
  confidence?: number;
  isPrediction?: boolean;
  isInterpolated?: boolean;
  isSmoothed?: boolean;
}

export interface PerformanceTrend {
  studentId?: string;
  dataPoints: DataPoint[];
  currentGPA?: number;
  percentile?: number;
  rank?: number;
  totalStudents?: number;
  subjects?: SubjectData[];
  lastUpdated?: string;
  projection?: DataPoint[];
  metrics?: PerformanceMetrics;
  enriched?: boolean;
  processedAt?: string;
  dataQuality?: number;
  insights?: string[];
  lastRealtimeSync?: string;
}

export interface TrendAnalysis {
  trend: 'improving' | 'declining' | 'stable';
  slope: number;
  intercept: number;
  r2Score: number;
  confidence: number;
  patterns?: TrendPattern[];
  insights?: string[];
  currentGPA: number;
  projectedGPA: number;
  gpaChange: number;
  percentile: number;
  rank?: number;
  totalStudents?: number;
  percentileChange: number;
  improvementRate: number;
  dataPointsCount: number;
  analysisDate?: string;
}

export interface SubjectData {
  id: string;
  name: string;
  category: string;
  credits: number;
  currentGrade: number;
  previousGrade?: number;
  classAverage?: number;
  rank?: number;
  totalStudents?: number;
  attendance?: number;
  completedAssignments?: number;
  totalAssignments?: number;
  weakTopics?: string[];
  recommendation?: string;
  trend: number;
}

// Prediction Types
export interface PredictiveMetrics {
  dataPoints: DataPoint[];
  trend: 'improving' | 'declining' | 'stable' | 'accelerating' | 'decelerating';
  mostLikely?: { gpa: number; date: string };
  bestCase?: { gpa: number; date: string };
  worstCase?: { gpa: number; date: string };
  confidence: number;
  modelType: string;
  modelAccuracy?: number;
  generatedAt: string;
  metrics?: {
    mae: number;
    rmse: number;
    mape: number;
  };
  seasonalityApplied?: boolean;
  seasonalFactors?: number[];
  externalFactorsIncluded?: boolean;
  factors?: any[];
  ensemble?: boolean;
  models?: string[];
  weights?: number[];
  slope?: number;
  intercept?: number;
  r2Score?: number;
  coefficients?: number[];
  degree?: number;
  alpha?: number;
  beta?: number;
  studyHoursNeeded?: number;
  weakAreas?: WeakArea[];
}

export interface PredictionConfig {
  modelType: 'linear' | 'polynomial' | 'exponential' | 'ml';
  horizonDays: number;
  confidenceLevel: number;
  includeSeasonality: boolean;
  includeExternalFactors: boolean;
  customFeatures?: string[];
  historicalData: DataPoint[];
}

// Weakness Analysis Types
export interface WeaknessAnalysis {
  weakAreas: WeakArea[];
  overallWeaknessScore?: number;
  recommendations?: string[];
  improvementPotential?: number;
  priorityOrder?: string[];
}

export interface WeakArea {
  id: string;
  name: string;
  currentScore: number;
  targetScore?: number;
  classAverage?: number;
  credits?: number;
  impactOnGPA?: number;
  difficulty?: number;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  priority?: number;
  estimatedImprovementTime?: string;
  potentialImprovement?: number;
  subject?: string;
}

export interface ImprovementPlan {
  areaId: string;
  areaName: string;
  currentPerformance: number;
  targetPerformance: number;
  timeline: string;
  strategies: string[];
  resources: string[];
  milestones: any[];
  estimatedEffort: number;
  priority: number;
}

// Pattern Detection Types
export interface TrendPattern {
  type: string;
  strength: number;
  description: string;
  startDate: string;
  endDate: string;
}

export interface SeasonalPattern {
  period: number;
  amplitude: number;
  phase: number;
  significance: number;
}

export interface Anomaly {
  date: string;
  value: number;
  expected?: number;
  deviation?: number;
  zScore?: number;
  type: 'positive' | 'negative' | 'sudden_change';
  severity: 'low' | 'medium' | 'high';
  description: string;
}

// Configuration Types
export interface TrendOptions {
  subjectId?: string;
  timeRange?: string;
  includeProjections?: boolean;
  groupBySubject?: boolean;
  semesterId?: string;
}

export interface AnalyticsConfig {
  enableRealtime?: boolean;
  enablePredictions?: boolean;
  cacheTimeout?: number;
  refreshInterval?: number;
  confidenceThreshold?: number;
}

// Metrics Types
export interface PerformanceMetrics {
  overallGPA: number;
  gpaChange: number;
  strongSubjects: number;
  needsAttention: number;
  totalCredits: number;
  averageGrade: number;
  medianGrade: number;
  standardDeviation: number;
  distribution: GradeDistribution;
  trends: SubjectTrends;
}

export interface GradeDistribution {
  A: number;
  B: number;
  C: number;
  D: number;
  F: number;
}

export interface SubjectTrends {
  improving: number;
  declining: number;
  stable: number;
}

// Model Types
export interface PredictionModel {
  id: string;
  type: string;
  accuracy: number;
  lastTrained: string;
  parameters: any;
}

export interface ModelPerformance {
  accuracy: number;
  loss: number;
  validationLoss?: number;
  metrics?: any;
}

// Time Series Types
export interface TimeSeriesData {
  timestamps: string[];
  values: number[];
  metadata?: any;
}

export interface TimeRange {
  label: string;
  value: string;
  days: number;
}

// Response Types
export interface AnalyticsResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface ErrorResponse {
  error: string;
  code: string;
  details?: any;
}

// Enums
export enum AnalysisType {
  TREND = 'trend',
  PREDICTION = 'prediction',
  WEAKNESS = 'weakness',
  COMPARISON = 'comparison'
}

export enum ModelType {
  LINEAR = 'linear',
  POLYNOMIAL = 'polynomial',
  EXPONENTIAL = 'exponential',
  ML = 'ml',
  ENSEMBLE = 'ensemble'
}

export enum Severity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum TrendDirection {
  IMPROVING = 'improving',
  DECLINING = 'declining',
  STABLE = 'stable'
}

// Utility Types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type AsyncResult<T> = Promise<{ data?: T; error?: Error }>;