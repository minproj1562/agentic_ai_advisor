// modules/agent1/shared/components/RecommendationCard.tsx
import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb,
  TrendingUp,
  Target,
  Clock,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  BookOpen,
  Star,
  Info
} from 'lucide-react';

interface RecommendationCardProps {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  impact: number; // 0-100
  timeRequired: string;
  actionItems?: string[];
  resources?: Array<{
    title: string;
    url: string;
    type: 'video' | 'article' | 'book' | 'course';
  }>;
  onAccept?: () => void;
  onDismiss?: () => void;
  onLearnMore?: () => void;
  className?: string;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({
  title,
  description,
  priority,
  impact,
  timeRequired,
  actionItems = [],
  resources = [],
  onAccept,
  onDismiss,
  onLearnMore,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAccepted, setIsAccepted] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  const getPriorityConfig = useCallback(() => {
    switch (priority) {
      case 'high':
        return {
          color: 'red',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-700',
          icon: <AlertCircle className="w-5 h-5" />
        };
      case 'medium':
        return {
          color: 'yellow',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-700',
          icon: <Target className="w-5 h-5" />
        };
      case 'low':
        return {
          color: 'blue',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          textColor: 'text-blue-700',
          icon: <Lightbulb className="w-5 h-5" />
        };
    }
  }, [priority]);

  const getImpactColor = useCallback((value: number) => {
    if (value >= 80) return 'bg-green-500';
    if (value >= 60) return 'bg-blue-500';
    if (value >= 40) return 'bg-yellow-500';
    return 'bg-gray-400';
  }, []);

  const handleAccept = useCallback(() => {
    setIsAccepted(true);
    onAccept?.();
    setTimeout(() => setIsDismissed(true), 500);
  }, [onAccept]);

  const handleDismiss = useCallback(() => {
    setIsDismissed(true);
    onDismiss?.();
  }, [onDismiss]);

  const priorityConfig = getPriorityConfig();

  if (isDismissed && !isAccepted) return null;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ 
          opacity: isAccepted ? 0 : 1, 
          y: 0,
          scale: isAccepted ? 0.95 : 1
        }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className={`${priorityConfig.bgColor} ${priorityConfig.borderColor} border rounded-xl p-6 ${className}`}
      >
        {/* Success Overlay */}
        {isAccepted && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-green-100 rounded-xl flex items-center justify-center z-10"
          >
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-2" />
              <p className="text-green-700 font-semibold">Recommendation Accepted!</p>
            </div>
          </motion.div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg ${priorityConfig.bgColor}`}>
              {priorityConfig.icon}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-600 mt-1">{description}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.textColor} ${priorityConfig.bgColor}`}>
              {priority.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-600">Impact Score</span>
              <span className="text-sm font-medium">{impact}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${impact}%` }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className={`h-2 rounded-full ${getImpactColor(impact)}`}
              />
            </div>
          </div>
          
          <div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Time Required</span>
            </div>
            <p className="text-sm font-medium mt-1">{timeRequired}</p>
          </div>
        </div>

        {/* Expandable Content */}
        <motion.div
          animate={{ height: isExpanded ? 'auto' : 0 }}
          initial={{ height: 0 }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          {/* Action Items */}
          {actionItems.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Action Items</h4>
              <ul className="space-y-2">
                {actionItems.map((item, index) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-2"
                  >
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-600">{item}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          )}

          {/* Resources */}
          {resources.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Recommended Resources</h4>
              <div className="grid grid-cols-1 gap-2">
                {resources.map((resource, index) => (
                  <motion.a
                    key={index}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-2 p-2 bg-white rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <BookOpen className="w-4 h-4 text-blue-500" />
                    <span className="text-sm text-gray-700 flex-1">{resource.title}</span>
                    <span className="text-xs text-gray-500 capitalize">{resource.type}</span>
                  </motion.a>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* Actions */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <Info className="w-4 h-4" />
            <span>{isExpanded ? 'Show Less' : 'Show More'}</span>
            <ChevronRight className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
          </button>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleDismiss}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Dismiss
            </button>
            <button
              onClick={onLearnMore}
              className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 transition-colors"
            >
              Learn More
            </button>
            <button
              onClick={handleAccept}
              className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors ${
                priority === 'high' 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : priority === 'medium'
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              Accept & Start
            </button>
          </div>
        </div>

        {/* Rating */}
        <div className="absolute top-2 right-2">
          <div className="flex items-center gap-1">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                className={`w-3 h-3 ${
                  i < Math.floor(impact / 20) 
                    ? 'text-yellow-400 fill-current' 
                    : 'text-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default RecommendationCard;