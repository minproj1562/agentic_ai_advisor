// modules/agent1/student-analysis/types/student-analysis.types.ts
export interface StudentAnalysisData {
  studentId: string;
  name: string;
  email: string;
  department: string;
  semester: number;
  cgpa: number;
  lastSgpa: number;
  trend: 'improving' | 'declining' | 'stable';
  riskLevel: 'high' | 'medium' | 'low';
  weaknesses: WeaknessData[];
  lastUpdated: string;
}

export interface WeaknessData {
  subject: string;
  topic: string[];
  weakness_score: number;
  confidence: number;
  recommended_resources: Resource[];
}

export interface Resource {
  type: 'video' | 'book' | 'article' | 'course';
  title: string;
  url?: string;
  author?: string;
  duration?: string;
  chapters?: number[];
}

export interface DetailedAnalysis {
  student_id: string;
  performance_history: PerformanceHistory;
  weaknesses: WeaknessData[];
  predictions: PredictionResult;
  improvement_suggestions: ImprovementSuggestion[];
  confidence_score: number;
}

export interface PerformanceHistory {
  raw_data: PerformanceRecord[];
  sgpa_trend: string;
  subject_performance: SubjectPerformance;
  weak_subjects: Record<string, number>;
  current_cgpa: number;
  total_semesters: number;
}

export interface PerformanceRecord {
  semester: number;
  subject: string;
  marks: number;
  total: number;
  percentage: number;
  sgpa: number;
  cgpa: number;
}

export interface SubjectPerformance {
  [subject: string]: {
    mean: number;
    std: number;
  };
}

export interface PredictionResult {
  predicted_sgpa: number;
  confidence: number;
  trend: string;
  risk_factors: string[];
  improvement_potential: ImprovementPotential;
}

export interface ImprovementPotential {
  current: number;
  potential_max: number;
  recommended_focus_areas: string[];
  estimated_effort_hours: number;
}

export interface ImprovementSuggestion {
  subject: string;
  priority: 'high' | 'medium' | 'low';
  actions: string[];
  resources: Resource[];
  timeline: string;
  expected_improvement: string;
}

export interface GraphData {
  lineChart: LineChartData[];
  radarChart: RadarChartData[];
  statistics: Statistics;
}

export interface LineChartData {
  name: string;
  SGPA: number;
  CGPA: number;
}

export interface RadarChartData {
  subject: string;
  score: number;
  fullMark: number;
}

export interface Statistics {
  avgCGPA: number;
  trend: string;
  weakSubjectsCount: number;
}