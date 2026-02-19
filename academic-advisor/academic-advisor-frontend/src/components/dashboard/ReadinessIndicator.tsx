// src/components/dashboard/ReadinessIndicator.tsx
import React from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  AlertCircle,
  TrendingUp,
  Clock,
  Target,
  ChevronRight,
  Shield,
  Zap
} from 'lucide-react';
import { ReadinessResponse, ReadinessLevel, RecommendationType } from '../../services/weakness.service';

interface ReadinessIndicatorProps {
  readiness: ReadinessResponse;
  compact?: boolean;
  onViewDetails?: () => void;
  onViewStudyPlan?: () => void;
}

const ReadinessIndicator: React.FC<ReadinessIndicatorProps> = ({
  readiness,
  compact = false,
  onViewDetails,
  onViewStudyPlan
}) => {
  // Get colors and icons based on readiness level
  const getLevelConfig = (level: ReadinessLevel) => {
    switch (level) {
      case 'excellent':
        return {
          color: 'green',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-700',
          icon: <CheckCircle className="h-6 w-6 text-green-600" />,
          label: 'Excellent',
          gradient: 'from-green-500 to-emerald-500'
        };
      case 'good':
        return {
          color: 'blue',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          textColor: 'text-blue-700',
          icon: <CheckCircle className="h-6 w-6 text-blue-600" />,
          label: 'Good',
          gradient: 'from-blue-500 to-cyan-500'
        };
      case 'moderate':
        return {
          color: 'yellow',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-700',
          icon: <AlertCircle className="h-6 w-6 text-yellow-600" />,
          label: 'Moderate',
          gradient: 'from-yellow-500 to-orange-500'
        };
      case 'low':
        return {
          color: 'orange',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          textColor: 'text-orange-700',
          icon: <AlertTriangle className="h-6 w-6 text-orange-600" />,
          label: 'Low',
          gradient: 'from-orange-500 to-red-500'
        };
      case 'not_ready':
      default:
        return {
          color: 'red',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-700',
          icon: <XCircle className="h-6 w-6 text-red-600" />,
          label: 'Not Ready',
          gradient: 'from-red-500 to-pink-500'
        };
    }
  };

  const getRecommendationConfig = (type: RecommendationType) => {
    switch (type) {
      case 'proceed':
        return {
          icon: <Zap className="h-5 w-5" />,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          label: 'Ready to Proceed'
        };
      case 'proceed_with_caution':
        return {
          icon: <Shield className="h-5 w-5" />,
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          label: 'Proceed with Caution'
        };
      case 'improve_first':
        return {
          icon: <TrendingUp className="h-5 w-5" />,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          label: 'Improve First'
        };
      case 'do_not_proceed':
      default:
        return {
          icon: <XCircle className="h-5 w-5" />,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          label: 'Do Not Proceed Yet'
        };
    }
  };

  const levelConfig = getLevelConfig(readiness.readiness_level);
  const recConfig = getRecommendationConfig(readiness.recommendation_type);

  // Compact view for dashboard widgets
  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`${levelConfig.bgColor} ${levelConfig.borderColor} border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow`}
        onClick={onViewDetails}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {levelConfig.icon}
            <div>
              <p className="font-semibold text-gray-900">Academic Readiness</p>
              <p className={`text-sm ${levelConfig.textColor}`}>
                {levelConfig.label} - {readiness.overall_readiness_score.toFixed(0)}%
              </p>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-400" />
        </div>
      </motion.div>
    );
  }

  // Full view
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border overflow-hidden"
    >
      {/* Header with score */}
      <div className={`bg-gradient-to-r ${levelConfig.gradient} p-6 text-white`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold opacity-90">Academic Readiness Score</h3>
            <div className="flex items-baseline mt-2">
              <span className="text-5xl font-bold">
                {readiness.overall_readiness_score.toFixed(0)}
              </span>
              <span className="text-2xl ml-1 opacity-80">%</span>
            </div>
            <p className="mt-1 text-sm opacity-80">{levelConfig.label}</p>
          </div>
          <div className="text-right">
            <div className={`${recConfig.bgColor} ${recConfig.color} px-3 py-1 rounded-full text-sm font-medium inline-flex items-center`}>
              {recConfig.icon}
              <span className="ml-1">{recConfig.label}</span>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="h-2 bg-white/30 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${readiness.overall_readiness_score}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="h-full bg-white rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Primary Recommendation */}
      <div className="p-4 border-b bg-gray-50">
        <p className="text-gray-800 font-medium">{readiness.primary_recommendation}</p>
      </div>

      {/* Category Breakdown */}
      <div className="p-4 grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {readiness.interest_readiness.toFixed(0)}%
          </div>
          <p className="text-xs text-gray-500 mt-1">Interest Readiness</p>
        </div>
        <div className="text-center border-x">
          <div className="text-2xl font-bold text-blue-600">
            {readiness.elective_readiness.toFixed(0)}%
          </div>
          <p className="text-xs text-gray-500 mt-1">Elective Readiness</p>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {readiness.honours_readiness.toFixed(0)}%
          </div>
          <p className="text-xs text-gray-500 mt-1">Honours Readiness</p>
        </div>
      </div>

      {/* Flags */}
      {(readiness.has_critical_weakness || readiness.has_blockers || readiness.is_first_semester) && (
        <div className="px-4 pb-4 flex flex-wrap gap-2">
          {readiness.has_critical_weakness && (
            <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full flex items-center">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Critical Weakness
            </span>
          )}
          {readiness.has_blockers && (
            <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full flex items-center">
              <XCircle className="h-3 w-3 mr-1" />
              Has Blockers
            </span>
          )}
          {readiness.is_first_semester && (
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              First Semester
            </span>
          )}
        </div>
      )}

      {/* Focus Areas */}
      {readiness.subjects_to_focus.length > 0 && (
        <div className="p-4 border-t">
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
            <Target className="h-4 w-4 mr-1" />
            Priority Subjects
          </h4>
          <div className="flex flex-wrap gap-2">
            {readiness.subjects_to_focus.map((subject, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded-lg"
              >
                {subject}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Preparation Time */}
      <div className="p-4 border-t bg-gray-50 flex items-center justify-between">
        <div className="flex items-center text-gray-600">
          <Clock className="h-4 w-4 mr-2" />
          <span className="text-sm">
            Estimated preparation: <strong>{readiness.estimated_preparation_time}</strong>
          </span>
        </div>
        {onViewStudyPlan && (
          <button
            onClick={onViewStudyPlan}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center"
          >
            View Study Plan
            <ChevronRight className="h-4 w-4 ml-1" />
          </button>
        )}
      </div>

      {/* Detailed Recommendations */}
      {readiness.detailed_recommendations.length > 0 && (
        <div className="p-4 border-t">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Recommendations</h4>
          <ul className="space-y-2">
            {readiness.detailed_recommendations.slice(0, 4).map((rec, idx) => (
              <li key={idx} className="flex items-start text-sm text-gray-600">
                <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
};

export default ReadinessIndicator;