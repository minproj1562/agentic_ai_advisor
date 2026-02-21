// academic-advisor-frontend/src/services/chatbot.service.ts

import { auth } from './firebase.config';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

// Intent patterns for client-side classification
const INTENT_PATTERNS = {
  SYLLABUS_QUERY: [
    /\b(syllabus|topic|unit|chapter|concept|explain|what is|define|definition)\b/i,
    /\b(deadlock|mutex|semaphore|normalization|sql|algorithm|data structure)\b/i,
    /\b(operating system|os|dbms|database|network|compiler)\b/i,
  ],
  FACULTY_QUERY: [
    /\b(faculty|professor|teacher|instructor|mentor|dr\.?|prof\.?)\b/i,
    /\b(who teaches|taught by|teaching)\b/i,
    /\b(recommend|suggest)\b.*\b(mentor|faculty|professor)\b/i,
  ],
  PERFORMANCE_QUERY: [
    /\b(performance|grade|marks|score|cgpa|gpa|sgpa|result)\b/i,
    /\b(weak|strong|improve|better|progress)\b/i,
    /\b(my|student)\b.*\b(analysis|report|standing)\b/i,
  ],
  ELECTIVE_QUERY: [
    /\b(elective|optional|choose|select)\b.*\b(subject|course)\b/i,
    /\b(which|what)\b.*\b(elective|subject)\b.*\b(choose|take|select)\b/i,
    /\b(recommend|suggest)\b.*\b(elective|course|subject)\b/i,
  ],
  CAREER_QUERY: [
    /\b(career|job|placement|industry|company|work)\b/i,
    /\b(skill|roadmap|path|future|opportunity)\b/i,
    /\b(software|developer|engineer|analyst|scientist)\b.*\b(become|career)\b/i,
  ],
  OUT_OF_SCOPE: [
    /\b(movie|film|actor|actress|bollywood|hollywood|netflix)\b/i,
    /\b(cricket|football|soccer|basketball|ipl|fifa)\b/i,
    /\b(politics|election|vote|government|minister)\b/i,
    /\b(weather|recipe|cook|travel|vacation)\b/i,
    /\b(game|gaming|pubg|fortnite|minecraft)\b/i,
  ],
};

// Knowledge base for offline responses
const KNOWLEDGE_BASE: Record<string, any> = {
  deadlock: {
    definition: "A deadlock is a situation in operating systems where two or more processes are unable to proceed because each is waiting for resources held by the other.",
    key_points: [
      "Occurs when processes hold resources while waiting for others",
      "Four necessary conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait",
      "Can be prevented by eliminating any one of the four conditions",
      "Detection involves resource allocation graphs"
    ],
    exam_relevance: "High - frequently asked in OS exams, especially regarding prevention and detection strategies",
    related_topics: ["Process Synchronization", "Mutex", "Semaphores", "Resource Allocation"]
  },
  normalization: {
    definition: "Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity.",
    key_points: [
      "1NF: Eliminate repeating groups, ensure atomic values",
      "2NF: Remove partial dependencies (must be in 1NF)",
      "3NF: Remove transitive dependencies (must be in 2NF)",
      "BCNF: Every determinant must be a candidate key"
    ],
    exam_relevance: "Very High - core DBMS concept, expect questions on identifying normal forms and decomposition",
    related_topics: ["Functional Dependencies", "Database Design", "SQL", "ER Model"]
  },
  mutex: {
    definition: "A mutex (mutual exclusion) is a synchronization primitive that ensures only one thread or process can access a shared resource at a time.",
    key_points: [
      "Binary state: locked or unlocked",
      "Only the thread that locked the mutex can unlock it",
      "Prevents race conditions in concurrent programming",
      "Different from semaphore (which can allow multiple accesses)"
    ],
    exam_relevance: "High - important for process synchronization questions",
    related_topics: ["Semaphores", "Critical Section", "Deadlock", "Thread Safety"]
  },
  semaphore: {
    definition: "A semaphore is a synchronization tool used to control access to shared resources by multiple processes in a concurrent system.",
    key_points: [
      "Two types: Binary semaphore (0 or 1) and Counting semaphore (any non-negative value)",
      "Operations: wait() or P() decrements, signal() or V() increments",
      "Used to solve producer-consumer, reader-writer problems",
      "Can lead to deadlock if not used properly"
    ],
    exam_relevance: "Very High - commonly asked in OS exams with numerical problems",
    related_topics: ["Mutex", "Process Synchronization", "Critical Section", "Deadlock"]
  },
  sql: {
    definition: "SQL (Structured Query Language) is a standard programming language used to manage and manipulate relational databases.",
    key_points: [
      "DDL: CREATE, ALTER, DROP, TRUNCATE",
      "DML: SELECT, INSERT, UPDATE, DELETE",
      "DCL: GRANT, REVOKE",
      "TCL: COMMIT, ROLLBACK, SAVEPOINT"
    ],
    exam_relevance: "Very High - expect query writing and optimization questions",
    related_topics: ["Joins", "Subqueries", "Indexes", "Transactions"]
  },
  "machine learning": {
    definition: "Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
    key_points: [
      "Types: Supervised, Unsupervised, Reinforcement Learning",
      "Common algorithms: Linear Regression, Decision Trees, Neural Networks, SVM",
      "Key concepts: Training, Testing, Validation, Overfitting, Underfitting",
      "Applications: Image recognition, NLP, Recommendation systems"
    ],
    exam_relevance: "High - growing importance in curriculum",
    related_topics: ["Deep Learning", "Neural Networks", "Data Science", "AI"]
  }
};

