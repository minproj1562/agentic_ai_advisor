// src/hooks/useChatbot.ts

import { useState, useCallback, useEffect } from 'react';
import { chatbotService } from '../services/chatbot.service';
import type {
  ChatMessage,
  ChatResponseContent,
  ChatFeedback,
  SentimentData,
} from '../types/chatbot.types';

interface UseChatbotReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  suggestions: string[];
  sessionToken: string | null;
  isOnline: boolean;
  currentSentiment: SentimentData | null;
  sendMessage: (message: string) => Promise<void>;
  clearSession: () => Promise<void>;
  submitFeedback: (feedback: ChatFeedback) => Promise<boolean>;
  retryConnection: () => void;
}

export const useChatbot = (): UseChatbotReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [currentSentiment, setCurrentSentiment] = useState<SentimentData | null>(null);

  useEffect(() => {
    chatbotService.restoreSession();
    setSessionToken(chatbotService.getSessionToken());

    const init = async () => {
      const sug = await chatbotService.getSuggestions();
      setSuggestions(sug);
      const history = await chatbotService.getHistory();
      if (history.length > 0) setMessages(history);
    };
    init();
  }, []);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim() || isLoading) return;

      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: message.trim(),
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      chatbotService.addToHistory(userMsg);
      setIsLoading(true);

      // Add loading indicator
      const loadingMsg: ChatMessage = {
        id: 'loading',
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isLoading: true,
      };
      setMessages((prev) => [...prev, loadingMsg]);

      try {
        const response = await chatbotService.sendMessage(message.trim());

        // Remove loading message
        setMessages((prev) => prev.filter((m) => m.id !== 'loading'));

        const responseContent = typeof response === 'object' ? response : null;

        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response,
          timestamp: new Date().toISOString(),
          intent: responseContent?.intent,
          confidence: responseContent?.confidence as 'High' | 'Medium' | 'Low' | undefined,
          sentiment: responseContent?.sentiment,
          advisorSuggestion: responseContent?.advisor_suggestion,
          fromCache: responseContent?.from_cache,
          llmEnhanced: responseContent?.llm_enhanced,
        };

        setMessages((prev) => [...prev, assistantMsg]);
        chatbotService.addToHistory(assistantMsg);
        setSessionToken(chatbotService.getSessionToken());
        setIsOnline(chatbotService.isOnlineMode());

        // Update current sentiment
        if (responseContent?.sentiment) {
          setCurrentSentiment(responseContent.sentiment);
        }

        const newSug = await chatbotService.getSuggestions();
        setSuggestions(newSug);
      } catch (err) {
        console.error('Chat error:', err);

        // Remove loading message
        setMessages((prev) => prev.filter((m) => m.id !== 'loading'));

        const errMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'An error occurred. Please try again.',
          timestamp: new Date().toISOString(),
          isError: true,
          advisorSuggestion: {
            message: '💡 If issues persist, please contact your faculty advisor.',
            action: 'Contact support',
            reason: 'human_escalation',
          },
        };
        setMessages((prev) => [...prev, errMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );

  const clearSession = useCallback(async () => {
    await chatbotService.clearSession();
    setMessages([]);
    setSessionToken(null);
    setIsOnline(true);
    setCurrentSentiment(null);
    const sug = await chatbotService.getSuggestions();
    setSuggestions(sug);
  }, []);

  const submitFeedback = useCallback(async (fb: ChatFeedback) => {
    return chatbotService.submitFeedback(fb);
  }, []);

  const retryConnection = useCallback(() => {
    chatbotService.retryBackendConnection();
    setIsOnline(true);
  }, []);

  return {
    messages,
    isLoading,
    suggestions,
    sessionToken,
    isOnline,
    currentSentiment,
    sendMessage,
    clearSession,
    submitFeedback,
    retryConnection,
  };
};