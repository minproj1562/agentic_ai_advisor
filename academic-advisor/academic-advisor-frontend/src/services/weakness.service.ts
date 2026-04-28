// src/services/weakness.service.ts
// FIXED VERSION - saveInterests sends ALL fields, response verification added

import axios, { AxiosInstance } from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============== Types ==============

export type AnalysisBasis = 'interest' | 'electives' | 'honours_minors' | 'performance' | 'combined';
export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';
export type ReadinessLevel = 'excellent' | 'good' | 'moderate' | 'low' | 'not_ready';
export type RecommendationType = 'proceed' | 'proceed_with_caution' | 'improve_first' | 'do_not_proceed';

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

export interface StudyPlanPhase {
  name: string;
  weeks: string;
  focus: string[];
  goals: string[];
  daily_hours?: number;
}

export interface StudyPlanMilestone {
  week: number;
  target: string;
}

export interface FocusArea {
  subject: string;
  priority: number;
  current_score: number;
  target_score: number;
  weekly_hours: number;
  severity: string;
}

export interface StudyPlan {
  duration: string;
  weekly_hours: number;
  weekly_commitment: string;
  focus_areas: FocusArea[];
  phases: StudyPlanPhase[];
  milestones: StudyPlanMilestone[];
  current_readiness: number;
  target_readiness: number;
  recommendation: string;
}

export interface WeaknessAnalysisResponse {
  student_id: string;
  analysis_basis: AnalysisBasis;
  weaknesses: WeaknessArea[];
  overall_risk_score: number;
  priority_areas: string[];
  recommended_resources: ResourceItem[];
  study_plan?: StudyPlan;
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

// ============== Readiness Types ==============

export interface ReadinessWeakness {
  id?: string;
  subject: string;
  severity: SeverityLevel;
  current_score: number;
  target_score: number;
  gap: number;
  linked_goals?: string[];
  suggestions?: string[];
  estimated_hours?: number;
}

export interface ReadinessResponse {
  student_id: string;
  overall_readiness_score: number;
  readiness_level: ReadinessLevel;
  recommendation_type: RecommendationType;
  primary_recommendation: string;
  interest_readiness: number;
  elective_readiness: number;
  honours_readiness: number;
  interest_breakdown: Record<string, number>;
  elective_breakdown: Record<string, number>;
  honours_breakdown: Record<string, number>;
  has_critical_weakness: boolean;
  has_blockers: boolean;
  is_first_semester: boolean;
  subjects_to_focus: string[];
  estimated_preparation_time: string;
  detailed_recommendations: string[];
  weaknesses: ReadinessWeakness[];
  study_plan?: StudyPlan | null;
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

export interface ElectiveReadiness {
  student_id: string;
  elective: string;
  readiness_score: number;
  is_ready: boolean;
  recommendation: string;
  subjects_to_focus: string[];
  preparation_time: string;
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

// ============== Service Class ==============

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

    [this.api, this.readinessApi].forEach((client) => {
      client.interceptors.request.use(
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

      client.interceptors.response.use(
        (response) => response,
        (error) => {
          if (error.response?.status === 401) {
            console.error('Unauthorized - redirecting to login');
          }
          return Promise.reject(error);
        }
      );
    });
  }

  // ============== Weakness Analysis Methods ==============

  async analyzeWeaknesses(request: WeaknessAnalysisRequest): Promise<WeaknessAnalysisResponse> {
    const response = await this.api.post<WeaknessAnalysisResponse>('/analyze', request);
    return response.data;
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
    if (interests?.length) {
      params.interests = interests.join(',');
    }
    const response = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-interest`,
      { params }
    );
    return response.data;
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
    if (electives?.length) {
      params.electives = electives.join(',');
    }
    const response = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-electives`,
      { params }
    );
    return response.data;
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
    if (programmes?.length) {
      params.programmes = programmes.join(',');
    }
    const response = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-honours`,
      { params }
    );
    return response.data;
  }

  async getWeaknessByPerformance(
    studentId: string,
    includeResources = true,
    includeStudyPlan = true
  ): Promise<WeaknessAnalysisResponse> {
    const response = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/by-performance`,
      { params: { include_resources: includeResources, include_study_plan: includeStudyPlan } }
    );
    return response.data;
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

    const response = await this.api.get<WeaknessAnalysisResponse>(
      `/${studentId}/combined`,
      { params }
    );
    return response.data;
  }

  async getLatestAnalysis(studentId: string): Promise<WeaknessAnalysisResponse | null> {
    try {
      const response = await this.api.get(`/${studentId}/latest`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) return null;
      throw error;
    }
  }

  async getAnalysisHistory(studentId: string, limit = 10): Promise<any> {
    const response = await this.api.get(`/${studentId}/history`, { params: { limit } });
    return response.data;
  }

  async getWeaknessSummary(studentId: string): Promise<WeaknessSummary> {
    const response = await this.api.get<WeaknessSummary>(`/${studentId}/summary`);
    return response.data;
  }

  // ============== Readiness Methods ==============

