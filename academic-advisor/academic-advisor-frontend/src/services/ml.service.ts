// src/services/ml.service.ts
import axios, { AxiosInstance } from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==================== NEW: SCORE BREAKDOWN TYPES ====================
export type CareerPredictionResponse = any;

// ==================== ACADEMIC RECOMMENDATIONS TYPE ====================

export interface WeaknessItem {
  subject: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  average_score: number;
  gap: number;
  trend: string;
  topics: string[];
  improvement_plan: any;
  resources: any[];
  confidence: number;
}

export interface ImmediateAction {
  priority: string;
  action: string;
  reason?: string;
  subjects?: string[];
  improvement_plan?: any;
}

export interface HonoursEligibility {
  eligible: boolean;
  cgpa: number;
  required_cgpa?: number;
  message: string;
  available_programs?: Array<{ program: string; type: string; credits?: number }>;
  cgpa_gap?: number;
  application_deadline?: string;
  suggestions?: string[];
}

export interface FocusArea {
  area: string;
  reason: string;
  average_score: number;
}

export interface InterestBasedRecommendation {
  elective_name: string;
  interest: string;
  match_score: number;
  reason: string;
  semester_available?: number[];
}

export interface CurriculumRecommendations {
  immediate_actions: ImmediateAction[];
  elective_suggestions: any[];
  honours_minor_eligibility: HonoursEligibility;
  focus_areas: FocusArea[];
}

export interface AcademicRecommendations {
  weaknesses: WeaknessItem[];
  curriculum_recommendations: CurriculumRecommendations;
  interest_based_recommendations: InterestBasedRecommendation[];
  student_info: {
    name: string;
    branch: string;
    semester: number;
    cgpa: number;
  };
  curriculum_info?: any;
}

export interface SubjectContribution {
  subject: string;
  score: number;
  weight: number;
  contribution: number;
  status: 'strong' | 'adequate' | 'weak';
}

export interface MissingSubject {
  subject: string;
  weight: number;
  impact: string;
}

export interface AcademicComponent {
  score: number;
  max_possible: number;
  percentage: number;
  contributing_subjects: SubjectContribution[];
  missing_subjects: MissingSubject[];
  strong_subjects: string[];
  weak_subjects: string[];
}

export interface MatchedInterest {
  interest: string;
  strength: number;
  contribution: number;
}

export interface UnmatchedInterest {
  interest: string;
  potential_boost: number;
}

export interface InterestComponent {
  score: number;
  max_possible: number;
  percentage: number;
  matched_interests: MatchedInterest[];
  unmatched_interests: UnmatchedInterest[];
  semantic_similarity: number;
}

export interface RelevantProject {
  title: string;
  matched_skills: string[];
  complexity: number;
  relevance_score: number;
}

export interface ProjectComponent {
  score: number;
  max_possible: number;
  percentage: number;
  relevant_projects: RelevantProject[];
  keyword_hits: number;
  missing_project_skills: string[];
  average_complexity: number;
  total_projects_analyzed: number;
}

export interface ScoreBreakdown {
  academic_component: AcademicComponent;
  interest_component: InterestComponent;
  project_component: ProjectComponent;
}

export interface RankingComparison {
  compared_to: string;
  score_difference: number;
  message: string;
}

export interface RankingExplanation {
  rank: number;
  total_options: number;
  why_this_rank: string;
  vs_other_electives: RankingComparison[];
  improvement_tips: string[];
}

export interface ConfidenceFactors {
  has_marks: boolean;
  has_interests: boolean;
  has_projects: boolean;
  marks_count: number;
  project_count: number;
  interest_count: number;
}

export interface ConfidenceMetrics {
  overall: number;
  data_completeness: number;
  model_confidence: number;
  factors: ConfidenceFactors;
}

// ==================== ADDITIONAL TYPES FOR MISSING METHODS ====================

export interface QuickInsights {
  placementReadiness: number;
  immediateActions: string[];
  strengthAreas: string[];
  improvementAreas: string[];
}

export interface ProjectPortfolioAnalysis {
  portfolioStrength: number;
  industryRelevance: number;
  innovationScore: number;
  technicalDepth: number;
  missingAreas: string[];
  recommendations: string[];
}

export interface PeerComparisonMetrics {
  percentile: number;
  yourPosition: number;
  totalStudents: number;
  averageCGPA: number;
  strengths: string[];
  weaknesses: string[];
}

export interface AICareerInsight {
  domain: string;
  matchScore: number;
  currentSkillGap: number;
  industryDemand: number;
  salaryRange: string;
  topCompanies: string[];
  requiredSkills: string[];
  preparationPath: string[];
}

