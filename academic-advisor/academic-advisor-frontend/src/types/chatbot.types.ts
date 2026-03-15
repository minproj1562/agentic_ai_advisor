// src/types/chatbot.types.ts
// Complete file with all types including Sentiment and AdvisorSuggestion

// ══════════════════════════════════════════════════════════
// SENTIMENT ANALYSIS TYPES
// ══════════════════════════════════════════════════════════

export interface SentimentData {
  mood: 'positive' | 'negative' | 'neutral' | 'frustrated' | 'confused' | 'anxious';
  confidence: number;
  is_frustrated?: boolean;
  is_confused?: boolean;
  is_anxious?: boolean;
  is_positive?: boolean;
  is_urgent?: boolean;
  tone_adjustment?: string;
  compound?: number;
  positive?: number;
  negative?: number;
  neutral?: number;
}

export interface AdvisorSuggestion {
  message: string;
  action: string;
  reason: 'sentiment' | 'low_confidence' | 'human_escalation' | 'complex_issue' | 'offline' | string;
}

// ══════════════════════════════════════════════════════════
// CHAT MESSAGE TYPES
// ══════════════════════════════════════════════════════════

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string | ChatResponseContent;
  timestamp: string;
  intent?: string;
  confidence?: 'High' | 'Medium' | 'Low';
  isLoading?: boolean;
  isError?: boolean;
  // Sentiment data
  sentiment?: SentimentData;
  // Advisor suggestion
  advisorSuggestion?: AdvisorSuggestion;
  // Cache indicator
  fromCache?: boolean;
  // LLM enhanced
  llmEnhanced?: boolean;
}

export interface ChatResponseContent {
  type: string;
  intent: string;
  content: Record<string, any>;
  confidence: string;
  session_token?: string;
  processing_time_ms?: number;
  sources?: Array<Record<string, any>>;
  // New fields
  sentiment?: SentimentData;
  advisor_suggestion?: AdvisorSuggestion;
  from_cache?: boolean;
  llm_generated?: boolean;
  llm_enhanced?: boolean;
  sentiment_adapted?: boolean;
}

// ══════════════════════════════════════════════════════════
// SYLLABUS TYPES (Person A)
// ══════════════════════════════════════════════════════════

export interface ConceptExplanation {
  definition: string;
  explanation?: string;
  key_points: string[];
  subtopics?: string[];
  important_notes?: string;
  exam_relevance?: string;
  unit_context?: string;
  related_topics?: string[];
  examples?: string[];
  subject?: string;
  topic?: string;
}

export interface SyllabusBreakdown {
  code: string;
  name: string;
  semester: number;
  credits: number;
  description?: string;
  learning_outcomes?: string[];
  reference_books?: string[];
  units: Array<{
    unit_number: number;
    title: string;
    topics: string[];
  }>;
  faculty?: Array<{ name: string; designation: string; rating?: number }>;
}

// ══════════════════════════════════════════════════════════
// FACULTY TYPES (Person A)
// ══════════════════════════════════════════════════════════

export interface FacultyRecommendation {
  recommendations: Array<{
    name: string;
    department: string;
    designation?: string;
    subjects?: string[];
    subjects_taught?: string[];
    research_areas?: string[];
    teaching_style?: string;
    reasoning?: string[];
    match_score?: number;
    rating?: number;
    experience_years?: number;
    is_available_for_mentoring?: boolean;
    office_hours?: string;
  }>;
  selection_criteria?: string;
  total_found?: number;
}

export interface FacultyListItem {
  name: string;
  department: string;
  designation?: string;
  subjects_taught?: string[];
  experience_years?: number;
  rating?: number;
  email?: string;
}

export interface FacultyListResponse {
  faculty: FacultyListItem[];
  count: number;
  filter_applied?: string;
}

// ══════════════════════════════════════════════════════════
// CAREER TYPES (Person B)
// ══════════════════════════════════════════════════════════

export interface CareerGuidance {
  career: {
    title: string;
    category?: string;
    description: string;
    required_skills: string[];
    recommended_subjects?: string[];
    recommended_electives?: string[];
    job_titles?: string[];
    salary_range?: {
      entry_level?: string;
      mid_level?: string;
      senior_level?: string;
      top_companies?: string;
      min?: string;
      max?: string;
      average?: string;
    };
    top_companies_india?: string[];
    top_companies_global?: string[];
    certifications?: string[];
    market_demand?: string;
    growth_potential?: string;
  };
  roadmap?: Array<{
    step: number;
    title: string;
    description: string;
    duration: string;
  }>;
  next_steps?: string[];
  personalized_advice?: string;
  gap_analysis?: {
    matching_skills?: string[];
    missing_skills?: string[];
    skill_match_pct?: number;
    cgpa_meets?: boolean;
    recommended_cgpa?: number;
    your_cgpa?: number;
  };
}

export interface CareerListResponse {
  message: string;
  careers: Array<{
    title: string;
    category?: string;
    demand?: string;
    description?: string;
    salary?: string;
  }>;
  hint?: string;
}

