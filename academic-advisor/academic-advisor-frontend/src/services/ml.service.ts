// src/services/ml.service.ts
import { auth } from './firebase.config';

// ======================== BASIC TYPE DEFINITIONS ========================

export interface StudentAcademicData {
  current_cgpa: number;
  attendance_percentage: number;
  assignment_completion_ratio: number;
  study_hours_per_week: number;
  extracurricular_activities: string[];
}

export interface SubjectScore {
  subject_code: string;
  subject_name: string;
  credits: number;
  internal_marks: number;
  external_marks: number;
  total_marks: number;
  grade: string;
  semester: number;
}

export interface PredictionRequest {
  student_id: string;
  academic_data: StudentAcademicData;
  historical_scores: Array<{
    semester: number;
    gpa: number;
    credits: number;
  }>;
  current_semester: number;
  subject_scores?: SubjectScore[];
}

export interface PredictionResponse {
  student_id: string;
  predictions: {
    next_semester_gpa: number;
    confidence_score: number;
    risk_level: 'Low' | 'Medium' | 'High';
    risk_probability: number;
    expected_graduation_cgpa: number;
    improvement_potential: number;
  };
  risk_factors: string[];
  recommendations: string[];
  trend_analysis: {
    trend: 'improving' | 'declining' | 'stable' | 'insufficient_data';
    trend_coefficient?: number;
    average_gpa?: number;
    best_semester?: number;
    worst_semester?: number;
  };
  generated_at: string;
}

export interface WeaknessAnalysisRequest {
  student_id: string;
  subject_scores: SubjectScore[];
  target_cgpa: number;
}

export interface WeaknessDetail {
  subject: string;
  marks: number;
  credits: number;
  performance: string;
  gap: number;
  topics: string[];
  improvement_strategy: string[];
}

export interface WeaknessAnalysisResponse {
  student_id: string;
  analysis: {
    weaknesses: WeaknessDetail[];
    strengths: Array<{
      subject: string;
      marks: number;
      performance: string;
    }>;
    overall_performance: string;
    priority_subjects: WeaknessDetail[];
    study_plan: {
      weekly_hours: number;
      daily_hours: number;
      focus_distribution: Record<string, string>;
      recommended_resources: string[];
    };
    cgpa_improvement_needed: number;
    estimated_effort_hours: number;
    success_probability: number;
  };
  generated_at: string;
}

export interface CareerPredictionRequest {
  student_id: string;
  skills: string[];
  interests: string[];
  cgpa: number;
  projects: string[];
  internships: string[];
}

export interface CareerPath {
  career: string;
  match_score: number;
  skill_match: number;
  cgpa_eligible: boolean;
  missing_skills: string[];
  salary_range: string;
  growth_potential: string;
  preparation_path: string[];
  industry_demand: string;
  required_certifications: string[];
  top_companies: string[];
}

export interface CareerPredictionResponse {
  student_id: string;
  recommended_careers: CareerPath[];
  skill_development_priority: string[];
  internship_recommendations: Array<{
    role: string;
    duration: string;
    skills_to_gain: string[];
    min_cgpa_required: string;
    application_tip: string;
  }>;
  generated_at: string;
}

// ======================== ADVANCED ML TYPES ========================