export interface ComprehensiveStudentAnalysis {
  performanceMetrics: {
    predictedCGPA: number;
    performanceTrend: 'improving' | 'stable' | 'declining';
    strengthAreas: string[];
    weaknessAreas: string[];
  };
  careerInsights: Array<{ domain: string; matchScore: number }>;
  futureProjections: {
    placementProbability: number;
  };
  personalizedRecommendations: {
    immediateActions: Array<{
      action: string;
      priority: string;
      impact: number;
      effort: number;
      deadline: string;
    }>;
  };
}

// ==================== LEGACY TYPES (kept for backward compatibility) ====================

export interface SubjectScore {
  subject_code: string;
  subject_name: string;
  credits: number;
  internal_marks: number;
  external_marks: number;
  total_marks: number;
  grade: string;
  grade_points: number;
  semester: number;
  course_type: 'PCC' | 'PEC' | 'LBC' | 'SBL' | 'MNP' | 'MJP' | 'INT' | 'BSC' | 'ESC' | 'AEC' | 'OEC' | 'MDM';
  is_elective: boolean;
  is_practical: boolean;
}

export interface StudentAcademicData {
  student_id: string;
  name: string;
  roll_number: string;
  branch: string;
  admission_year: number;
  current_semester: number;
  current_cgpa: number;
  total_credits_earned: number;
  semesters: SemesterData[];
}

export interface SemesterData {
  semester_number: number;
  academic_year: string;
  sgpa: number;
  credits_earned: number;
  subjects: SubjectScore[];
}

export interface TrendAnalysis {
  trend: 'improving' | 'declining' | 'stable';
  trend_coefficient?: number;
  average_gpa?: number;
  best_semester?: number;
  worst_semester?: number;
  consistency_score?: number;
}

export interface PredictionResponse {
  student_id: string;
  predictions: {
    next_semester_gpa: number;
    expected_graduation_cgpa: number;
    confidence_score: number;
    risk_level: 'Low' | 'Medium' | 'High';
    risk_probability: number;
    improvement_potential: number;
  };
  trend_analysis: TrendAnalysis;
  risk_factors: string[];
  recommendations: string[];
  model_info: {
    model_type: string;
    accuracy: number;
    last_trained: string;
  };
}

export interface WeaknessData {
  subject: string;
  subject_code: string;
  marks: number;
  max_marks: number;
  gap: number;
  credits: number;
  performance: 'poor' | 'below_average' | 'average';
  topics: string[];
  improvement_strategy: string[];
}

export interface StudyPlan {
  weekly_hours: number;
  daily_hours: number;
  focus_distribution: Record<string, string>;
  recommended_resources: string[];
  milestones: Array<{
    week: number;
    target: string;
  }>;
}

export interface WeaknessAnalysisResponse {
  student_id: string;
  analysis: {
    overall_performance: 'excellent' | 'good' | 'average' | 'below_average' | 'poor';
    success_probability: number;
    weaknesses: WeaknessData[];
    priority_subjects: WeaknessData[];
    cgpa_improvement_needed: number;
    estimated_effort_hours: number;
    study_plan: StudyPlan;
  };
  recommendations: string[];
  timestamp: string;
}

// ==================== RECOMMENDATION TYPES ====================

export interface RecommendationBasis {
  interests_weight: number;
  performance_weight: number;
  projects_weight: number;
}

export interface SkillGap {
  subject: string;
  current_score: number;
  target_score: number;
  gap: number;
  importance: 'High' | 'Medium' | 'Low';
}

export interface ElectiveRecommendation {
  elective_code: string;
  elective_name: string;
  credits: number;
  match_score: number;
  
  // NEW: Structured breakdown
  score_breakdown?: ScoreBreakdown;
  ranking_explanation?: RankingExplanation;
  confidence?: ConfidenceMetrics;
  
  // Legacy fields
  match_explanation: string;
  prerequisites_met: boolean;
  skill_alignment: string[];
  career_relevance: string[];
  recommendation_basis: RecommendationBasis;
  pair?: string;
  skill_gaps: SkillGap[];
}

export interface HonoursScoreBreakdown {
  academic_score: number;
  interest_score: number;
  project_score: number;
  matched_subjects: Array<{ subject: string; score: number }>;
  matched_interests: string[];
  relevant_projects: RelevantProject[];
}