// ══════════════════════════════════════════════════════════
// PERFORMANCE TYPES (Person B)
// ══════════════════════════════════════════════════════════

export interface PerformanceAnalysis {
  profile?: {
    name: string;
    branch: string;
    semester: number | string;
    cgpa: number;
  };
  current_cgpa?: number;
  latest_sgpa?: number;
  sgpa_trend?: Array<{ semester: number; sgpa: number; credits?: number }>;
  trend_direction?: 'improving' | 'stable' | 'declining';
  subject_analysis?: Array<{
    subject: string;
    score: number;
    grade?: string;
    status: 'weak' | 'average' | 'strong';
  }>;
  weak_subjects?: string[];
  strong_subjects?: string[];
  insights?: string[];
  recommendations?: string[];
  ai_insights?: string;
  message?: string;
}

// ══════════════════════════════════════════════════════════
// ELECTIVE TYPES (Person B)
// ══════════════════════════════════════════════════════════

export interface ElectiveRecommendation {
  recommendations: Array<{
    code?: string;
    name: string;
    category?: string;
    credits?: number;
    description?: string;
    skills?: string[];
    career_paths?: string[];
    difficulty?: string;
    score?: number;
    reasons?: string[];
    reason?: string;
  }>;
  based_on?: {
    interests?: string[];
    semester?: number;
    career_goals?: string[];
  };
  advice?: string;
  message?: string;
}

// ══════════════════════════════════════════════════════════
// MENTOR RECOMMENDATION TYPE
// ══════════════════════════════════════════════════════════

export interface MentorRecommendation {
  recommendations: Array<{
    name: string;
    department: string;
    designation?: string;
    subjects_taught?: string[];
    specializations?: string[];
    match_reason: string;
    email?: string;
  }>;
  based_on?: {
    weak_subjects?: string[];
    query_subject?: string;
  };
  message?: string;
}

// ══════════════════════════════════════════════════════════
// STUDY PLAN TYPES (Person B)
// ══════════════════════════════════════════════════════════

export interface StudyPlan {
  semester?: number | string;
  daily_schedule?: Array<{
    subject: string;
    priority: 'high' | 'normal' | 'low';
    suggested_hours: number;
    time_slot?: string;
  }>;
  weekly_goals?: string[];
  focus_areas?: string[];
  recommendations?: string[];
  total_daily_hours?: number;
  ai_study_tips?: string;
  exam_tips?: string[];
  message?: string;
}

// ══════════════════════════════════════════════════════════
// FEEDBACK TYPES
// ══════════════════════════════════════════════════════════

export interface ChatFeedback {
  session_id: string;
  message_id: string;
  rating: number;
  feedback_text?: string;
  was_helpful?: boolean;
}

// ══════════════════════════════════════════════════════════
// SESSION TYPES
// ══════════════════════════════════════════════════════════

export interface ChatSession {
  session_token: string;
  messages: ChatMessage[];
  created_at: string;
  is_active: boolean;
  user_id?: string;
  expires_at?: string;
}

// ══════════════════════════════════════════════════════════
// INTENT TYPES
// ══════════════════════════════════════════════════════════

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
  | 'ERROR'
  | 'MENTOR_QUERY'   
  | 'RESOURCE_QUERY';     // ← ADD


// ══════════════════════════════════════════════════════════
// API RESPONSE TYPES
// ══════════════════════════════════════════════════════════

export interface ChatApiResponse {
  type: string;
  intent: string;
  content: Record<string, any>;
  confidence: string;
  session_token?: string;
  processing_time_ms?: number;
  sources?: Array<Record<string, any>>;
  sentiment?: SentimentData;
  advisor_suggestion?: AdvisorSuggestion;
  from_cache?: boolean;
  llm_generated?: boolean;
  llm_enhanced?: boolean;
}

export interface SuggestionsResponse {
  success: boolean;
  suggestions: string[];
}

export interface HistoryResponse {
  success: boolean;
  messages: ChatMessage[];
  count: number;
  session_token?: string;
}

export interface FeedbackResponse {
  success: boolean;
  status: string;
  message?: string;
}

// ══════════════════════════════════════════════════════════
// QUIZ TYPES
// ══════════════════════════════════════════════════════════

export interface QuizQuestion {
  q: string;
  options: string[];
  correct: number;         // 0-based index
  explanation: string;
}

export interface QuizContent {
  topic: string;
  subject?: string;
  questions: QuizQuestion[];
  total: number;
  source: 'ai_generated' | 'built_in';
}

// ══════════════════════════════════════════════════════════
// RESOURCE TYPES
// ══════════════════════════════════════════════════════════

export interface ResourceItem {
  title: string;
  type: string;            // "Video", "Notes", "Practice", "Course"
  url: string;
  platform: string;
  rating: number;
  difficulty: string;
  duration?: string;
}

export interface ResourceListContent {
  query: string;
  resources: ResourceItem[];
  count: number;
  message: string;
  cta?: {
    text: string;
    url: string;
  };
}