export interface StudentPerformanceMetrics {
  cgpa: number;
  sgpa: number[];
  attendanceRate: number;
  assignmentCompletionRate: number;
  subjectWisePerformance: SubjectPerformance[];
  strengthAreas: string[];
  weaknessAreas: string[];
  performanceTrend: 'improving' | 'stable' | 'declining';
  predictedCGPA: number;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface SubjectPerformance {
  subjectName: string;
  grade: string;
  score: number;
  difficulty: number;
  improvement: number;
  recommendations: string[];
}

export interface AICareerInsight {
  domain: string;
  matchScore: number;
  requiredSkills: Skill[];
  currentSkillGap: number;
  recommendedCourses: Course[];
  industryDemand: number;
  salaryRange: { min: number; max: number; median: number };
  topCompanies: Company[];
  preparationRoadmap: RoadmapStep[];
}

export interface Skill {
  name: string;
  currentLevel: number;
  requiredLevel: number;
  importance: number;
  learningResources: Resource[];
}

export interface Course {
  courseId: string;
  courseName: string;
  faculty: FacultyRecommendation;
  relevance: number;
  difficulty: number;
  prerequisites: string[];
  expectedOutcome: string;
  careerImpact: number;
}

export interface FacultyRecommendation {
  facultyId: string;
  name: string;
  rating: number;
  teachingStyle: string;
  expertise: string[];
  studentFeedbackScore: number;
  successRate: number;
}

export interface Company {
  name: string;
  sector: string;
  hiringProbability: number;
  requiredCGPA: number;
  preferredSkills: string[];
}

export interface RoadmapStep {
  semester: number;
  courses: string[];
  skills: string[];
  projects: string[];
  certifications: string[];
  internships: string[];
  milestone: string;
}

export interface ComprehensiveStudentAnalysis {
  studentId: string;
  timestamp: string;
  performanceMetrics: StudentPerformanceMetrics;
  careerInsights: AICareerInsight[];
  personalizedRecommendations: PersonalizedRecommendations;
  projectAnalysis: ProjectPortfolioAnalysis;
  peerComparison: PeerComparisonMetrics;
  futureProjections: FutureProjections;
}

export interface PersonalizedRecommendations {
  immediateActions: Action[];
  shortTermGoals: Goal[];
  longTermGoals: Goal[];
  skillDevelopmentPlan: SkillPlan[];
  mentorshipSuggestions: Mentor[];
  networkingOpportunities: NetworkEvent[];
}

export interface ProjectPortfolioAnalysis {
  totalProjects: number;
  domainDistribution: { [key: string]: number };
  skillCoverage: number;
  innovationScore: number;
  industryRelevance: number;
  portfolioStrength: number;
  missingAreas: string[];
  suggestedProjects: SuggestedProject[];
}

export interface PeerComparisonMetrics {
  percentile: number;
  averageCGPA: number;
  yourPosition: number;
  totalStudents: number;
  strengths: string[];
  areasToImprove: string[];
  topPerformers: StudentProfile[];
}

export interface FutureProjections {
  expectedGraduation: GraduationProjection;
  placementProbability: number;
  expectedPackageRange: { min: number; max: number };
  topMatchingCompanies: Company[];
  preparednessScore: number;
  timeToReadiness: number; // months
}

interface Weakness {
  area: string;
  severity: number;
  impact: string;
  suggestedActions: string[];
}

interface ImprovementStep {
  step: number;
  action: string;
  duration: number;
  resources: string[];
  expectedOutcome: string;
}

interface Action {
  priority: 'high' | 'medium' | 'low';
  action: string;
  deadline: string;
  impact: number;
  effort: number;
}

interface Goal {
  goal: string;
  timeline: string;
  milestones: string[];
  success_criteria: string;
}

interface SkillPlan {
  skill: string;
  currentLevel: number;
  targetLevel: number;
  learningPath: string[];
  estimatedTime: number;
}

interface Mentor {
  name: string;
  expertise: string[];
  matchScore: number;
  availability: string;
}

interface NetworkEvent {
  event: string;
  date: string;
  relevance: number;
  expectedBenefit: string;
}

interface SuggestedProject {
  title: string;
  domain: string;
  technologies: string[];
  difficulty: number;
  careerImpact: number;
  estimatedDuration: number;
}

interface StudentProfile {
  name: string;
  cgpa: number;
  projects: number;
  achievements: string[];
}

interface GraduationProjection {
  expectedCGPA: number;
  confidence: number;
  risks: string[];
  opportunities: string[];
}

interface DailyPlan {
  day: string;
  subjects: { subject: string; hours: number; topics: string[] }[];
  breaks: string[];
  revision: string[];
}

interface FocusArea {
  area: string;
  priority: number;
  currentScore: number;
  targetScore: number;
  strategies: string[];
}

interface Resource {
  type: 'video' | 'article' | 'book' | 'course' | 'tutorial';
  title: string;
  url: string;
  duration: string;
  difficulty: number;
  rating: number;
}

// ======================== ML SERVICE CLASS ========================

class MLService {
  private baseUrl: string;
  private advancedBaseURL = '/api/v1/ml';

  constructor() {
    // Use environment variable or fallback to localhost
    this.baseUrl = import.meta.env?.VITE_ML_SERVER_URL || 'http://localhost:5001';
  }

  private async getAuthToken(): Promise<string> {
    const token = await auth.currentUser?.getIdToken();
    if (!token) throw new Error('No authentication token available');
    return token;
  }

