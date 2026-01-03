// components/dashboard/cards/MentorshipSlotsCard.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar,
  Clock,
  Plus,
  Video,
  Users,
  MapPin,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { MentorshipSlot } from '../../../types/dashboard.types';
import { format, addDays, startOfWeek, isSameDay, isToday, isFuture } from 'date-fns';
import { cn } from '../../../utils/cn';
import toast from 'react-hot-toast';
import { getThemeTransition } from '../../../utils/theme.utils';

interface MentorshipSlotsCardProps {
  slots: MentorshipSlot[];
  onSlotClick?: (slot: MentorshipSlot) => void;
  onAddSlot?: () => void;
}

const MentorshipSlotsCard: React.FC<MentorshipSlotsCardProps> = ({
  slots,
  onSlotClick,
  onAddSlot
}) => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'week' | 'day'>('week');

  const weekDays = useMemo(() => {
    const start = startOfWeek(selectedDate, { weekStartsOn: 1 });
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [selectedDate]);

  const slotsForSelectedDate = useMemo(() => {
    return slots.filter(slot => isSameDay(slot.date, selectedDate));
  }, [slots, selectedDate]);

  const upcomingSlots = useMemo(() => {
    return slots
      .filter(slot => isFuture(slot.date) || isToday(slot.date))
      .sort((a, b) => a.date.getTime() - b.date.getTime())
      .slice(0, 3);
  }, [slots]);

  const getSlotTypeColor = (type: MentorshipSlot['type']) => {
    switch (type) {
      case 'Emergency':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      case 'Group':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      default:
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
    }
  };

  const getSlotTypeIcon = (type: MentorshipSlot['type']) => {
    switch (type) {
      case 'Emergency':
        return <AlertCircle className="w-3 h-3" />;
      case 'Group':
        return <Users className="w-3 h-3" />;
      default:
        return <Video className="w-3 h-3" />;
    }
  };

  const handlePreviousWeek = () => {
    setSelectedDate(prev => addDays(prev, -7));
  };

  const handleNextWeek = () => {
    setSelectedDate(prev => addDays(prev, 7));
  };

  const handleSlotAction = (slot: MentorshipSlot) => {
    if (onSlotClick) {
      onSlotClick(slot);
    } else {
      toast.success(`Slot ${slot.isBooked ? 'details' : 'booking'} opened`);
    }
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', getThemeTransition())}>
      <div className={cn('flex items-center justify-between mb-4', getThemeTransition())}>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Mentorship Slots
        </h3>
        <button
          onClick={onAddSlot}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium',
            getThemeTransition()
          )}
        >
          <Plus className="w-4 h-4" />
          Add Slot
        </button>
      </div>

      {/* View Mode Toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setViewMode('week')}
          className={cn(
            'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors',
            viewMode === 'week'
              ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600',
            getThemeTransition()
          )}
        >
          Week View
        </button>
        <button
          onClick={() => setViewMode('day')}
          className={cn(
            'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors',
            viewMode === 'day'
              ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600',
            getThemeTransition()
          )}
        >
          Day View
        </button>
      </div>

      {viewMode === 'week' ? (
        // Week View
        <div>
          {/* Week Navigation */}
          <div className="flex items-center justify-between mb-3">
            <button
              onClick={handlePreviousWeek}
              className={cn('p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors', getThemeTransition())}
            >
              <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {format(weekDays[0], 'MMM d')} - {format(weekDays[6], 'MMM d, yyyy')}
            </span>
            <button
              onClick={handleNextWeek}
              className={cn('p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors', getThemeTransition())}
            >
              <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>

          {/* Week Days Grid */}
          <div className="grid grid-cols-7 gap-1">
            {weekDays.map((day, index) => {
              const daySlots = slots.filter(slot => isSameDay(slot.date, day));
              const isSelected = isSameDay(day, selectedDate);
              const isDayToday = isToday(day);

              return (
                <motion.button
                  key={index}
                  onClick={() => setSelectedDate(day)}
                  className={cn(
                    'p-2 rounded-lg text-center transition-all',
                    isSelected
                      ? 'bg-indigo-100 dark:bg-indigo-900/20 ring-2 ring-indigo-500'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700',
                    isDayToday && 'ring-2 ring-indigo-300 dark:ring-indigo-700',
                    getThemeTransition()
                  )}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {format(day, 'EEE')}
                  </p>
                  <p className={cn(
                    'text-lg font-semibold',
                    isSelected
                      ? 'text-indigo-600 dark:text-indigo-400'
                      : 'text-gray-900 dark:text-white'
                  )}>
                    {format(day, 'd')}
                  </p>
                  {daySlots.length > 0 && (
                    <div className="flex justify-center gap-1 mt-1">
                      {daySlots.slice(0, 3).map((_, i) => (
                        <div
                          key={i}
                          className="w-1 h-1 bg-indigo-500 rounded-full"
                        />
                      ))}
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        </div>
      ) : (
        // Day View
        <div>
          {/* Day Navigation */}
          <div className="flex items-center justify-between mb-3">
            <button
              onClick={() => setSelectedDate(prev => addDays(prev, -1))}
              className={cn('p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors', getThemeTransition())}
            >
              <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {format(selectedDate, 'EEEE, MMMM d, yyyy')}
            </span>
            <button
              onClick={() => setSelectedDate(prev => addDays(prev, 1))}
              className={cn('p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors', getThemeTransition())}
            >
              <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
      )}

      {/* Selected Day Slots */}
      <div className={cn('mt-4 space-y-2', getThemeTransition())}>
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {format(selectedDate, 'EEEE')} Slots ({slotsForSelectedDate.length})
        </h4>
        
        {slotsForSelectedDate.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No slots scheduled</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {slotsForSelectedDate.map((slot, index) => (
              <motion.div
                key={slot.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => handleSlotAction(slot)}
                className={cn(
                  'p-3 rounded-lg border cursor-pointer transition-all',
                  slot.isBooked
                    ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50'
                    : 'border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30',
                  getThemeTransition()
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {slot.startTime} - {slot.endTime}
                      </span>
                    </div>
                    <span className={cn(
                      'px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1',
                      getSlotTypeColor(slot.type)
                    )}>
                      {getSlotTypeIcon(slot.type)}
                      {slot.type}
                    </span>
                  </div>
                  
                  {slot.isBooked ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        Booked
                      </span>
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    </div>
                  ) : (
                    <span className="text-xs font-medium text-green-600 dark:text-green-400">
                      Available
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Upcoming Slots Summary */}
      <div className={cn('mt-4 pt-4 border-t border-gray-200 dark:border-gray-700', getThemeTransition())}>
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Next Appointments
        </h4>
        <div className="space-y-2">
          {upcomingSlots.map(slot => (
            <div
              key={slot.id}
              className="flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-indigo-500 rounded-full" />
                <span className="text-gray-600 dark:text-gray-400">
                  {format(slot.date, 'MMM d')} at {slot.startTime}
                </span>
              </div>
              <span className={cn(
                'px-2 py-0.5 rounded text-xs',
                slot.isBooked
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                  : 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400',
                getThemeTransition()
              )}>
                {slot.isBooked ? 'Booked' : 'Open'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MentorshipSlotsCard;