// src/services/weakness.service.ts
// Updated to match corrected backend response shapes.
// Adds: effort_readiness_score, total_gap_hours, study_load_warning,
//       effort_detail, low_confidence_flag, credits on weaknesses.

import axios, { AxiosInstance } from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ══════════════════════════════════════════════════════════════
//  SHARED TYPES
// ══════════════════════════════════════════════════════════════

export type AnalysisBasis =
  | 'interest'
  | 'electives'
  | 'honours_minors'
  | 'performance'
  | 'combined';

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';
export type ReadinessLevel =
  | 'excellent'
  | 'good'
  | 'moderate'
  | 'low'
  | 'not_ready';
export type RecommendationType =
  | 'proceed'
  | 'proceed_with_caution'
  | 'improve_first'
  | 'do_not_proceed';

// ══════════════════════════════════════════════════════════════
//  WEAKNESS ANALYSIS TYPES (unchanged from original)
// ══════════════════════════════════════════════════════════════

export interface WeaknessArea {
  id: string;
  subject: string;
  topic?: string;
  current_score: number;
  target_score: number;
  gap_percentage: number;
  severity: SeverityLevel;
  confidence: number;
  related_to: string;
  analysis_basis: AnalysisBasis;
  improvement_suggestions: string[];
  recommended_resources: ResourceItem[];
  estimated_improvement_time: string;
  priority: number;
  impact_on_interest?: string;
  impact_on_elective?: string;
  impact_on_career?: string;
}

export interface ResourceItem {
  type: 'course' | 'video' | 'practice' | 'article' | 'book';
  platform: string;
  title: string;
  url?: string;
  author?: string;
  duration?: string;
}

export interface WeaknessAnalysisResponse {
  student_id: string;
  analysis_basis: AnalysisBasis;
  weaknesses: WeaknessArea[];
  overall_risk_score: number;
  priority_areas: string[];
  recommended_resources: ResourceItem[];
  study_plan?: Record<string, any> | null;
  analysis_timestamp: string;
  total_weaknesses: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  key_insights: string[];
  improvement_potential: number;
}

export interface WeaknessAnalysisRequest {
  student_id: string;
  analysis_basis: AnalysisBasis;
  interests?: string[];
  recommended_electives?: string[];
  honours_minors?: string[];
  include_resources?: boolean;
  include_study_plan?: boolean;
}

export interface WeaknessSummary {
  student_id: string;
  has_analysis: boolean;
  overall_risk_score: number;
  total_weaknesses: number;
  critical_count: number;
  high_count: number;
  priority_subjects: string[];
  needs_attention: boolean;
  last_analyzed?: string;
}

// ══════════════════════════════════════════════════════════════
//  READINESS TYPES — Updated to match backend
// ══════════════════════════════════════════════════════════════

/**
 * Per-weakness entry from the readiness engine.
 * Matches WeaknessEntry in app/models/readiness.py
 */
export interface ReadinessWeakness {
  id?: string;
  subject: string;
  severity: SeverityLevel;
  current_score: number;
  target_score: number;
  gap: number;
  importance: number;
  importance_label: string;
  confidence: number;

  /**
   * True when subject was matched with confidence < 0.7
   * (partial or word-overlap match).
   * Frontend can show this as a softer warning.
   */
  low_confidence_flag: boolean;

  /** Credits from the student's actual SubjectScore record. */
  credits: number;

  linked_goals: string[];
  goal_types: string[];
  suggestions: string[];
  resources: Array<{
    type: string;
    platform: string;
    title: string;
    url: string;
  }>;

  /**
   * Total hours to close this gap.
   * Formula: gap × credits × 0.1 × multipliers
   * Study plan divides this by duration_weeks for weekly hours.
   */
  estimated_hours: number;

  priority_rank: number;
}

/**
 * Per-subject effort estimate from the effort calculator.
 * Matches SubjectStudyEstimate in app/models/readiness.py
 */
export interface SubjectStudyEstimate {
  subject_name: string;
  subject_code?: string;
  credits: number;
  current_score: number;
  required_min: number;
  is_backlog: boolean;
  is_taken: boolean;
  semester: number;
  gap_to_target: number;

  /**
   * coverage_ratio = min(score / min_score, 1.0)
   * Represents how much of the requirement is already satisfied.
   */
  coverage_ratio: number;

  /**
   * Total hours needed to close the gap for this subject.
   * Formula: gap × credits × 0.1 × backlog_mult × semester_mult
   */
  study_hours_to_close_gap: number;
}

/**
 * Effort readiness result block.
 * Matches EffortReadinessResult in app/models/readiness.py
 */
