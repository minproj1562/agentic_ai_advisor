// academic-advisor/academic-advisor-frontend/src/components/meetings/StudentMeetingRequest.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import {
  User,
  Mail,
  Calendar,
  Clock,
  MapPin,
  Send,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
  Search,
  Filter,
  BookOpen,
  GraduationCap,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import apiClient from '../../services/api.service';
import { useAuth } from '../../contexts/AuthContext';

// Types
interface FacultyBasicInfo {
  user_id: string;
  name: string;
  email: string;
  department: string;
  designation: string;
  photo_url?: string;
  specializations: string[];
  profile_completeness: number;
}

interface MeetingRequest {
  request_id: string;
  faculty_id: string;
  faculty_name: string;
  subject: string;
  message: string;
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

interface RequestFormData {
  subject: string;
  message: string;
  urgency: 'low' | 'normal' | 'high';
  preferred_dates: string[];
}

// Faculty Card Component
const FacultyCard: React.FC<{
  faculty: FacultyBasicInfo;
  onSelect: (faculty: FacultyBasicInfo) => void;
}> = ({ faculty, onSelect }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-5 cursor-pointer
                 border border-gray-200 dark:border-gray-700 hover:border-indigo-400 
                 dark:hover:border-indigo-500 transition-all"
      onClick={() => onSelect(faculty)}
    >
      <div className="flex items-start gap-4">
        <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full 
                        flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
          {faculty.photo_url ? (
            <img src={faculty.photo_url} alt={faculty.name} className="w-full h-full rounded-full object-cover" />
          ) : (
            faculty.name.charAt(0)
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 dark:text-white truncate">
            {faculty.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {faculty.designation}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            {faculty.department}
          </p>
          
          {faculty.specializations.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {faculty.specializations.slice(0, 3).map((spec, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 
                             dark:text-indigo-300 rounded-full text-xs"
                >
                  {spec}
                </span>
              ))}
              {faculty.specializations.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{faculty.specializations.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// Request Form Modal
const RequestFormModal: React.FC<{
  faculty: FacultyBasicInfo;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ faculty, onClose, onSuccess }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { control, handleSubmit, formState: { errors } } = useForm<RequestFormData>({
    defaultValues: {
      subject: '',
      message: '',
      urgency: 'normal',
      preferred_dates: []
    }
  });

  const onSubmit = async (data: RequestFormData) => {
    setIsSubmitting(true);
    
    try {
      await apiClient.post('/meetings/student/create', {
        faculty_id: faculty.user_id,
        subject: data.subject,
        message: data.message,
        urgency: data.urgency,
        preferred_dates: data.preferred_dates
      });
      
      toast.success('Meeting request sent successfully!');
      onSuccess();
      onClose();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send request');
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
              Request Meeting
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
          
          {/* Faculty Info */}
          <div className="flex items-center gap-3 mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center text-white font-bold">
              {faculty.name.charAt(0)}
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{faculty.name}</p>
              <p className="text-sm text-gray-500">{faculty.designation}, {faculty.department}</p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Subject / Topic *
            </label>
            <Controller
              name="subject"
              control={control}
              rules={{ 
                required: 'Subject is required',
                minLength: { value: 5, message: 'Subject must be at least 5 characters' }
              }}
              render={({ field }) => (
                <input
                  {...field}
                  type="text"
                  placeholder="e.g., Guidance on Machine Learning project"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              )}
            />
            {errors.subject && (
              <p className="text-red-500 text-sm mt-1">{errors.subject.message}</p>
            )}
          </div>

          {/* Message */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Message *
            </label>
            <Controller
              name="message"
              control={control}
              rules={{ 
                required: 'Message is required',
                minLength: { value: 20, message: 'Please provide more details (at least 20 characters)' }
              }}
              render={({ field }) => (
                <textarea
                  {...field}
                  rows={4}
                  placeholder="Describe what you'd like to discuss, your current progress, and any specific questions you have..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                             focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                />
              )}
            />
            {errors.message && (
              <p className="text-red-500 text-sm mt-1">{errors.message.message}</p>
            )}
          </div>

          {/* Urgency */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Urgency
            </label>
            <Controller
              name="urgency"
              control={control}
              render={({ field }) => (
                <div className="flex gap-3">
                  {['low', 'normal', 'high'].map((level) => (
                    <button
                      key={level}
                      type="button"
                      onClick={() => field.onChange(level)}
                      className={`flex-1 py-2 px-4 rounded-lg border-2 font-medium capitalize transition-all
                        ${field.value === level
                          ? level === 'high'
                            ? 'border-red-500 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                            : level === 'normal'
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300'
                              : 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                          : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                        }`}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              )}
            />
          </div>

          {/* Info Note */}
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-blue-700 dark:text-blue-300">
              The faculty will review your request and schedule a meeting at their convenience.
              You'll receive a notification once they respond.
            </p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg
                       font-medium flex items-center justify-center gap-2 
                       hover:from-indigo-700 hover:to-purple-700 transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Sending Request...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Send Request
              </>
            )}
          </button>
        </form>
      </motion.div>
    </motion.div>
  );
};

// Request Status Card
const RequestStatusCard: React.FC<{
  request: MeetingRequest;
  onCancel: (requestId: string) => void;
  onFeedback: (requestId: string) => void;
}> = ({ request, onCancel, onFeedback }) => {
  const [expanded, setExpanded] = useState(false);

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    accepted: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    rejected: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
  };

  const statusIcons = {
    pending: <Clock className="w-4 h-4" />,
    accepted: <CheckCircle className="w-4 h-4" />,
    rejected: <X className="w-4 h-4" />,
    cancelled: <X className="w-4 h-4" />,
    completed: <CheckCircle className="w-4 h-4" />
  };

  return (
    <motion.div
      layout
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden"
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${statusColors[request.status]}`}>
                {statusIcons[request.status]}
                {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
              </span>
              <span className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(request.created_at), { addSuffix: true })}
              </span>
            </div>
            
            <h3 className="font-medium text-gray-900 dark:text-white truncate">
              {request.subject}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              with {request.faculty_name}
            </p>
          </div>
          
          <button className="p-1">
            {expanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* Scheduled Meeting Preview */}
        {request.status === 'accepted' && request.scheduled_meeting && (
          <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1 text-green-700 dark:text-green-300">
                <Calendar className="w-4 h-4" />
                {format(new Date(request.scheduled_meeting.date), 'MMM dd, yyyy')}
              </div>
              <div className="flex items-center gap-1 text-green-700 dark:text-green-300">
                <Clock className="w-4 h-4" />
                {request.scheduled_meeting.start_time}
              </div>
              <div className="flex items-center gap-1 text-green-700 dark:text-green-300">
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
              {/* Message */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Your Message
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                  {request.message}
                </p>
              </div>

              {/* Faculty Response */}
              {request.faculty_response && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Faculty Response
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 bg-indigo-50 dark:bg-indigo-900/20 p-3 rounded-lg">
                    {request.faculty_response}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                {request.status === 'pending' && (
                  <button
                    onClick={() => onCancel(request.request_id)}
                    className="px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 
                               dark:hover:bg-red-900/20 rounded-lg transition-colors text-sm font-medium"
                  >
                    Cancel Request
                  </button>
                )}
                
                {request.status === 'completed' && (
                  <button
                    onClick={() => onFeedback(request.request_id)}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 
                               transition-colors text-sm font-medium"
                  >
                    Leave Feedback
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Main Component
const StudentMeetingRequest: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'browse' | 'my-requests'>('browse');
  const [facultyList, setFacultyList] = useState<FacultyBasicInfo[]>([]);
  const [myRequests, setMyRequests] = useState<MeetingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFaculty, setSelectedFaculty] = useState<FacultyBasicInfo | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');

  // Fetch faculty list
  useEffect(() => {
    const fetchFaculty = async () => {
      try {
        const response = await apiClient.get('/faculty-profile/list', {
          params: {
            department: departmentFilter || undefined,
            page: 1,
            page_size: 50
          }
        });
        setFacultyList(response.data.faculty);
      } catch (error) {
        console.error('Failed to fetch faculty:', error);
        toast.error('Failed to load faculty list');
      }
    };

    if (activeTab === 'browse') {
      fetchFaculty();
    }
  }, [activeTab, departmentFilter]);

  // Fetch my requests
  useEffect(() => {
    const fetchMyRequests = async () => {
      setLoading(true);
      try {
        const response = await apiClient.get('/meetings/student/requests');
        setMyRequests(response.data);
      } catch (error) {
        console.error('Failed to fetch requests:', error);
      } finally {
        setLoading(false);
      }
    };

    if (activeTab === 'my-requests') {
      fetchMyRequests();
    } else {
      setLoading(false);
    }
  }, [activeTab]);

  const handleCancelRequest = async (requestId: string) => {
    if (!confirm('Are you sure you want to cancel this request?')) return;
    
    try {
      await apiClient.post(`/meetings/student/cancel/${requestId}`);
      setMyRequests(prev => prev.filter(r => r.request_id !== requestId));
      toast.success('Request cancelled');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to cancel request');
    }
  };

  const handleFeedback = (requestId: string) => {
    // Open feedback modal - implement as needed
    toast('Feedback feature coming soon!');
  };

  const filteredFaculty = facultyList.filter(f =>
    f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.specializations.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const pendingCount = myRequests.filter(r => r.status === 'pending').length;
  const acceptedCount = myRequests.filter(r => r.status === 'accepted').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Meeting Requests
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Request meetings with faculty members for guidance
          </p>
        </div>

        {/* Stats */}
        <div className="flex gap-4">
          <div className="px-4 py-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
            <p className="text-xs text-yellow-600 dark:text-yellow-400">Pending</p>
            <p className="text-xl font-bold text-yellow-700 dark:text-yellow-300">{pendingCount}</p>
          </div>
          <div className="px-4 py-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <p className="text-xs text-green-600 dark:text-green-400">Scheduled</p>
            <p className="text-xl font-bold text-green-700 dark:text-green-300">{acceptedCount}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('browse')}
          className={`px-4 py-3 font-medium transition-colors relative ${
            activeTab === 'browse'
              ? 'text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Browse Faculty
          {activeTab === 'browse' && (
            <motion.div
              layoutId="activeTab"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600"
            />
          )}
        </button>
        <button
          onClick={() => setActiveTab('my-requests')}
          className={`px-4 py-3 font-medium transition-colors relative ${
            activeTab === 'my-requests'
              ? 'text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          My Requests
          {myRequests.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 
                           dark:text-indigo-400 rounded-full text-xs">
              {myRequests.length}
            </span>
          )}
          {activeTab === 'my-requests' && (
            <motion.div
              layoutId="activeTab"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600"
            />
          )}
        </button>
      </div>

      {/* Content */}
      {activeTab === 'browse' ? (
        <div className="space-y-4">
          {/* Search & Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name or specialization..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Information Technology">Information Technology</option>
              <option value="Electronics">Electronics</option>
              <option value="Mechanical">Mechanical</option>
            </select>
          </div>

          {/* Faculty Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFaculty.map((faculty) => (
              <FacultyCard
                key={faculty.user_id}
                faculty={faculty}
                onSelect={setSelectedFaculty}
              />
            ))}
          </div>

          {filteredFaculty.length === 0 && (
            <div className="text-center py-12">
              <User className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No faculty found matching your criteria</p>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          ) : myRequests.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <p className="text-gray-500 dark:text-gray-400 mb-4">You haven't made any meeting requests yet</p>
              <button
                onClick={() => setActiveTab('browse')}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Browse Faculty
              </button>
            </div>
          ) : (
            myRequests.map((request) => (
              <RequestStatusCard
                key={request.request_id}
                request={request}
                onCancel={handleCancelRequest}
                onFeedback={handleFeedback}
              />
            ))
          )}
        </div>
      )}

      {/* Request Form Modal */}
      <AnimatePresence>
        {selectedFaculty && (
          <RequestFormModal
            faculty={selectedFaculty}
            onClose={() => setSelectedFaculty(null)}
            onSuccess={() => setActiveTab('my-requests')}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// Export as default
export default StudentMeetingRequest;