// src/components/meetings/MeetingsCalendar.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  addMonths,
  subMonths,
  startOfWeek,
  endOfWeek,
  parseISO
} from 'date-fns';
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  User,
  Video,
  X,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api.service';

// Types
interface ScheduledMeeting {
  id: string;
  request_id: string;
  date: string;
  start_time: string;
  end_time: string;
  venue: string;
  subject: string;
  with_name: string;
  with_role: 'student' | 'faculty';
  status: 'upcoming' | 'completed' | 'cancelled';
}

interface MeetingDetailModalProps {
  meeting: ScheduledMeeting;
  onClose: () => void;
  userRole: 'student' | 'faculty' | 'admin'; // FIXED: Added 'admin' to the union type
}

// Meeting Detail Modal
const MeetingDetailModal: React.FC<MeetingDetailModalProps> = ({ meeting, onClose, userRole }) => {
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
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm opacity-80 mb-1">
                {format(parseISO(meeting.date), 'EEEE, MMMM d, yyyy')}
              </p>
              <h2 className="text-xl font-bold">{meeting.subject}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Time & Location */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Time</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {meeting.start_time} - {meeting.end_time}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                <MapPin className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Location</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {meeting.venue}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                <User className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Meeting with
                </p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {meeting.with_name}
                  <span className="text-sm text-gray-500 ml-1">
                    ({meeting.with_role === 'faculty' ? 'Faculty' : 'Student'})
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Status Badge */}
          <div className={`p-3 rounded-lg ${
            meeting.status === 'upcoming'
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
              : meeting.status === 'completed'
                ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                : 'bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600'
          }`}>
            <div className="flex items-center gap-2">
              <AlertCircle className={`w-4 h-4 ${
                meeting.status === 'upcoming' ? 'text-green-600' :
                meeting.status === 'completed' ? 'text-blue-600' : 'text-gray-500'
              }`} />
              <span className={`text-sm font-medium ${
                meeting.status === 'upcoming' ? 'text-green-700 dark:text-green-300' :
                meeting.status === 'completed' ? 'text-blue-700 dark:text-blue-300' : 'text-gray-600'
              }`}>
                {meeting.status === 'upcoming' && 'This meeting is scheduled'}
                {meeting.status === 'completed' && 'This meeting has been completed'}
                {meeting.status === 'cancelled' && 'This meeting was cancelled'}
              </span>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Calendar Component
