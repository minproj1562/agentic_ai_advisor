// src/components/messaging/MessageCenter.tsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Paperclip, 
  Search, 
  MoreVertical, 
  Clock,
  CheckCircle,
  AlertCircle,
  Save,
  RefreshCw,
  User,
  Bot,
  Archive,
  X,
  Mic,
  MicOff,
  Image as ImageIcon,
  File,
  Smile,
  Settings,
  Download,
  Trash2,
  Edit,
  Reply,
  Forward,
  Star,
  Filter,
  Calendar,
  Phone,
  Video,
  Info
} from 'lucide-react';

// Mock hooks (replace with actual implementations)
const useMessaging = () => {
  return {
    isOnline: true,
    sendMessage: async (message: any) => {
      console.log('Sending message:', message);
      return Promise.resolve();
    },
    saveDraft: (draft: string) => {
      localStorage.setItem('messageDraft', draft);
    },
    loadDrafts: () => {
      const draft = localStorage.getItem('messageDraft');
      return draft ? [draft] : [];
    },
    clearDrafts: () => {
      localStorage.removeItem('messageDraft');
    },
    loadMessages: async (): Promise<Message[]> => {
      // Mock messages with proper typing
      return [
        {
          id: '1',
          text: 'Welcome to the message center! How can I help you today?',
          sender: 'ai',
          senderName: 'Smart Assistant',
          timestamp: new Date(Date.now() - 300000),
          status: 'read',
        }
      ];
    },
    markAsRead: (messageId: string) => {
      console.log('Marking as read:', messageId);
    },
    deleteMessage: (messageId: string) => {
      console.log('Deleting message:', messageId);
    },
    editMessage: (messageId: string, text: string) => {
      console.log('Editing message:', messageId, text);
    },
    starMessage: (messageId: string) => {
      console.log('Starring message:', messageId);
    },
    addReaction: (messageId: string, emoji: string) => {
      console.log('Adding reaction:', messageId, emoji);
    }
  };
};

const useAuth = () => {
  return {
    user: {
      id: '1',
      name: 'John Doe',
      avatar: '/user-avatar.png'
    }
  };
};

const useAnalytics = () => {
  return {
    trackEvent: (event: string, data: any) => {
      console.log('Analytics event:', event, data);
    }
  };
};

// Mock toast (replace with actual react-hot-toast)
const toast = {
  success: (message: string) => console.log('Success:', message),
  error: (message: string) => console.log('Error:', message),
};