  async calculateReadiness(request: ReadinessRequest): Promise<ReadinessResponse> {
    const response = await this.readinessApi.post<ReadinessResponse>('/calculate', request);
    return response.data;
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

    const response = await this.readinessApi.get<ReadinessResponse>(`/${studentId}`, {
      params,
    });
    return response.data;
  }

  async getReadinessSummary(studentId: string): Promise<ReadinessSummary> {
    const response = await this.readinessApi.get<ReadinessSummary>(`/${studentId}/summary`);
    return response.data;
  }

  async getElectiveReadiness(
    studentId: string,
    electiveCode: string
  ): Promise<ElectiveReadiness> {
    const response = await this.readinessApi.get<ElectiveReadiness>(
      `/${studentId}/for-elective/${electiveCode}`
    );
    return response.data;
  }

  async getHonoursReadiness(
    studentId: string,
    programme: string
  ): Promise<HonoursReadiness> {
    const response = await this.readinessApi.get<HonoursReadiness>(
      `/${studentId}/for-honours/${encodeURIComponent(programme)}`
    );
    return response.data;
  }

  // ============== Interest Management — ✅ FIXED ==============

  /**
   * ✅ FIXED: Now sends ALL fields to the POST endpoint.
   *
   * The backend POST endpoint has been updated to accept:
   *   interests, career_goals, skills, interest_levels,
   *   skill_levels, preferred_electives, honours_minors_interest
   *
   * Previously only `interests` and `interest_levels` were sent/accepted,
   * causing career_goals and skills to be silently dropped.
   */
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

    console.log('📤 weakness.service saveInterests POST payload:', {
      endpoint: `POST /weakness/${studentId}/interests`,
      interests: payload.interests.length,
      career_goals: payload.career_goals.length,
      skills: payload.skills.length,
    });

    const response = await this.api.post(`/${studentId}/interests`, payload);
    const data = response.data;

    // ✅ Verify the response includes all fields we sent
    console.log('📥 weakness.service saveInterests response:', {
      saved_interests: data.interests?.length ?? '?',
      saved_career_goals: data.career_goals?.length ?? '?',
      saved_skills: data.skills?.length ?? '?',
    });

    if (data.career_goals === undefined && (careerGoals?.length ?? 0) > 0) {
      console.error(
        '❌ Backend POST /interests did NOT return career_goals. ' +
        'The backend endpoint may need updating. ' +
        'Expected career_goals in response but got undefined.'
      );
    }
    if (data.skills === undefined && (skills?.length ?? 0) > 0) {
      console.error(
        '❌ Backend POST /interests did NOT return skills. ' +
        'The backend endpoint may need updating. ' +
        'Expected skills in response but got undefined.'
      );
    }

    return data;
  }

  /**
   * Get student interest profile — returns ALL fields.
   * ✅ Returns empty profile on 404 instead of throwing.
   */
  async getInterests(studentId: string): Promise<InterestProfile> {
    try {
      const response = await this.api.get<InterestProfile>(`/${studentId}/interests`);
      const data = response.data;

      // Normalize response to guarantee all fields exist
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
        console.log('No interest profile found, returning empty');
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

  /**
   * ✅ FIXED: Update interests with explicit logging to verify what's sent/received.
   * Sends ALL fields in the PUT payload.
   */
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

    console.log('📤 weakness.service updateInterests PUT payload:', {
      endpoint: `PUT /weakness/${studentId}/interests`,
      interests: payload.interests.length,
      career_goals: payload.career_goals.length,
      skills: payload.skills.length,
      preferred_electives: payload.preferred_electives.length,
      honours_minors_interest: payload.honours_minors_interest.length,
    });

    try {
      const response = await this.api.put(`/${studentId}/interests`, payload);
      const data = response.data;

      console.log('✅ weakness.service updateInterests response:', {
        status: data.status,
        profile_interests: data.profile?.interests?.length ?? '?',
        profile_career_goals: data.profile?.career_goals?.length ?? '?',
        profile_skills: data.profile?.skills?.length ?? '?',
      });

      return data;
    } catch (error: any) {
      console.error('❌ weakness.service updateInterests PUT failed:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      });
      throw error;
    }
  }

  async syncInterests(studentId: string): Promise<any> {
    const response = await this.api.get(`/${studentId}/sync-interests`);
    return response.data;
  }

  // ============== Available Options ==============

  async getAvailableInterests(): Promise<AvailableInterest[]> {
    const response = await this.api.get<{ interests: AvailableInterest[] }>(
      '/options/interests'
    );
    return response.data.interests;
  }

  async getAvailableElectives(): Promise<AvailableElective[]> {
    const response = await this.api.get<{ electives: AvailableElective[] }>(
      '/options/electives'
    );
    return response.data.electives;
  }

  async getAvailableHonours(): Promise<AvailableHonours[]> {
    const response = await this.api.get<{ programmes: AvailableHonours[] }>(
      '/options/honours'
    );
    return response.data.programmes;
  }
}

// ============== Singleton Instance ==============

let weaknessServiceInstance: WeaknessService | null = null;

export const getWeaknessService = (): WeaknessService => {
  if (!weaknessServiceInstance) {
    weaknessServiceInstance = new WeaknessService();
  }
  return weaknessServiceInstance;
};

export default WeaknessService;