export interface HonoursRecommendation {
  program: string;
  type: 'honours' | 'minor';
  match_score: number;
  eligibility: boolean;
  required_cgpa: number;
  career_paths: string[];
  explanation: string;
  skills_gained: string[];
  score_breakdown?: HonoursScoreBreakdown;
}

export interface CareerScoreBreakdown {
  interest_score: number;
  project_score: number;
  cgpa_score: number;
  matched_interests: string[];
  relevant_projects: RelevantProject[];
}

export interface CareerRecommendation {
  career: string;
  match_score: number;
  cgpa_eligible: boolean;
  required_cgpa: number;
  salary_range: string;
  growth_potential: string;
  top_companies: string[];
  missing_skills: string[];
  preparation_path: string[];
  required_certifications: string[];
  score_breakdown?: CareerScoreBreakdown;
}

export interface CumulativeRecommendationResponse {
  electives: ElectiveRecommendation[];
  open_electives?: ElectiveRecommendation[];
  honours: HonoursRecommendation[];
  careers: CareerRecommendation[];
  model_info: {
    models_used: string[];
    is_ml_trained: boolean;
    is_oe_ml_trained?: boolean;
    version: string;
    cached?: boolean;
    cached_at?: string;
  };
  computation_time_ms: number;
  data_summary?: {
    total_marks_subjects: number;
    total_interests: number;
    total_projects: number;
    cgpa: number;
  };
}

// ==================== PROJECT ANALYSIS TYPES ====================

export interface InferredInterest {
  domain: string;
  confidence: number;
  matched_keywords: string[];
  source: string;
  relatedSkills?: string[];
  careerPaths?: string[];
  industryRelevance?: number;
  keywords?: string[];
}

export interface ProjectAnalysisResult {
  extracted_skills: string[];
  complexity_score: number;
  inferred_interests: InferredInterest[];
}

export interface ComprehensiveProjectAnalysisResponse {
  success: boolean;
  project_analysis: ProjectAnalysisResult;
  cumulative_recommendations: CumulativeRecommendationResponse;
  data_summary: {
    total_marks_subjects: number;
    total_interests: number;
    total_projects: number;
    cgpa: number;
  };
  model_info: {
    is_ml_trained: boolean;
    models_used: string[];
    version: string;
  };
  student_info: {
    branch: string;
    semester: number;
    user_id: string;
  };
  generated_at: string;
}

// Legacy type for backward compatibility
export interface LegacyProjectAnalysisResult {
  inferred_interests: Array<{
    domain: string;
    confidence: number;
    keywords: string[];
    relatedSkills: string[];
    careerPaths: string[];
    industryRelevance: number;
  }>;
  elective_recommendations: Array<{
    elective: string;
    code: string;
    match_score: number;
    reasons: string[];
    skills_to_gain: string[];
    career_relevance: string;
    difficulty_level: string;
  }>;
  honours_minor_recommendations: Array<{
    program: string;
    type: string;
    match_score: number;
    courses: string[];
    career_paths: string[];
    credits: number;
    semester_commitment: string;
    reasons: string[];
  }>;
  career_paths: Array<{
    title: string;
    match_score: number;
    salary_range: string;
    market_demand: string;
    growth_potential: string;
    required_skills: string[];
    companies_hiring: string[];
    honours_program?: string;
    preparation_path: string[];
  }>;
  skill_gap_analysis: {
    current_skills: string[];
    skill_gaps: string[];
    priority_skills: string[];
    learning_resources: Record<string, Array<{ platform: string; course: string }>>;
    completeness_percentage: number;
    estimated_learning_time: string;
  };
  next_steps: Array<{
    action: string;
    category: string;
    priority: string;
    deadline: string;
    details: string;
  }>;
  metadata: {
    analysis_date: string;
    confidence_score: number;
    model_version: string;
    data_sources: string[];
  };
}

export interface InterestProfile {
  student_id: string;
  declared_interests: string[];
  inferred_interests: string[];
  career_goals: string[];
  skills: string[];
  topDomains: Array<{
    name: string;
    strength: number;
  }>;
  profile_completeness: number;
  recommendations?: {
    electives: ElectiveRecommendation[];
    honours_programs: HonoursRecommendation[];
    career_paths: CareerRecommendation[];
  };
}

export interface ModelInfo {
  is_trained: boolean;
  model_version: string;
  models_available: string[];
  last_trained?: string;
  training_accuracy?: number;
  feature_dimension?: number;
  electives_supported?: string[];
}

export interface TrainingMetrics {
  accuracy: number;
  f1_macro: number;
  f1_weighted: number;
  per_class: Record<string, { precision: number; recall: number; f1: number }>;
  cross_val_mean: number;
  cross_val_std: number;
  confusion_matrix: number[][];
  n_training_samples: number;
  n_test_samples: number;
  model_type: string;
  timestamp: string;
}

