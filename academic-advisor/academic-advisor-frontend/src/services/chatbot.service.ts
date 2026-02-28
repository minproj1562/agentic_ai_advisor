// academic-advisor-frontend/src/services/chatbot.service.ts

import { auth } from './firebase.config';
import type { ChatMessage, ChatResponseContent, ChatFeedback } from '../types/chatbot.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Out-of-scope patterns ───────────────────────────────

const OUT_OF_SCOPE_PATTERNS = [
  /\b(movie|film|actor|actress|bollywood|hollywood|netflix)\b/i,
  /\b(cricket|football|soccer|basketball|ipl|fifa|sports)\b/i,
  /\b(politics|election|vote|government|minister|party)\b/i,
  /\b(weather|recipe|cook|food|restaurant|hotel)\b/i,
  /\b(game|gaming|pubg|fortnite|minecraft|gta)\b/i,
  /\b(relationship|dating|love|marriage)\b/i,
];

function isOutOfScope(msg: string): boolean {
  return OUT_OF_SCOPE_PATTERNS.some(p => p.test(msg));
}

// ── Service ─────────────────────────────────────────────

class ChatbotService {
  private sessionToken: string | null = null;
  private conversationHistory: ChatMessage[] = [];
  private isBackendAvailable = true;

  constructor() {
    this.restoreSession();
  }

  // ── Core: send message ────────────────────────────────

  async sendMessage(
    message: string,
    includeStudentData = true,
  ): Promise<ChatResponseContent | string> {
    // Client-side out-of-scope guard
    if (isOutOfScope(message)) {
      return 'Beyond my scope';
    }

    // Try backend
    if (this.isBackendAvailable) {
      try {
        const token = await this.getAuthToken();

        const res = await fetch(`${API_BASE_URL}/api/v1/chatbot/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            message,
            session_token: this.sessionToken,
            include_student_data: includeStudentData,
          }),
        });

        if (res.ok) {
          const ct = res.headers.get('content-type');
          if (ct?.includes('text/plain')) {
            return await res.text();
          }
          const data = await res.json();
          if (data.session_token) {
            this.sessionToken = data.session_token;
            this.saveSession();
          }
          return data;
        }

        console.warn('Backend error, switching to offline');
        this.isBackendAvailable = false;
      } catch (err) {
        console.warn('Backend unreachable:', err);
        this.isBackendAvailable = false;
      }
    }

    // Offline fallback
    return this.offlineResponse(message);
  }

  // ── Feedback (Task 22) ────────────────────────────────

  async submitFeedback(feedback: ChatFeedback): Promise<boolean> {
    try {
      const token = await this.getAuthToken();
      const res = await fetch(`${API_BASE_URL}/api/v1/chatbot/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(feedback),
      });
      return res.ok;
    } catch {
      console.warn('Feedback submission failed');
      return false;
    }
  }

  // ── Suggestions ───────────────────────────────────────

  async getSuggestions(): Promise<string[]> {
    if (this.isBackendAvailable) {
      try {
        const token = await this.getAuthToken();
        const res = await fetch(
          `${API_BASE_URL}/api/v1/chatbot/suggestions${
            this.sessionToken ? `?session_token=${this.sessionToken}` : ''
          }`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        );
        if (res.ok) {
          const data = await res.json();
          return data.suggestions || this.defaultSuggestions();
        }
      } catch { /* fall through */ }
    }
    return this.defaultSuggestions();
  }

  // ── History ───────────────────────────────────────────

  async getHistory(limit = 20): Promise<ChatMessage[]> {
    return this.conversationHistory.slice(-limit);
  }

  addToHistory(msg: ChatMessage): void {
    this.conversationHistory.push(msg);
    if (this.conversationHistory.length > 50) {
      this.conversationHistory = this.conversationHistory.slice(-50);
    }
  }

  // ── Session management ────────────────────────────────

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
      } catch { /* ignore */ }
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
        const s = JSON.parse(saved);
        this.sessionToken = s.token;
        this.conversationHistory = s.history || [];
      }
    } catch { /* ignore */ }
  }

  isOnlineMode(): boolean {
    return this.isBackendAvailable;
  }

  retryBackendConnection(): void {
    this.isBackendAvailable = true;
  }

  isOutOfScope(response: ChatResponseContent | string): boolean {
    if (typeof response === 'string') return response === 'Beyond my scope';
    return response.intent === 'OUT_OF_SCOPE';
  }

  // ── Private helpers ───────────────────────────────────

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
      'How to become a data scientist?',
      'Show my academic performance',
      'Which electives for ML career?',
      'Create a study plan',
      'Career options in cybersecurity?',
    ];
  }

  private offlineResponse(message: string): ChatResponseContent {
    return {
      type: 'text',
      intent: 'GENERAL',
      content: {
        message:
          "I'm currently in offline mode with limited capabilities.\n\n" +
          'I can help with:\n' +
          '📚 Syllabus & concepts\n' +
          '👨‍🏫 Faculty info\n' +
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

export const chatbotService = new ChatbotService();
export type { ChatMessage, ChatResponseContent };