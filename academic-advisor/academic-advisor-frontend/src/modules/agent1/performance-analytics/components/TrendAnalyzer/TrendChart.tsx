// modules/agent1/performance-analytics/components/TrendAnalyzer/TrendChart.tsx
import React, { useMemo, useRef, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Dot,
  Area,
  ComposedChart
} from 'recharts';
import { format, parseISO, isValid } from 'date-fns';
import { motion } from 'framer-motion';
import { PerformanceTrend, Anomaly, TimeRange } from '../../types/analytics.types';

// Safe date formatting utility
const safeFormatDate = (dateString: string, fallback: string = 'Unknown'): string => {
  try {
    if (!dateString) return fallback;
    
    const date = new Date(dateString);
    if (!isValid(date)) {
      console.warn('Invalid date string:', dateString);
      return fallback;
    }
    
    return format(date, 'MMM dd');
  } catch (error) {
    console.error('Date formatting error:', error);
    return fallback;
  }
};

// Safe number formatting
const formatGPA = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return value.toFixed(2);
};

const formatPercentage = (value: number | undefined | null, decimals: number = 1): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return `${value.toFixed(decimals)}%`;
};

// Data processing utilities
const processTrendData = (dataPoints: any[]): any[] => {
  if (!dataPoints || !Array.isArray(dataPoints) || dataPoints.length === 0) {
    console.warn('No valid data points provided');
    return [];
  }

  return dataPoints
    .map((point, index) => {
      try {
        // Ensure required fields with fallbacks
        const safePoint = {
          ...point,
          date: point.date || new Date().toISOString(),
          gpa: typeof point.gpa === 'number' ? point.gpa : point.sgpa || 8.0,
          percentile: typeof point.percentile === 'number' ? point.percentile : 50,
          improvement: typeof point.improvement === 'number' ? point.improvement : 0,
          semester: point.semester || index + 1
        };

        return {
          ...safePoint,
          displayDate: safeFormatDate(safePoint.date, `Sem ${safePoint.semester}`),
          originalDate: safePoint.date,
          upperBound: safePoint.gpa + 0.2,
          lowerBound: safePoint.gpa - 0.2
        };
      } catch (error) {
        console.error('Error processing data point:', point, error);
        return null;
      }
    })
    .filter(point => point !== null);
};

interface TrendChartProps {
  data: PerformanceTrend;
  activeMetric: 'gpa' | 'percentile' | 'improvement';
  timeRange: TimeRange;
  anomalies?: Anomaly[];
  isLoading?: boolean;
  height?: number;
  showProjection?: boolean;
  showConfidenceBands?: boolean;
}

