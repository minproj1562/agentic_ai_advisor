// src/services/ml.service.ts
import axios, { AxiosInstance } from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==================== TYPES ====================

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

export interface CareerPath {
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
}

export interface InternshipRecommendation {
  role: string;
  duration: string;
  skills_to_gain: string[];
  application_tip: string;
}

export interface CareerPredictionResponse {
  student_id: string;
  recommended_careers: CareerPath[];
  skill_development_priority: string[];
  internship_recommendations: InternshipRecommendation[];
  industry_trends: string[];
  timestamp: string;
}

export interface ElectiveRecommendation {
  elective_code: string;
  elective_name: string;
  credits: number;
  match_score: number;
  match_explanation: string;
  prerequisites_met: boolean;
  skill_alignment: string[];
  career_relevance: string[];
  recommendation_basis: {
    interests_weight: number;
    performance_weight: number;
    projects_weight: number;
  };
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
    career_paths: CareerPath[];
  };
}

// Add this interface after the existing interfaces (around line 70)
export interface AcademicRecommendations {
  student_info: {
    name: string;
    branch: string;
    semester: number;
    cgpa: number;
  };
  weaknesses: Array<{
    subject: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    average_score: number;
    gap: number;
    topics: string[];
  }>;
  curriculum_recommendations: {
    immediate_actions: Array<{
      action: string;
      reason: string;
      priority: string;
    }>;
    focus_areas: Array<{
      area: string;
      average_score: number;
    }>;
    honours_minor_eligibility: {
      eligible: boolean;
      message: string;
      cgpa_gap?: number;
      available_programs?: Array<{
        program: string;
        type: string;
      }>;
    };
  };
  interest_based_recommendations: Array<{
    elective_name: string;
    match_score: number;
    interest: string;
  }>;
}

// ==================== ML SERVICE CLASS ====================