// Mock EmojiPicker (replace with actual emoji-picker-react)
const EmojiPicker: React.FC<{ onEmojiClick: (emoji: any) => void }> = ({ onEmojiClick }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-80">
      <div className="grid grid-cols-8 gap-2">
        {['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣'].map((emoji, index) => (
          <button
            key={index}
            onClick={() => onEmojiClick({ emoji })}
            className="text-2xl hover:bg-gray-100 rounded p-1"
          >
            {emoji}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">Simple emoji picker</p>
    </div>
  );
};

// Types
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'system' | 'ai' | 'support';
  senderName?: string;
  senderAvatar?: string;
  timestamp: Date;
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'failed';
  attachments?: Attachment[];
  replyTo?: string;
  edited?: boolean;
  starred?: boolean;
  reactions?: Reaction[];
}

interface Attachment {
  id: string;
  type: 'image' | 'file' | 'audio';
  url: string;
  name: string;
  size: number;
}

interface Reaction {
  emoji: string;
  userId: string;
  timestamp: Date;
}

interface MessageCenterProps {
  isOpen: boolean;
  onClose: () => void;
  position?: 'bottom-right' | 'bottom-left' | 'center';
}

const MessageCenter: React.FC<MessageCenterProps> = ({ 
  isOpen, 
  onClose, 
  position = 'bottom-right' 
}) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<'all' | 'starred' | 'unread'>('all');
  const [showSettings, setShowSettings] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();
  const { 
    isOnline, 
    sendMessage, 
    saveDraft, 
    loadDrafts,
    clearDrafts,
    loadMessages,
    markAsRead,
    deleteMessage,
    editMessage,
    starMessage,
    addReaction
  } = useMessaging();

  // Load messages on mount
  useEffect(() => {
    const loadInitialMessages = async () => {
      try {
        const initialMessages = await loadMessages();
        setMessages(initialMessages);
        
        // Load drafts
        const drafts = loadDrafts();
        if (drafts.length > 0 && !message) {
          setMessage(drafts[0]);
          toast.success('Draft restored');
        }
      } catch (error) {
        console.error('Failed to load messages:', error);
      }
    };

    if (isOpen) {
      loadInitialMessages();
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-save draft
  useEffect(() => {
    const draftTimer = setTimeout(() => {
      if (message.trim() && !isOnline) {
        saveDraft(message);
      }
    }, 2000);

    return () => clearTimeout(draftTimer);
  }, [message, isOnline, saveDraft]);

  // Handle sending message
  const handleSend = async () => {
    if (!message.trim() && attachments.length === 0) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: 'user',
      senderName: user?.name || 'You',
      senderAvatar: user?.avatar,
      timestamp: new Date(),
      status: 'sending',
      attachments: attachments.map(file => ({
        id: Date.now().toString(),
        type: file.type.startsWith('image/') ? 'image' : 'file',
        url: URL.createObjectURL(file),
        name: file.name,
        size: file.size,
      })),
    };

    setMessages(prev => [...prev, newMessage]);
    setMessage('');
    setAttachments([]);

    if (isOnline) {
      try {
        await sendMessage(newMessage);
        
        // Update message status
        setMessages(prev => 
          prev.map(msg => 
            msg.id === newMessage.id 
              ? { ...msg, status: 'delivered' }
              : msg
          )
        );

        // Track analytics
        trackEvent('message_sent', {
          messageLength: message.length,
          hasAttachments: attachments.length > 0,
          userId: user?.id,
        });

        // Simulate AI response
        setTimeout(() => {
          setIsTyping(true);
          setTimeout(() => {
            const aiResponse: Message = {
              id: Date.now().toString(),
              text: "Thanks for your message! Our team will respond shortly. Is there anything specific I can help you with?",
              sender: 'ai',
              senderName: 'Smart Assistant',
              senderAvatar: '/ai-avatar.png',
              timestamp: new Date(),
              status: 'delivered',
            };
            setMessages(prev => [...prev, aiResponse]);
            setIsTyping(false);
          }, 2000);
        }, 1000);
      } catch (error) {
        // Update message status to failed
        setMessages(prev => 
          prev.map(msg => 
            msg.id === newMessage.id 
              ? { ...msg, status: 'failed' }
              : msg
          )
        );
        
        toast.error('Failed to send message. Saved as draft.');
        saveDraft(message);
      }
    } else {
      saveDraft(message);
      toast.success('Message saved as draft (offline mode)');
    }
  };

  // Handle file attachment
  const handleFileAttachment = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    const validFiles = files.filter(file => {
      if (file.size > maxSize) {
        toast.error(`${file.name} is too large. Max size is 10MB.`);
        return false;
      }
      return true;
    });

    setAttachments(prev => [...prev, ...validFiles]);
    
    trackEvent('attachment_added', {
      count: validFiles.length,
      types: validFiles.map(f => f.type),
    });
  };

  // Handle voice recording
  const toggleRecording = async () => {
    if (isRecording) {
      // Stop recording logic
      setIsRecording(false);
      toast.success('Recording saved');
    } else {
      // Start recording logic
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsRecording(true);
        // Implement actual recording logic here
      } catch (error) {
        toast.error('Microphone access denied');
      }
    }
  };

  // Handle keyboard shortcuts
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    
    if (e.key === 'Escape') {
      onClose();
    }
  };

  // Filter messages based on filter type
  const filteredMessages = messages.filter(msg => {
    if (filterType === 'starred') return msg.starred;
    if (filterType === 'unread') return msg.status !== 'read';
    
    if (searchQuery) {
      return msg.text.toLowerCase().includes(searchQuery.toLowerCase());
    }
    
    return true;
  });

  // Position classes
  const positionClasses = {
    'bottom-right': 'bottom-24 right-8',
    'bottom-left': 'bottom-24 left-8',
    'center': 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 100, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 100, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className={`fixed ${positionClasses[position]} w-[420px] max-w-[calc(100vw-4rem)] h-[680px] max-h-[calc(100vh-8rem)] bg-white rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden`}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-white">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="h-12 w-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <Bot className="h-7 w-7" />
                  </div>
                  <span className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white ${
                    isOnline ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                </div>
                <div>
                  <h3 className="font-bold text-lg">Smart Assistant</h3>
                  <p className="text-xs opacity-90 flex items-center">
                    {isOnline ? (
                      <>
                        <span className="h-2 w-2 bg-green-400 rounded-full mr-1 animate-pulse" />
                        Online • Typically replies instantly
                      </>
                    ) : (
                      <>
                        <span className="h-2 w-2 bg-gray-400 rounded-full mr-1" />
                        Offline • Messages will be saved
                      </>
                    )}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label="Settings"
                >
                  <Settings className="h-5 w-5" />
                </button>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Search and Filter Bar */}
            <div className="flex space-x-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white/60" />
                <input
                  type="text"
                  placeholder="Search messages..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/20 backdrop-blur-xl rounded-xl text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50"
                />
              </div>
              
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as 'all' | 'starred' | 'unread')}
                className="px-3 py-2 bg-white/20 backdrop-blur-xl rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-white/50"
              >
                <option value="all">All</option>
                <option value="starred">Starred</option>
                <option value="unread">Unread</option>
              </select>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-white">
            {filteredMessages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center h-full text-gray-400"
              >
                <div className="h-16 w-16 mb-4 opacity-50 flex items-center justify-center">
                  <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <p className="text-lg font-medium">No messages yet</p>
                <p className="text-sm mt-1">Start a conversation!</p>
              </motion.div>
            ) : (
              filteredMessages.map((msg, index) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  onMouseEnter={() => setSelectedMessage(msg.id)}
                  onMouseLeave={() => setSelectedMessage(null)}
                >
                  <div className={`max-w-[75%] relative group`}>
                    {/* Message Bubble */}
                    <div
                      className={`p-3 rounded-2xl ${
                        msg.sender === 'user'
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                          : msg.sender === 'ai'
                          ? 'bg-white border border-gray-200 text-gray-800'
                          : 'bg-yellow-100 border border-yellow-300 text-gray-800'
                      }`}
                    >
                      {/* Sender Info (for non-user messages) */}
                      {msg.sender !== 'user' && (
                        <div className="flex items-center mb-2">
                          <div className="h-6 w-6 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white text-xs font-bold mr-2">
                            {msg.sender === 'ai' ? <Bot className="h-4 w-4" /> : msg.senderName?.[0]}
                          </div>
                          <span className="text-xs font-semibold">
                            {msg.senderName || (msg.sender === 'ai' ? 'AI Assistant' : 'System')}
                          </span>
                        </div>
                      )}
                      
                      {/* Message Text */}
                      <p className={`text-sm ${msg.sender === 'user' ? 'text-white' : ''}`}>
                        {msg.text}
                      </p>
                      
                      {/* Attachments */}
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div className="mt-2 space-y-2">
                          {msg.attachments.map(attachment => (
                            <div
                              key={attachment.id}
                              className={`flex items-center space-x-2 p-2 rounded-lg ${
                                msg.sender === 'user' ? 'bg-white/20' : 'bg-gray-100'
                              }`}
                            >
                              {attachment.type === 'image' ? (
                                <ImageIcon className="h-4 w-4" />
                              ) : (
                                <File className="h-4 w-4" />
                              )}
                              <span className="text-xs truncate">{attachment.name}</span>
                              <Download className="h-3 w-3 cursor-pointer hover:scale-110 transition-transform" />
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {/* Message Footer */}
                      <div className={`flex items-center justify-between mt-2 text-xs ${
                        msg.sender === 'user' ? 'text-white/70' : 'text-gray-500'
                      }`}>
                        <span>{msg.timestamp.toLocaleTimeString()}</span>
                        {msg.sender === 'user' && (
                          <span className="flex items-center ml-2">
                            {msg.status === 'sending' && <Clock className="h-3 w-3 animate-spin" />}
                            {msg.status === 'sent' && <CheckCircle className="h-3 w-3" />}
                            {msg.status === 'delivered' && (
                              <div className="flex">
                                <CheckCircle className="h-3 w-3" />
                                <CheckCircle className="h-3 w-3 -ml-1" />
                              </div>
                            )}
                            {msg.status === 'read' && (
                              <div className="flex text-blue-400">
                                <CheckCircle className="h-3 w-3" />
                                <CheckCircle className="h-3 w-3 -ml-1" />
                              </div>
                            )}
                            {msg.status === 'failed' && <AlertCircle className="h-3 w-3 text-red-400" />}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Message Actions (shown on hover) */}
                    {selectedMessage === msg.id && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className={`absolute ${
                          msg.sender === 'user' ? 'left-0' : 'right-0'
                        } top-0 flex items-center space-x-1 bg-white rounded-lg shadow-lg p-1 -mt-10`}
                      >
                        <button
                          onClick={() => starMessage(msg.id)}
                          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                          aria-label="Star message"
                        >
                          <Star className={`h-4 w-4 ${msg.starred ? 'text-yellow-500 fill-current' : 'text-gray-500'}`} />
                        </button>
                        <button
                          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                          aria-label="Reply"
                        >
                          <Reply className="h-4 w-4 text-gray-500" />
                        </button>
                        <button
                          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                          aria-label="Forward"
                        >
                          <Forward className="h-4 w-4 text-gray-500" />
                        </button>
                        {msg.sender === 'user' && (
                          <>
                            <button
                              onClick={() => editMessage(msg.id, msg.text)}
                              className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                              aria-label="Edit"
                            >
                              <Edit className="h-4 w-4 text-gray-500" />
                            </button>
                            <button
                              onClick={() => deleteMessage(msg.id)}
                              className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                              aria-label="Delete"
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </button>
                          </>
                        )}
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              ))
            )}
            
            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center space-x-2 text-gray-500"
              >
                <div className="flex items-center space-x-1 bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <motion.span
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0 }}
                    className="h-2 w-2 bg-gray-400 rounded-full"
                  />
                  <motion.span
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
                    className="h-2 w-2 bg-gray-400 rounded-full"
                  />
                  <motion.span
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }}
                    className="h-2 w-2 bg-gray-400 rounded-full"
                  />
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Attachments Preview */}
          {attachments.length > 0 && (
            <div className="px-4 py-2 bg-gray-50 border-t">
              <div className="flex items-center space-x-2 overflow-x-auto">
                {attachments.map((file, index) => (
                  <div
                    key={index}
                    className="relative flex-shrink-0 p-2 bg-white rounded-lg border border-gray-200"
                  >
                    <button
                      onClick={() => setAttachments(prev => prev.filter((_, i) => i !== index))}
                      className="absolute -top-2 -right-2 h-5 w-5 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                    {file.type.startsWith('image/') ? (
                      <img
                        src={URL.createObjectURL(file)}
                        alt={file.name}
                        className="h-16 w-16 object-cover rounded"
                      />
                    ) : (
                      <div className="h-16 w-16 flex flex-col items-center justify-center">
                        <File className="h-8 w-8 text-gray-400" />
                        <span className="text-xs text-gray-500 truncate w-full text-center">
                          {file.name}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Offline Banner */}
          {!isOnline && (
            <div className="bg-yellow-50 border-t border-yellow-200 px-4 py-2 flex items-center justify-between">
              <div className="flex items-center text-yellow-700">
                <AlertCircle className="h-4 w-4 mr-2" />
                <span className="text-xs">Offline mode - messages will be saved locally</span>
              </div>
              <button
                onClick={() => window.location.reload()}
                className="p-1 hover:bg-yellow-100 rounded transition-colors"
                aria-label="Retry connection"
              >
                <RefreshCw className="h-4 w-4 text-yellow-700" />
              </button>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t bg-white p-4">
            {/* Action Buttons */}
            <div className="flex items-center space-x-2 mb-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
                aria-label="Attach file"
              >
                <Paperclip className="h-5 w-5 text-gray-500" />
              </button>
              
              <button
                onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
                aria-label="Add emoji"
              >
                <Smile className="h-5 w-5 text-gray-500" />
              </button>
              
              <button
                onClick={toggleRecording}
                className={`p-2 rounded-xl transition-colors ${
                  isRecording ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100 text-gray-500'
                }`}
                aria-label={isRecording ? 'Stop recording' : 'Start recording'}
              >
                {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </button>
              
              <div className="flex-1" />
              
              <span className="text-xs text-gray-500">
                {message.length}/1000
              </span>
            </div>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileAttachment}
              className="hidden"
              accept="image/*,.pdf,.doc,.docx,.txt"
            />

            {/* Emoji Picker */}
            {showEmojiPicker && (
              <div className="absolute bottom-20 right-4">
                <EmojiPicker
                  onEmojiClick={(emoji) => {
                    setMessage(prev => prev + emoji.emoji);
                    setShowEmojiPicker(false);
                  }}
                />
              </div>
            )}

            {/* Message Input */}
            <div className="flex items-end space-x-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={isRecording ? "Recording..." : "Type your message..."}
                  className="w-full px-4 py-3 bg-gray-100 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                  rows={1}
                  disabled={isRecording}
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                />
                
                {/* Recording indicator */}
                {isRecording && (
                  <motion.div
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-2"
                  >
                    <span className="h-2 w-2 bg-red-500 rounded-full" />
                    <span className="text-red-600 text-sm font-medium">Recording...</span>
                  </motion.div>
                )}
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSend}
                disabled={(!message.trim() && attachments.length === 0) || isRecording}
                className={`p-3 rounded-xl transition-all ${
                  message.trim() || attachments.length > 0
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:shadow-lg'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
                aria-label="Send message"
              >
                <Send className="h-5 w-5" />
              </motion.button>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
              <div className="flex items-center space-x-3">
                {message.length > 0 && !isOnline && (
                  <button
                    onClick={() => {
                      saveDraft(message);
                      toast.success('Draft saved');
                    }}
                    className="flex items-center space-x-1 text-purple-600 hover:text-purple-700"
                  >
                    <Save className="h-3 w-3" />
                    <span>Save draft</span>
                  </button>
                )}
                
                {loadDrafts().length > 0 && (
                  <button
                    onClick={() => {
                      clearDrafts();
                      toast.success('Drafts cleared');
                    }}
                    className="flex items-center space-x-1 text-gray-600 hover:text-gray-700"
                  >
                    <Trash2 className="h-3 w-3" />
                    <span>Clear drafts ({loadDrafts().length})</span>
                  </button>
                )}
              </div>
              
              <button
                className="flex items-center space-x-1 text-gray-600 hover:text-gray-700"
                onClick={() => {
                  trackEvent('help_requested', { from: 'message_center' });
                  window.open('/help', '_blank');
                }}
              >
                <Info className="h-3 w-3" />
                <span>Help</span>
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default MessageCenter;