const TrendChart: React.FC<TrendChartProps> = ({
  data,
  activeMetric,
  timeRange,
  anomalies = [],
  isLoading = false,
  height = 400,
  showProjection = true,
  showConfidenceBands = true
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  
  const processedData = useMemo(() => {
    if (!data?.dataPoints) {
      console.warn('No data available for chart');
      return [];
    }

    try {
      let chartData = processTrendData(data.dataPoints);

      // Add projection data if available and enabled
      if (showProjection && data.projection) {
        const projectionData = processTrendData(data.projection).map(point => ({
          ...point,
          isProjection: true
        }));
        chartData = [...chartData, ...projectionData];
      }

      console.log('📊 Processed chart data:', chartData);
      return chartData;
    } catch (error) {
      console.error('Error processing chart data:', error);
      return [];
    }
  }, [data, showProjection]);

  const anomalyPoints = useMemo(() => {
    return anomalies.map(anomaly => ({
      date: safeFormatDate(anomaly.date),
      value: anomaly.value,
      type: anomaly.type,
      severity: anomaly.severity
    }));
  }, [anomalies]);

  const getMetricConfig = (metric: string) => {
    const configs = {
      gpa: {
        dataKey: 'gpa',
        stroke: '#3B82F6',
        fill: '#93C5FD',
        name: 'GPA',
        formatter: formatGPA,
        domain: [0, 10]
      },
      percentile: {
        dataKey: 'percentile',
        stroke: '#10B981',
        fill: '#86EFAC',
        name: 'Percentile',
        formatter: (value: number) => `${Math.round(value)}th`,
        domain: [0, 100]
      },
      improvement: {
        dataKey: 'improvement',
        stroke: '#F59E0B',
        fill: '#FDE047',
        name: 'Improvement',
        formatter: formatPercentage,
        domain: ['dataMin - 10', 'dataMax + 10']
      }
    };

    return configs[metric as keyof typeof configs] || configs.gpa;
  };

  const metricConfig = getMetricConfig(activeMetric);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    const anomaly = anomalyPoints.find(a => a.date === label);

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white p-4 rounded-lg shadow-xl border border-gray-200 min-w-[200px]"
      >
        <p className="font-semibold text-gray-900 mb-2">{label}</p>
        
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm text-gray-600">GPA:</span>
            <span className="font-medium">{formatGPA(data.gpa)}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm text-gray-600">Percentile:</span>
            <span className="font-medium">{data.percentile}th</span>
          </div>
          {data.improvement !== undefined && (
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-gray-600">Improvement:</span>
              <span className={`font-medium ${data.improvement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercentage(data.improvement)}
              </span>
            </div>
          )}
        </div>

        {data.isProjection && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="text-xs text-blue-600 font-medium">📊 Projected Value</p>
          </div>
        )}

        {anomaly && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className={`text-xs font-medium ${
              anomaly.severity === 'high' ? 'text-red-600' : 
              anomaly.severity === 'medium' ? 'text-orange-600' : 'text-yellow-600'
            }`}>
              ⚠️ {anomaly.severity?.toUpperCase()} Anomaly
            </p>
          </div>
        )}
      </motion.div>
    );
  };

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    const anomaly = anomalyPoints.find(a => a.date === payload.displayDate);
    
    if (anomaly) {
      return (
        <g>
          <circle
            cx={cx}
            cy={cy}
            r={6}
            fill={anomaly.severity === 'high' ? '#EF4444' : anomaly.severity === 'medium' ? '#F59E0B' : '#FCD34D'}
            stroke="#fff"
            strokeWidth={2}
          />
        </g>
      );
    }
    
    if (payload.isProjection) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={4}
          fill="#8B5CF6"
          stroke="#fff"
          strokeWidth={2}
          strokeDasharray="2 2"
        />
      );
    }
    
    return (
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={metricConfig.stroke}
        stroke="#fff"
        strokeWidth={2}
      />
    );
  };

  if (!processedData || processedData.length === 0) {
    return (
      <div 
        className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height: `${height}px` }}
      >
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium mb-2">No Chart Data Available</p>
          <p className="text-sm">Performance data will appear here when available</p>
          <p className="text-xs mt-2">Check Firebase for student performance records</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={chartRef} className="relative">
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10 rounded-lg">
          <div className="flex items-center gap-2 text-gray-600">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            Loading chart data...
          </div>
        </div>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={processedData}
          margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
        >
          <defs>
            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={metricConfig.stroke} stopOpacity={0.3} />
              <stop offset="95%" stopColor={metricConfig.stroke} stopOpacity={0} />
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
          
          <XAxis
            dataKey="displayDate"
            stroke="#6B7280"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
            tickMargin={10}
          />
          
          <YAxis
            stroke="#6B7280"
            tick={{ fontSize: 12 }}
            domain={metricConfig.domain}
            tickFormatter={metricConfig.formatter}
            tickMargin={10}
            width={60}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend
            wrapperStyle={{
              paddingTop: '10px',
              fontSize: '12px'
            }}
          />
          
          {/* Confidence bands */}
          {showConfidenceBands && activeMetric === 'gpa' && (
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill="url(#colorGradient)"
              fillOpacity={0.3}
            />
          )}
          
          {/* Reference lines for key thresholds */}
          {activeMetric === 'gpa' && (
            <>
              <ReferenceLine 
                y={3.5} 
                stroke="#10B981" 
                strokeDasharray="3 3" 
                strokeOpacity={0.7}
                label={{ 
                  value: "Dean's List", 
                  position: 'right',
                  fontSize: 12,
                  fill: '#10B981'
                }} 
              />
              <ReferenceLine 
                y={2.0} 
                stroke="#F59E0B" 
                strokeDasharray="3 3" 
                strokeOpacity={0.7}
                label={{ 
                  value: "Minimum", 
                  position: 'right',
                  fontSize: 12,
                  fill: '#F59E0B'
                }} 
              />
            </>
          )}
          
          {/* Main metric line */}
          <Line
            type="monotone"
            dataKey={metricConfig.dataKey}
            stroke={metricConfig.stroke}
            strokeWidth={3}
            name={metricConfig.name}
            dot={<CustomDot />}
            activeDot={{ 
              r: 6, 
              stroke: '#fff', 
              strokeWidth: 2,
              fill: metricConfig.stroke 
            }}
            connectNulls={true}
          />
          
          {/* Anomaly markers */}
          {anomalyPoints.map((anomaly, index) => (
            <ReferenceLine
              key={index}
              x={anomaly.date}
              stroke="#EF4444"
              strokeWidth={2}
              strokeDasharray="3 3"
              strokeOpacity={0.7}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
      
      {/* Chart Legend */}
      <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-blue-500"></div>
          <span className="text-gray-600">Actual</span>
        </div>
        {showProjection && data.projection && data.projection.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-purple-500 border-dashed border-purple-500 border"></div>
            <span className="text-gray-600">Projected</span>
          </div>
        )}
        {anomalyPoints.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-gray-600">Anomaly</span>
          </div>
        )}
        {showConfidenceBands && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-3 bg-blue-200 rounded-sm"></div>
            <span className="text-gray-600">Confidence</span>
          </div>
        )}
      </div>

      {/* Data Summary */}
      <div className="mt-2 text-center">
        <p className="text-xs text-gray-500">
          Showing {processedData.length} data points • {timeRange.label}
        </p>
        <p className="text-xs text-gray-400">
          Data source: Firebase • Updated dynamically
        </p>
      </div>
    </div>
  );
};

export default TrendChart;