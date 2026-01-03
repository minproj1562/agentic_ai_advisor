// src/components/dashboard/sections/Messages.tsx
import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Paperclip, Search, Phone, Video, MoreVertical,
  Smile, Mic, Image, File, X, Check, CheckCheck, Clock,
  Star, Archive, Trash2, Reply, Forward, Pin, Bell,
  BellOff, Filter, Download, MessageSquare, Users
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow, format, isToday, isYesterday } from 'date-fns';
import { cn } from '../../../utils/cn';
import { auth } from '../../../services/firebase.config';
import toast from 'react-hot-toast';
import EmojiPicker from 'emoji-picker-react';

interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  receiverId: string;
  content: string;
  type: 'text' | 'image' | 'file' | 'voice';
  attachments?: Array<{
    name: string;
    url: string;
    size: number;
    type: string;
  }>;
  timestamp: Date;
  read: boolean;
  delivered: boolean;
  edited?: boolean;
  editedAt?: Date;
  replyTo?: string;
  reactions?: Array<{
    userId: string;
    emoji: string;
  }>;
}

interface Conversation {
  id: string;
  participantId: string;
  participantName: string;
  participantAvatar?: string;
  participantRole: 'student' | 'faculty';
  lastMessage: Message;
  unreadCount: number;
  isPinned: boolean;
  isMuted: boolean;
  isArchived: boolean;
  isOnline: boolean;
  lastSeen?: Date;
  typing?: boolean;
}

