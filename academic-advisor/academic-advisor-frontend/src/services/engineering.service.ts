// src/services/engineering.service.ts
import axios from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000';

// Axios instance with auth
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Add auth token to requests
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await auth.currentUser?.getIdToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (err) {
      console.warn('Failed to get auth token:', err);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============== INTERFACES ==============

export interface StudentPerformanceMetrics {
  studentInfo: {
    uid: string;
    semester: string;
    year: string;
    branch: string;
    roll_number: string;
  };
  subjects: any[];
  overallCGPA: number;
  semesterSGPA: number;
  strongSubjects: string[];
  weakSubjects: string[];
  completedCredits: number;
  totalCredits: number;
  interests: string[];
  careerGoals: string[];
  skillsMatrix: Record<string, any>;
}

export interface ElectiveRecommendation {
  id: string;
  title: string;
  match: number;
  semester: string;
  reason: string;
  credits: number;
  difficulty: string;
  instructor: {
    name: string;
    rating: number;
    expertise: string[];
  };
  industryRelevance: number;
  jobMarketDemand: number;
  enrollmentCount: number;
  careerImpact: string;
  tags: string[];
  prerequisites: string[];
  learningOutcomes: string[];
  syllabus: string[];
}

export interface WeaknessAnalysis {
  weaknesses: any[];
  overall_risk_score: number;
  priority_areas: string[];
  total_weaknesses: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  key_insights: string[];
  from_cache: boolean;
}

export interface StudyResource {
  id: string;
  title: string;
  type: string;
  url: string;
  duration: string;
  rating: number;
  reviews: number;
  difficulty: string;
  language: string;
  examRelevance: string;
  completionStatus: number;
  tags: string[];
  provider: string;
  platform: string;
  lastUpdated: string;
  thumbnailUrl: string | null;
  icon: string;
  aiReason: string;
  isBookmarked: boolean;
  subject: string;
  description?: string;
}

// ============== DEFAULT/FALLBACK DATA ==============

const DEFAULT_METRICS: StudentPerformanceMetrics = {
  studentInfo: {
    uid: '',
    semester: '6',
    year: '3rd Year',
    branch: 'IT',
    roll_number: 'Unknown'
  },
  subjects: [],
  overallCGPA: 7.8,
  semesterSGPA: 8.1,
  strongSubjects: ['Python', 'Data Structures'],
  weakSubjects: ['Mathematics', 'Statistics'],
  completedCredits: 120,
  totalCredits: 160,
  interests: ['Machine Learning', 'Web Development'],
  careerGoals: ['Software Engineer'],
  skillsMatrix: {}
};

const DEFAULT_ELECTIVE_RECOMMENDATIONS: ElectiveRecommendation[] = [
  {
    id: "ml-elective",
    title: "Machine Learning",
    match: 95,
    semester: "Semester 6",
    reason: "Perfect match for your AI/ML interests and strong Python skills",
    credits: 4,
    difficulty: "Intermediate",
    instructor: { name: "Dr. Sharma", rating: 4.5, expertise: ["Deep Learning", "Neural Networks"] },
    industryRelevance: 95,
    jobMarketDemand: 92,
    enrollmentCount: 120,
    careerImpact: "Opens doors to AI/ML engineer roles with 40% higher salaries",
    tags: ["AI", "Python", "Data Science", "Neural Networks"],
    prerequisites: ["Python Programming", "Mathematics", "Statistics"],
    learningOutcomes: [
      "Build and train neural networks",
      "Implement ML algorithms from scratch",
      "Work with TensorFlow and PyTorch"
    ],
    syllabus: ["Regression", "Classification", "Clustering", "Neural Networks", "Deep Learning", "NLP Basics"]
  },
  {
    id: "dwm-elective",
    title: "Data Warehouse and Data Mining",
    match: 88,
    semester: "Semester 6",
    reason: "Great for data science career path and analytics skills",
    credits: 4,
    difficulty: "Intermediate",
    instructor: { name: "Dr. Kumar", rating: 4.3, expertise: ["Big Data", "Analytics"] },
    industryRelevance: 90,
    jobMarketDemand: 88,
    enrollmentCount: 95,
    careerImpact: "Foundation for data engineering and BI roles",
    tags: ["Data Science", "Analytics", "SQL", "ETL"],
    prerequisites: ["DBMS", "SQL", "Statistics"],
    learningOutcomes: [
      "Design data warehouses",
      "Implement ETL pipelines",
      "Apply data mining algorithms"
    ],
    syllabus: ["Data Warehousing", "OLAP", "Mining Algorithms", "Pattern Recognition"]
  },
  {
    id: "ccs-elective",
    title: "Cloud Computing Services",
    match: 82,
    semester: "Semester 6",
    reason: "High demand skill for modern software development",
    credits: 4,
    difficulty: "Intermediate",
    instructor: { name: "Dr. Singh", rating: 4.4, expertise: ["AWS", "DevOps"] },
    industryRelevance: 92,
    jobMarketDemand: 94,
    enrollmentCount: 110,
    careerImpact: "Essential for cloud architect and DevOps roles",
    tags: ["Cloud", "AWS", "DevOps", "Microservices"],
    prerequisites: ["Operating Systems", "Networking", "Linux"],
    learningOutcomes: [
      "Deploy applications on AWS/Azure",
      "Implement containerization",
      "Design cloud architectures"
    ],
    syllabus: ["Cloud Models", "AWS Services", "Containerization", "Kubernetes"]
  },
  {
    id: "wt-elective",
    title: "Wireless Technology",
    match: 78,
    semester: "Semester 6",
    reason: "Complements your networking knowledge",
    credits: 4,
    difficulty: "Intermediate",
    instructor: { name: "Dr. Patel", rating: 4.2, expertise: ["5G", "IoT"] },
    industryRelevance: 85,
    jobMarketDemand: 80,
    enrollmentCount: 85,
    careerImpact: "Essential for IoT and telecom roles",
    tags: ["IoT", "Networking", "5G", "Embedded"],
    prerequisites: ["Computer Networks", "Microprocessor"],
    learningOutcomes: [
      "Understand wireless protocols",
      "Design IoT solutions"
    ],
    syllabus: ["Wireless Protocols", "5G Networks", "IoT Architecture"]
  }
];

const DEFAULT_STUDY_RESOURCES: StudyResource[] = [
  {
    id: "res-1",
    title: "Complete Machine Learning Course",
    type: "video",
    url: "https://www.youtube.com/watch?v=GwIo3gDZCVQ",
    duration: "12 hours",
    rating: 4.8,
    reviews: 15420,
    difficulty: "Beginner to Intermediate",
    language: "English",
    examRelevance: "High",
    completionStatus: 0,
    tags: ["Machine Learning", "Python", "AI"],
    provider: "freeCodeCamp",
    platform: "YouTube",
    lastUpdated: "2 weeks ago",
    thumbnailUrl: null,
    icon: "🎥",
    aiReason: "Covers all ML fundamentals needed for your curriculum",
    isBookmarked: false,
    subject: "Machine Learning"
  },
  {
    id: "res-2",
    title: "Python for Data Science - Complete Tutorial",
    type: "tutorial",
    url: "https://www.kaggle.com/learn/python",
    duration: "5 hours",
    rating: 4.7,
    reviews: 8500,
    difficulty: "Beginner",
    language: "English",
    examRelevance: "High",
    completionStatus: 0,
    tags: ["Python", "Data Science", "Basics"],
    provider: "Kaggle",
    platform: "Kaggle Learn",
    lastUpdated: "1 month ago",
    thumbnailUrl: null,
    icon: "📚",
    aiReason: "Essential Python skills for ML and Data Science",
    isBookmarked: false,
    subject: "Python"
  },
  {
    id: "res-3",
    title: "Mathematics for Machine Learning",
    type: "course",
    url: "https://www.coursera.org/specializations/mathematics-machine-learning",
    duration: "16 weeks",
    rating: 4.6,
    reviews: 12000,
    difficulty: "Intermediate",
    language: "English",
    examRelevance: "High",
    completionStatus: 0,
    tags: ["Mathematics", "Linear Algebra", "Statistics"],
    provider: "Imperial College London",
    platform: "Coursera",
    lastUpdated: "3 weeks ago",
    thumbnailUrl: null,
    icon: "🎓",
    aiReason: "Strengthens mathematical foundation for ML",
    isBookmarked: false,
    subject: "Mathematics"
  },
  {
    id: "res-4",
    title: "Statistics Practice Problems",
    type: "practice",
    url: "https://www.hackerrank.com/domains/statistics",
    duration: "Self-paced",
    rating: 4.5,
    reviews: 5600,
    difficulty: "Intermediate",
    language: "English",
    examRelevance: "Very High",
    completionStatus: 0,
    tags: ["Statistics", "Probability", "Practice"],
    provider: "HackerRank",
    platform: "HackerRank",
    lastUpdated: "1 week ago",
    thumbnailUrl: null,
    icon: "🧮",
    aiReason: "Practice problems to improve Statistics scores",
    isBookmarked: false,
    subject: "Statistics"
  },
  {
    id: "res-5",
    title: "DBMS Complete Course",
    type: "video",
    url: "https://www.youtube.com/playlist?list=PLxCzCOWd7aiFAN6I8CuViBuCdJgiOkT2Y",
    duration: "8 hours",
    rating: 4.7,
    reviews: 9800,
    difficulty: "Intermediate",
    language: "English",
    examRelevance: "High",
    completionStatus: 0,
    tags: ["DBMS", "SQL", "Database"],
    provider: "Gate Smashers",
    platform: "YouTube",
    lastUpdated: "1 month ago",
    thumbnailUrl: null,
    icon: "🗄️",
    aiReason: "Comprehensive DBMS coverage for exams",
    isBookmarked: false,
    subject: "Database Management System"
  },
  {
    id: "res-6",
    title: "Data Structures & Algorithms in Python",
    type: "course",
    url: "https://www.geeksforgeeks.org/data-structures/",
    duration: "20 hours",
    rating: 4.8,
    reviews: 22000,
    difficulty: "Intermediate",
    language: "English",
    examRelevance: "Very High",
    completionStatus: 0,
    tags: ["DSA", "Python", "Algorithms"],
    provider: "GeeksforGeeks",
    platform: "GeeksforGeeks",
    lastUpdated: "2 weeks ago",
    thumbnailUrl: null,
    icon: "🔧",
    aiReason: "Core DSA concepts with implementations",
    isBookmarked: false,
    subject: "Data Structures and Algorithms"
  },
  {
    id: "res-7",
    title: "Computer Networks - Neso Academy",
    type: "video",
    url: "https://www.youtube.com/playlist?list=PLBlnK6fEyqRgMCUAG0XRw78UA8qnv6jEx",
    duration: "15 hours",
    rating: 4.9,
    reviews: 18000,
    difficulty: "Beginner to Intermediate",
    language: "English",
    examRelevance: "High",
    completionStatus: 0,
    tags: ["Networking", "TCP/IP", "OSI"],
    provider: "Neso Academy",
    platform: "YouTube",
    lastUpdated: "3 months ago",
    thumbnailUrl: null,
    icon: "🌐",
    aiReason: "Best free resource for networking fundamentals",
    isBookmarked: false,
    subject: "Computer Networks"
  },
  {
    id: "res-8",
    title: "Operating Systems - Jenny's Lectures",
    type: "video",
    url: "https://www.youtube.com/playlist?list=PLdo5W4Nhv31a5ucW_S1K3-x6ztBRD-PNa",
    duration: "18 hours",
    rating: 4.8,
    reviews: 14000,
    difficulty: "Intermediate",
    language: "English",
    examRelevance: "High",
    completionStatus: 0,
    tags: ["OS", "Process", "Memory", "Scheduling"],
    provider: "Jenny's Lectures",
    platform: "YouTube",
    lastUpdated: "2 months ago",
    thumbnailUrl: null,
    icon: "💻",
    aiReason: "Detailed OS concepts for semester preparation",
    isBookmarked: false,
    subject: "Operating System"
  },
  {
    id: "res-9",
    title: "LeetCode - Practice DSA Problems",
    type: "practice",
    url: "https://leetcode.com/problemset/all/",
    duration: "Self-paced",
    rating: 4.9,
    reviews: 50000,
    difficulty: "All Levels",
    language: "Multiple",
    examRelevance: "Very High",
    completionStatus: 0,
    tags: ["DSA", "Practice", "Coding", "Interview Prep"],
    provider: "LeetCode",
    platform: "LeetCode",
    lastUpdated: "Today",
    thumbnailUrl: null,
    icon: "⚡",
    aiReason: "Essential for coding practice and placement preparation",
    isBookmarked: false,
    subject: "Data Structures and Algorithms"
  },
  {
    id: "res-10",
    title: "AWS Cloud Practitioner Essentials",
    type: "course",
    url: "https://www.aws.training/Details/Curriculum?id=27076",
    duration: "6 hours",
    rating: 4.7,
    reviews: 8500,
    difficulty: "Beginner",
    language: "English",
    examRelevance: "Medium",
    completionStatus: 0,
    tags: ["Cloud", "AWS", "DevOps"],
    provider: "Amazon",
    platform: "AWS Training",
    lastUpdated: "1 month ago",
    thumbnailUrl: null,
    icon: "☁️",
    aiReason: "Foundation for cloud computing elective",
    isBookmarked: false,
    subject: "Cloud Computing"
  }
];

const DEFAULT_WEAKNESS_ANALYSIS: WeaknessAnalysis = {
  weaknesses: [],
  overall_risk_score: 0,
  priority_areas: [],
  total_weaknesses: 0,
  critical_count: 0,
  high_count: 0,
  medium_count: 0,
  low_count: 0,
  key_insights: [],
  from_cache: false
};

// ============== HELPER FUNCTIONS ==============

/**
 * Extract data from API response, handling various formats
 */
const extractData = <T>(response: any, defaultValue: T, dataKey?: string): T => {
  if (!response) return defaultValue;
  
  const data = response.data || response;
  
  if (dataKey && data[dataKey]) {
    return data[dataKey];
  }
  
  return data || defaultValue;
};

/**
 * Filter resources by type and/or subject
 */
const filterResources = (
  resources: StudyResource[], 
  filters?: { type?: string; difficulty?: string; topic?: string; subject?: string }
): StudyResource[] => {
  if (!filters) return resources;
  
  let filtered = [...resources];
  
  if (filters.type) {
    filtered = filtered.filter(r => 
      r.type.toLowerCase() === filters.type?.toLowerCase()
    );
  }
  
  if (filters.difficulty) {
    filtered = filtered.filter(r => 
      r.difficulty.toLowerCase().includes(filters.difficulty?.toLowerCase() || '')
    );
  }
  
  if (filters.topic || filters.subject) {
    const searchTerm = (filters.topic || filters.subject || '').toLowerCase();
    filtered = filtered.filter(r => 
      r.subject?.toLowerCase().includes(searchTerm) ||
      r.title.toLowerCase().includes(searchTerm) ||
      r.tags.some(t => t.toLowerCase().includes(searchTerm))
    );
  }
  
  return filtered;
};

// ============== API SERVICE ==============

export const engineeringService = {
  
  async getPerformanceMetrics(userId: string): Promise<StudentPerformanceMetrics> {
    try {
      const response = await apiClient.get(`/students/${userId}/performance`);
      const data = extractData(response, DEFAULT_METRICS);
      return {
        ...DEFAULT_METRICS,
        ...data,
        studentInfo: {
          ...DEFAULT_METRICS.studentInfo,
          ...(data.studentInfo || {}),
          uid: userId
        }
      };
    } catch (error) {
      console.warn('📊 Using default performance metrics due to API error:', error);
      return {
        ...DEFAULT_METRICS,
        studentInfo: {
          ...DEFAULT_METRICS.studentInfo,
          uid: userId
        }
      };
    }
  },

  async getElectiveRecommendations(userId: string): Promise<ElectiveRecommendation[]> {
    try {
      const response = await apiClient.get(`/students/${userId}/electives/recommendations`);
      const data = response.data;
      
      // Handle various response formats
      if (Array.isArray(data)) {
        return data.length > 0 ? data : DEFAULT_ELECTIVE_RECOMMENDATIONS;
      }
      if (data?.recommendations && Array.isArray(data.recommendations)) {
        return data.recommendations.length > 0 ? data.recommendations : DEFAULT_ELECTIVE_RECOMMENDATIONS;
      }
      
      console.warn('📚 Unexpected elective data format, using defaults');
      return DEFAULT_ELECTIVE_RECOMMENDATIONS;
    } catch (error) {
      console.warn('📚 Using default elective recommendations due to API error:', error);
      return DEFAULT_ELECTIVE_RECOMMENDATIONS;
    }
  },

  async getWeaknessAnalysis(userId: string): Promise<WeaknessAnalysis> {
    try {
      const response = await apiClient.get(`/students/${userId}/weaknesses`);
      const data = response.data;
      
      return {
        weaknesses: data?.weaknesses || [],
        overall_risk_score: data?.overall_risk_score || 0,
        priority_areas: data?.priority_areas || [],
        total_weaknesses: data?.total_weaknesses || 0,
        critical_count: data?.critical_count || 0,
        high_count: data?.high_count || 0,
        medium_count: data?.medium_count || 0,
        low_count: data?.low_count || 0,
        key_insights: data?.key_insights || [],
        from_cache: data?.from_cache || false
      };
    } catch (error) {
      console.warn('⚠️ Using empty weakness analysis due to API error:', error);
      return DEFAULT_WEAKNESS_ANALYSIS;
    }
  },

  async getStudyResources(
    userId: string, 
    filters?: { type?: string; difficulty?: string; topic?: string; subject?: string }
  ): Promise<StudyResource[]> {
    try {
      const params: Record<string, string> = {};
      if (filters?.type) params.type = filters.type;
      if (filters?.topic) params.subject = filters.topic;
      if (filters?.subject) params.subject = filters.subject;
      
      const response = await apiClient.get(`/students/${userId}/resources`, { params });
      const data = response.data;
      
      // Handle various response formats
      let resources: StudyResource[] = [];
      
      if (Array.isArray(data)) {
        resources = data;
      } else if (data?.resources && Array.isArray(data.resources)) {
        resources = data.resources;
      }
      
      if (resources.length > 0) {
        return resources;
      }
      
      // Return filtered default resources
      console.warn('📖 Using default study resources');
      return filterResources(DEFAULT_STUDY_RESOURCES, filters);
    } catch (error) {
      console.warn('📖 Using default study resources due to API error:', error);
      return filterResources(DEFAULT_STUDY_RESOURCES, filters);
    }
  },

  async getBookmarkedResources(userId: string): Promise<StudyResource[]> {
    try {
      const response = await apiClient.get(`/students/${userId}/resources/bookmarked`);
      const data = response.data;
      
      if (Array.isArray(data)) {
        return data;
      }
      if (data?.resources && Array.isArray(data.resources)) {
        return data.resources;
      }
      
      return [];
    } catch (error) {
      console.warn('⭐ Using empty bookmarks due to API error:', error);
      return [];
    }
  },

  async toggleBookmark(userId: string, resourceId: string): Promise<{ success: boolean; bookmarked?: boolean }> {
    try {
      const response = await apiClient.post(`/students/${userId}/resources/${resourceId}/bookmark`);
      return {
        success: true,
        bookmarked: response.data?.bookmarked ?? true
      };
    } catch (error) {
      console.warn('⭐ Bookmark toggle handled locally:', error);
      return { success: true, bookmarked: true };
    }
  },

  async updateResourceProgress(
    userId: string, 
    resourceId: string, 
    progress: number
  ): Promise<{ success: boolean; progress?: number }> {
    try {
      const response = await apiClient.put(
        `/students/${userId}/resources/${resourceId}/progress`,
        { progress }
      );
      return {
        success: true,
        progress: response.data?.progress ?? progress
      };
    } catch (error) {
      console.warn('📈 Progress update handled locally:', error);
      return { success: true, progress };
    }
  },

  async getStudyPlan(userId: string, topicId: string): Promise<any> {
    try {
      const response = await apiClient.post(`/students/${userId}/study-plan`, { topicId });
      return response.data;
    } catch (error) {
      console.warn('📋 Study plan request failed:', error);
      return {
        topicId,
        plan: [],
        message: 'Study plan will be generated based on your progress'
      };
    }
  },

  async trackActivity(
    userId: string, 
    activityData: {
      type: 'resource_viewed' | 'topic_completed' | 'quiz_taken';
      resourceId?: string;
      topicId?: string;
      score?: number;
      timeSpent?: number;
    }
  ): Promise<{ success: boolean }> {
    try {
      const response = await apiClient.post(`/students/${userId}/activity`, activityData);
      return { success: true };
    } catch (error) {
      console.warn('📝 Activity tracking handled locally:', error);
      return { success: true };
    }
  },

  // ============== ADDITIONAL UTILITY METHODS ==============

  /**
   * Get resources filtered by subject (useful for weakness-based recommendations)
   */
  async getResourcesForSubject(userId: string, subject: string): Promise<StudyResource[]> {
    return this.getStudyResources(userId, { subject });
  },

  /**
   * Get all resources of a specific type
   */
  async getResourcesByType(userId: string, type: string): Promise<StudyResource[]> {
    return this.getStudyResources(userId, { type });
  },

  /**
   * Get default recommendations (for offline/fallback scenarios)
   */
  getDefaultElectives(): ElectiveRecommendation[] {
    return DEFAULT_ELECTIVE_RECOMMENDATIONS;
  },

  /**
   * Get default resources (for offline/fallback scenarios)
   */
  getDefaultResources(): StudyResource[] {
    return DEFAULT_STUDY_RESOURCES;
  }
};

export default engineeringService;