export interface EffortDetail {
  /**
   * Credit-weighted coverage ratio × 100 (0–100).
   * Higher = more requirements already satisfied by current marks.
   * Capped at 60 if any subject is below passing grade (40%).
   */
  effort_readiness_score: number;

  /**
   * Named for API compatibility.
   * Actually stores TOTAL gap hours (not per-week).
   * Study plan divides by duration_weeks.
   */
  estimated_study_load_weekly: number;

  /** Σ(credits × 2) for all required subjects. */
  total_required_min_hours: number;

  has_backlog: boolean;
  study_load_warning: string | null;
  per_subject_estimates: SubjectStudyEstimate[];
}

export interface StudyPlanFocusArea {
  subject: string;
  priority: number;
  current_score: number;
  target_score: number;

  /** Total hours for this subject across the full plan. */
  total_hours: number;

  /** Hours per week allocated to this subject. */
  weekly_hours: number;

  severity: string;
  credits: number;
}

export interface StudyPlanPhase {
  name: string;
  weeks: string;
  focus: string[];
  goals: string[];
}

export interface StudyPlanMilestone {
  week: number;
  target: string;
}

export interface StudyPlan {
  duration?: string | number;
  duration_weeks: number;
  weekly_hours: number;
  weekly_commitment: string;

  /** Σ estimated_hours for top 6 weaknesses. */
  total_gap_hours: number;

  /**
   * Weekly extra study budget used for duration calculation.
   * 20 if credits < 15, 15 if 15–20, 10 if > 20.
   */
  extra_budget_per_week: number;

  focus_areas: StudyPlanFocusArea[];
  phases: StudyPlanPhase[];
  milestones: StudyPlanMilestone[];
  current_readiness: number;
  target_readiness: number;
  total_credits_registered: number;
  recommendation: string;

  /** Present when no weaknesses detected. */
  message?: string;
}

/**
 * Main readiness response.
 * Matches ReadinessResponse in app/models/readiness.py
 */
export interface ReadinessResponse {
  student_id: string;

  // Core scores
  overall_readiness_score: number;
  readiness_level: ReadinessLevel;
  recommendation_type: RecommendationType;
  primary_recommendation: string;

  // Category scores
  interest_readiness: number;
  elective_readiness: number;
  honours_readiness: number;
  interest_breakdown: Record<string, number>;
  elective_breakdown: Record<string, number>;
  honours_breakdown: Record<string, number>;

  // Flags
  has_critical_weakness: boolean;
  has_blockers: boolean;
  is_first_semester: boolean;

  // Focus + timing
  subjects_to_focus: string[];
  estimated_preparation_time: string;
  detailed_recommendations: string[];

  // Weaknesses + study plan
  weaknesses: ReadinessWeakness[];
  study_plan: StudyPlan | null;

  // Effort fields
  effort_readiness_score: number;

  /**
   * total_gap_hours: Σ estimated_hours across all weaknesses.
   * This is TOTAL hours, not per-week.
   */
  total_gap_hours: number;

  study_load_warning: string | null;

  /** Full effort breakdown — null if calculation failed. */
  effort_detail: EffortDetail | null;

  analysis_timestamp: string;
}

export interface ReadinessRequest {
  student_id: string;
  interests?: string[];
  electives?: string[];
  honours_minors?: string[];
}

export interface ReadinessSummary {
  student_id: string;
  overall_readiness: number;
  level: ReadinessLevel;
  can_proceed: boolean;
  critical_issues: boolean;
  primary_action: string;
  timestamp: string;
}

export interface PrerequisiteDetail {
  subject_name: string;
  subject_code?: string;
  current_score: number;
  required_score: number;
  gap: number;
  coverage_ratio: number;
  importance: number;
  importance_label: string;
  status: 'strong' | 'adequate' | 'weak' | 'missing';
  is_taken: boolean;
  confidence: number;
  low_confidence_flag: boolean;
}

export interface ElectiveReadiness {
  student_id: string;
  elective: string;
  elective_code?: string;
  readiness_score: number;
  readiness_level: string;
  is_ready: boolean;
  recommendation: string;
  prerequisites: PrerequisiteDetail[];
  strengths: string[];
  gaps: string[];
  subjects_to_focus: string[];
  preparation_plan: string[];
  preparation_time: string;
  estimated_preparation_weeks: number;
}

export interface HonoursReadiness {
  student_id: string;
  programme: string;
  readiness_score: number;
  is_eligible: boolean;
  recommendation: string;
  blockers: string[];
  preparation_time: string;
  detailed_steps: string[];
}

export interface InterestProfile {
  student_id: string;
  interests: string[];
  interest_levels: Record<string, number>;
  career_goals: string[];
  preferred_electives: string[];
  honours_minors_interest: string[];
  skills: string[];
  skill_levels: Record<string, number>;
}

