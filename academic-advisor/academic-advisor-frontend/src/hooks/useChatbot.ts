// academic-advisor-frontend/src/hooks/useChatbot.ts

import { useState, useCallback, useEffect } from 'react';
import { chatbotService } from '../services/chatbot.service';
import { ChatMessage, ChatResponseContent } from '../types/chatbot.types';

interface UseChatbotReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  suggestions: string[];
  sessionToken: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearSession: () => Promise<void>;
  loadHistory: () => Promise<void>;
}

export const useChatbot = (): UseChatbotReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  // Initialize
  useEffect(() => {
    chatbotService.restoreSession();
    setSessionToken(chatbotService.getSessionToken());
    
    const loadInitialData = async () => {
      const sug = await chatbotService.getSuggestions();
      setSuggestions(sug);
      
      const history = await chatbotService.getHistory();
      if (history.length > 0) {
        setMessages(history);
      }
    };
    
    loadInitialData();
  }, []);

  // Send message
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await chatbotService.sendMessage(message.trim());
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
        intent: typeof response === 'object' ? response.intent : undefined,
        confidence: typeof response === 'object' ? response.confidence as any : undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setSessionToken(chatbotService.getSessionToken());

      // Update suggestions
      const newSuggestions = await chatbotService.getSuggestions();
      setSuggestions(newSuggestions);

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'An error occurred. Please try again.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  // Clear session
  const clearSession = useCallback(async () => {
    await chatbotService.clearSession();
    setMessages([]);
    setSessionToken(null);
    
    const sug = await chatbotService.getSuggestions();
    setSuggestions(sug);
  }, []);

  // Load history
  const loadHistory = useCallback(async () => {
    const history = await chatbotService.getHistory();
    setMessages(history);
  }, []);

  return {
    messages,
    isLoading,
    suggestions,
    sessionToken,
    sendMessage,
    clearSession,
    loadHistory,
  };
};