  // Add this helper method for API calls
  private async makeAPICall(endpoint: string, options: RequestInit = {}) {
    const token = await this.getAuthToken();
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return response.json();
  }

  // ======================== BASIC ML METHODS ========================

  // Get GPA predictions and risk assessment
  async getPredictions(
    studentId: string,
    academicData: StudentAcademicData,
    historicalScores: Array<{ semester: number; gpa: number; credits: number }>,
    currentSemester: number
  ): Promise<PredictionResponse> {
    try {
      const token = await this.getAuthToken();
      
      const response = await fetch(`${this.baseUrl}/api/v1/predictions/${studentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          student_id: studentId,
          academic_data: academicData,
          historical_scores: historicalScores,
          current_semester: currentSemester
        })
      });

      if (!response.ok) {
        throw new Error(`Prediction failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting predictions:', error);
      
      // Return mock data if ML server is down
      return this.getMockPredictions(studentId, academicData, historicalScores, currentSemester);
    }
  }

  // Mock predictions for when ML server is unavailable
  private getMockPredictions(
    studentId: string,
    academicData: StudentAcademicData,
    historicalScores: Array<{ semester: number; gpa: number; credits: number }>,
    currentSemester: number
  ): PredictionResponse {
    const avgGpa = historicalScores.reduce((sum, score) => sum + score.gpa, 0) / historicalScores.length;
    const nextGpa = Math.min(10, Math.max(6, avgGpa + (Math.random() - 0.5)));
    
    return {
      student_id: studentId,
      predictions: {
        next_semester_gpa: parseFloat(nextGpa.toFixed(2)),
        confidence_score: 0.7,
        risk_level: nextGpa < 7 ? 'High' : nextGpa < 8 ? 'Medium' : 'Low',
        risk_probability: nextGpa < 7 ? 0.8 : nextGpa < 8 ? 0.5 : 0.2,
        expected_graduation_cgpa: parseFloat((avgGpa * 0.8 + nextGpa * 0.2).toFixed(2)),
        improvement_potential: parseFloat((1 - (nextGpa / 10)).toFixed(2))
      },
      risk_factors: [
        "Consistency in performance needed",
        "Focus on core subjects required"
      ],
      recommendations: [
        "Create a study schedule and stick to it",
        "Seek help for difficult subjects early",
        "Participate in group study sessions"
      ],
      trend_analysis: {
        trend: nextGpa > avgGpa ? 'improving' : 'declining',
        trend_coefficient: nextGpa - avgGpa,
        average_gpa: parseFloat(avgGpa.toFixed(2)),
        best_semester: Math.max(...historicalScores.map(s => s.gpa)),
        worst_semester: Math.min(...historicalScores.map(s => s.gpa))
      },
      generated_at: new Date().toISOString()
    };
  }

  // Analyze subject weaknesses
  async analyzeWeaknesses(
    studentId: string,
    subjectScores: SubjectScore[],
    targetCgpa: number = 8.0
  ): Promise<WeaknessAnalysisResponse> {
    try {
      const token = await this.getAuthToken();
      
      const response = await fetch(`${this.baseUrl}/api/v1/weakness-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          student_id: studentId,
          subject_scores: subjectScores,
          target_cgpa: targetCgpa
        })
      });

      if (!response.ok) {
        throw new Error(`Weakness analysis failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error analyzing weaknesses:', error);
      return this.getMockWeaknessAnalysis(studentId, subjectScores, targetCgpa);
    }
  }

  // Mock weakness analysis
  private getMockWeaknessAnalysis(
    studentId: string,
    subjectScores: SubjectScore[],
    targetCgpa: number
  ): WeaknessAnalysisResponse {
    const weaknesses = subjectScores
      .filter(score => score.total_marks < 70)
      .map(score => ({
        subject: score.subject_name,
        marks: score.total_marks,
        credits: score.credits,
        performance: score.total_marks < 50 ? 'Poor' : 'Needs Improvement',
        gap: targetCgpa * 10 - score.total_marks,
        topics: ['Fundamentals', 'Problem Solving'],
        improvement_strategy: [
          'Practice previous year questions',
          'Focus on key concepts',
          'Seek faculty guidance'
        ]
      }));

    const strengths = subjectScores
      .filter(score => score.total_marks >= 80)
      .map(score => ({
        subject: score.subject_name,
        marks: score.total_marks,
        performance: 'Excellent'
      }));

    return {
      student_id: studentId,
      analysis: {
        weaknesses,
        strengths,
        overall_performance: weaknesses.length > 3 ? 'Needs Attention' : 'Good',
        priority_subjects: weaknesses.slice(0, 2),
        study_plan: {
          weekly_hours: 20,
          daily_hours: 4,
          focus_distribution: {
            [weaknesses[0]?.subject || 'Mathematics']: '40%',
            [weaknesses[1]?.subject || 'Programming']: '30%',
            'Other Subjects': '30%'
          },
          recommended_resources: [
            'Textbook exercises',
            'Online tutorials',
            'Practice tests'
          ]
        },
        cgpa_improvement_needed: targetCgpa - (subjectScores.reduce((sum, s) => sum + s.total_marks, 0) / subjectScores.length / 10),
        estimated_effort_hours: weaknesses.length * 10,
        success_probability: 0.75
      },
      generated_at: new Date().toISOString()
    };
  }

  // Get career predictions
  async predictCareer(
    studentId: string,
    skills: string[],
    interests: string[],
    cgpa: number,
    projects: string[],
    internships: string[] = []
  ): Promise<CareerPredictionResponse> {
    try {
      const token = await this.getAuthToken();
      
      const response = await fetch(`${this.baseUrl}/api/v1/career-prediction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          student_id: studentId,
          skills,
          interests,
          cgpa,
          projects,
          internships
        })
      });

      if (!response.ok) {
        throw new Error(`Career prediction failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error predicting career:', error);
      return this.getMockCareerPrediction(studentId, skills, interests, cgpa, projects, internships);
    }
  }

  // Mock career prediction
  private getMockCareerPrediction(
    studentId: string,
    skills: string[],
    interests: string[],
    cgpa: number,
    projects: string[],
    internships: string[]
  ): CareerPredictionResponse {
    const careers = [
      {
        career: 'Software Engineer',
        match_score: 85,
        skill_match: 80,
        cgpa_eligible: cgpa >= 7.0,
        missing_skills: ['System Design', 'Cloud Computing'],
        salary_range: '₹6L - ₹20L',
        growth_potential: 'High',
        preparation_path: ['Learn DSA', 'Build Projects', 'Practice Coding'],
        industry_demand: 'Very High',
        required_certifications: ['AWS', 'Google Cloud'],
        top_companies: ['Google', 'Microsoft', 'Amazon']
      },
      {
        career: 'Data Scientist',
        match_score: 75,
        skill_match: 70,
        cgpa_eligible: cgpa >= 7.5,
        missing_skills: ['Machine Learning', 'Statistics'],
        salary_range: '₹8L - ₹25L',
        growth_potential: 'Very High',
        preparation_path: ['Learn Python', 'Study Statistics', 'Build ML Models'],
        industry_demand: 'High',
        required_certifications: ['TensorFlow', 'Data Science'],
        top_companies: ['IBM', 'Tesla', 'Netflix']
      }
    ];

    return {
      student_id: studentId,
      recommended_careers: careers,
      skill_development_priority: ['Programming', 'Problem Solving', 'Communication'],
      internship_recommendations: [
        {
          role: 'Software Development Intern',
          duration: '3-6 months',
          skills_to_gain: ['Backend Development', 'API Design'],
          min_cgpa_required: '7.0+',
          application_tip: 'Focus on projects and coding skills'
        }
      ],
      generated_at: new Date().toISOString()
    };
  }

  // Get text embeddings
  async getEmbeddings(texts: string[]): Promise<number[][]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/embeddings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ texts })
      });