// Faculty database for offline responses
const FACULTY_DATABASE = [
  {
    name: "Dr. Rajesh Kumar",
    department: "Computer Science",
    subjects: ["Operating Systems", "System Programming", "Computer Networks"],
    experience: 15,
    research_areas: ["Distributed Systems", "Cloud Computing"],
    teaching_style: "Interactive with practical demonstrations",
    rating: 4.5
  },
  {
    name: "Dr. Priya Sharma",
    department: "Computer Science",
    subjects: ["Database Management Systems", "Data Warehousing", "Big Data"],
    experience: 20,
    research_areas: ["Data Mining", "Machine Learning"],
    teaching_style: "Conceptual with real-world case studies",
    rating: 4.8
  },
  {
    name: "Dr. Amit Verma",
    department: "Computer Science",
    subjects: ["Machine Learning", "Artificial Intelligence", "Deep Learning"],
    experience: 8,
    research_areas: ["Neural Networks", "Computer Vision", "NLP"],
    teaching_style: "Project-based learning with coding exercises",
    rating: 4.6
  },
  {
    name: "Dr. Sunita Patel",
    department: "Computer Science",
    subjects: ["Data Structures", "Algorithms", "Competitive Programming"],
    experience: 12,
    research_areas: ["Algorithm Optimization", "Computational Complexity"],
    teaching_style: "Problem-solving focused",
    rating: 4.7
  }
];

class ChatbotService {
  private sessionToken: string | null = null;
  private conversationHistory: ChatMessage[] = [];
  private isBackendAvailable: boolean = true;

  constructor() {
    this.restoreSession();
  }

  /**
   * Classify intent locally
   */
  private classifyIntent(message: string): { intent: string; confidence: number } {
    const messageLower = message.toLowerCase();

    // Check out of scope first
    for (const pattern of INTENT_PATTERNS.OUT_OF_SCOPE) {
      if (pattern.test(messageLower)) {
        return { intent: 'OUT_OF_SCOPE', confidence: 0.95 };
      }
    }

    // Check other intents
    const intentScores: Record<string, number> = {};
    
    for (const [intent, patterns] of Object.entries(INTENT_PATTERNS)) {
      if (intent === 'OUT_OF_SCOPE') continue;
      
      let score = 0;
      for (const pattern of patterns) {
        if (pattern.test(messageLower)) {
          score += 0.3;
        }
      }
      if (score > 0) {
        intentScores[intent] = Math.min(score, 0.9);
      }
    }

    const bestIntent = Object.entries(intentScores).sort((a, b) => b[1] - a[1])[0];
    
    if (bestIntent && bestIntent[1] > 0.2) {
      return { intent: bestIntent[0], confidence: bestIntent[1] };
    }

    return { intent: 'GENERAL', confidence: 0.5 };
  }

