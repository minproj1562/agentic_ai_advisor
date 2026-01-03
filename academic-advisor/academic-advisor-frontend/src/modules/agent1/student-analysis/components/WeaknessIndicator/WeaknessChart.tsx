// modules/agent1/student-analysis/components/WeaknessIndicator/WeaknessChart.tsx
import React from 'react';
import { 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  ResponsiveContainer 
} from 'recharts';
import { WeaknessData } from '../../types/student-analysis.types';

interface WeaknessChartProps {
  weaknesses: WeaknessData[];
}

export const WeaknessChart: React.FC<WeaknessChartProps> = ({ weaknesses }) => {
  const data = weaknesses.map(w => ({
    subject: w.subject,
    weakness: w.weakness_score * 100,
    fullMark: 100
  }));

  return (
    <div className="mt-6">
      <h4 className="text-sm font-medium mb-2">Weakness Distribution</h4>
      <ResponsiveContainer width="100%" height={250}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" />
          <PolarRadiusAxis angle={90} domain={[0, 100]} />
          <Radar 
            name="Weakness Level" 
            dataKey="weakness" 
            stroke="#ef4444" 
            fill="#ef4444" 
            fillOpacity={0.6} 
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};