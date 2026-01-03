// modules/agent1/performance-analytics/components/SubjectPerformance/SubjectRadar.tsx
import React, { useMemo } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip
} from 'recharts';
import { SubjectData } from '../../types/analytics.types';
import { formatPercentage } from '../../utils/formatters';

interface SubjectRadarProps {
  subjects: SubjectData[];
  height?: number;
  showComparison?: boolean;
  className?: string;
}

const SubjectRadar: React.FC<SubjectRadarProps> = ({
  subjects,
  height = 400,
  showComparison = true,
  className = ''
}) => {
  const radarData = useMemo(() => {
    return subjects.slice(0, 8).map(subject => ({
      subject: subject.name.length > 15 
        ? subject.name.substring(0, 15) + '...' 
        : subject.name,
      yourScore: subject.currentGrade,
      classAverage: showComparison ? subject.classAverage : null,
      fullMark: 100
    }));
  }, [subjects, showComparison]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-900 mb-2">{payload[0].payload.subject}</p>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Your Score:</span>
            <span className="font-medium">{payload[0].value}%</span>
          </div>
          {showComparison && payload[1] && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span className="text-sm text-gray-600">Class Avg:</span>
              <span className="font-medium">{payload[1].value}%</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={radarData}>
          <PolarGrid 
            stroke="#E5E7EB"
            strokeDasharray="3 3"
          />
          <PolarAngleAxis 
            dataKey="subject"
            tick={{ fontSize: 12, fill: '#6B7280' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#9CA3AF' }}
          />
          
          <Radar
            name="Your Score"
            dataKey="yourScore"
            stroke="#3B82F6"
            fill="#3B82F6"
            fillOpacity={0.6}
            strokeWidth={2}
          />
          
          {showComparison && (
            <Radar
              name="Class Average"
              dataKey="classAverage"
              stroke="#6B7280"
              fill="#6B7280"
              fillOpacity={0.3}
              strokeWidth={2}
              strokeDasharray="5 5"
            />
          )}
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend
            wrapperStyle={{
              paddingTop: '20px',
              fontSize: '14px'
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SubjectRadar;