// modules/agent1/student-analysis/components/PerformanceTrends/TrendPredictor.tsx
import React from 'react';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { PredictionResult } from '../../types/student-analysis.types';

interface TrendPredictorProps {
  predictions: PredictionResult;
}

export const TrendPredictor: React.FC<TrendPredictorProps> = ({ predictions }) => {
  const getTrendIcon = () => {
    if (predictions.trend === 'improving') {
      return <TrendingUp className="w-5 h-5 text-green-500" />;
    } else if (predictions.trend === 'declining') {
      return <TrendingDown className="w-5 h-5 text-red-500" />;
    }
    return <AlertCircle className="w-5 h-5 text-yellow-500" />;
  };

  return (
    <div className="mt-6 p-4 bg-blue-50 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium">Next Semester Prediction</h4>
        {getTrendIcon()}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Predicted SGPA</p>
          <p className="text-2xl font-bold text-blue-600">
            {predictions.predicted_sgpa.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Confidence</p>
          <p className="text-2xl font-bold text-gray-700">
            {(predictions.confidence * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {predictions.risk_factors.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-red-600 mb-2">Risk Factors:</p>
          <ul className="text-xs space-y-1">
            {predictions.risk_factors.map((factor, idx) => (
              <li key={idx} className="flex items-center">
                <span className="w-1 h-1 bg-red-500 rounded-full mr-2"></span>
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4">
        <p className="text-sm font-medium text-green-600 mb-2">Improvement Areas:</p>
        <div className="text-xs space-y-1">
          {predictions.improvement_potential.recommended_focus_areas.map((area, idx) => (
            <div key={idx} className="flex items-center">
              <span className="w-1 h-1 bg-green-500 rounded-full mr-2"></span>
              {area}
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Recommended study time: {predictions.improvement_potential.estimated_effort_hours} hours/day
        </p>
      </div>
    </div>
  );
};