      if (!response.ok) {
        throw new Error(`Embedding generation failed: ${response.statusText}`);
      }

      const result = await response.json();
      return result.embeddings;
    } catch (error) {
      console.error('Error getting embeddings:', error);
      // Return mock embeddings (384-dimensional zeros for all-MiniLM-L6-v2)
      return texts.map(() => new Array(384).fill(0));
    }
  }

  // Calculate similarity between texts
  async calculateSimilarity(texts: string[]): Promise<{
    similarity_matrix: number[][];
    most_similar_pairs: Array<{
      text1: string;
      text2: string;
      similarity: number;
    }>;
    average_similarity: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/similarity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ texts })
      });

      if (!response.ok) {
        throw new Error(`Similarity calculation failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error calculating similarity:', error);
      
      // Mock similarity matrix
      const matrix = texts.map(() => texts.map(() => Math.random()));
      return {
        similarity_matrix: matrix,
        most_similar_pairs: [],
        average_similarity: 0.5
      };
    }
  }

  // Check ML server health
  async checkHealth(): Promise<{
    status: string;
    models: Record<string, string>;
    version: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET'
      });
      
      if (!response.ok) {
        throw new Error('ML server is not healthy');
      }

      return await response.json();
    } catch (error) {
      console.error('ML server health check failed:', error);
      return {
        status: 'unavailable',
        models: { 'all-MiniLM-L6-v2': 'offline' },
        version: '1.0.0'
      };
    }
  }

  // ======================== ADVANCED ML METHODS ========================

  async getComprehensiveAnalysis(studentId: string): Promise<ComprehensiveStudentAnalysis> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/comprehensive-analysis/${studentId}`);
    } catch (error) {
      console.error('Error fetching comprehensive analysis:', error);
      // Return mock data for development
      return this.getMockComprehensiveAnalysis(studentId);
    }
  }

  // Mock comprehensive analysis for development
  private getMockComprehensiveAnalysis(studentId: string): ComprehensiveStudentAnalysis {
    return {
      studentId,
      timestamp: new Date().toISOString(),
      performanceMetrics: {
        cgpa: 8.2,
        sgpa: [7.5, 8.0, 8.2, 8.5, 8.7, 8.2],
        attendanceRate: 85,
        assignmentCompletionRate: 90,
        subjectWisePerformance: [
          {
            subjectName: 'Data Structures',
            grade: 'A',
            score: 85,
            difficulty: 4,
            improvement: 5,
            recommendations: ['Practice tree algorithms', 'Solve LeetCode problems']
          },
          {
            subjectName: 'Database Systems',
            grade: 'B+',
            score: 78,
            difficulty: 3,
            improvement: -2,
            recommendations: ['Study normalization', 'Practice SQL queries']
          }
        ],
        strengthAreas: ['Programming', 'Algorithms', 'Web Development'],
        weaknessAreas: ['Database Design', 'System Architecture'],
        performanceTrend: 'improving',
        predictedCGPA: 8.5,
        riskLevel: 'low'
      },
      careerInsights: [
        {
          domain: 'Software Engineering',
          matchScore: 85,
          requiredSkills: [
            {
              name: 'JavaScript',
              currentLevel: 80,
              requiredLevel: 90,
              importance: 9,
              learningResources: []
            }
          ],
          currentSkillGap: 15,
          recommendedCourses: [],
          industryDemand: 95,
          salaryRange: { min: 600000, max: 2000000, median: 1200000 },
          topCompanies: [
            { name: 'Google', sector: 'Tech', hiringProbability: 80, requiredCGPA: 7.5, preferredSkills: ['DSA', 'System Design'] }
          ],
          preparationRoadmap: [
            {
              semester: 6,
              courses: ['Advanced Algorithms', 'Cloud Computing'],
              skills: ['System Design', 'AWS'],
              projects: ['Microservices Architecture'],
              certifications: ['AWS Certified'],
              internships: ['Backend Development'],
              milestone: 'Build scalable systems'
            }
          ]
        }
      ],
      personalizedRecommendations: {
        immediateActions: [
          { priority: 'high', action: 'Improve database concepts', deadline: '2024-12-01', impact: 8, effort: 6 }
        ],
        shortTermGoals: [],
        longTermGoals: [],
        skillDevelopmentPlan: [],
        mentorshipSuggestions: [],
        networkingOpportunities: []
      },
      projectAnalysis: {
        totalProjects: 5,
        domainDistribution: { 'Web Development': 3, 'AI/ML': 2 },
        skillCoverage: 75,
        innovationScore: 70,
        industryRelevance: 80,
        portfolioStrength: 75,
        missingAreas: ['Mobile Development', 'DevOps'],
        suggestedProjects: []
      },
      peerComparison: {
        percentile: 85,
        averageCGPA: 7.8,
        yourPosition: 15,
        totalStudents: 120,
        strengths: ['Programming Skills', 'Project Work'],
        areasToImprove: ['Theory Subjects', 'Database Concepts'],
        topPerformers: []
      },
      futureProjections: {
        expectedGraduation: {
          expectedCGPA: 8.4,
          confidence: 85,
          risks: ['Database course performance'],
          opportunities: ['Strong programming skills']
        },
        placementProbability: 88,
        expectedPackageRange: { min: 800000, max: 1800000 },
        topMatchingCompanies: [
          { name: 'Microsoft', sector: 'Tech', hiringProbability: 75, requiredCGPA: 8.0, preferredSkills: ['C#', '.NET'] }
        ],
        preparednessScore: 82,
        timeToReadiness: 3
      }
    };
  }

  async predictPerformance(
    currentGrades: number[],
    attendance: number,
    projectCount: number
  ): Promise<{
    predictedCGPA: number;
    confidence: number;
    factors: { factor: string; impact: number }[];
    recommendations: string[];
  }> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/predict-performance`, {
        method: 'POST',
        body: JSON.stringify({
          currentGrades,
          attendance,
          projectCount
        })
      });
    } catch (error) {
      console.error('Error predicting performance:', error);
      throw error;
    }
  }

  async getCareerPathAnalysis(
    skills: string[],
    interests: string[],
    academicPerformance: any
  ): Promise<AICareerInsight[]> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/career-path-analysis`, {
        method: 'POST',
        body: JSON.stringify({
          skills,
          interests,
          academicPerformance
        })
      });
    } catch (error) {
      console.error('Error analyzing career path:', error);
      throw error;
    }
  }

  async getFacultyRecommendations(
    courseId: string,
    learningStyle: string,
    pastPerformance: any
  ): Promise<FacultyRecommendation[]> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/faculty-recommendations`, {
        method: 'POST',
        body: JSON.stringify({
          courseId,
          learningStyle,
          pastPerformance
        })
      });
    } catch (error) {
      console.error('Error getting faculty recommendations:', error);
      throw error;
    }
  }

  async getCourseRecommendations(
    studentProfile: any,
    careerGoals: string[],
    currentSemester: number
  ): Promise<Course[]> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/course-recommendations`, {
        method: 'POST',
        body: JSON.stringify({
          studentProfile,
          careerGoals,
          currentSemester
        })
      });
    } catch (error) {
      console.error('Error getting course recommendations:', error);
      throw error;
    }
  }

  async advancedAnalyzeWeaknesses(
    grades: any,
    projectPerformance: any
  ): Promise<{
    weaknesses: Weakness[];
    improvementPlan: ImprovementStep[];
    estimatedTimeToImprove: number;
  }> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/analyze-weaknesses`, {
        method: 'POST',
        body: JSON.stringify({
          grades,
          projectPerformance
        })
      });
    } catch (error) {
      console.error('Error analyzing weaknesses:', error);
      throw error;
    }
  }

  async getPersonalizedLearningPath(
    studentId: string,
    targetCareer: string
  ): Promise<RoadmapStep[]> {
    try {
      return await this.makeAPICall(
        `${this.advancedBaseURL}/learning-path/${studentId}?career=${targetCareer}`
      );
    } catch (error) {
      console.error('Error getting learning path:', error);
      throw error;
    }
  }

  async analyzeProjectPortfolio(
    projects: any[],
    targetIndustry: string
  ): Promise<ProjectPortfolioAnalysis> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/analyze-portfolio`, {
        method: 'POST',
        body: JSON.stringify({
          projects,
          targetIndustry
        })
      });
    } catch (error) {
      console.error('Error analyzing portfolio:', error);
      throw error;
    }
  }

  async getPeerComparison(
    studentId: string,
    branch: string,
    semester: number
  ): Promise<PeerComparisonMetrics> {
    try {
      return await this.makeAPICall(
        `${this.advancedBaseURL}/peer-comparison/${studentId}?branch=${branch}&semester=${semester}`
      );
    } catch (error) {
      console.error('Error getting peer comparison:', error);
      throw error;
    }
  }

  async getPlacementReadiness(studentId: string): Promise<{
    readinessScore: number;
    strengths: string[];
    gaps: string[];
    actionItems: Action[];
    timelineToReady: number;
    recommendedCompanies: Company[];
  }> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/placement-readiness/${studentId}`);
    } catch (error) {
      console.error('Error checking placement readiness:', error);
      throw error;
    }
  }

  async generateStudyPlan(
    weakSubjects: string[],
    availableHours: number,
    examDate: Date
  ): Promise<{
    dailySchedule: DailyPlan[];
    focusAreas: FocusArea[];
    expectedImprovement: number;
    resources: Resource[];
  }> {
    try {
      return await this.makeAPICall(`${this.advancedBaseURL}/generate-study-plan`, {
        method: 'POST',
        body: JSON.stringify({
          weakSubjects,
          availableHours,
          examDate: examDate.toISOString()
        })
      });
    } catch (error) {
      console.error('Error generating study plan:', error);
      throw error;
    }
  }

  // ======================== HYBRID METHODS ========================

  // Get comprehensive student insights combining basic and advanced analysis
  async getStudentInsights(studentId: string): Promise<{
    basic: PredictionResponse;
    advanced: ComprehensiveStudentAnalysis;
    career: CareerPredictionResponse;
  }> {
    try {
      const [basicAnalysis, advancedAnalysis, careerAnalysis] = await Promise.all([
        this.getPredictions(
          studentId,
          {
            current_cgpa: 0, // Will be populated from profile
            attendance_percentage: 0,
            assignment_completion_ratio: 0,
            study_hours_per_week: 0,
            extracurricular_activities: []
          },
          [],
          1
        ),
        this.getComprehensiveAnalysis(studentId),
        this.predictCareer(studentId, [], [], 0, [])
      ]);

      return {
        basic: basicAnalysis,
        advanced: advancedAnalysis,
        career: careerAnalysis
      };
    } catch (error) {
      console.error('Error getting comprehensive student insights:', error);
      throw error;
    }
  }

  // Generate personalized roadmap for student
  async generatePersonalizedRoadmap(
    studentId: string,
    targetCareer: string,
    currentSkills: string[]
  ): Promise<{
    learningPath: RoadmapStep[];
    skillDevelopment: SkillPlan[];
    projectSuggestions: SuggestedProject[];
    timeline: {
      totalDuration: number;
      milestones: { semester: number; milestone: string }[];
    };
  }> {
    try {
      const [learningPath, careerInsights, portfolioAnalysis] = await Promise.all([
        this.getPersonalizedLearningPath(studentId, targetCareer),
        this.getCareerPathAnalysis(currentSkills, [], {}),
        this.analyzeProjectPortfolio([], targetCareer)
      ]);

      return {
        learningPath,
        skillDevelopment: careerInsights[0]?.requiredSkills.map(skill => ({
          skill: skill.name,
          currentLevel: skill.currentLevel,
          targetLevel: skill.requiredLevel,
          learningPath: skill.learningResources.map(r => r.title),
          estimatedTime: 30 // Default 30 days per skill
        })) || [],
        projectSuggestions: portfolioAnalysis.suggestedProjects,
        timeline: {
          totalDuration: learningPath.reduce((total, step) => total + 6, 0), // 6 months per semester
          milestones: learningPath.map(step => ({
            semester: step.semester,
            milestone: step.milestone
          }))
        }
      };
    } catch (error) {
      console.error('Error generating personalized roadmap:', error);
      throw error;
    }
  }

  // Get quick insights for dashboard widget
  async getQuickInsights(studentId: string): Promise<{
    riskLevel: string;
    predictedCGPA: number;
    topCareerMatch: string;
    placementReadiness: number;
    immediateActions: string[];
  }> {
    try {
      const comprehensive = await this.getComprehensiveAnalysis(studentId);
      
      return {
        riskLevel: comprehensive.performanceMetrics.riskLevel,
        predictedCGPA: comprehensive.performanceMetrics.predictedCGPA,
        topCareerMatch: comprehensive.careerInsights[0]?.domain || 'Not Available',
        placementReadiness: comprehensive.futureProjections.placementProbability,
        immediateActions: comprehensive.personalizedRecommendations.immediateActions
          .slice(0, 3)
          .map(action => action.action)
      };
    } catch (error) {
      console.error('Error getting quick insights:', error);
      return {
        riskLevel: 'medium',
        predictedCGPA: 8.0,
        topCareerMatch: 'Software Engineering',
        placementReadiness: 75,
        immediateActions: [
          'Complete pending assignments',
          'Review weak subjects',
          'Update your project portfolio'
        ]
      };
    }
  }
}

export const mlService = new MLService();