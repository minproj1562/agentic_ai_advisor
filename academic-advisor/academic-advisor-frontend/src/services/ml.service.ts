// src/services/ml.service.ts

import { auth } from './firebase.config';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// ==================== INTERFACES ====================

export interface StudentAcademicData {
  current_cgpa: number;
  attendance_percentage: number;
  assignment_completion_ratio: number;
  study_hours_per_week: number;
  extracurricular_activities: string[];
}

export interface SubjectScore {
  subject_name: string;
  subject_code: string;
  credits: number;
  internal_marks: number;
  external_marks: number;
  total_marks: number;
  grade: string;
  is_practical: boolean;
}

export interface PredictionResponse {
  status: string;
  predictions: {
    next_semester_gpa: number;
    risk_level: 'Low' | 'Medium' | 'High';
    risk_probability: number;
    expected_graduation_cgpa: number;
    improvement_potential: number;
    confidence_score: number;
  };
  trend_analysis: {
    trend: 'improving' | 'stable' | 'declining';
    average_gpa?: number;
    best_semester?: number;
    worst_semester?: number;
    trend_coefficient?: number;
  };
  risk_factors: string[];
  recommendations: string[];
}

export interface WeaknessData {
  subject: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  average_score: number;
  gap: number;
  trend: string;
  topics: string[];
  improvement_plan: {
    duration: string;
    daily_hours: number;
    focus_areas: string[];
    milestones: any[];
  };
  resources: any[];
}

export interface WeaknessAnalysisResponse {
  status: string;
  analysis: {
    overall_performance: string;
    weaknesses: WeaknessData[];
    priority_subjects: any[];
    success_probability: number;
    cgpa_improvement_needed: number;
    estimated_effort_hours: number;
    study_plan: {
      weekly_hours: number;
      daily_hours: number;
      focus_distribution: Record<string, string>;
      recommended_resources: string[];
    };
  };
}

export interface CareerPath {
  title: string;
  match_score: number;
  source_domains: string[];
  required_skills: string[];
  honours_program: string | null;
  market_demand: string;
  salary_range: string;
  growth_potential: string;
  preparation_path: string[];
  companies_hiring: string[];
}

export interface CareerPredictionResponse {
  recommended_careers: Array<{
    career: string;
    match_score: number;
    salary_range: string;
    growth_potential: string;
    cgpa_eligible: boolean;
    top_companies: string[];
    missing_skills: string[];
    preparation_path: string[];
    required_certifications: string[];
  }>;
  skill_development_priority: string[];
  internship_recommendations: Array<{
    role: string;
    duration: string;
    skills_to_gain: string[];
    application_tip: string;
  }>;
}

export interface InterestProfile {
  declared_interests: string[];
  career_goals: string[];
  skills: string[];
  topDomains: Array<{
    name: string;
    strength: number;
    projectCount: number;
    relatedSkills: string[];
    careerPaths: string[];
  }>;
  recommendations: {
    electives: any[];
    honours_programs: any[];
    career_paths: any[];
  };
  profile_completeness: number;
}

export interface ProjectAnalysisResult {
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
    reasons: string[];
    courses: string[];
    career_paths: string[];
    credits: number;
    semester_commitment: string;
  }>;
  career_paths: CareerPath[];
  skill_gap_analysis: {
    current_skills: string[];
    skill_gaps: string[];
    priority_skills: string[];
    learning_resources: Record<string, any[]>;
    completeness_percentage: number;
    estimated_learning_time: string;
  };
  next_steps: Array<{
    priority: string;
    category: string;
    action: string;
    details: string;
    deadline: string;
  }>;
  metadata: {
    analysis_date: string;
    student_branch: string;
    student_semester: number;
    confidence_score: number;
  };
}

export interface AcademicRecommendations {
  weaknesses: WeaknessData[];
  curriculum_recommendations: {
    immediate_actions: any[];
    elective_suggestions: any[];
    honours_minor_eligibility: any;
    focus_areas: any[];
  };
  interest_based_recommendations: any[];
  student_info: {
    name: string;
    branch: string;
    semester: number;
    cgpa: number;
  };
  curriculum_info: any;
}

export interface ComprehensiveStudentAnalysis {
  studentId: string;
  timestamp: string;
  performanceMetrics: {
    cgpa: number;
    sgpa: number[];
    attendanceRate: number;
    assignmentCompletionRate: number;
    subjectWisePerformance: any[];
    strengthAreas: string[];
    weaknessAreas: string[];
    performanceTrend: string;
    predictedCGPA: number;
    riskLevel: string;
  };
  careerInsights: any[];
  personalizedRecommendations: {
    immediateActions: any[];
    shortTermGoals: any[];
    longTermGoals: any[];
    skillDevelopmentPlan: any[];
    mentorshipSuggestions: any[];
    networkingOpportunities: any[];
  };
  projectAnalysis: any;
  peerComparison: any;
  futureProjections: any;
}

// ==================== ML SERVICE CLASS ====================

