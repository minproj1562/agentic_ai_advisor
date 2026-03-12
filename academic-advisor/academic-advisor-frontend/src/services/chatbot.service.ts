// academic-advisor-frontend/src/services/chatbot.service.ts

import { auth } from './firebase.config';
import type { ChatMessage, ChatResponseContent, ChatFeedback } from '../types/chatbot.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ══════════════════════════════════════════════════════════
// OUT-OF-SCOPE DETECTION
// ══════════════════════════════════════════════════════════

const OUT_OF_SCOPE_PATTERNS = [
  /\b(movie|film|actor|actress|bollywood|hollywood|netflix|show|series)\b/i,
  /\b(cricket|football|soccer|basketball|ipl|fifa|sports|match|player)\b/i,
  /\b(politics|election|vote|government|minister|party|congress|bjp)\b/i,
  /\b(weather|recipe|cook|food|restaurant|hotel|travel|vacation)\b/i,
  /\b(game|gaming|pubg|fortnite|minecraft|gta|xbox|playstation)\b/i,
  /\b(relationship|dating|love|marriage|breakup)\b/i,
  /\b(religion|god|temple|church|mosque|prayer)\b/i,
];

function isOutOfScope(msg: string): boolean {
  return OUT_OF_SCOPE_PATTERNS.some(p => p.test(msg));
}

// ══════════════════════════════════════════════════════════
// CHATBOT SERVICE CLASS
// ══════════════════════════════════════════════════════════

class ChatbotService {
  private sessionToken: string | null = null;
  private conversationHistory: ChatMessage[] = [];
  private isBackendAvailable = true;

  constructor() {
    this.restoreSession();
  }

  // ──────────────────────────────────────────────────────
  // CORE: Send Message
  // ──────────────────────────────────────────────────────

