// academic-advisor/academic-advisor-frontend/src/components/dashboard/PerformanceChart.tsx
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface PerformanceData {
  currentSGPI: number;
  previousSGPI: number;
  trend: 'up' | 'down' | 'stable';
  percentageChange: number;
  semesterWiseData: Array<{
    semester: number;
    sgpi: number;
    credits?: number;
    courses?: number;
  }>;
}

interface Props {
  data: PerformanceData | null;
}

const PerformanceChart: React.FC<Props> = ({ data }) => {
  const [hoveredSemester, setHoveredSemester] = useState<number | null>(null);
  const [animationComplete, setAnimationComplete] = useState(false);

  useEffect(() => {
    // Trigger animation after component mounts
    const timer = setTimeout(() => setAnimationComplete(true), 100);
    return () => clearTimeout(timer);
  }, []);

  if (!data || !data.semesterWiseData || data.semesterWiseData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No performance data available</p>
      </div>
    );
  }

  // Calculate chart dimensions
  const maxSGPI = 10;
  const minSGPI = 0;
  const chartHeight = 256; // h-64 in pixels
  const dataPoints = data.semesterWiseData.length;
  
  // Sort data by semester
  const sortedData = [...data.semesterWiseData].sort((a, b) => a.semester - b.semester);

  // Calculate positions for line chart
  const points = sortedData.map((item, index) => {
    // If only one data point, center it at 50%
    const x = dataPoints === 1 ? 50 : (index / (dataPoints - 1)) * 100;
    const y = ((maxSGPI - item.sgpi) / (maxSGPI - minSGPI)) * 100;
    return { x, y, data: item };
  });

  // Create SVG path
  const pathData = points
    .map((point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`;
      return `L ${point.x} ${point.y}`;
    })
    .join(' ');

  // Create area path (filled area under the line)
  // For single point, we don't draw an area or we draw a vertical line?
  // Let's just make it a zero-width area if only 1 point.
  const areaPath = dataPoints > 1 
    ? `${pathData} L 100 100 L 0 100 Z`
    : `M 50 ${points[0].y} L 50 100 Z`;

  // Get trend color
  const getTrendColor = () => {
    if (data.trend === 'up') return 'text-green-600';
    if (data.trend === 'down') return 'text-red-600';
    return 'text-gray-600';
  };

  const getTrendIcon = () => {
    if (data.trend === 'up') return <TrendingUp className="h-5 w-5" />;
    if (data.trend === 'down') return <TrendingDown className="h-5 w-5" />;
    return <Minus className="h-5 w-5" />;
  };

  return (
    <div className="w-full">
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">Performance Trend</h3>
            <div className={`flex items-center space-x-1 ${getTrendColor()}`}>
              {getTrendIcon()}
              <span className="text-sm font-medium">
                {data.percentageChange > 0 ? '+' : ''}{data.percentageChange.toFixed(2)}%
              </span>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-1">SGPI across semesters</p>
        </div>
        
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900">{data.currentSGPI.toFixed(2)}</p>
          <p className="text-xs text-gray-500">Current SGPI</p>
        </div>
      </div>

      {/* SVG Line Chart */}
      <div className="relative h-64 bg-gradient-to-b from-blue-50 to-white rounded-lg p-4">
        <svg
          className="w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((y) => (
            <line
              key={y}
              x1="0"
              y1={y}
              x2="100"
              y2={y}
              stroke="#e5e7eb"
              strokeWidth="0.2"
              strokeDasharray="2,2"
            />
          ))}
          
          {/* Area under the line */}
          <motion.path
            d={areaPath}
            fill="url(#gradient)"
            fillOpacity="0.1"
            initial={{ opacity: 0 }}
            animate={{ opacity: animationComplete ? 0.3 : 0 }}
            transition={{ duration: 1 }}
          />
          
          {/* Line */}
          <motion.path
            d={pathData}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="0.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: animationComplete ? 1 : 0 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
          />
          
          {/* Data points */}
          {points.map((point, index) => (
            <g key={index}>
              <motion.circle
                cx={point.x}
                cy={point.y}
                r="1.5"
                fill="#3b82f6"
                stroke="#ffffff"
                strokeWidth="0.5"
                initial={{ scale: 0 }}
                animate={{ scale: animationComplete ? 1 : 0 }}
                transition={{ delay: 0.1 * index, duration: 0.3 }}
                onMouseEnter={() => setHoveredSemester(point.data.semester)}
                onMouseLeave={() => setHoveredSemester(null)}
                style={{ cursor: 'pointer' }}
              />
              
              {/* Hover tooltip */}
              {hoveredSemester === point.data.semester && (
                <g>
                  <rect
                    x={point.x - 10}
                    y={point.y - 12}
                    width="20"
                    height="8"
                    fill="#1f2937"
                    rx="1"
                  />
                  <text
                    x={point.x}
                    y={point.y - 6}
                    textAnchor="middle"
                    fill="white"
                    fontSize="3"
                    fontWeight="bold"
                  >
                    {point.data.sgpi.toFixed(2)}
                  </text>
                </g>
              )}
            </g>
          ))}
          
          {/* Gradient definition */}
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 -ml-8">
          <span>10.0</span>
          <span>7.5</span>
          <span>5.0</span>
          <span>2.5</span>
          <span>0.0</span>
        </div>

        {/* X-axis labels */}
        <div className={`absolute bottom-0 left-0 w-full flex ${dataPoints === 1 ? 'justify-center' : 'justify-between'} text-xs text-gray-500 mt-2 px-4`}>
          {sortedData.map((item) => (
            <span key={item.semester} className="text-center">
              Sem {item.semester}
            </span>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-50 rounded-lg p-3"
        >
          <p className="text-xs text-gray-500">Current</p>
          <p className="text-lg font-bold text-gray-900">{data.currentSGPI.toFixed(2)}</p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gray-50 rounded-lg p-3"
        >
          <p className="text-xs text-gray-500">Previous</p>
          <p className="text-lg font-bold text-gray-900">{data.previousSGPI.toFixed(2)}</p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gray-50 rounded-lg p-3"
        >
          <p className="text-xs text-gray-500">Average</p>
          <p className="text-lg font-bold text-gray-900">
            {(sortedData.reduce((sum, d) => sum + d.sgpi, 0) / sortedData.length).toFixed(2)}
          </p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className={`rounded-lg p-3 ${
            data.trend === 'up' ? 'bg-green-50' : 
            data.trend === 'down' ? 'bg-red-50' : 'bg-gray-50'
          }`}
        >
          <p className="text-xs text-gray-500">Trend</p>
          <p className={`text-lg font-bold capitalize ${
            data.trend === 'up' ? 'text-green-600' : 
            data.trend === 'down' ? 'text-red-600' : 'text-gray-600'
          }`}>
            {data.trend}
          </p>
        </motion.div>
      </div>

      {/* Semester Details */}
      <div className="mt-6 space-y-2">
        {sortedData.slice().reverse().slice(0, 3).map((semester) => (
          <motion.div
            key={semester.semester}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * semester.semester }}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-sm font-bold text-blue-600">{semester.semester}</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Semester {semester.semester}</p>
                <p className="text-xs text-gray-500">
                  {semester.credits ? `${semester.credits} Credits` : 'No credit info'} • 
                  {semester.courses ? ` ${semester.courses} Courses` : ' No course info'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-gray-900">{semester.sgpi.toFixed(2)}</p>
              <p className="text-xs text-gray-500">SGPI</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default PerformanceChart;