  /**
   * Generate offline response based on intent
   */
  private generateOfflineResponse(message: string, intent: string): ChatResponseContent | string {
    const messageLower = message.toLowerCase();

    // Handle out of scope
    if (intent === 'OUT_OF_SCOPE') {
      return "Beyond my scope";
    }

    // Handle syllabus queries
    if (intent === 'SYLLABUS_QUERY') {
      // Find matching topic in knowledge base
      for (const [topic, data] of Object.entries(KNOWLEDGE_BASE)) {
        if (messageLower.includes(topic)) {
          return {
            type: 'concept_explanation',
            intent: 'SYLLABUS_QUERY',
            content: {
              definition: data.definition,
              key_points: data.key_points,
              exam_relevance: data.exam_relevance,
              related_topics: data.related_topics
            },
            confidence: 'High'
          };
        }
      }

      // Generic syllabus response
      return {
        type: 'text',
        intent: 'SYLLABUS_QUERY',
        content: {
          message: "I can help you understand academic concepts. Could you please specify which topic or subject you'd like to learn about? For example, you can ask about:\n\n• Operating Systems concepts (deadlock, mutex, semaphores)\n• Database concepts (normalization, SQL, transactions)\n• Data Structures and Algorithms\n• Machine Learning basics"
        },
        confidence: 'Medium'
      };
    }

    // Handle faculty queries
    if (intent === 'FACULTY_QUERY') {
      // Check if asking about specific subject
      const subjectKeywords = ['os', 'operating system', 'dbms', 'database', 'ml', 'machine learning', 'ai', 'data structure', 'algorithm'];
      let matchedSubject = '';
      
      for (const keyword of subjectKeywords) {
        if (messageLower.includes(keyword)) {
          matchedSubject = keyword;
          break;
        }
      }

      if (matchedSubject || messageLower.includes('recommend') || messageLower.includes('mentor')) {
        const relevantFaculty = FACULTY_DATABASE.filter(f => {
          if (!matchedSubject) return true;
          return f.subjects.some(s => s.toLowerCase().includes(matchedSubject));
        });

        return {
          type: 'faculty_recommendation',
          intent: 'FACULTY_QUERY',
          content: {
            recommendations: relevantFaculty.slice(0, 3).map(f => ({
              name: f.name,
              department: f.department,
              subjects: f.subjects,
              research_areas: f.research_areas,
              teaching_style: f.teaching_style,
              experience_years: f.experience,
              rating: f.rating,
              reasoning: [`Expert in ${f.subjects[0]}`, `${f.experience} years experience`, `Rating: ${f.rating}/5`]
            })),
            selection_criteria: "Based on subject expertise and teaching experience"
          },
          confidence: 'High'
        };
      }

      // List all faculty
      return {
        type: 'faculty_list',
        intent: 'FACULTY_QUERY',
        content: {
          faculty: FACULTY_DATABASE.map(f => ({
            name: f.name,
            department: f.department,
            subjects_taught: f.subjects,
            experience_years: f.experience,
            rating: f.rating
          })),
          count: FACULTY_DATABASE.length
        },
        confidence: 'High'
      };
    }

    // Handle performance queries
    if (intent === 'PERFORMANCE_QUERY') {
      return {
        type: 'text',
        intent: 'PERFORMANCE_QUERY',
        content: {
          message: "To provide your performance analysis, I need access to your academic records. Please ensure you have:\n\n1. Completed your academic profile setup\n2. Entered your semester-wise grades\n3. Updated your current semester information\n\nOnce your data is available, I can provide:\n• SGPA/CGPA trend analysis\n• Subject-wise performance breakdown\n• Weakness identification\n• Improvement recommendations"
        },
        confidence: 'Medium'
      };
    }

    // Handle elective queries
    if (intent === 'ELECTIVE_QUERY') {
      return {
        type: 'elective_recommendation',
        intent: 'ELECTIVE_QUERY',
        content: {
          recommendations: [
            {
              name: "Cloud Computing",
              category: "Professional Elective",
              relevance: 0.9,
              description: "Learn cloud platforms like AWS, Azure, GCP",
              career_paths: ["Cloud Architect", "DevOps Engineer"]
            },
            {
              name: "Machine Learning",
              category: "Professional Elective",
              relevance: 0.85,
              description: "Fundamentals of ML algorithms and applications",
              career_paths: ["Data Scientist", "ML Engineer"]
            },
            {
              name: "Cybersecurity",
              category: "Professional Elective",
              relevance: 0.8,
              description: "Network security, cryptography, ethical hacking",
              career_paths: ["Security Analyst", "Penetration Tester"]
            }
          ],
          advice: "Choose electives aligned with your career goals and interests. Consider prerequisites and workload."
        },
        confidence: 'Medium'
      };
    }

    // Handle career queries
    if (intent === 'CAREER_QUERY') {
      return {
        type: 'text',
        intent: 'CAREER_QUERY',
        content: {
          message: "Based on engineering academics, here are common career paths:\n\n**Software Development**\n• Skills: Programming, DSA, System Design\n• Salary: 6-30+ LPA\n\n**Data Science/ML**\n• Skills: Python, Statistics, ML algorithms\n• Salary: 8-35+ LPA\n\n**Cloud/DevOps**\n• Skills: AWS/Azure, Docker, Kubernetes\n• Salary: 8-25+ LPA\n\n**Cybersecurity**\n• Skills: Network security, Ethical hacking\n• Salary: 6-20+ LPA\n\nWould you like detailed guidance on any specific career path?"
        },
        confidence: 'High'
      };
    }

    // General response
    return {
      type: 'text',
      intent: 'GENERAL',
      content: {
        message: "I'm your Academic Guidance Assistant. I can help you with:\n\n📚 **Syllabus Queries** - Explain concepts, topics, and units\n👨‍🏫 **Faculty Information** - Find mentors and subject experts\n📊 **Performance Analysis** - Understand your academic standing\n📖 **Elective Recommendations** - Choose the right courses\n💼 **Career Guidance** - Plan your professional path\n\nHow can I assist you today?"
      },
      confidence: 'High'
    };
  }

