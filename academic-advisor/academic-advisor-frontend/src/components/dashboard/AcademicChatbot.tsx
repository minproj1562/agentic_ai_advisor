// academic-advisor-frontend/src/components/dashboard/AcademicChatbot.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  RefreshCw, 
  Lightbulb, 
  X, 
  Minimize2, 
  Maximize2,
  Wifi,
  WifiOff,
  AlertCircle,
  CheckCircle,
  BookOpen,
  GraduationCap,
  Users,
  Briefcase,
  Sparkles
} from 'lucide-react';
import { chatbotService, ChatMessage, ChatResponseContent } from '../../services/chatbot.service';
import { useAuth } from '../../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

interface AcademicChatbotProps {
  isFloating?: boolean;
  defaultOpen?: boolean;
  className?: string;
}

const AcademicChatbot: React.FC<AcademicChatbotProps> = ({
  isFloating = true,
  defaultOpen = false,
  className = '',
}) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load suggestions on mount
  useEffect(() => {
    const loadInitialData = async () => {
      const sug = await chatbotService.getSuggestions();
      setSuggestions(sug);
      
      chatbotService.restoreSession();
      const history = await chatbotService.getHistory();
      if (history.length > 0) {
        setMessages(history);
        setShowSuggestions(false);
      }
    };
    
    loadInitialData();
  }, []);

  // Update online status
  useEffect(() => {
    setIsOnline(chatbotService.isOnlineMode());
  }, [messages]);

  // Handle sending messages
  const handleSendMessage = async (message: string = inputValue) => {
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    chatbotService.addToHistory(userMessage);
    setInputValue('');
    setIsLoading(true);
    setShowSuggestions(false);

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isLoading: true,
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      const response = await chatbotService.sendMessage(message.trim());
      
      // Remove loading message and add response
      setMessages(prev => {
        const filtered = prev.filter(m => !m.isLoading);
        
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: response,
          timestamp: new Date().toISOString(),
          intent: typeof response === 'object' ? response.intent : undefined,
          confidence: typeof response === 'object' ? response.confidence as any : undefined,
        };
        
        chatbotService.addToHistory(assistantMessage);
        return [...filtered, assistantMessage];
      });

      // Update online status
      setIsOnline(chatbotService.isOnlineMode());

      // Update suggestions
      const newSuggestions = await chatbotService.getSuggestions();
      setSuggestions(newSuggestions);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => {
        const filtered = prev.filter(m => !m.isLoading);
        return [...filtered, {
          id: Date.now().toString(),
          role: 'assistant',
          content: {
            type: 'text',
            intent: 'ERROR',
            content: {
              message: "I apologize, but I encountered an issue. Please try again or rephrase your question."
            },
            confidence: 'Low'
          },
          timestamp: new Date().toISOString(),
          isError: true,
        }];
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle clear session
  const handleClearSession = async () => {
    await chatbotService.clearSession();
    setMessages([]);
    setShowSuggestions(true);
    setIsOnline(true);
    const sug = await chatbotService.getSuggestions();
    setSuggestions(sug);
  };

  // Handle retry connection
  const handleRetryConnection = () => {
    chatbotService.retryBackendConnection();
    setIsOnline(true);
  };

  // Get intent icon
  const getIntentIcon = (intent?: string) => {
    switch (intent) {
      case 'SYLLABUS_QUERY':
        return <BookOpen className="w-4 h-4 text-blue-500" />;
      case 'FACULTY_QUERY':
        return <Users className="w-4 h-4 text-green-500" />;
      case 'PERFORMANCE_QUERY':
        return <GraduationCap className="w-4 h-4 text-purple-500" />;
      case 'ELECTIVE_QUERY':
        return <Sparkles className="w-4 h-4 text-yellow-500" />;
      case 'CAREER_QUERY':
        return <Briefcase className="w-4 h-4 text-indigo-500" />;
      default:
        return <Bot className="w-4 h-4 text-gray-500" />;
    }
  };

  // Render message content
  const renderMessageContent = (message: ChatMessage) => {
    const content = message.content;
    
    if (message.isLoading) {
      return (
        <div className="flex items-center space-x-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="text-gray-500">Thinking...</span>
        </div>
      );
    }

    // Plain text (out of scope or error)
    if (typeof content === 'string') {
      const isOutOfScope = content === 'Beyond my scope' || content === 'Irrelevant query';
      return (
        <div className={`${isOutOfScope ? 'text-orange-600' : ''}`}>
          {isOutOfScope && <AlertCircle className="w-4 h-4 inline mr-1" />}
          <p className="whitespace-pre-wrap">{content}</p>
        </div>
      );
    }

    // Structured response
    return renderStructuredResponse(content as ChatResponseContent, message.intent);
  };

  // Render structured response
  const renderStructuredResponse = (response: ChatResponseContent, intent?: string) => {
    const { type, content, confidence } = response;

    switch (type) {
      case 'concept_explanation':
        return (
          <div className="space-y-3">
            {content.definition && (
              <div>
                <h4 className="font-semibold text-sm text-blue-600 dark:text-blue-400 flex items-center gap-1">
                  <BookOpen className="w-4 h-4" />
                  Definition
                </h4>
                <p className="text-gray-700 dark:text-gray-300 mt-1">{content.definition}</p>
              </div>
            )}
            {content.key_points?.length > 0 && (
              <div>
                <h4 className="font-semibold text-sm text-blue-600 dark:text-blue-400">Key Points</h4>
                <ul className="list-disc list-inside space-y-1 mt-1 text-gray-700 dark:text-gray-300">
                  {content.key_points.map((point: string, idx: number) => (
                    <li key={idx} className="text-sm">{point}</li>
                  ))}
                </ul>
              </div>
            )}
            {content.related_topics?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {content.related_topics.map((topic: string, idx: number) => (
                  <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    {topic}
                  </span>
                ))}
              </div>
            )}
            {content.exam_relevance && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded text-sm border-l-2 border-yellow-400">
                <span className="font-semibold text-yellow-700 dark:text-yellow-400">📝 Exam Relevance: </span>
                <span className="text-yellow-800 dark:text-yellow-300">{content.exam_relevance}</span>
              </div>
            )}
            <ConfidenceBadge confidence={confidence} />
          </div>
        );

      case 'faculty_recommendation':
        return (
          <div className="space-y-3">
            <h4 className="font-semibold flex items-center gap-1">
              <Users className="w-4 h-4 text-green-500" />
              Recommended Faculty
            </h4>
            {content.recommendations?.map((rec: any, idx: number) => (
              <div key={idx} className="border dark:border-gray-700 rounded-lg p-3 bg-white dark:bg-gray-800">
                <div className="flex justify-between items-start">
                  <div>
                    <h5 className="font-medium text-gray-900 dark:text-white">{rec.name}</h5>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{rec.department}</p>
                  </div>
                  {rec.rating && (
                    <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-1 rounded flex items-center gap-1">
                      ⭐ {rec.rating}
                    </span>
                  )}
                </div>
                <div className="mt-2 text-sm space-y-1">
                  <p><span className="font-medium text-gray-700 dark:text-gray-300">Subjects:</span> <span className="text-gray-600 dark:text-gray-400">{rec.subjects?.join(', ')}</span></p>
                  {rec.research_areas && (
                    <p><span className="font-medium text-gray-700 dark:text-gray-300">Research:</span> <span className="text-gray-600 dark:text-gray-400">{rec.research_areas?.join(', ')}</span></p>
                  )}
                  {rec.teaching_style && (
                    <p><span className="font-medium text-gray-700 dark:text-gray-300">Style:</span> <span className="text-gray-600 dark:text-gray-400">{rec.teaching_style}</span></p>
                  )}
                </div>
                {rec.reasoning?.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 flex flex-wrap gap-1">
                    {rec.reasoning.map((reason: string, i: number) => (
                      <span key={i} className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                        ✓ {reason}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <ConfidenceBadge confidence={confidence} />
          </div>
        );

      case 'faculty_list':
        return (
          <div className="space-y-3">
            <h4 className="font-semibold">Faculty Directory ({content.count} members)</h4>
            <div className="space-y-2">
              {content.faculty?.map((f: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  <div>
                    <p className="font-medium text-sm">{f.name}</p>
                    <p className="text-xs text-gray-500">{f.subjects_taught?.join(', ')}</p>
                  </div>
                  <span className="text-xs text-gray-400">{f.experience_years}y exp</span>
                </div>
              ))}
            </div>
            <ConfidenceBadge confidence={confidence} />
          </div>
        );

      case 'elective_recommendation':
        return (
          <div className="space-y-3">
            <h4 className="font-semibold flex items-center gap-1">
              <Sparkles className="w-4 h-4 text-yellow-500" />
              Recommended Electives
            </h4>
            {content.recommendations?.map((rec: any, idx: number) => (
              <div key={idx} className="border dark:border-gray-700 rounded-lg p-3">
                <div className="flex justify-between items-start">
                  <h5 className="font-medium">{rec.name}</h5>
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                    {rec.category}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.description}</p>
                {rec.career_paths && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {rec.career_paths.map((path: string, i: number) => (
                      <span key={i} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded">
                        → {path}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {content.advice && (
              <p className="text-sm text-gray-500 italic">{content.advice}</p>
            )}
            <ConfidenceBadge confidence={confidence} />
          </div>
        );

      case 'text':
      default:
        return (
          <div className="space-y-2">
            <p className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
              {content.message || JSON.stringify(content)}
            </p>
            {confidence && <ConfidenceBadge confidence={confidence} />}
          </div>
        );
    }
  };

  // Confidence badge
  const ConfidenceBadge: React.FC<{ confidence: string }> = ({ confidence }) => {
    const config = {
      High: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', icon: '✓' },
      Medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400', icon: '~' },
      Low: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', icon: '!' },
    };

    const { bg, text, icon } = config[confidence as keyof typeof config] || config.Medium;

    return (
      <div className="flex justify-end mt-2">
        <span className={`text-xs px-2 py-0.5 rounded ${bg} ${text}`}>
          {icon} {confidence} Confidence
        </span>
      </div>
    );
  };

  // Floating chat button
  if (isFloating && !isOpen) {
    return (
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all z-50"
      >
        <Bot className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
      </motion.button>
    );
  }

  // Container classes
  const containerClasses = isFloating
    ? `fixed bottom-6 right-6 w-[400px] ${isMinimized ? 'h-14' : 'h-[600px]'} bg-white dark:bg-gray-900 rounded-xl shadow-2xl flex flex-col z-50 transition-all duration-300 border border-gray-200 dark:border-gray-700`
    : `w-full h-full bg-white dark:bg-gray-900 rounded-xl shadow-lg flex flex-col ${className}`;

  return (
    <div className={containerClasses}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b dark:border-gray-700 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-xl">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Bot className="w-8 h-8" />
            <span className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${isOnline ? 'bg-green-400' : 'bg-yellow-400'}`} />
          </div>
          <div>
            <h3 className="font-semibold">Academic Assistant</h3>
            {!isMinimized && (
              <p className="text-xs text-white/80 flex items-center gap-1">
                {isOnline ? (
                  <>
                    <Wifi className="w-3 h-3" />
                    Online Mode
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3" />
                    Offline Mode
                  </>
                )}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-1">
          {!isOnline && (
            <button
              onClick={handleRetryConnection}
              className="p-1.5 hover:bg-white/20 rounded transition-colors"
              title="Retry connection"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={handleClearSession}
            className="p-1.5 hover:bg-white/20 rounded transition-colors"
            title="Clear chat"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          {isFloating && (
            <>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:bg-white/20 rounded transition-colors"
              >
                {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/20 rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Offline mode notice */}
          {!isOnline && (
            <div className="px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800">
              <p className="text-xs text-yellow-700 dark:text-yellow-400 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Running in offline mode with limited knowledge base
              </p>
            </div>
          )}

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Welcome message */}
            {messages.length === 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-8"
              >
                <div className="w-16 h-16 mx-auto bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-4">
                  <Bot className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200 text-lg">
                  Academic Guidance Assistant
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 max-w-xs mx-auto">
                  I can help you with syllabus explanations, faculty info, performance analysis, and career guidance.
                </p>
                
                {/* Quick action buttons */}
                <div className="mt-4 grid grid-cols-2 gap-2 max-w-xs mx-auto">
                  {[
                    { icon: <BookOpen className="w-4 h-4" />, text: "Syllabus", color: "blue" },
                    { icon: <Users className="w-4 h-4" />, text: "Faculty", color: "green" },
                    { icon: <GraduationCap className="w-4 h-4" />, text: "Performance", color: "purple" },
                    { icon: <Briefcase className="w-4 h-4" />, text: "Career", color: "orange" },
                  ].map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(`Help me with ${item.text.toLowerCase()}`)}
                      className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors
                        bg-${item.color}-50 hover:bg-${item.color}-100 text-${item.color}-700
                        dark:bg-${item.color}-900/20 dark:hover:bg-${item.color}-900/30 dark:text-${item.color}-400`}
                    >
                      {item.icon}
                      {item.text}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Suggestions */}
            {showSuggestions && suggestions.length > 0 && messages.length === 0 && (
              <div className="space-y-2">
                <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                  <Lightbulb className="w-4 h-4 mr-1 text-yellow-500" />
                  <span>Try these questions:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion, idx) => (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      onClick={() => handleSendMessage(suggestion)}
                      className="text-xs bg-gray-100 dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-lg transition-colors border border-transparent hover:border-blue-200 dark:hover:border-blue-800"
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl p-3 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                        : message.isError
                        ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.role === 'assistant' && (
                        <div className="mt-0.5 flex-shrink-0">
                          {message.isError ? (
                            <AlertCircle className="w-5 h-5 text-red-500" />
                          ) : (
                            getIntentIcon(message.intent)
                          )}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        {renderMessageContent(message)}
                      </div>
                      {message.role === 'user' && (
                        <User className="w-5 h-5 mt-0.5 text-white/80 flex-shrink-0" />
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-b-xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center space-x-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about academics..."
                className="flex-1 px-4 py-2.5 border dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className="p-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg transition-all shadow-md disabled:shadow-none"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </form>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
              Academic queries only • {isOnline ? 'Connected' : 'Offline mode'}
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default AcademicChatbot;