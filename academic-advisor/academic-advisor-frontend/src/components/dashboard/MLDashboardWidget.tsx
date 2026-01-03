// src/components/dashboard/MLDashboardWidget.tsx

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, TrendingUp, AlertTriangle, Target, Loader2 } from 'lucide-react';
import { mlService } from '../../services/ml.service';
import { useAuth } from '../../contexts/AuthContext';

interface MLDashboardWidgetProps {
  cgpa: number;
  attendance: number;
  onViewDetails: () => void;
}

export const MLDashboardWidget: React.FC<MLDashboardWidgetProps> = ({
  cgpa,
  attendance,
  onViewDetails
}) => {
  const { user } = useAuth();
  const [predictions, setPredictions] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.uid) {
      fetchQuickPredictions();
    }
  }, [user, cgpa, attendance]);

  const fetchQuickPredictions = async () => {
    if (!user?.uid) return;

    try {
      const result = await mlService.getPredictions(
        user.uid,
        {
          current_cgpa: cgpa,
          attendance_percentage: attendance,
          assignment_completion_ratio: 0.8,
          study_hours_per_week: 25,
          extracurricular_activities: []
        },
        [],
        5
      );
      setPredictions(result);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
        <div className="flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
          <span className="ml-2 text-purple-700">Loading ML insights...</span>
        </div>
      </div>
    );
  }

  if (!predictions) return null;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'Low': return 'text-green-600';
      case 'Medium': return 'text-yellow-600';
      case 'High': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-purple-900 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          ML Predictions
        </h3>
        <button
          onClick={onViewDetails}
          className="text-sm text-purple-600 hover:text-purple-700 font-medium"
        >
          View Details →
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="text-center">
          <p className="text-xs text-gray-600">Next SGPA</p>
          <p className="text-xl font-bold text-purple-700">
            {predictions.predictions.next_semester_gpa.toFixed(2)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">Risk Level</p>
          <p className={`text-xl font-bold ${getRiskColor(predictions.predictions.risk_level)}`}>
            {predictions.predictions.risk_level}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">Trend</p>
          <div className="flex items-center justify-center">
            {predictions.trend_analysis.trend === 'improving' ? (
              <TrendingUp className="w-5 h-5 text-green-600" />
            ) : predictions.trend_analysis.trend === 'declining' ? (
              <AlertTriangle className="w-5 h-5 text-red-600" />
            ) : (
              <Target className="w-5 h-5 text-gray-600" />
            )}
          </div>
        </div>
      </div>

      {predictions.recommendations?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-purple-200">
          <p className="text-xs text-purple-700">
            💡 {predictions.recommendations[0]}
          </p>
        </div>
      )}
    </motion.div>
  );
};