  /**
   * Send a message and get response
   */
  async sendMessage(message: string, includeStudentData = true): Promise<ChatResponseContent | string> {
    // Classify intent locally first
    const { intent, confidence } = this.classifyIntent(message);

    // Handle out of scope immediately
    if (intent === 'OUT_OF_SCOPE') {
      return "Beyond my scope";
    }

    // Try backend first if available
    if (this.isBackendAvailable) {
      try {
        const token = await this.getAuthToken();
        
        const response = await fetch(`${API_BASE_URL}/api/v1/chatbot/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: JSON.stringify({
            message,
            session_token: this.sessionToken,
            include_student_data: includeStudentData
          })
        });

        if (response.ok) {
          const contentType = response.headers.get('content-type');
          
          if (contentType?.includes('text/plain')) {
            return await response.text();
          }
          
          const data = await response.json();
          
          if (data.session_token) {
            this.sessionToken = data.session_token;
            this.saveSession();
          }
          
          return data;
        }

        // If backend returns error, fall back to offline mode
        console.warn('Backend returned error, using offline mode');
        this.isBackendAvailable = false;
        
      } catch (error) {
        console.warn('Backend unavailable, using offline mode:', error);
        this.isBackendAvailable = false;
      }
    }

    // Generate offline response
    return this.generateOfflineResponse(message, intent);
  }

  /**
   * Get auth token
   */
  private async getAuthToken(): Promise<string | null> {
    try {
      const currentUser = auth.currentUser;
      if (currentUser) {
        return await currentUser.getIdToken();
      }
    } catch (error) {
      console.warn('Could not get auth token:', error);
    }
    return null;
  }

  /**
   * Get conversation history
   */
  async getHistory(limit = 20): Promise<ChatMessage[]> {
    // Return local history if backend unavailable
    return this.conversationHistory.slice(-limit);
  }

  /**
   * Get query suggestions
   */
  async getSuggestions(): Promise<string[]> {
    return [
      "Explain the concept of deadlock",
      "What is normalization in DBMS?",
      "Who teaches Operating Systems?",
      "Recommend electives for ML career",
      "How to become a data scientist?"
    ];
  }

  /**
   * Clear session
   */
  async clearSession(): Promise<void> {
    this.sessionToken = null;
    this.conversationHistory = [];
    localStorage.removeItem('chatbot_session');
    this.isBackendAvailable = true; // Reset backend availability
  }

  /**
   * Add message to local history
   */
  addToHistory(message: ChatMessage): void {
    this.conversationHistory.push(message);
    if (this.conversationHistory.length > 50) {
      this.conversationHistory = this.conversationHistory.slice(-50);
    }
  }

  /**
   * Get session token
   */
  getSessionToken(): string | null {
    return this.sessionToken;
  }

  /**
   * Restore session from storage
   */
  restoreSession(): void {
    try {
      const saved = localStorage.getItem('chatbot_session');
      if (saved) {
        const session = JSON.parse(saved);
        this.sessionToken = session.token;
        this.conversationHistory = session.history || [];
      }
    } catch (error) {
      console.error('Error restoring session:', error);
    }
  }

  /**
   * Save session to storage
   */
  private saveSession(): void {
    if (this.sessionToken) {
      localStorage.setItem('chatbot_session', JSON.stringify({
        token: this.sessionToken,
        history: this.conversationHistory.slice(-20),
        timestamp: new Date().toISOString()
      }));
    }
  }

  /**
   * Check if response is out of scope
   */
  isOutOfScope(response: ChatResponseContent | string): boolean {
    if (typeof response === 'string') {
      return response === 'Beyond my scope' || response === 'Irrelevant query';
    }
    return response.intent === 'OUT_OF_SCOPE';
  }

  /**
   * Check if backend is available
   */
  isOnlineMode(): boolean {
    return this.isBackendAvailable;
  }

  /**
   * Force retry backend connection
   */
  retryBackendConnection(): void {
    this.isBackendAvailable = true;
  }
}

export const chatbotService = new ChatbotService();