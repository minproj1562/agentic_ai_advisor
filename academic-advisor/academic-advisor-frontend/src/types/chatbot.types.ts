// academic-advisor-frontend/src/types/chatbot.types.ts

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string | ChatResponseContent;
  timestamp: string;
  intent?: string;
  confidence?: 'High' | 'Medium' | 'Low';
  isLoading?: boolean;
}

export interface ChatResponseContent {
  type: string;
  intent: string;
  content: Record<string, any>;
  confidence: string;
  session_token?: string;
  processing_time_ms?: number;
  sources?: Array<Record<string, any>>;
}

export interface ConceptExplanation {
  definition: string;
  key_points: string[];
  subtopics?: string[];
  important_notes?: string;
  exam_relevance?: string;
  unit_context?: string;
}

export interface FacultyRecommendation {
  recommendations: Array<{
    name: string;
    department: string;
    subjects: string[];
    research_areas: string[];
    teaching_style: string;
    reasoning: string[];
    match_score: number;
  }>;
  selection_criteria: string;
}

export interface PerformanceAnalysis {
  overall_performance: {
    cgpa: number;
    semester: number;
    credits_completed: number;
  };
  subject_analysis: Array<{
    subject: string;
    grade: string;
    status: 'weak' | 'average' | 'strong';
  }>;
  weak_areas: string[];
  strong_areas: string[];
  improvement_suggestions: string[];
  attendance: number;
}

export interface StudyPlan {
  daily_schedule: Array<{
    subject: string;
    priority: 'high' | 'normal';
    suggested_hours: number;
  }>;
  weekly_goals: string[];
  focus_areas: string[];
  recommendations: string[];
}

export interface ChatSession {
  session_token: string;
  messages: ChatMessage[];
  created_at: string;
  is_active: boolean;
}

export type IntentType = 
  | 'SYLLABUS_QUERY'
  | 'FACULTY_QUERY'
  | 'PERFORMANCE_QUERY'
  | 'ELECTIVE_QUERY'
  | 'CAREER_QUERY'
  | 'STUDY_PLAN_QUERY'
  | 'OUT_OF_SCOPE';