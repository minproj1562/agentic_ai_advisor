// modules/agent1/student-analysis/components/PerformanceTrends/index.tsx
import React, { useMemo } from 'react';
import { TrendPredictor } from './TrendPredictor';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { PerformanceHistory } from '../../types/student-analysis.types';

interface PerformanceTrendsProps {
  history: PerformanceHistory;
  predictions?: any;
}

export const PerformanceTrends: React.FC<PerformanceTrendsProps> = ({ 
  history, 
  predictions 
}) => {
  const chartData = useMemo(() => {
    const historicalData = history.raw_data.reduce((acc, record) => {
      const existing = acc.find(d => d.semester === record.semester);
      if (existing) {
        existing.sgpa = record.sgpa;
        existing.cgpa = record.cgpa;
      } else {
        acc.push({
          semester: record.semester,
          name: `Sem ${record.semester}`,
          sgpa: record.sgpa,
          cgpa: record.cgpa
        });
      }
      return acc;
    }, [] as any[]);

    // Add prediction if available
    if (predictions) {
      const nextSem = Math.max(...historicalData.map(d => d.semester)) + 1;
      historicalData.push({
        semester: nextSem,
        name: `Sem ${nextSem} (Predicted)`,
        sgpa: predictions.predicted_sgpa,
        cgpa: null, // CGPA can't be predicted without all subject grades
        isPrediction: true
      });
    }

    return historicalData;
  }, [history, predictions]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Performance Trends</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 10]} />
          <Tooltip />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="sgpa" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6' }}
            name="SGPA"
          />
          <Line 
            type="monotone" 
            dataKey="cgpa" 
            stroke="#10b981" 
            strokeWidth={2}
            dot={{ fill: '#10b981' }}
            name="CGPA"
          />
        </LineChart>
      </ResponsiveContainer>

      {predictions && <TrendPredictor predictions={predictions} />}
    </div>
  );
};