const Messages: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(new Set());
  const [isRecording, setIsRecording] = useState(false);
  const [filterType, setFilterType] = useState<'all' | 'unread' | 'pinned' | 'archived'>('all');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch conversations
  const { data: conversations, isLoading: conversationsLoading } = useQuery({
    queryKey: ['conversations', facultyId, filterType],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/conversations?filter=${filterType}`, // Fixed: Changed to import.meta.env
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch conversations');
      return response.json() as Promise<Conversation[]>;
    },
    refetchInterval: 5000 // Poll every 5 seconds for new messages
  });

  // Fetch messages for selected conversation
  const { data: messages, isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', selectedConversation?.id],
    queryFn: async () => {
      if (!selectedConversation) return [];
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/conversations/${selectedConversation.id}/messages`, // Fixed: Changed to import.meta.env
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch messages');
      return response.json() as Promise<Message[]>;
    },
    enabled: !!selectedConversation,
    refetchInterval: 3000 // Poll every 3 seconds for new messages
  });

  // Send message mutation
  const sendMessage = useMutation({
    mutationFn: async (data: { content: string; type: Message['type']; attachments?: any[] }) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/conversations/${selectedConversation?.id}/messages`, // Fixed: Changed to import.meta.env
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            ...data,
            senderId: facultyId,
            receiverId: selectedConversation?.participantId
          })
        }
      );
      if (!response.ok) throw new Error('Failed to send message');
      return response.json();
    },
    onSuccess: () => {
      setMessageInput('');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConversation?.id] }); // Fixed: invalidateQueries syntax
      queryClient.invalidateQueries({ queryKey: ['conversations', facultyId] }); // Fixed: invalidateQueries syntax
      scrollToBottom();
    },
    onError: (error: Error) => {
      toast.error(error.message);
    }
  });

  // Mark as read mutation
  const markAsRead = useMutation({
    mutationFn: async (conversationId: string) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/conversations/${conversationId}/read`, // Fixed: Changed to import.meta.env
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to mark as read');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', facultyId] }); // Fixed: invalidateQueries syntax
    }
  });

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Mark messages as read when conversation is selected
  useEffect(() => {
    if (selectedConversation && selectedConversation.unreadCount > 0) {
      markAsRead.mutate(selectedConversation.id);
    }
  }, [selectedConversation]);

  // Filter conversations based on search
  const filteredConversations = useMemo(() => {
    if (!conversations) return [];
    return conversations.filter(conv =>
      conv.participantName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.lastMessage.content.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [conversations, searchQuery]);

  // Group messages by date
  const groupedMessages = useMemo(() => {
    if (!messages) return {};
    
    const groups: { [key: string]: Message[] } = {};
    messages.forEach(message => {
      const date = new Date(message.timestamp);
      let key: string;
      
      if (isToday(date)) {
        key = 'Today';
      } else if (isYesterday(date)) {
        key = 'Yesterday';
      } else {
        key = format(date, 'MMMM d, yyyy');
      }
      
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(message);
    });
    
    return groups;
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (messageInput.trim() && selectedConversation) {
      sendMessage.mutate({
        content: messageInput,
        type: 'text'
      });
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/upload`, // Fixed: Changed to import.meta.env
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      if (!response.ok) throw new Error('Upload failed');
      
      const { url, name, size, type } = await response.json();
      
      sendMessage.mutate({
        content: `Sent a file: ${name}`,
        type: 'file',
        attachments: [{ url, name, size, type }]
      });
    } catch (error) {
      toast.error('Failed to upload file');
    }
  };

  return (
    <div className="flex h-[calc(100vh-200px)] bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
      {/* Conversations Sidebar */}
      <div className="w-96 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Messages
          </h3>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Filters */}
          <div className="flex gap-2 mt-3">
            {(['all', 'unread', 'pinned', 'archived'] as const).map(filter => (
              <button
                key={filter}
                onClick={() => setFilterType(filter)}
                className={cn(
                  'px-3 py-1 text-xs font-medium rounded-lg capitalize transition-colors',
                  filterType === filter
                    ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                )}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {conversationsLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <AnimatePresence>
              {filteredConversations.map((conversation, index) => (
                <motion.div
                  key={conversation.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => setSelectedConversation(conversation)}
                  className={cn(
                    'flex items-center gap-3 p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors relative',
                    selectedConversation?.id === conversation.id && 'bg-indigo-50 dark:bg-indigo-900/20'
                  )}
                >
                  {/* Avatar */}
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                      {conversation.participantAvatar ? (
                        <img
                          src={conversation.participantAvatar}
                          alt={conversation.participantName}
                          className="w-full h-full rounded-full object-cover"
                        />
                      ) : (
                        conversation.participantName.charAt(0).toUpperCase()
                      )}
                    </div>
                    {conversation.isOnline && (
                      <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-800" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900 dark:text-white truncate">
                        {conversation.participantName}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDistanceToNow(new Date(conversation.lastMessage.timestamp), { addSuffix: true })}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                        {conversation.typing ? (
                          <span className="italic">Typing...</span>
                        ) : (
                          conversation.lastMessage.content
                        )}
                      </p>
                      {conversation.unreadCount > 0 && (
                        <span className="px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
                          {conversation.unreadCount}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Pinned indicator */}
                  {conversation.isPinned && (
                    <Pin className="absolute top-2 right-2 w-4 h-4 text-gray-400" />
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Chat Area */}
      {selectedConversation ? (
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                {selectedConversation.participantName.charAt(0).toUpperCase()}
              </div>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">
                  {selectedConversation.participantName}
                </h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {selectedConversation.isOnline ? (
                    <span className="text-green-500">Online</span>
                  ) : (
                    selectedConversation.lastSeen && (
                      <span>Last seen {formatDistanceToNow(new Date(selectedConversation.lastSeen), { addSuffix: true })}</span>
                    )
                  )}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                <Phone className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                <Video className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                <MoreVertical className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messagesLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
              </div>
            ) : (
              Object.entries(groupedMessages).map(([date, dateMessages]) => (
                <div key={date}>
                  {/* Date Separator */}
                  <div className="flex items-center justify-center my-4">
                    <div className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded-full text-xs text-gray-600 dark:text-gray-400">
                      {date}
                    </div>
                  </div>
                  
                  {/* Messages */}
                  {dateMessages.map((message, index) => {
                    const isOwn = message.senderId === facultyId;
                    return (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={cn(
                          'flex gap-2',
                          isOwn ? 'justify-end' : 'justify-start'
                        )}
                      >
                        {!isOwn && (
                          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                            {selectedConversation.participantName.charAt(0).toUpperCase()}
                          </div>
                        )}
                        
                        <div
                          className={cn(
                            'max-w-md px-4 py-2 rounded-2xl',
                            isOwn
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                          )}
                        >
                          {message.type === 'text' ? (
                            <p className="text-sm">{message.content}</p>
                          ) : message.type === 'image' ? (
                            <img
                              src={message.attachments?.[0]?.url}
                              alt="Image"
                              className="rounded-lg max-w-xs"
                            />
                          ) : message.type === 'file' ? (
                            <a
                              href={message.attachments?.[0]?.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 text-sm"
                            >
                              <File className="w-4 h-4" />
                              {message.attachments?.[0]?.name}
                            </a>
                          ) : null}
                          
                          <div className={cn(
                            'flex items-center gap-1 mt-1',
                            isOwn ? 'justify-end' : 'justify-start'
                          )}>
                            <span className={cn(
                              'text-xs',
                              isOwn ? 'text-indigo-200' : 'text-gray-500 dark:text-gray-400'
                            )}>
                              {format(new Date(message.timestamp), 'HH:mm')}
                            </span>
                            {isOwn && (
                              message.read ? (
                                <CheckCheck className="w-3 h-3 text-indigo-200" />
                              ) : message.delivered ? (
                                <Check className="w-3 h-3 text-indigo-200" />
                              ) : (
                                <Clock className="w-3 h-3 text-indigo-200" />
                              )
                            )}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <Paperclip className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                hidden
                onChange={handleFileUpload}
              />
              
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder="Type a message..."
                  className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                
                <button
                  type="button"
                  onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                >
                  <Smile className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </button>
                
                {showEmojiPicker && (
                  <div className="absolute bottom-full right-0 mb-2">
                    <EmojiPicker
                      onEmojiClick={(emojiObject) => {
                        setMessageInput(prev => prev + emojiObject.emoji);
                        setShowEmojiPicker(false);
                      }}
                    />
                  </div>
                )}
              </div>
              
              <button
                type="submit"
                disabled={!messageInput.trim() || sendMessage.isPending} // Fixed: Changed isLoading to isPending
                className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sendMessage.isPending ? ( // Fixed: Changed isLoading to isPending
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="text-center">
            <MessageSquare className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Select a conversation
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Choose a conversation from the list to start messaging
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Messages;