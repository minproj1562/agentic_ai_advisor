// src/components/meetings/FacultyMeetingManagement.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import {
  User,
  Calendar,
  Clock,
  MapPin,
  Check,
  X,
  MessageSquare,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Mail,
  Phone,
  GraduationCap,
  FileText,
  CheckCircle,
  XCircle,
  CalendarCheck,
  Filter
} from 'lucide-react';
import { format, formatDistanceToNow, addDays } from 'date-fns';
import apiClient from '../../services/api.service';
import { useAuth } from '../../contexts/AuthContext';

// Types
interface MeetingRequest {
  request_id: string;
  student_id: string;
  student_name: string;
  student_email: string;
  student_department?: string;
  student_semester?: number;
  faculty_id: string;
  faculty_name: string;
  subject: string;
  message: string;
  urgency: 'low' | 'normal' | 'high';
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled' | 'completed';
  created_at: string;
  scheduled_meeting?: {
    date: string;
    start_time: string;
    end_time: string;
    venue: string;
    additional_notes?: string;
  };
  faculty_response?: string;
}

interface ScheduleFormData {
  date: string;
  start_time: string;
  end_time: string;
  venue: string;
  response_message: string;
}

// Schedule Meeting Modal
const ScheduleModal: React.FC<{
  request: MeetingRequest;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ request, onClose, onSuccess }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { control, handleSubmit, watch, formState: { errors } } = useForm<ScheduleFormData>({
    defaultValues: {
      date: format(addDays(new Date(), 1), 'yyyy-MM-dd'),
      start_time: '10:00',
      end_time: '10:30',
      venue: '',
      response_message: ''
    }
  });

  const onSubmit = async (data: ScheduleFormData) => {
    setIsSubmitting(true);
    
    try {
      await apiClient.post(`/meetings/faculty/accept/${request.request_id}`, {
        date: new Date(data.date).toISOString(),
        start_time: data.start_time,
        end_time: data.end_time,
        venue: data.venue,
        response_message: data.response_message || null
      });
      
      toast.success('Meeting scheduled successfully!');
      onSuccess();
      onClose();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to schedule meeting');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Schedule Meeting
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Student Info */}
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">
                {request.student_name.charAt(0)}
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">{request.student_name}</p>
                <p className="text-sm text-gray-500">
                  {request.student_department && `${request.student_department} • `}
                  {request.student_semester && `Sem ${request.student_semester}`}
                </p>
              </div>
            </div>
            <div className="mt-3 p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{request.subject}</p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Date *
            </label>
            <Controller
              name="date"
              control={control}
              rules={{ required: 'Date is required' }}
              render={({ field }) => (
                <input
                  {...field}
                  type="date"
                  min={format(new Date(), 'yyyy-MM-dd')}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              )}
            />
            {errors.date && (
              <p className="text-red-500 text-sm mt-1">{errors.date.message}</p>
            )}
          </div>

          {/* Time */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Start Time *
              </label>
              <Controller
                name="start_time"
                control={control}
                rules={{ required: 'Start time is required' }}
                render={({ field }) => (
                  <input
                    {...field}
                    type="time"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                               bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                               focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                )}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                End Time *
              </label>
              <Controller
                name="end_time"
                control={control}
                rules={{ required: 'End time is required' }}
                render={({ field }) => (
                  <input
                    {...field}
                    type="time"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                               bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                               focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                )}
              />
            </div>
          </div>

          {/* Venue */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Venue / Location *
            </label>
            <Controller
              name="venue"
              control={control}
              rules={{ required: 'Venue is required' }}
              render={({ field }) => (
                <input
                  {...field}
                  type="text"
                  placeholder="e.g., Room 301, CS Building"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              )}
            />
            {errors.venue && (
              <p className="text-red-500 text-sm mt-1">{errors.venue.message}</p>
            )}
          </div>

          {/* Message (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Message to Student (optional)
            </label>
            <Controller
              name="response_message"
              control={control}
              render={({ field }) => (
                <textarea
                  {...field}
                  rows={3}
                  placeholder="Any instructions or notes for the student..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                />
              )}
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 
                         dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 
                         dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 py-3 bg-green-600 text-white rounded-lg font-medium 
                         flex items-center justify-center gap-2 hover:bg-green-700 
                         transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Scheduling...
                </>
              ) : (
                <>
                  <CalendarCheck className="w-5 h-5" />
                  Schedule Meeting
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};

// Reject Modal
const RejectModal: React.FC<{
  request: MeetingRequest;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ request, onClose, onSuccess }) => {
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleReject = async () => {
    if (reason.length < 10) {
      toast.error('Please provide a reason (at least 10 characters)');
      return;
    }

    setIsSubmitting(true);
    
    try {
      await apiClient.post(`/meetings/faculty/reject/${request.request_id}`, {
        reason
      });
      
      toast.success('Request declined');
      onSuccess();
      onClose();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to decline request');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Decline Request
            </h2>
          </div>

          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Please provide a reason for declining this meeting request from {request.student_name}.
          </p>

          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={4}
            placeholder="e.g., I'm on leave during this period. Please reach out after..."
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
          />

          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 
                         dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 
                         dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleReject}
              disabled={isSubmitting || reason.length < 10}
              className="flex-1 py-3 bg-red-600 text-white rounded-lg font-medium 
                         hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="w-5 h-5 animate-spin mx-auto" />
              ) : (
                'Decline Request'
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Request Card Component
const RequestCard: React.FC<{
  request: MeetingRequest;
  onAccept: () => void;
  onReject: () => void;
  onComplete: () => void;
}> = ({ request, onAccept, onReject, onComplete }) => {
  const [expanded, setExpanded] = useState(false);

  const urgencyColors = {
    low: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    normal: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    high: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
  };

  return (
    <motion.div
      layout
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden"
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full 
                            flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
              {request.student_name.charAt(0)}
            </div>
            
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {request.student_name}
                </h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${urgencyColors[request.urgency]}`}>
                  {request.urgency === 'high' ? '🔴 Urgent' : request.urgency === 'normal' ? 'Normal' : 'Low'}
                </span>
              </div>
              
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {request.student_department && `${request.student_department}`}
                {request.student_semester && ` • Semester ${request.student_semester}`}
              </p>
              
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-2">
                {request.subject}
              </p>
              
              <p className="text-xs text-gray-500 mt-1">
                {formatDistanceToNow(new Date(request.created_at), { addSuffix: true })}
              </p>
            </div>
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            {expanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* Scheduled Meeting Info (if accepted) */}
        {request.status === 'accepted' && request.scheduled_meeting && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-xs font-medium text-green-700 dark:text-green-300 mb-2">Scheduled Meeting</p>
            <div className="flex flex-wrap gap-4 text-sm text-green-800 dark:text-green-200">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {format(new Date(request.scheduled_meeting.date), 'MMM dd, yyyy')}
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {request.scheduled_meeting.start_time} - {request.scheduled_meeting.end_time}
              </div>
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {request.scheduled_meeting.venue}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 dark:border-gray-700"
          >
            <div className="p-4 space-y-4">
              {/* Student Message */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Student's Message
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg whitespace-pre-wrap">
                  {request.message}
                </p>
              </div>

              {/* Student Contact */}
              <div className="flex items-center gap-4 text-sm">
                <a 
                  href={`mailto:${request.student_email}`}
                  className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  <Mail className="w-4 h-4" />
                  {request.student_email}
                </a>
              </div>

              {/* Actions */}
              {request.status === 'pending' && (
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={onReject}
                    className="flex-1 py-2 border border-red-300 dark:border-red-600 text-red-600 
                               dark:text-red-400 rounded-lg font-medium hover:bg-red-50 
                               dark:hover:bg-red-900/20 transition-colors flex items-center justify-center gap-2"
                  >
                    <XCircle className="w-4 h-4" />
                    Decline
                  </button>
                  <button
                    onClick={onAccept}
                    className="flex-1 py-2 bg-green-600 text-white rounded-lg font-medium 
                               hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Accept & Schedule
                  </button>
                </div>
              )}

              {request.status === 'accepted' && (
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={onComplete}
                    className="flex-1 py-2 bg-blue-600 text-white rounded-lg font-medium 
                               hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Mark as Completed
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Main Component
const FacultyMeetingManagement: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'pending' | 'upcoming' | 'past'>('pending');
  const [requests, setRequests] = useState<{
    pending: MeetingRequest[];
    accepted: MeetingRequest[];
    past: MeetingRequest[];
  }>({ pending: [], accepted: [], past: [] });
  const [loading, setLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState<MeetingRequest | null>(null);
  const [modalType, setModalType] = useState<'schedule' | 'reject' | null>(null);

  // Fetch requests
  const fetchRequests = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/meetings/faculty/requests');
      setRequests({
        pending: response.data.pending || [],
        accepted: response.data.accepted || [],
        past: response.data.past || []
      });
    } catch (error) {
      console.error('Failed to fetch requests:', error);
      toast.error('Failed to load meeting requests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleComplete = async (requestId: string) => {
    try {
      await apiClient.post(`/meetings/faculty/complete/${requestId}`);
      toast.success('Meeting marked as complete');
      fetchRequests();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to mark complete');
    }
  };

  const openScheduleModal = (request: MeetingRequest) => {
    setSelectedRequest(request);
    setModalType('schedule');
  };

  const openRejectModal = (request: MeetingRequest) => {
    setSelectedRequest(request);
    setModalType('reject');
  };

  const closeModal = () => {
    setSelectedRequest(null);
    setModalType(null);
  };

  const getCurrentRequests = () => {
    switch (activeTab) {
      case 'pending':
        return requests.pending;
      case 'upcoming':
        return requests.accepted;
      case 'past':
        return requests.past;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Meeting Requests
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage meeting requests from students
          </p>
        </div>

        {/* Stats */}
        <div className="flex gap-4">
          <div className="px-4 py-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg text-center">
            <p className="text-xs text-yellow-600 dark:text-yellow-400">Pending</p>
            <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
              {requests.pending.length}
            </p>
          </div>
          <div className="px-4 py-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-center">
            <p className="text-xs text-green-600 dark:text-green-400">Upcoming</p>
            <p className="text-2xl font-bold text-green-700 dark:text-green-300">
              {requests.accepted.length}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'pending', label: 'Pending', count: requests.pending.length },
          { id: 'upcoming', label: 'Upcoming', count: requests.accepted.length },
          { id: 'past', label: 'Past', count: requests.past.length }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-3 font-medium transition-colors relative ${
              activeTab === tab.id
                ? 'text-indigo-600 dark:text-indigo-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                activeTab === tab.id
                  ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}>
                {tab.count}
              </span>
            )}
            {activeTab === tab.id && (
              <motion.div
                layoutId="facultyActiveTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600"
              />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        </div>
      ) : getCurrentRequests().length === 0 ? (
        <div className="text-center py-12">
          <MessageSquare className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {activeTab === 'pending'
              ? 'No pending meeting requests'
              : activeTab === 'upcoming'
                ? 'No upcoming meetings'
                : 'No past meetings'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {getCurrentRequests().map((request) => (
            <RequestCard
              key={request.request_id}
              request={request}
              onAccept={() => openScheduleModal(request)}
              onReject={() => openRejectModal(request)}
              onComplete={() => handleComplete(request.request_id)}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <AnimatePresence>
        {selectedRequest && modalType === 'schedule' && (
          <ScheduleModal
            request={selectedRequest}
            onClose={closeModal}
            onSuccess={fetchRequests}
          />
        )}
        
        {selectedRequest && modalType === 'reject' && (
          <RejectModal
            request={selectedRequest}
            onClose={closeModal}
            onSuccess={fetchRequests}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default FacultyMeetingManagement;