export interface AvailableInterest {
  id: string;
  name: string;
  category: string;
}

export interface AvailableElective {
  code: string;
  name: string;
  credits: number;
  pair: number;
}

export interface AvailableHonours {
  id: string;
  name: string;
  type: 'honours' | 'minor';
  min_cgpa: number;
}

// ══════════════════════════════════════════════════════════════
//  SERVICE CLASS
// ══════════════════════════════════════════════════════════════

class WeaknessService {
  private api: AxiosInstance;
  private readinessApi: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/v1/weakness`,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });

    this.readinessApi = axios.create({
      baseURL: `${API_BASE_URL}/api/v1/readiness`,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });

    // Attach auth token to both clients
    [this.api, this.readinessApi].forEach(client => {
      client.interceptors.request.use(
        async config => {
          try {
            const currentUser = auth.currentUser;
            if (currentUser) {
              const token = await currentUser.getIdToken();
              if (token && config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
              }
              return config;
            }

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
        error => Promise.reject(error)
      );

      client.interceptors.response.use(
        response => response,
        error => {
          if (error.response?.status === 401) {
            console.error('Unauthorized');
          }
          const message =
            error.response?.data?.detail ||
            error.response?.data?.message ||
            error.message ||
            'An unexpected error occurred';
          return Promise.reject(new Error(message));
        }
      );
    });
  }

  // ── Weakness Analysis ────────────────────────────────────────

  async analyzeWeaknesses(
    request: WeaknessAnalysisRequest
  ): Promise<WeaknessAnalysisResponse> {
    const { data } = await this.api.post<WeaknessAnalysisResponse>(
      '/analyze',
      request
    );
    return data;
  }

  async getWeaknessByInterest(
    studentId: string,
    interests?: string[],
    includeResources = true,
    includeStudyPlan = true
  ): Promise<WeaknessAnalysisResponse> {
    const params: Record<string, any> = {
      include_resources: includeResources,
      include_study_plan: includeStudyPlan,
    };
    if (interests?.length) params.interests = interests.join(',');
    const { data } = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-interest`,
      { params }
    );
    return data;
  }

  async getWeaknessByElectives(
    studentId: string,
    electives?: string[],
    includeResources = true,
    includeStudyPlan = true
  ): Promise<WeaknessAnalysisResponse> {
    const params: Record<string, any> = {
      include_resources: includeResources,
      include_study_plan: includeStudyPlan,
    };
    if (electives?.length) params.electives = electives.join(',');
    const { data } = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-electives`,
      { params }
    );
    return data;
  }

  async getWeaknessByHonours(
    studentId: string,
    programmes?: string[],
    includeResources = true,
    includeStudyPlan = true
  ): Promise<WeaknessAnalysisResponse> {
    const params: Record<string, any> = {
      include_resources: includeResources,
      include_study_plan: includeStudyPlan,
    };
    if (programmes?.length) params.programmes = programmes.join(',');
    const { data } = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-honours`,
      { params }
    );
    return data;
  }

  async getWeaknessByPerformance(
    studentId: string,
    includeResources = true,
    includeStudyPlan = true
  ): Promise<WeaknessAnalysisResponse> {
    const { data } = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-performance`,
      {
        params: {
          include_resources: includeResources,
          include_study_plan: includeStudyPlan,
        },
      }
    );
    return data;
  }

  async getCombinedAnalysis(
    studentId: string,
    interests?: string[],
    electives?: string[],
    honours?: string[],
    includeResources = true,
    includeStudyPlan = true
  ): Promise<WeaknessAnalysisResponse> {
    const params: Record<string, any> = {
      include_resources: includeResources,
      include_study_plan: includeStudyPlan,
    };
    if (interests?.length) params.interests = interests.join(',');
    if (electives?.length) params.electives = electives.join(',');
    if (honours?.length) params.honours = honours.join(',');
    const { data } = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/combined`,
      { params }
    );
    return data;
  }

  async getLatestAnalysis(
    studentId: string
  ): Promise<WeaknessAnalysisResponse | null> {
    try {
      const { data } = await this.api.get(`/${studentId}/latest`);
      return data;
    } catch (error: any) {
      if (error.response?.status === 404) return null;
      throw error;
    }
  }

  async getAnalysisHistory(
    studentId: string,
    limit = 10
  ): Promise<any> {
    const { data } = await this.api.get(`/${studentId}/history`, {
      params: { limit },
    });
    return data;
  }

  async getWeaknessSummary(
    studentId: string
  ): Promise<WeaknessSummary> {
    const { data } = await this.api.get<WeaknessSummary>(
      `/${studentId}/summary`
    );
    return data;
  }

  // ── Readiness ────────────────────────────────────────────────

  async calculateReadiness(
    request: ReadinessRequest
  ): Promise<ReadinessResponse> {
    const { data } = await this.readinessApi.post<ReadinessResponse>(
      '/calculate',
      request
    );
    return data;
  }

  async getReadiness(
    studentId: string,
    interests?: string[],
    electives?: string[],
    honours?: string[]
  ): Promise<ReadinessResponse> {
    const params: Record<string, any> = {};
    if (interests?.length) params.interests = interests.join(',');
    if (electives?.length) params.electives = electives.join(',');
    if (honours?.length) params.honours = honours.join(',');

    const { data } = await this.readinessApi.get<ReadinessResponse>(
      `/${studentId}`,
      { params }
    );
    return data;
  }

  async getReadinessSummary(
    studentId: string
  ): Promise<ReadinessSummary> {
    const { data } = await this.readinessApi.get<ReadinessSummary>(
      `/${studentId}/summary`
    );
    return data;
  }

  async getElectiveReadiness(
    studentId: string,
    electiveCode: string
  ): Promise<ElectiveReadiness> {
    const { data } = await this.readinessApi.get<ElectiveReadiness>(
      `/${studentId}/for-elective/${electiveCode}`
    );
    return data;
  }

  async getHonoursReadiness(
    studentId: string,
    programme: string
  ): Promise<HonoursReadiness> {
    const { data } = await this.readinessApi.get<HonoursReadiness>(
      `/${studentId}/for-honours/${encodeURIComponent(programme)}`
    );
    return data;
  }

  // ── Interest Management ──────────────────────────────────────

  async saveInterests(
    studentId: string,
    interests: string[],
    careerGoals?: string[],
    skills?: string[],
    interestLevels?: Record<string, number>
  ): Promise<any> {
    const payload: Record<string, any> = {
      interests: interests || [],
      career_goals: careerGoals || [],
      skills: skills || [],
    };
    if (interestLevels && Object.keys(interestLevels).length > 0) {
      payload.interest_levels = interestLevels;
    }
    const { data } = await this.api.post(
      `/${studentId}/interests`,
      payload
    );
    return data;
  }

  async getInterests(studentId: string): Promise<InterestProfile> {
    try {
      const { data } = await this.api.get<InterestProfile>(
        `/${studentId}/interests`
      );
      return {
        student_id: data.student_id || studentId,
        interests: data.interests || [],
        interest_levels: data.interest_levels || {},
        career_goals: data.career_goals || [],
        preferred_electives: data.preferred_electives || [],
        honours_minors_interest: data.honours_minors_interest || [],
        skills: data.skills || [],
        skill_levels: data.skill_levels || {},
      };
    } catch (error: any) {
      if (error.response?.status === 404) {
        return {
          student_id: studentId,
          interests: [],
          interest_levels: {},
          career_goals: [],
          preferred_electives: [],
          honours_minors_interest: [],
          skills: [],
          skill_levels: {},
        };
      }
      throw error;
    }
  }

  async updateInterests(
    studentId: string,
    updates: Partial<Omit<InterestProfile, 'student_id'>>
  ): Promise<any> {
    const payload = {
      interests: updates.interests || [],
      career_goals: updates.career_goals || [],
      skills: updates.skills || [],
      interest_levels: updates.interest_levels || {},
      skill_levels: updates.skill_levels || {},
      preferred_electives: updates.preferred_electives || [],
      honours_minors_interest: updates.honours_minors_interest || [],
    };
    const { data } = await this.api.put(
      `/${studentId}/interests`,
      payload
    );
    return data;
  }

  async syncInterests(studentId: string): Promise<any> {
    const { data } = await this.api.get(
      `/${studentId}/sync-interests`
    );
    return data;
  }

  // ── Available Options ────────────────────────────────────────

  async getAvailableInterests(): Promise<AvailableInterest[]> {
    const { data } = await this.api.get<{
      interests: AvailableInterest[];
    }>('/options/interests');
    return data.interests;
  }

  async getAvailableElectives(): Promise<AvailableElective[]> {
    const { data } = await this.api.get<{
      electives: AvailableElective[];
    }>('/options/electives');
    return data.electives;
  }

  async getAvailableHonours(): Promise<AvailableHonours[]> {
    const { data } = await this.api.get<{
      programmes: AvailableHonours[];
    }>('/options/honours');
    return data.programmes;
  }
}

// ══════════════════════════════════════════════════════════════
//  SINGLETON
// ══════════════════════════════════════════════════════════════

let _instance: WeaknessService | null = null;

export const getWeaknessService = (): WeaknessService => {
  if (!_instance) _instance = new WeaknessService();
  return _instance;
};

export default WeaknessService;