const MeetingsCalendar: React.FC = () => {
  const { user } = useAuth();
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [meetings, setMeetings] = useState<ScheduledMeeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMeeting, setSelectedMeeting] = useState<ScheduledMeeting | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Fetch meetings
  useEffect(() => {
    const fetchMeetings = async () => {
      setLoading(true);
      try {
        const endpoint = user?.role === 'faculty' 
          ? '/meetings/faculty/requests'
          : '/meetings/student/requests';
        
        const response = await apiClient.get(endpoint);
        
        // Transform data to calendar format
        const allMeetings: ScheduledMeeting[] = [];
        
        // For faculty
        if (user?.role === 'faculty') {
          const accepted = response.data.accepted || [];
          const past = response.data.past || [];
          
          [...accepted, ...past].forEach((req: any) => {
            if (req.scheduled_meeting) {
              allMeetings.push({
                id: req.request_id,
                request_id: req.request_id,
                date: req.scheduled_meeting.date,
                start_time: req.scheduled_meeting.start_time,
                end_time: req.scheduled_meeting.end_time,
                venue: req.scheduled_meeting.venue,
                subject: req.subject,
                with_name: req.student_name,
                with_role: 'student',
                status: req.status === 'completed' ? 'completed' : 
                        req.status === 'cancelled' ? 'cancelled' : 'upcoming'
              });
            }
          });
        } else {
          // For students and admins
          (response.data || []).forEach((req: any) => {
            if (req.scheduled_meeting && req.status === 'accepted') {
              allMeetings.push({
                id: req.request_id,
                request_id: req.request_id,
                date: req.scheduled_meeting.date,
                start_time: req.scheduled_meeting.start_time,
                end_time: req.scheduled_meeting.end_time,
                venue: req.scheduled_meeting.venue,
                subject: req.subject,
                with_name: req.faculty_name,
                with_role: 'faculty',
                status: req.status === 'completed' ? 'completed' : 
                        req.status === 'cancelled' ? 'cancelled' : 'upcoming'
              });
            }
          });
        }
        
        setMeetings(allMeetings);
      } catch (error) {
        console.error('Failed to fetch meetings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMeetings();
  }, [user]);

  // Get days for the calendar grid
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const calendarStart = startOfWeek(monthStart);
    const calendarEnd = endOfWeek(monthEnd);
    
    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
  }, [currentMonth]);

  // Get meetings for a specific date
  const getMeetingsForDate = (date: Date) => {
    return meetings.filter(meeting => {
      const meetingDate = parseISO(meeting.date);
      return isSameDay(meetingDate, date);
    });
  };

  // Get meetings for selected date
  const selectedDateMeetings = selectedDate ? getMeetingsForDate(selectedDate) : [];

  // Navigation
  const prevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const nextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));
  const goToToday = () => {
    setCurrentMonth(new Date());
    setSelectedDate(new Date());
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
      {/* Calendar Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              {format(currentMonth, 'MMMM yyyy')}
            </h2>
            <button
              onClick={goToToday}
              className="px-3 py-1 text-sm bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 
                         dark:text-indigo-400 rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-800/30 
                         transition-colors"
            >
              Today
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={prevMonth}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button
              onClick={nextMonth}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="p-6">
        {/* Weekday Headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div
              key={day}
              className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Days Grid */}
        <div className="grid grid-cols-7 gap-1">
          {calendarDays.map((day, index) => {
            const dayMeetings = getMeetingsForDate(day);
            const isCurrentMonth = isSameMonth(day, currentMonth);
            const isSelected = selectedDate && isSameDay(day, selectedDate);
            const isTodayDate = isToday(day);

            return (
              <motion.button
                key={index}
                onClick={() => setSelectedDate(day)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`
                  relative aspect-square p-2 rounded-lg transition-all
                  ${!isCurrentMonth ? 'text-gray-300 dark:text-gray-600' : 'text-gray-900 dark:text-white'}
                  ${isSelected 
                    ? 'bg-indigo-600 text-white' 
                    : isTodayDate 
                      ? 'bg-indigo-100 dark:bg-indigo-900/30' 
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <span className={`text-sm font-medium ${isSelected ? 'text-white' : ''}`}>
                  {format(day, 'd')}
                </span>
                
                {/* Meeting Indicators */}
                {dayMeetings.length > 0 && (
                  <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
                    {dayMeetings.slice(0, 3).map((meeting, idx) => (
                      <div
                        key={idx}
                        className={`w-1.5 h-1.5 rounded-full ${
                          isSelected 
                            ? 'bg-white' 
                            : meeting.status === 'upcoming'
                              ? 'bg-green-500'
                              : meeting.status === 'completed'
                                ? 'bg-blue-500'
                                : 'bg-gray-400'
                        }`}
                      />
                    ))}
                    {dayMeetings.length > 3 && (
                      <span className={`text-xs ${isSelected ? 'text-white' : 'text-gray-500'}`}>
                        +{dayMeetings.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Selected Date Meetings */}
      {selectedDate && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            {format(selectedDate, 'EEEE, MMMM d, yyyy')}
          </h3>
          
          {selectedDateMeetings.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
              No meetings scheduled for this day
            </p>
          ) : (
            <div className="space-y-3">
              {selectedDateMeetings.map((meeting) => (
                <motion.div
                  key={meeting.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-4 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                    meeting.status === 'upcoming'
                      ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                      : meeting.status === 'completed'
                        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                        : 'bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600'
                  }`}
                  onClick={() => setSelectedMeeting(meeting)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {meeting.subject}
                      </p>
                      <div className="flex items-center gap-3 mt-1 text-sm text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {meeting.start_time}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {meeting.venue}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        with {meeting.with_name}
                      </p>
                    </div>
                    
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      meeting.status === 'upcoming'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
                        : meeting.status === 'completed'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                          : 'bg-gray-100 text-gray-600'
                    }`}>
                      {meeting.status}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-center gap-6 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>Upcoming</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-gray-400" />
            <span>Cancelled</span>
          </div>
        </div>
      </div>

      {/* Meeting Detail Modal */}
      <AnimatePresence>
        {selectedMeeting && (
          <MeetingDetailModal
            meeting={selectedMeeting}
            onClose={() => setSelectedMeeting(null)}
            // FIXED: Added type assertion to handle 'admin' role
            userRole={(user?.role as 'student' | 'faculty' | 'admin') || 'student'}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default MeetingsCalendar;