// ==================== ML SERVICE CLASS ====================

class MLService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.api.interceptors.request.use(
      async (config) => {
        try {
          // 1. Firebase user (faculty/admin)
          const currentUser = auth.currentUser;
          if (currentUser) {
            const token = await currentUser.getIdToken();
            if (token && config.headers) {
              config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
          }

          // 2. Student JWT from localStorage (students don't use Firebase)
          const storedToken =
            localStorage.getItem('auth_token') ||
            sessionStorage.getItem('auth_token');
          if (storedToken && config.headers) {
            config.headers.Authorization = `Bearer ${storedToken}`;
          }
        } catch (error) {
          console.error('Failed to get auth token:', error);
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // ==================== CUMULATIVE RECOMMENDATIONS ====================
    // ==================== ACADEMIC RECOMMENDATIONS ====================

  async getAcademicRecommendations(): Promise<AcademicRecommendations> {
    try {
      const response = await this.api.get('/ml-insights/academic-recommendations');
      return response.data?.data || response.data;
    } catch (error: any) {
      console.error('Error getting academic recommendations:', error);
      // Re-throw with meaningful message for the component to handle
      if (error.response?.status === 404) {
        const err = new Error('Student profile not found');
        (err as any).response = error.response;
        throw err;
      }
      throw error;
    }
  }
    // ==================== CAREER PREDICTION ====================

  async predictCareer(
    studentId: string,
    skills: string[],
    interests: string[],
    currentCGPA: number,
    projects: string[]
  ): Promise<any> {
    try {
      const response = await this.api.post('/ml-insights/career-path-analysis', {
        skills,
        interests,
        academicPerformance: { cgpa: currentCGPA },
        careerGoals: [],
      });
      return response.data;
    } catch (error) {
      console.error('Error predicting career:', error);
      return {
        recommended_paths: [],
        skill_matches: {},
        preparation_timeline: {}
      };
    }
  }

  async getRecommendations(
    includeElectives: boolean = true,
    includeHonours: boolean = true,
    includeCareer: boolean = true,
    forceRefresh: boolean = false
  ): Promise<CumulativeRecommendationResponse> {
    try {
      const response = await this.api.post<CumulativeRecommendationResponse>(
        '/recommendations/generate',
        {
          include_electives: includeElectives,
          include_honours: includeHonours,
          include_career: includeCareer,
          use_transformer: true,
          use_knn: true,
          use_logistic: true,
          force_refresh: forceRefresh
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      return this.getDefaultRecommendations();
    }
  }

  async submitRecommendationFeedback(
    type: 'elective' | 'honours' | 'career',
    itemId: string,
    rating: number,
    feedback: string
  ): Promise<void> {
    try {
      await this.api.post('/recommendations/feedback', {
        type,
        recommendation_id: itemId,
        rating,
        feedback,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  }

  async refreshRecommendations(): Promise<CumulativeRecommendationResponse> {
    try {
      const response = await this.api.post<CumulativeRecommendationResponse>(
        '/recommendations/refresh'
      );
      return response.data;
    } catch (error) {
      console.error('Error refreshing recommendations:', error);
      throw error;
    }
  }

  // ==================== ELECTIVE CHOICE TRACKING ====================

  async recordElectiveChoice(
    electiveCode: string,
    electiveName: string,
    isOpenElective: boolean = false,
    semester: number = 5,
    reason: string = ''
  ): Promise<any> {
    try {
      const response = await this.api.post('/recommendations/record-choice', {
        chosen_elective_code: electiveCode,
        chosen_elective_name: electiveName,
        is_open_elective: isOpenElective,
        semester,
        reason,
      });
      return response.data;
    } catch (error) {
      console.error('Error recording elective choice:', error);
      throw error;
    }
  }

  // ==================== IMPROVEMENT ROADMAP ====================

  async getImprovementRoadmap(
    electiveCode: string,
    isOpenElective: boolean = false
  ): Promise<any> {
    try {
      const response = await this.api.post('/recommendations/roadmap', {
        elective_code: electiveCode,
        is_open_elective: isOpenElective,
      });
      return response.data;
    } catch (error) {
      console.error('Error getting roadmap:', error);
      throw error;
    }
  }

  async getModelInfo(): Promise<ModelInfo> {
    try {
      const response = await this.api.get<ModelInfo>('/recommendations/model-info');
      return response.data;
    } catch (error) {
      console.error('Error getting model info:', error);
      return {
        is_trained: false,
        model_version: '1.0.0',
        models_available: ['Rule-Based']
      };
    }
  }

  // ==================== MISSING METHODS FOR StudentProjectsList ====================

async getComprehensiveAnalysis(userId?: string): Promise<ComprehensiveStudentAnalysis> {
  try {
    const response = await this.api.get('/ml-insights/comprehensive-analysis');  // ✅ uses auth token
    return response.data;
  } catch (error) {
    console.warn('Comprehensive analysis not available, using defaults');
    return this.getDefaultComprehensiveAnalysis();
  }
}

async getQuickInsights(userId?: string): Promise<QuickInsights> {
  try {
    const response = await this.api.get('/ml-insights/quick-insights/');  // ✅ auth token handles user
    return response.data;
  } catch (error) {
    console.warn('Quick insights not available, using defaults');
    return {
      placementReadiness: 72,
      immediateActions: [
        'Build more projects to strengthen portfolio',
        'Focus on Data Structures revision',
        'Start preparing for technical interviews'
      ],
      strengthAreas: ['Programming', 'Problem Solving'],
      improvementAreas: ['System Design', 'Testing']
    };
  }
}


async analyzeProjectPortfolio(
  projects?: any[],
  targetDomain?: string
): Promise<ProjectPortfolioAnalysis> {
  try {
    const response = await this.api.post('/ml-insights/portfolio-analysis', {});  // ✅ uses auth
    return response.data;
  } catch (error) {
    console.warn('Portfolio analysis not available, using defaults');
    return {
      portfolioStrength: 75,
      industryRelevance: 70,
      innovationScore: 65,
      technicalDepth: 72,
      missingAreas: ['System Design', 'Testing', 'CI/CD'],
      recommendations: ['Add more complex projects', 'Include open source contributions']
    };
  }
}

async getPeerComparison(
  userId?: string,
  branch?: string,
  semester?: number
): Promise<PeerComparisonMetrics> {
  try {
    const response = await this.api.get('/ml-insights/peer-comparison', {
      params: { branch: branch || 'IT', semester: semester || 4 }
    });
    return response.data;
  } catch (error) {
    console.warn('Peer comparison not available, using defaults');
    return {
      percentile: 75,
      yourPosition: 25,
      totalStudents: 100,
      averageCGPA: 7.5,
      strengths: ['Strong programming skills', 'Good project portfolio'],
      weaknesses: ['Need more certifications', 'Limited internship experience']
    };
  }
}


async getCareerPathAnalysis(
  skills: string[],
  interests: string[],
  academicProfile: { cgpa: number; projects: number }
): Promise<AICareerInsight[]> {
  try {
    const response = await this.api.post('/ml-insights/career-path-analysis', {
      skills,
      interests,
      academicPerformance: academicProfile,
      careerGoals: []
    });
    return response.data.recommended_paths || [];
  } catch (error) {
    console.warn('Career path analysis not available, using defaults');
    return [
      {
        domain: 'Software Development',
        matchScore: 85,
        currentSkillGap: 15,
        industryDemand: 90,
        salaryRange: '₹6-18 LPA',
        topCompanies: ['Google', 'Microsoft', 'Amazon'],
        requiredSkills: ['DSA', 'System Design', 'Cloud'],
        preparationPath: ['Master DSA', 'Build projects', 'Get certifications']
      },
      {
        domain: 'Data Science',
        matchScore: 72,
        currentSkillGap: 28,
        industryDemand: 85,
        salaryRange: '₹8-20 LPA',
        topCompanies: ['Google', 'Meta', 'Netflix'],
        requiredSkills: ['Python', 'ML', 'Statistics'],
        preparationPath: ['Learn Python', 'Complete ML courses', 'Build ML projects']
      }
    ];
  }
}

// Default types for fallbacks
private getDefaultComprehensiveAnalysis(): ComprehensiveStudentAnalysis {
  return {
    performanceMetrics: {
      predictedCGPA: 7.5,
      performanceTrend: 'stable',
      strengthAreas: ['Programming', 'Problem Solving'],
      weaknessAreas: ['System Design', 'Testing']
    },
    careerInsights: [
      { domain: 'Software Development', matchScore: 80 }
    ],
    futureProjections: {
      placementProbability: 75
    },
    personalizedRecommendations: {
      immediateActions: [
        { action: 'Focus on weak subjects', priority: 'high', impact: 8, effort: 6, deadline: 'This month' },
        { action: 'Build portfolio projects', priority: 'medium', impact: 7, effort: 5, deadline: 'This semester' }
      ]
    }
  };
}
  // ==================== PROJECT ANALYSIS ====================

async analyzeProjectComprehensive(
  projectData: Record<string, any>,
  studentBranch?: string,
  studentSemester?: number,
  files?: File[]
): Promise<ComprehensiveProjectAnalysisResponse> {
  try {
    const formData = new FormData();
    formData.append('project_data', JSON.stringify(projectData));
    
    if (studentBranch) formData.append('student_branch', studentBranch);
    if (studentSemester) formData.append('student_semester', studentSemester.toString());
    if (files && files.length > 0) {
      files.forEach(file => formData.append('files', file));
    }

    const response = await this.api.post<ComprehensiveProjectAnalysisResponse>(
      '/student-projects/analyze-comprehensive',   // ✅ FIXED path
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error analyzing project:', error);
    throw error;
  }
}


  // Convert new response to legacy format for backward compatibility
  convertToLegacyFormat(response: ComprehensiveProjectAnalysisResponse): LegacyProjectAnalysisResult {
    const { project_analysis, cumulative_recommendations } = response;
    
    return {
      inferred_interests: project_analysis.inferred_interests.map(i => ({
        domain: i.domain,
        confidence: i.confidence,
        keywords: i.matched_keywords || [],
        relatedSkills: i.relatedSkills || [],
        careerPaths: i.careerPaths || [],
        industryRelevance: i.industryRelevance || i.confidence * 0.9,
      })),
      elective_recommendations: cumulative_recommendations.electives.map(e => ({
        elective: e.elective_name,
        code: e.elective_code,
        match_score: e.match_score,
        reasons: [e.match_explanation],
        skills_to_gain: e.skill_alignment,
        career_relevance: e.career_relevance.join(', '),
        difficulty_level: 'Intermediate',
      })),
      honours_minor_recommendations: cumulative_recommendations.honours.map(h => ({
        program: h.program,
        type: h.type,
        match_score: h.match_score,
        courses: h.skills_gained,
        career_paths: h.career_paths,
        credits: 18,
        semester_commitment: '4 semesters',
        reasons: [h.explanation],
      })),
      career_paths: cumulative_recommendations.careers.map(c => ({
        title: c.career,
        match_score: c.match_score,
        salary_range: c.salary_range,
        market_demand: c.growth_potential === 'Very High' ? 'Very High' : 'High',
        growth_potential: c.growth_potential,
        required_skills: c.missing_skills,
        companies_hiring: c.top_companies,
        preparation_path: c.preparation_path,
      })),
      skill_gap_analysis: {
        current_skills: project_analysis.extracted_skills,
        skill_gaps: cumulative_recommendations.electives[0]?.skill_gaps?.map(g => g.subject) || [],
        priority_skills: cumulative_recommendations.electives[0]?.skill_alignment?.slice(0, 3) || [],
        learning_resources: {},
        completeness_percentage: Math.round(response.data_summary?.cgpa ? (response.data_summary.cgpa / 10) * 100 : 70),
        estimated_learning_time: '2-3 months',
      },
      next_steps: cumulative_recommendations.electives[0]?.ranking_explanation?.improvement_tips?.map((tip, i) => ({
        action: tip,
        category: 'Skills',
        priority: i === 0 ? 'high' : 'medium',
        deadline: 'This semester',
        details: tip,
      })) || [],
      metadata: {
        analysis_date: response.generated_at,
        confidence_score: cumulative_recommendations.electives[0]?.confidence?.overall || 0.75,
        model_version: response.model_info.version,
        data_sources: ['marks', 'interests', 'projects'],
      },
    };
  }

  // ==================== PREDICTIONS ====================

  async getPredictions(
    studentId: string,
    academicData: StudentAcademicData,
    historicalScores: Array<{ semester: number; gpa: number; credits: number }>,
    currentSemester: number
  ): Promise<PredictionResponse> {
    try {
      const response = await this.api.post<PredictionResponse>('/ml-insights/predictions/performance', {
        student_id: studentId,
        academic_data: academicData,
        historical_scores: historicalScores,
        current_semester: currentSemester
      });
      return response.data;
    } catch (error) {
      console.error('Error getting predictions:', error);
      return this.getDefaultPrediction(studentId, academicData);
    }
  }

  private getDefaultPrediction(studentId: string, academicData: StudentAcademicData): PredictionResponse {
    const cgpa = academicData.current_cgpa || 7.0;
    return {
      student_id: studentId,
      predictions: {
        next_semester_gpa: cgpa + 0.1,
        expected_graduation_cgpa: cgpa + 0.2,
        confidence_score: 0.75,
        risk_level: cgpa < 6 ? 'High' : cgpa < 7 ? 'Medium' : 'Low',
        risk_probability: cgpa < 6 ? 0.7 : cgpa < 7 ? 0.4 : 0.1,
        improvement_potential: Math.min(10 - cgpa, 2)
      },
      trend_analysis: {
        trend: 'stable',
        average_gpa: cgpa
      },
      risk_factors: cgpa < 7 ? ['CGPA below target'] : [],
      recommendations: ['Focus on weak subjects', 'Maintain study schedule'],
      model_info: {
        model_type: 'Ensemble',
        accuracy: 0.85,
        last_trained: new Date().toISOString()
      }
    };
  }

  // ==================== WEAKNESS ANALYSIS ====================

  async analyzeWeaknesses(
    studentId: string,
    subjectScores: SubjectScore[],
    currentCGPA: number
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const response = await this.api.post<WeaknessAnalysisResponse>('/ml-insights/analysis/weaknesses', {
        student_id: studentId,
        subject_scores: subjectScores,
        current_cgpa: currentCGPA
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing weaknesses:', error);
      return this.getDefaultWeaknessAnalysis(studentId, subjectScores, currentCGPA);
    }
  }

  private getDefaultWeaknessAnalysis(
    studentId: string,
    subjectScores: SubjectScore[],
    currentCGPA: number
  ): WeaknessAnalysisResponse {
    const weakSubjects = subjectScores
      .filter(s => (s.total_marks / 100) < 0.6)
      .map(s => ({
        subject: s.subject_name,
        subject_code: s.subject_code,
        marks: s.total_marks,
        max_marks: 100,
        gap: 60 - s.total_marks,
        credits: s.credits,
        performance: s.total_marks < 40 ? 'poor' as const : 'below_average' as const,
        topics: ['Core Concepts', 'Problem Solving'],
        improvement_strategy: [`Review ${s.subject_name} fundamentals`]
      }));

    return {
      student_id: studentId,
      analysis: {
        overall_performance: currentCGPA >= 8 ? 'excellent' : currentCGPA >= 7 ? 'good' : 'average',
        success_probability: Math.min(0.95, currentCGPA / 10),
        weaknesses: weakSubjects,
        priority_subjects: weakSubjects.slice(0, 3),
        cgpa_improvement_needed: Math.max(0, 7 - currentCGPA),
        estimated_effort_hours: weakSubjects.length * 20,
        study_plan: {
          weekly_hours: 15,
          daily_hours: 2,
          focus_distribution: {},
          recommended_resources: ['NPTEL', 'GeeksforGeeks'],
          milestones: []
        }
      },
      recommendations: ['Focus on weak subjects'],
      timestamp: new Date().toISOString()
    };
  }

  // ==================== INTEREST PROFILE ====================

  async updateInterests(
    interests: string[],
    careerGoals: string[],
    skills: string[]
  ): Promise<InterestProfile> {
    try {
      const response = await this.api.post('/ml-insights/interests/update', {
        interests,
        career_goals: careerGoals,
        skills
      });
      await this.refreshRecommendations();
      return response.data;
    } catch (error) {
      console.error('Error updating interests:', error);
      throw error;
    }
  }

  async getInterestProfile(): Promise<InterestProfile> {
    try {
      const response = await this.api.get<InterestProfile>('/ml-insights/interests/profile');
      return response.data;
    } catch (error) {
      console.error('Error getting interest profile:', error);
      return {
        student_id: '',
        declared_interests: [],
        inferred_interests: [],
        career_goals: [],
        skills: [],
        topDomains: [],
        profile_completeness: 0
      };
    }
  }

  // ==================== DEFAULT DATA ====================

  private getDefaultRecommendations(): CumulativeRecommendationResponse {
    return {
      electives: this.getDefaultElectives(),
      honours: this.getDefaultHonours(),
      careers: this.getDefaultCareers(),
      model_info: {
        models_used: ['Rule-Based (Fallback)'],
        is_ml_trained: false,
        version: '2.0.0'
      },
      computation_time_ms: 0
    };
  }

  private getDefaultElectives(): ElectiveRecommendation[] {
    return [
      {
        elective_code: 'ITPEC5012',
        elective_name: 'Machine Learning',
        credits: 3,
        match_score: 85,
        score_breakdown: {
          academic_component: {
            score: 34,
            max_possible: 40,
            percentage: 85,
            contributing_subjects: [
              { subject: 'Python', score: 85, weight: 3.0, contribution: 8.5, status: 'strong' },
              { subject: 'DSA', score: 78, weight: 2.5, contribution: 6.5, status: 'adequate' }
            ],
            missing_subjects: [],
            strong_subjects: ['Python', 'Mathematics'],
            weak_subjects: []
          },
          interest_component: {
            score: 27,
            max_possible: 30,
            percentage: 90,
            matched_interests: [
              { interest: 'AI/ML', strength: 100, contribution: 20 }
            ],
            unmatched_interests: [],
            semantic_similarity: 0.85
          },
          project_component: {
            score: 24,
            max_possible: 30,
            percentage: 80,
            relevant_projects: [
              { title: 'Sentiment Analyzer', matched_skills: ['Python', 'NLP'], complexity: 0.8, relevance_score: 90 }
            ],
            keyword_hits: 8,
            missing_project_skills: ['PyTorch', 'Computer Vision'],
            average_complexity: 0.75,
            total_projects_analyzed: 3
          }
        },
        ranking_explanation: {
          rank: 1,
          total_options: 4,
          why_this_rank: 'Strongest combined alignment across academics, interests, and projects',
          vs_other_electives: [
            { compared_to: 'Cloud Computing', score_difference: 12, message: '12 points higher than second choice' }
          ],
          improvement_tips: [
            'Add a Computer Vision project to boost score by ~5%',
            'Take AI course next semester for +8% academic alignment'
          ]
        },
        confidence: {
          overall: 0.87,
          data_completeness: 0.92,
          model_confidence: 0.85,
          factors: {
            has_marks: true,
            has_interests: true,
            has_projects: true,
            marks_count: 12,
            project_count: 3,
            interest_count: 4
          }
        },
        match_explanation: 'Ranked #1 of 4 electives with a cumulative score of 85%.',
        prerequisites_met: true,
        skill_alignment: ['TensorFlow', 'PyTorch', 'Scikit-learn', 'Neural Networks'],
        career_relevance: ['ML Engineer', 'Data Scientist', 'AI Researcher'],
        recommendation_basis: {
          interests_weight: 27,
          performance_weight: 34,
          projects_weight: 24
        },
        pair: 'Pair 1 (ML vs WT)',
        skill_gaps: []
      },
      {
        elective_code: 'ITPEC5015',
        elective_name: 'Cloud Computing Services',
        credits: 3,
        match_score: 73,
        match_explanation: 'Good performance in Networks and OS. Cloud skills are highly demanded.',
        prerequisites_met: true,
        skill_alignment: ['AWS', 'Azure', 'Docker', 'Kubernetes'],
        career_relevance: ['Cloud Architect', 'DevOps Engineer', 'SRE'],
        recommendation_basis: {
          interests_weight: 20,
          performance_weight: 30,
          projects_weight: 23
        },
        pair: 'Pair 2 (DWM vs CCS)',
        skill_gaps: []
      }
    ];
  }

  private getDefaultHonours(): HonoursRecommendation[] {
    return [
      {
        program: 'AI / ML Honours',
        type: 'honours',
        match_score: 82,
        eligibility: true,
        required_cgpa: 7.5,
        career_paths: ['ML Engineer', 'Data Scientist', 'AI Researcher'],
        explanation: 'Based on your interests and performance in mathematics/programming.',
        skills_gained: ['Deep Learning', 'NLP', 'Computer Vision', 'MLOps'],
        score_breakdown: {
          academic_score: 35,
          interest_score: 27,
          project_score: 20,
          matched_subjects: [{ subject: 'Python', score: 85 }],
          matched_interests: ['AI/ML'],
          relevant_projects: []
        }
      }
    ];
  }

  private getDefaultCareers(): CareerRecommendation[] {
    return [
      {
        career: 'Software Development Engineer',
        match_score: 85,
        cgpa_eligible: true,
        required_cgpa: 7.0,
        salary_range: '₹6-15 LPA',
        growth_potential: 'High',
        top_companies: ['Google', 'Microsoft', 'Amazon', 'Flipkart'],
        missing_skills: ['System Design'],
        preparation_path: ['Master DSA', 'Build full-stack projects', 'Practice LeetCode'],
        required_certifications: ['AWS Cloud Practitioner'],
        score_breakdown: {
          interest_score: 35,
          project_score: 30,
          cgpa_score: 20,
          matched_interests: ['Web Development'],
          relevant_projects: []
        }
      }
    ];
  }
}

export const mlService = new MLService();
export default mlService;