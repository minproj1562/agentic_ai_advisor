// academic-advisor-frontend/src/types/chatbot.types.ts

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string | ChatResponseContent;
  timestamp: string;
  intent?: string;
  confidence?: 'High' | 'Medium' | 'Low';
  isLoading?: boolean;
  isError?: boolean;
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

// ── Syllabus (Person A) ─────────────────────────────────

export interface ConceptExplanation {
  definition: string;
  key_points: string[];
  subtopics?: string[];
  important_notes?: string;
  exam_relevance?: string;
  unit_context?: string;
  related_topics?: string[];
}

export interface SyllabusBreakdown {
  code: string;
  name: string;
  semester: number;
  credits: number;
  units: Array<{
    unit_number: number;
    title: string;
    topics: string[];
  }>;
  faculty?: Array<{ name: string; designation: string }>;
}

// ── Faculty (Person A) ──────────────────────────────────

export interface FacultyRecommendation {
  recommendations: Array<{
    name: string;
    department: string;
    subjects: string[];
    research_areas: string[];
    teaching_style: string;
    reasoning: string[];
    match_score?: number;
    rating?: number;
    experience_years?: number;
  }>;
  selection_criteria: string;
}

export interface FacultyListItem {
  name: string;
  department: string;
  subjects_taught: string[];
  experience_years: number;
  rating?: number;
}

// ── Career (Person B) ───────────────────────────────────

export interface CareerGuidance {
  career: {
    title: string;
    category: string;
    description: string;
    required_skills: string[];
    recommended_subjects: string[];
    recommended_electives: string[];
    job_titles: string[];
    salary_range: {
      entry_level: string;
      mid_level: string;
      senior_level: string;
      top_companies: string;
    };
    top_companies_india: string[];
    top_companies_global: string[];
    certifications: string[];
    market_demand: string;
    growth_potential: string;
  };
  roadmap: Array<{
    step: number;
    title: string;
    description: string;
    duration: string;
  }>;
  next_steps: string[];
  personalized_advice?: string;
  gap_analysis?: {
    matching_skills: string[];
    missing_skills: string[];
    skill_match_pct: number;
    cgpa_meets: boolean;
    recommended_cgpa: number;
    your_cgpa: number;
  };
}

export interface CareerListResponse {
  message: string;
  careers: Array<{
    title: string;
    category: string;
    demand: string;
    description: string;
  }>;
  hint: string;
}

// ── Performance (Person B) ──────────────────────────────

export interface PerformanceAnalysis {
  profile: {
    name: string;
    branch: string;
    semester: number | string;
    cgpa: number;
  };
  current_cgpa: number;
  latest_sgpa: number;
  sgpa_trend: Array<{ semester: number; sgpa: number; credits?: number }>;
  trend_direction: 'improving' | 'stable' | 'declining';
  subject_analysis: Array<{
    subject: string;
    score: number;
    status: 'weak' | 'average' | 'strong';
  }>;
  weak_subjects: string[];
  strong_subjects: string[];
  insights: string[];
  recommendations: string[];
  ai_insights?: string;
}

// ── Elective (Person B) ─────────────────────────────────

export interface ElectiveRecommendation {
  recommendations: Array<{
    code: string;
    name: string;
    category: string;
    credits: number;
    description: string;
    skills: string[];
    career_paths: string[];
    difficulty: string;
    score: number;
    reasons: string[];
  }>;
  based_on: {
    interests: string[];
    semester: number;
  };
  advice: string;
}

// ── Study Plan (Person B) ───────────────────────────────

export interface StudyPlan {
  semester: number | string;
  daily_schedule: Array<{
    subject: string;
    priority: 'high' | 'normal';
    suggested_hours: number;
  }>;
  weekly_goals: string[];
  focus_areas: string[];
  recommendations: string[];
  total_daily_hours: number;
  ai_study_tips?: string;
}

// ── Feedback (Person B — Task 22) ───────────────────────

export interface ChatFeedback {
  session_id: string;
  message_id: string;
  rating: number;
  feedback_text?: string;
  was_helpful?: boolean;
}

// ── Session ─────────────────────────────────────────────

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
  | 'CLARIFICATION'
  | 'OUT_OF_SCOPE'
  | 'GENERAL'
  | 'ERROR';