/**
 * Type definitions for Student Analysis Table
 */

export interface StudentAnalysis {
  student_id: string;
  name: string;
  department: string;
  batch: number;
  current_semester: number;
  cgpa: number;
  sgpa_trend: number[];
  latest_sgpa: number;
  attendance: number;
  weaknesses: Weakness[];
  weakness_count: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  improvement_trend: 'improving' | 'stable' | 'declining';
  recommendations_pending: number;
  profile_completeness: number;
  last_updated: string;
  metadata: {
    total_credits: number;
    has_warnings: boolean;
    analysis_version: string;
    last_analysis_date?: string;
  };
  predictions?: {
    next_semester_prediction: number;
    confidence: number;
    risk_factors: string[];
  };
}

export interface Weakness {
  subject: string;
  topic?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  gap: number;
  priority: number;
  last_identified: string;
  improvement_suggestions: string[];
}

export interface FilterOptions {
  department: string;
  cgpaMin: number;
  cgpaMax: number;
  riskLevel: string;
  semester: number | null;
  hasWeaknesses: boolean;
  batch: number | null;
  attendanceMin: number;
  attendanceMax: number;
  improvementTrend?: string;
}

export interface SortConfig {
  field: keyof StudentAnalysis;
  direction: 'asc' | 'desc';
}

export interface BulkAction {
  type: 'analyze' | 'email' | 'report' | 'predict';
  studentIds: string[];
  parameters?: any;
}

export interface RealTimeUpdate {
  type: 'student_update' | 'bulk_update' | 'analysis_complete';
  data: any;
  timestamp: string;
}