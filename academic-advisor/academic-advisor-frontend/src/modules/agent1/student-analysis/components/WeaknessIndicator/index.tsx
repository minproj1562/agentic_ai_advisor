// modules/agent1/student-analysis/components/WeaknessIndicator/index.tsx
import React from 'react';
import { WeaknessChart } from './WeaknessChart';
import { WeaknessData } from '../../types/student-analysis.types';
import { AlertTriangle, BookOpen, Video } from 'lucide-react';

interface WeaknessIndicatorProps {
  weaknesses: WeaknessData[];
  studentId: string;
}

export const WeaknessIndicator: React.FC<WeaknessIndicatorProps> = ({ 
  weaknesses, 
  studentId 
}) => {
  const getSeverityColor = (score: number) => {
    if (score > 0.8) return 'text-red-600 bg-red-50';
    if (score > 0.6) return 'text-orange-600 bg-orange-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center mb-4">
        <AlertTriangle className="w-5 h-5 text-orange-500 mr-2" />
        <h3 className="text-lg font-semibold">Weakness Analysis</h3>
      </div>

      <div className="space-y-4">
        {weaknesses.map((weakness, index) => (
          <div 
            key={`${weakness.subject}-${index}`}
            className={`p-4 rounded-lg ${getSeverityColor(weakness.weakness_score)}`}
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <h4 className="font-medium">{weakness.subject}</h4>
                <p className="text-sm opacity-75">
                  Weakness Score: {(weakness.weakness_score * 100).toFixed(1)}%
                </p>
              </div>
              <span className="text-xs bg-white px-2 py-1 rounded">
                Confidence: {(weakness.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* Weak Topics */}
            <div className="mt-2">
              <p className="text-sm font-medium mb-1">Weak Topics:</p>
              <div className="flex flex-wrap gap-1">
                {weakness.topic.map((topic) => (
                  <span 
                    key={topic}
                    className="text-xs bg-white/50 px-2 py-1 rounded"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>

            {/* Resources */}
            <div className="mt-3">
              <p className="text-sm font-medium mb-2">Recommended Resources:</p>
              <div className="space-y-1">
                {weakness.recommended_resources.slice(0, 2).map((resource, idx) => (
                  <a
                    key={idx}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center text-xs hover:underline"
                  >
                    {resource.type === 'video' ? (
                      <Video className="w-3 h-3 mr-1" />
                    ) : (
                      <BookOpen className="w-3 h-3 mr-1" />
                    )}
                    {resource.title}
                    {resource.duration && (
                      <span className="ml-2 text-gray-500">({resource.duration})</span>
                    )}
                  </a>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <WeaknessChart weaknesses={weaknesses} />
    </div>
  );
};