  async sendMessage(
    message: string,
    studentData?: Record<string, unknown>,
    includeStudentData = true,
  ): Promise<ChatResponseContent | string> {
    // Client-side out-of-scope guard
    if (isOutOfScope(message)) {
      return this.createOutOfScopeResponse();
    }

    // Try backend
    if (this.isBackendAvailable) {
      try {
        const token = await this.getAuthToken();
        
        const requestBody: Record<string, unknown> = {
          message: message.trim(),
          session_token: this.sessionToken,
          include_student_data: includeStudentData,
        };
        
        if (includeStudentData && studentData) {
          requestBody.student_data = studentData;
        }

        console.log('📤 Sending to chatbot:', {
          message: message.trim().substring(0, 50) + '...',
          hasStudentData: !!studentData,
          hasSessionToken: !!this.sessionToken,
        });

        const response = await fetch(`${API_BASE_URL}/api/v1/chatbot/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(requestBody),
        });

        if (response.ok) {
          const data = await response.json();
          console.log('📥 JSON response:', {
            type: data.type,
            intent: data.intent,
            confidence: data.confidence,
          });
          
          // Update session token
          if (data.session_token) {
            this.sessionToken = data.session_token;
            this.saveSession();
          }
          
          return data as ChatResponseContent;
        }

        console.warn(`Backend returned ${response.status}, switching to offline`);
        this.isBackendAvailable = false;
        
      } catch (err) {
        console.warn('Backend unreachable:', err);
        this.isBackendAvailable = false;
      }
    }

    // Offline fallback
    return this.offlineResponse(message);
  }

  // ──────────────────────────────────────────────────────
  // Feedback
  // ──────────────────────────────────────────────────────

  async submitFeedback(feedback: ChatFeedback): Promise<boolean> {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/chatbot/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(feedback),
      });
      return response.ok;
    } catch {
      console.warn('Feedback submission failed');
      return false;
    }
  }

  // ──────────────────────────────────────────────────────
  // Suggestions
  // ──────────────────────────────────────────────────────

  async getSuggestions(): Promise<string[]> {
    if (this.isBackendAvailable) {
      try {
        const token = await this.getAuthToken();
        const url = this.sessionToken
          ? `${API_BASE_URL}/api/v1/chatbot/suggestions?session_token=${this.sessionToken}`
          : `${API_BASE_URL}/api/v1/chatbot/suggestions`;
          
        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        
        if (response.ok) {
          const data = await response.json();
          return data.suggestions || this.defaultSuggestions();
        }
      } catch {
        // Fall through to defaults
      }
    }
    return this.defaultSuggestions();
  }

  // ──────────────────────────────────────────────────────
  // History
  // ──────────────────────────────────────────────────────

  async getHistory(limit = 20): Promise<ChatMessage[]> {
    return this.conversationHistory.slice(-limit);
  }

  addToHistory(msg: ChatMessage): void {
    this.conversationHistory.push(msg);
    if (this.conversationHistory.length > 50) {
      this.conversationHistory = this.conversationHistory.slice(-50);
    }
  }

  // ──────────────────────────────────────────────────────
  // Session Management
  // ──────────────────────────────────────────────────────

  async clearSession(): Promise<void> {
    if (this.sessionToken && this.isBackendAvailable) {
      try {
        const token = await this.getAuthToken();
        await fetch(`${API_BASE_URL}/api/v1/chatbot/clear`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ session_token: this.sessionToken }),
        });
      } catch {
        // Ignore errors
      }
    }
    this.sessionToken = null;
    this.conversationHistory = [];
    localStorage.removeItem('chatbot_session');
    this.isBackendAvailable = true;
  }

  getSessionToken(): string | null {
    return this.sessionToken;
  }

  restoreSession(): void {
    try {
      const saved = localStorage.getItem('chatbot_session');
      if (saved) {
        const parsed = JSON.parse(saved);
        const timestamp = new Date(parsed.timestamp);
        const now = new Date();
        const hoursDiff = (now.getTime() - timestamp.getTime()) / (1000 * 60 * 60);
        
        if (hoursDiff < 24) {
          this.sessionToken = parsed.token;
          this.conversationHistory = parsed.history || [];
        } else {
          localStorage.removeItem('chatbot_session');
        }
      }
    } catch {
      // Ignore
    }
  }

  isOnlineMode(): boolean {
    return this.isBackendAvailable;
  }

  retryBackendConnection(): void {
    this.isBackendAvailable = true;
  }

  isOutOfScope(response: ChatResponseContent | string): boolean {
    if (typeof response === 'string') {
      return response.includes('out of scope') || response.includes('academic');
    }
    return response.intent === 'OUT_OF_SCOPE';
  }

  // ──────────────────────────────────────────────────────
  // Private Helpers
  // ──────────────────────────────────────────────────────

  private async getAuthToken(): Promise<string | null> {
    try {
      const user = auth.currentUser;
      return user ? await user.getIdToken() : null;
    } catch {
      return null;
    }
  }

  private saveSession(): void {
    if (this.sessionToken) {
      localStorage.setItem(
        'chatbot_session',
        JSON.stringify({
          token: this.sessionToken,
          history: this.conversationHistory.slice(-20),
          timestamp: new Date().toISOString(),
        }),
      );
    }
  }

  private defaultSuggestions(): string[] {
    return [
      'Explain deadlock in Operating Systems',
      'Who teaches Machine Learning?',
      'How to become a data scientist?',
      'Show my academic performance',
      'Recommend electives for AI career',
    ];
  }

  private createOutOfScopeResponse(): ChatResponseContent {
    return {
      type: 'text',
      intent: 'OUT_OF_SCOPE',
      content: {
        message: "I'm an academic advisor and can only help with academic-related queries.",
        scope: [
          '📚 Syllabus and course content',
          '👨‍🏫 Faculty information',
          '📊 Academic performance',
          '💼 Career guidance in tech',
        ],
      },
      confidence: 'High',
    };
  }

  private offlineResponse(message: string): ChatResponseContent {
    return {
      type: 'text',
      intent: 'GENERAL',
      content: {
        message:
          "I'm currently in offline mode with limited capabilities.\n\n" +
          'I can help you with:\n' +
          '📚 Syllabus & concepts\n' +
          '👨‍🏫 Faculty information\n' +
          '📊 Performance analysis\n' +
          '📖 Elective recommendations\n' +
          '💼 Career guidance\n' +
          '📅 Study plans\n\n' +
          'Please check your connection and try again.',
      },
      confidence: 'Low',
    };
  }
}

// ══════════════════════════════════════════════════════════
// EXPORT
// ══════════════════════════════════════════════════════════

export const chatbotService = new ChatbotService();
export type { ChatMessage, ChatResponseContent };