class MLService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = BACKEND_URL;
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = await auth.currentUser?.getIdToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // ==================== COMPREHENSIVE ANALYSIS ====================

  async getComprehensiveAnalysis(
    studentId: string,
    includeTrends: boolean = true,
    includeComparisons: boolean = true,
    includeInterests: boolean = true
  ): Promise<ComprehensiveStudentAnalysis> {
    try {
      const headers = await this.getAuthHeaders();
      
      const params = new URLSearchParams({
        include_trends: includeTrends.toString(),
        include_comparisons: includeComparisons.toString(),
        include_interests: includeInterests.toString()
      });

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/comprehensive-analysis?${params}`,
        { headers }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch comprehensive analysis');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error fetching comprehensive analysis:', error);
      throw error;
    }
  }

  // ==================== ACADEMIC RECOMMENDATIONS ====================

  async getAcademicRecommendations(): Promise<AcademicRecommendations> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/academic-recommendations`,
        { headers }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch academic recommendations');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error fetching academic recommendations:', error);
      throw error;
    }
  }

  // ==================== INTEREST MANAGEMENT ====================

  async getInterestProfile(): Promise<InterestProfile> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/interests`,
        { headers }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch interest profile');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error fetching interest profile:', error);
      throw error;
    }
  }

  async updateInterests(
    interests: string[],
    careerGoals?: string[],
    skills?: string[]
  ): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/interests/update`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            interests,
            career_goals: careerGoals,
            skills
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update interests');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating interests:', error);
      throw error;
    }
  }

  // ==================== PREDICTIONS ====================

  async getPredictions(
    studentId: string,
    academicData: StudentAcademicData,
    historicalScores: Array<{ semester: number; gpa: number; credits: number }>,
    currentSemester: number
  ): Promise<PredictionResponse> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/predict-performance`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            currentGrades: {},
            attendance: academicData.attendance_percentage,
            projectCount: 0,
            studyHours: academicData.study_hours_per_week,
            extracurricular: academicData.extracurricular_activities
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch predictions');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching predictions:', error);
      throw error;
    }
  }

  // ==================== WEAKNESS ANALYSIS ====================

  async analyzeWeaknesses(
    studentId: string,
    subjectScores: SubjectScore[],
    currentCgpa: number
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/academic-recommendations`,
        { headers }
      );

      if (!response.ok) {
        throw new Error('Failed to analyze weaknesses');
      }

      const data = await response.json();
      
      return {
        status: 'success',
        analysis: {
          overall_performance: data.data.student_info.cgpa >= 7.5 ? 'good' : 
                               data.data.student_info.cgpa >= 6.0 ? 'average' : 'needs_improvement',
          weaknesses: data.data.weaknesses || [],
          priority_subjects: data.data.weaknesses?.slice(0, 3) || [],
          success_probability: 0.75,
          cgpa_improvement_needed: Math.max(0, 7.5 - data.data.student_info.cgpa),
          estimated_effort_hours: 100,
          study_plan: {
            weekly_hours: 20,
            daily_hours: 3,
            focus_distribution: {},
            recommended_resources: []
          }
        }
      };
    } catch (error) {
      console.error('Error analyzing weaknesses:', error);
      throw error;
    }
  }

  // ==================== CAREER PREDICTIONS ====================

  async predictCareer(
    studentId: string,
    skills: string[],
    interests: string[],
    cgpa: number,
    projects: string[]
  ): Promise<CareerPredictionResponse> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/career-path-analysis`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            skills,
            interests,
            academicPerformance: { cgpa },
            careerGoals: []
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to predict career');
      }

      const data = await response.json();
      return data.career_insights;
    } catch (error) {
      console.error('Error predicting career:', error);
      throw error;
    }
  }

  // ==================== ELECTIVE RECOMMENDATIONS ====================

  async getElectiveRecommendations(semester?: number): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();

      const url = semester 
        ? `${this.baseUrl}/api/v1/ml/elective-recommendations?semester=${semester}`
        : `${this.baseUrl}/api/v1/ml/elective-recommendations`;

      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Failed to fetch elective recommendations');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching elective recommendations:', error);
      throw error;
    }
  }

  // ==================== HONOURS/MINOR ELIGIBILITY ====================

  async checkHonoursEligibility(): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();

      const response = await fetch(
        `${this.baseUrl}/api/v1/ml/honours-minor-eligibility`,
        { headers }
      );

      if (!response.ok) {
        throw new Error('Failed to check honours eligibility');
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking honours eligibility:', error);
      throw error;
    }
  }

  // ==================== PROJECT ANALYSIS ====================

  async analyzeProjectComprehensive(
    projectData: any,
    files: File[] = []
  ): Promise<ProjectAnalysisResult> {
    try {
      const token = await auth.currentUser?.getIdToken();
      
      const formData = new FormData();
      formData.append('project_data', JSON.stringify(projectData));
      
      // Get student branch and semester from localStorage
      const branch = localStorage.getItem('userBranch') || 'IT';
      const semester = parseInt(localStorage.getItem('userSemester') || '5');
      
      formData.append('student_branch', branch);
      formData.append('student_semester', semester.toString());
      
      // Add files if any
      files.forEach((file, index) => {
        formData.append('files', file);
      });

      const response = await fetch(
        `${this.baseUrl}/api/v1/projects/analyze-comprehensive`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error('Failed to analyze project');
      }

      const data = await response.json();
      return data.analysis;
    } catch (error) {
      console.error('Error analyzing project:', error);
      throw error;
    }
  }

  // ==================== CAREER GUIDANCE ====================

  async getCareerGuidance(interests?: any[]): Promise<any> {
    try {
      const token = await auth.currentUser?.getIdToken();
      
      const formData = new FormData();
      const branch = localStorage.getItem('userBranch') || 'IT';
      formData.append('student_branch', branch);

      const response = await fetch(
        `${this.baseUrl}/api/v1/projects/career-guidance`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get career guidance');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting career guidance:', error);
      throw error;
    }
  }
}

export const mlService = new MLService();
export default mlService;