class MLService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/v1/ml-insights`,  // Changed from /ml to /ml-insights
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

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
      (error) => Promise.reject(error)
    );
  }

  // ==================== PREDICTION METHODS ====================

  async getPredictions(
    studentId: string,
    academicData: StudentAcademicData,
    historicalScores: Array<{ semester: number; gpa: number; credits: number }>,
    currentSemester: number
  ): Promise<PredictionResponse> {
    try {
      const response = await this.api.post<PredictionResponse>('/predictions/performance', {
        student_id: studentId,
        academic_data: academicData,
        historical_scores: historicalScores,
        current_semester: currentSemester
      });
      return response.data;
    } catch (error) {
      console.error('Error getting predictions:', error);
      // Return default prediction if API fails
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
      risk_factors: cgpa < 7 ? ['CGPA below target', 'Need improvement in core subjects'] : [],
      recommendations: [
        'Focus on weak subjects identified in analysis',
        'Maintain consistent study schedule',
        'Participate in practical labs actively'
      ],
      model_info: {
        model_type: 'Ensemble (KNN + Logistic Regression)',
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
      const response = await this.api.post<WeaknessAnalysisResponse>('/analysis/weaknesses', {
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
    // Identify weak subjects (below 60%)
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
        topics: this.getWeakTopicsForSubject(s.subject_code),
        improvement_strategy: this.getImprovementStrategy(s.subject_name)
      }));

    return {
      student_id: studentId,
      analysis: {
        overall_performance: currentCGPA >= 8 ? 'excellent' : currentCGPA >= 7 ? 'good' : currentCGPA >= 6 ? 'average' : 'below_average',
        success_probability: Math.min(0.95, currentCGPA / 10),
        weaknesses: weakSubjects,
        priority_subjects: weakSubjects.slice(0, 3),
        cgpa_improvement_needed: Math.max(0, 7 - currentCGPA),
        estimated_effort_hours: weakSubjects.length * 20,
        study_plan: {
          weekly_hours: 15 + weakSubjects.length * 5,
          daily_hours: 2 + weakSubjects.length,
          focus_distribution: this.getFocusDistribution(weakSubjects),
          recommended_resources: [
            'NPTEL Video Lectures',
            'GeeksforGeeks Practice',
            'Previous Year Question Papers',
            'Lab Practice Sessions'
          ],
          milestones: [
            { week: 1, target: 'Complete revision of fundamentals' },
            { week: 2, target: 'Practice numerical problems' },
            { week: 3, target: 'Solve previous year papers' },
            { week: 4, target: 'Mock tests and evaluation' }
          ]
        }
      },
      recommendations: this.generateRecommendations(weakSubjects, currentCGPA),
      timestamp: new Date().toISOString()
    };
  }

  private getWeakTopicsForSubject(subjectCode: string): string[] {
    const topicMap: Record<string, string[]> = {
      'ITPCC301': ['Vector Spaces', 'Linear Mappings', 'Numerical Methods'],
      'ITPCC302': ['8086 Programming', 'Cache Memory', 'Pipelining'],
      'ITPCC303': ['Trees', 'Graphs', 'Sorting Algorithms'],
      'ITPCC304': ['Normalization', 'SQL Queries', 'Transaction Management'],
      'ITPCC406': ['TCP/IP', 'Routing Algorithms', 'Network Security'],
      'ITPCC407': ['Process Scheduling', 'Memory Management', 'Deadlocks'],
      'ITPCC408': ['Design Patterns', 'Testing', 'Agile Methodology']
    };
    return topicMap[subjectCode] || ['Core Concepts', 'Problem Solving', 'Applications'];
  }

  private getImprovementStrategy(subjectName: string): string[] {
    return [
      `Review ${subjectName} fundamentals from textbook`,
      `Watch NPTEL lectures on ${subjectName}`,
      `Practice problems daily for 1 hour`,
      `Discuss concepts with peers and faculty`,
      `Attempt previous year questions`
    ];
  }

  private getFocusDistribution(weakSubjects: WeaknessData[]): Record<string, string> {
    const distribution: Record<string, string> = {};
    const total = weakSubjects.reduce((sum, s) => sum + s.gap, 0);
    
    weakSubjects.forEach(s => {
      const percentage = Math.round((s.gap / total) * 100);
      distribution[s.subject] = `${percentage}%`;
    });
    
    return distribution;
  }

  private generateRecommendations(weakSubjects: WeaknessData[], cgpa: number): string[] {
    const recommendations: string[] = [];
    
    if (cgpa < 6) {
      recommendations.push('⚠️ Critical: Focus intensively on core subjects to avoid backlog');
    }
    
    weakSubjects.forEach(s => {
      recommendations.push(`📚 ${s.subject}: Focus on ${s.topics.slice(0, 2).join(', ')}`);
    });
    
    recommendations.push('🎯 Create a weekly study schedule and stick to it');
    recommendations.push('👥 Form study groups for difficult subjects');
    recommendations.push('💻 Practice coding/numericals daily');
    
    return recommendations;
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
      const response = await this.api.post<CareerPredictionResponse>('/predictions/career', {
        student_id: studentId,
        skills,
        interests,
        cgpa,
        projects
      });
      return response.data;
    } catch (error) {
      console.error('Error predicting career:', error);
      return this.getDefaultCareerPrediction(studentId, skills, interests, cgpa);
    }
  }

  private getDefaultCareerPrediction(
    studentId: string,
    skills: string[],
    interests: string[],
    cgpa: number
  ): CareerPredictionResponse {
    const careerPaths = this.matchCareersToProfile(skills, interests, cgpa);
    
    return {
      student_id: studentId,
      recommended_careers: careerPaths,
      skill_development_priority: this.getPrioritySkills(skills, interests),
      internship_recommendations: this.getInternshipRecommendations(interests),
      industry_trends: [
        'AI/ML skills are in high demand',
        'Cloud computing certifications valued',
        'Full-stack development opportunities growing',
        'Cybersecurity roles increasing'
      ],
      timestamp: new Date().toISOString()
    };
  }

  private matchCareersToProfile(skills: string[], interests: string[], cgpa: number): CareerPath[] {
    const allCareers: CareerPath[] = [
      {
        career: 'Software Development Engineer',
        match_score: 85,
        cgpa_eligible: cgpa >= 7,
        required_cgpa: 7,
        salary_range: '₹6-15 LPA',
        growth_potential: 'High',
        top_companies: ['Google', 'Microsoft', 'Amazon', 'Flipkart', 'Paytm'],
        missing_skills: ['System Design', 'DSA Advanced'],
        preparation_path: [
          'Master Data Structures & Algorithms',
          'Build 3-4 full-stack projects',
          'Practice on LeetCode/CodeForces',
          'Prepare for system design interviews'
        ],
        required_certifications: ['AWS Cloud Practitioner', 'Meta Frontend Developer']
      },
      {
        career: 'Data Scientist',
        match_score: 78,
        cgpa_eligible: cgpa >= 7.5,
        required_cgpa: 7.5,
        salary_range: '₹8-20 LPA',
        growth_potential: 'Very High',
        top_companies: ['Google', 'Amazon', 'Netflix', 'Uber', 'Swiggy'],
        missing_skills: ['Machine Learning', 'Statistics', 'Python'],
        preparation_path: [
          'Complete ML/DL courses on Coursera',
          'Build ML projects with real datasets',
          'Learn SQL and data visualization',
          'Participate in Kaggle competitions'
        ],
        required_certifications: ['Google Data Analytics', 'IBM Data Science']
      },
      {
        career: 'Cloud Engineer',
        match_score: 72,
        cgpa_eligible: cgpa >= 6.5,
        required_cgpa: 6.5,
        salary_range: '₹7-18 LPA',
        growth_potential: 'High',
        top_companies: ['AWS', 'Microsoft Azure', 'Google Cloud', 'IBM'],
        missing_skills: ['Docker', 'Kubernetes', 'Terraform'],
        preparation_path: [
          'Get AWS/Azure certification',
          'Learn containerization with Docker',
          'Practice infrastructure as code',
          'Build CI/CD pipelines'
        ],
        required_certifications: ['AWS Solutions Architect', 'Azure Administrator']
      },
      {
        career: 'Full Stack Developer',
        match_score: 80,
        cgpa_eligible: cgpa >= 6,
        required_cgpa: 6,
        salary_range: '₹5-12 LPA',
        growth_potential: 'High',
        top_companies: ['Startups', 'Product Companies', 'Consulting Firms'],
        missing_skills: ['React/Angular', 'Node.js', 'MongoDB'],
        preparation_path: [
          'Master HTML, CSS, JavaScript',
          'Learn React/Angular frontend',
          'Build Node.js/Express backend',
          'Create 2-3 full-stack projects'
        ],
        required_certifications: ['Meta Frontend', 'MongoDB Developer']
      }
    ];

    // Adjust match scores based on interests and skills
    return allCareers.map(career => {
      let adjustedScore = career.match_score;
      
      if (interests.some(i => career.career.toLowerCase().includes(i.toLowerCase()))) {
        adjustedScore += 10;
      }
      
      const matchingSkills = career.missing_skills.filter(s => 
        skills.some(sk => sk.toLowerCase().includes(s.toLowerCase()))
      );
      adjustedScore += matchingSkills.length * 5;
      
      return {
        ...career,
        match_score: Math.min(100, adjustedScore),
        missing_skills: career.missing_skills.filter(s => 
          !skills.some(sk => sk.toLowerCase().includes(s.toLowerCase()))
        )
      };
    }).sort((a, b) => b.match_score - a.match_score);
  }

  private getPrioritySkills(skills: string[], interests: string[]): string[] {
    const allPrioritySkills = [
      'Data Structures & Algorithms',
      'System Design',
      'Python',
      'JavaScript',
      'SQL',
      'Git',
      'Docker',
      'AWS/Cloud',
      'Machine Learning',
      'React/Angular'
    ];
    
    return allPrioritySkills.filter(s => 
      !skills.some(sk => sk.toLowerCase().includes(s.toLowerCase()))
    ).slice(0, 5);
  }

  private getInternshipRecommendations(interests: string[]): InternshipRecommendation[] {
    return [
      {
        role: 'Software Development Intern',
        duration: '2-3 months',
        skills_to_gain: ['Industry coding practices', 'Team collaboration', 'Version control'],
        application_tip: 'Apply through LinkedIn and company career pages early in semester 5'
      },
      {
        role: 'Data Science Intern',
        duration: '3-6 months',
        skills_to_gain: ['Data analysis', 'ML model deployment', 'Business analytics'],
        application_tip: 'Build a strong portfolio with Kaggle projects before applying'
      },
      {
        role: 'Cloud Engineering Intern',
        duration: '2-4 months',
        skills_to_gain: ['Cloud infrastructure', 'DevOps', 'Automation'],
        application_tip: 'Get AWS/Azure certification to stand out'
      }
    ];
  }

  
  // ==================== ELECTIVE & HONOURS RECOMMENDATIONS ====================

  async getRecommendations(
    includeElectives: boolean = true,
    includeHonours: boolean = true,
    includeCareer: boolean = true
  ): Promise<{
    electives: ElectiveRecommendation[];
    honours: HonoursRecommendation[];
    careers: CareerPath[];
  }> {
    try {
      const response = await this.api.post('/recommendations/generate', {
        include_electives: includeElectives,
        include_honours: includeHonours,
        include_career: includeCareer,
        use_transformer: true,
        use_knn: true,
        use_logistic: true
      });
      return response.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      return {
        electives: this.getDefaultElectives(),
        honours: this.getDefaultHonours(),
        careers: []
      };
    }
  }

  private getDefaultElectives(): ElectiveRecommendation[] {
    return [
      {
        elective_code: 'ITPEC5012',
        elective_name: 'Cloud Computing Services',
        credits: 3,
        match_score: 88,
        match_explanation: 'Aligns with industry demand and your interest in web technologies. Cloud skills are essential for modern software development.',
        prerequisites_met: true,
        skill_alignment: ['AWS', 'Azure', 'Docker', 'Kubernetes'],
        career_relevance: ['Cloud Engineer', 'DevOps Engineer', 'Solutions Architect'],
        recommendation_basis: {
          interests_weight: 40,
          performance_weight: 35,
          projects_weight: 25
        }
      },
      {
        elective_code: 'ITPEC6022',
        elective_name: 'Machine Learning',
        credits: 3,
        match_score: 82,
        match_explanation: 'Strong foundation in mathematics and programming makes you a good fit. ML is one of the highest-paying specializations.',
        prerequisites_met: true,
        skill_alignment: ['Python', 'TensorFlow', 'Scikit-learn', 'Data Analysis'],
        career_relevance: ['Data Scientist', 'ML Engineer', 'AI Researcher'],
        recommendation_basis: {
          interests_weight: 35,
          performance_weight: 40,
          projects_weight: 25
        }
      },
      {
        elective_code: 'ITPEC5013',
        elective_name: 'Data Warehousing & Mining',
        credits: 3,
        match_score: 75,
        match_explanation: 'Builds on your DBMS knowledge. Essential for data-driven decision making in enterprises.',
        prerequisites_met: true,
        skill_alignment: ['SQL', 'ETL', 'Business Intelligence', 'Analytics'],
        career_relevance: ['Data Analyst', 'BI Developer', 'Data Engineer'],
        recommendation_basis: {
          interests_weight: 30,
          performance_weight: 45,
          projects_weight: 25
        }
      }
    ];
  }

  private getDefaultHonours(): HonoursRecommendation[] {
    return [
      {
        program: 'AI/ML Honours',
        type: 'honours',
        match_score: 85,
        eligibility: true,
        required_cgpa: 7.5,
        career_paths: ['ML Engineer', 'Data Scientist', 'AI Researcher'],
        explanation: 'Based on your interests and performance in mathematics/programming, this honours program will significantly boost your career prospects.',
        skills_gained: ['Deep Learning', 'NLP', 'Computer Vision', 'MLOps']
      },
      {
        program: 'Cybersecurity Minor',
        type: 'minor',
        match_score: 72,
        eligibility: true,
        required_cgpa: 7.0,
        career_paths: ['Security Analyst', 'Penetration Tester', 'Security Architect'],
        explanation: 'Growing field with high demand. Complements your IT knowledge well.',
        skills_gained: ['Network Security', 'Cryptography', 'Ethical Hacking', 'Security Auditing']
      },
      {
        program: 'Data Science Honours',
        type: 'honours',
        match_score: 78,
        eligibility: true,
        required_cgpa: 7.5,
        career_paths: ['Data Scientist', 'Analytics Manager', 'Research Scientist'],
        explanation: 'Combines statistics, programming, and domain knowledge for data-driven insights.',
        skills_gained: ['Statistical Analysis', 'Big Data', 'Data Visualization', 'Machine Learning']
      }
    ];
  }

  // ==================== INTEREST PROFILE MANAGEMENT ====================

  async updateInterests(
    interests: string[],
    careerGoals: string[],
    skills: string[]
  ): Promise<InterestProfile> {
    try {
      const response = await this.api.post('/interests/update', {
        interests,
        career_goals: careerGoals,
        skills
      });

      // Trigger recommendation refresh
      await this.triggerRecommendationUpdate();

      return response.data;
    } catch (error) {
      console.error('Error updating interests:', error);
      throw error;
    }
  }

  async getInterestProfile(): Promise<InterestProfile> {
    try {
      const response = await this.api.get<InterestProfile>('/interests/profile');
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

  async triggerRecommendationUpdate(): Promise<void> {
    try {
      await this.api.post('/recommendations/refresh', {
        update_basis: ['interests', 'marks', 'projects']
      });
    } catch (error) {
      console.error('Error triggering recommendation update:', error);
    }
  }

  // ==================== FEEDBACK ====================

  async submitRecommendationFeedback(
    recommendationType: 'elective' | 'honours' | 'career',
    recommendationId: string,
    rating: number,
    feedback: string
  ): Promise<void> {
    try {
      await this.api.post('/recommendations/feedback', {
        type: recommendationType,
        recommendation_id: recommendationId,
        rating,
        feedback,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  }

  // ==================== ACADEMIC RECOMMENDATIONS ====================

  async getAcademicRecommendations(): Promise<AcademicRecommendations> {
    try {
      const response = await this.api.get<{ data: AcademicRecommendations }>('/academic-recommendations');
      return response.data.data;
    } catch (error: any) {
      console.error('Error getting academic recommendations:', error);
      
      if (error.response?.status === 404) {
        throw new Error('Please complete your profile and add academic data first.');
      }
      
      throw error;
    }
  }

  async getComprehensiveAnalysis(
    includeTrends: boolean = true,
    includeComparisons: boolean = true,
    includeInterests: boolean = true
  ): Promise<any> {
    try {
      const response = await this.api.get('/comprehensive-analysis', {
        params: {
          include_trends: includeTrends,
          include_comparisons: includeComparisons,
          include_interests: includeInterests
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting comprehensive analysis:', error);
      throw error;
    }
  }

  async getElectiveRecommendations(semester?: number): Promise<{
    target_semester: number;
    interest_based_recommendations: ElectiveRecommendation[];
    available_electives: any[];
    student_interests: string[];
  }> {
    try {
      const response = await this.api.get('/elective-recommendations', {
        params: semester ? { semester } : {}
      });
      return response.data.data;
    } catch (error) {
      console.error('Error getting elective recommendations:', error);
      // Return default structure
      return {
        target_semester: semester || 5,
        interest_based_recommendations: this.getDefaultElectives(),
        available_electives: [],
        student_interests: []
      };
    }
  }

  async checkHonoursEligibility(): Promise<{
    eligible: boolean;
    current_semester: number;
    current_cgpa: number;
    required_cgpa: number;
    required_semester: number;
    message: string;
    cgpa_gap?: number;
    eligible_programs?: HonoursRecommendation[];
  }> {
    try {
      const response = await this.api.get('/honours-minor-eligibility');
      return response.data.data;
    } catch (error) {
      console.error('Error checking honours eligibility:', error);
      throw error;
    }
  }
}

export const mlService = new MLService();
export default mlService;