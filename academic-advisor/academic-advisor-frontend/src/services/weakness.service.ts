// src/services/weakness.service.ts
import axios, { AxiosInstance } from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============== Types ==============

export type AnalysisBasis = 'interest' | 'electives' | 'honours_minors' | 'performance' | 'combined';
export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

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

export interface StudyPlan {
  duration: string;
  weekly_hours?: number;
  weekly_commitment?: string;
  focus_areas: Array<{
    topic: string;
    priority: number;
    current_score?: number;
    target_score?: number;
    weekly_hours?: number;
  }>;
  phases: Array<{
    name?: string;
    week?: string;
    weeks?: string;
    focus: string | string[];
    goals?: string[];
  }>;
  milestones: Array<{
    week: number;
    target: string;
  }>;
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

export interface InterestProfile {
  student_id: string;
  interests: string[];
  interest_levels: { [key: string]: number };
  career_goals: string[];
  preferred_electives: string[];
  honours_minors_interest: string[];
  skills: string[];
  skill_levels: { [key: string]: number };
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

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/v1/weakness`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      async (config) => {
        try {
          const currentUser = auth.currentUser;
          if (currentUser) {
            const token = await currentUser.getIdToken();
            if (token && config.headers) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          }
        } catch (error) {
          console.error('Failed to get auth token:', error);
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          console.error('Unauthorized - redirecting to login');
          // Handle unauthorized
        }
        return Promise.reject(error);
      }
    );
  }

  // ============== Analysis Methods ==============

  /**
   * Perform comprehensive weakness analysis
   */
  async analyzeWeaknesses(
    request: WeaknessAnalysisRequest
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const response = await this.api.post<WeaknessAnalysisResponse>('/analyze', request);
      return response.data;
    } catch (error) {
      console.error('Error analyzing weaknesses:', error);
      throw error;
    }
  }

  /**
   * Get weaknesses based on student interests
   */
  async getWeaknessByInterest(
    studentId: string,
    interests?: string[],
    includeResources: boolean = true,
    includeStudyPlan: boolean = true
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const params: any = {
        include_resources: includeResources,
        include_study_plan: includeStudyPlan,
      };

      if (interests && interests.length > 0) {
        params.interests = interests.join(',');
      }

      const response = await this.api.get<WeaknessAnalysisResponse>(
        `/${studentId}/by-interest`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting weakness by interest:', error);
      throw error;
    }
  }

  /**
   * Get weaknesses based on recommended electives
   */
  async getWeaknessByElectives(
    studentId: string,
    electives?: string[],
    includeResources: boolean = true,
    includeStudyPlan: boolean = true
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const params: any = {
        include_resources: includeResources,
        include_study_plan: includeStudyPlan,
      };

      if (electives && electives.length > 0) {
        params.electives = electives.join(',');
      }

      const response = await this.api.get<WeaknessAnalysisResponse>(
        `/${studentId}/by-electives`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting weakness by electives:', error);
      throw error;
    }
  }

  /**
   * Get weaknesses based on honours/minors
   */
  async getWeaknessByHonours(
    studentId: string,
    programmes?: string[],
    includeResources: boolean = true,
    includeStudyPlan: boolean = true
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const params: any = {
        include_resources: includeResources,
        include_study_plan: includeStudyPlan,
      };

      if (programmes && programmes.length > 0) {
        params.programmes = programmes.join(',');
      }

      const response = await this.api.get<WeaknessAnalysisResponse>(
        `/${studentId}/by-honours`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting weakness by honours:', error);
      throw error;
    }
  }

  /**
   * Get weaknesses based on academic performance only
   */
  async getWeaknessByPerformance(
    studentId: string,
    includeResources: boolean = true,
    includeStudyPlan: boolean = true
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const params = {
        include_resources: includeResources,
        include_study_plan: includeStudyPlan,
      };

      const response = await this.api.get<WeaknessAnalysisResponse>(
        `/${studentId}/by-performance`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting weakness by performance:', error);
      throw error;
    }
  }

  /**
   * Get combined weakness analysis (all factors)
   */
  async getCombinedAnalysis(
    studentId: string,
    interests?: string[],
    electives?: string[],
    honours?: string[],
    includeResources: boolean = true,
    includeStudyPlan: boolean = true
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const params: any = {
        include_resources: includeResources,
        include_study_plan: includeStudyPlan,
      };

      if (interests && interests.length > 0) {
        params.interests = interests.join(',');
      }
      if (electives && electives.length > 0) {
        params.electives = electives.join(',');
      }
      if (honours && honours.length > 0) {
        params.honours = honours.join(',');
      }

      const response = await this.api.get<WeaknessAnalysisResponse>(
        `/${studentId}/combined`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting combined analysis:', error);
      throw error;
    }
  }

  /**
   * Get latest cached analysis
   */
  async getLatestAnalysis(studentId: string): Promise<any> {
    try {
      const response = await this.api.get(`/${studentId}/latest`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null; // No analysis found
      }
      console.error('Error getting latest analysis:', error);
      throw error;
    }
  }

  /**
   * Get analysis history
   */
  async getAnalysisHistory(
    studentId: string,
    limit: number = 10
  ): Promise<any> {
    try {
      const response = await this.api.get(`/${studentId}/history`, {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error('Error getting analysis history:', error);
      throw error;
    }
  }

  /**
   * Get weakness summary (lightweight)
   */
  async getWeaknessSummary(
    studentId: string
  ): Promise<WeaknessSummary> {
    try {
      const response = await this.api.get<WeaknessSummary>(
        `/${studentId}/summary`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting weakness summary:', error);
      throw error;
    }
  }

  // ============== Interest Management ==============

  /**
   * Save student interests
   */
  async saveInterests(
    studentId: string,
    interests: string[],
    interestLevels?: { [key: string]: number }
  ): Promise<any> {
    try {
      const response = await this.api.post(`/${studentId}/interests`, {
        interests,
        interest_levels: interestLevels,
      });
      return response.data;
    } catch (error) {
      console.error('Error saving interests:', error);
      throw error;
    }
  }

  /**
   * Get student interests
   */
  async getInterests(studentId: string): Promise<InterestProfile> {
    try {
      const response = await this.api.get<InterestProfile>(
        `/${studentId}/interests`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting interests:', error);
      throw error;
    }
  }

  /**
   * Update student interests (partial update)
   */
  async updateInterests(
    studentId: string,
    updates: Partial<Omit<InterestProfile, 'student_id'>>
  ): Promise<any> {
    try {
      const response = await this.api.put(`/${studentId}/interests`, updates);
      return response.data;
    } catch (error) {
      console.error('Error updating interests:', error);
      throw error;
    }
  }

  // ============== Available Options ==============

  /**
   * Get available interests for selection
   */
  async getAvailableInterests(): Promise<AvailableInterest[]> {
    try {
      const response = await this.api.get<{ interests: AvailableInterest[] }>(
        '/options/interests'
      );
      return response.data.interests;
    } catch (error) {
      console.error('Error getting available interests:', error);
      throw error;
    }
  }

  /**
   * Get available electives
   */
  async getAvailableElectives(): Promise<AvailableElective[]> {
    try {
      const response = await this.api.get<{ electives: AvailableElective[] }>(
        '/options/electives'
      );
      return response.data.electives;
    } catch (error) {
      console.error('Error getting available electives:', error);
      throw error;
    }
  }

  /**
   * Get available honours/minors
   */
  async getAvailableHonours(): Promise<AvailableHonours[]> {
    try {
      const response = await this.api.get<{ programmes: AvailableHonours[] }>(
        '/options/honours'
      );
      return response.data.programmes;
    } catch (error) {
      console.error('Error getting available honours:', error);
      throw error;
    }
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