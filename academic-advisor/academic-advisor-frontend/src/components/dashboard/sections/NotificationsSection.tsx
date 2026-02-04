// src/components/dashboard/sections/NotificationsSection.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bell, Check, CheckCheck, Archive, Trash2,
  Filter, Calendar, MessageSquare, UserPlus,
  AlertCircle, Info, CheckCircle, X, Clock
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import toast from 'react-hot-toast';
import apiClient from '../../../services/api.service';
import { cn } from '../../../utils/cn';

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  data?: any;
  read: boolean;
  created_at: string;
}

interface NotificationsSectionProps {
  userId: string;
}

const NotificationsSection: React.FC<NotificationsSectionProps> = ({ userId }) => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Fetch notifications
  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', userId, filter],
    queryFn: async () => {
      const response = await apiClient.get(`/notifications?unread_only=${filter === 'unread'}`);
      return response.data;
    },
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000, // Refetch every minute
  });

  const notifications: Notification[] = data?.notifications || [];
  const unreadCount = data?.unread_count || 0;

  // Mark as read mutation
  const markReadMutation = useMutation({
    mutationFn: async (notificationId: string) => {
      await apiClient.post(`/notifications/${notificationId}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });

  // Mark all as read mutation
  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/notifications/read-all');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast.success('All notifications marked as read');
    }
  });

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'meeting_request':
        return <Calendar className="w-5 h-5 text-blue-500" />;
      case 'meeting_accepted':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'meeting_rejected':
        return <X className="w-5 h-5 text-red-500" />;
      case 'message':
        return <MessageSquare className="w-5 h-5 text-purple-500" />;
      case 'student_assigned':
        return <UserPlus className="w-5 h-5 text-indigo-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getNotificationColor = (type: string, read: boolean) => {
    if (read) return 'border-l-gray-300 dark:border-l-gray-600';
    
    switch (type) {
      case 'meeting_request':
        return 'border-l-blue-500';
      case 'meeting_accepted':
        return 'border-l-green-500';
      case 'meeting_rejected':
        return 'border-l-red-500';
      case 'warning':
        return 'border-l-yellow-500';
      default:
        return 'border-l-indigo-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Bell className="w-6 h-6" />
            Notifications
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 bg-red-500 text-white text-sm rounded-full">
                {unreadCount}
              </span>
            )}
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Stay updated with your activities
          </p>
        </div>

        <div className="flex gap-2">
          {/* Filter Toggle */}
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setFilter('all')}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                filter === 'all'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400'
              )}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                filter === 'unread'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400'
              )}
            >
              Unread
            </button>
          </div>

          {/* Mark All Read */}
          {unreadCount > 0 && (
            <button
              onClick={() => markAllReadMutation.mutate()}
              disabled={markAllReadMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              <CheckCheck className="w-4 h-4" />
              Mark All Read
            </button>
          )}
        </div>
      </div>

      {/* Notifications List */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-gray-500 mt-4">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center">
            <Bell className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {filter === 'unread' 
                ? 'You\'re all caught up!' 
                : 'Notifications will appear here when you have activity'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            <AnimatePresence mode="popLayout">
              {notifications.map((notification, index) => (
                <motion.div
                  key={notification.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    'relative border-l-4 transition-colors cursor-pointer',
                    getNotificationColor(notification.type, notification.read),
                    notification.read
                      ? 'bg-gray-50 dark:bg-gray-800/50'
                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  )}
                  onClick={() => {
                    setExpandedId(expandedId === notification.id ? null : notification.id);
                    if (!notification.read) {
                      markReadMutation.mutate(notification.id);
                    }
                  }}
                >
                  <div className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 mt-0.5">
                        {getNotificationIcon(notification.type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <h4 className={cn(
                              'text-sm font-medium',
                              notification.read
                                ? 'text-gray-600 dark:text-gray-400'
                                : 'text-gray-900 dark:text-white'
                            )}>
                              {notification.title}
                            </h4>
                            
                            <AnimatePresence>
                              {expandedId === notification.id && (
                                <motion.p
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="text-sm text-gray-600 dark:text-gray-400 mt-2"
                                >
                                  {notification.message}
                                </motion.p>
                              )}
                            </AnimatePresence>
                            
                            <div className="flex items-center gap-2 mt-1">
                              <Clock className="w-3 h-3 text-gray-400" />
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                              </span>
                            </div>
                          </div>
                          
                          {!notification.read && (
                            <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsSection;