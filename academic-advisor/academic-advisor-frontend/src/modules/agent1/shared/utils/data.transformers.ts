// modules/agent1/shared/utils/data.transformers.ts
// FIXED: Create local types since the import is missing
interface DataPoint {
  date: string;
  gpa: number;
  percentile?: number;
  improvement?: number;
  confidence?: number;
  isPrediction?: boolean;
  isInterpolated?: boolean;
  movingAverage?: number;
}

interface PerformanceTrend {
  studentId: string;
  dataPoints: DataPoint[];
  currentGPA?: number;
  percentile?: number;
  subjects?: SubjectData[];
  lastUpdated?: string;
  projection?: any[];
  metrics?: any;
}

interface SubjectData {
  id: string;
  name: string;
  category: string;
  credits: number;
  currentGrade: number;
  previousGrade?: number;
  classAverage?: number;
  rank?: number;
  totalStudents?: number;
  attendance?: number;
  completedAssignments?: number;
  totalAssignments?: number;
  weakTopics?: string[];
  recommendation?: string;
  trend: number;
}

// FIXED: Create local date-fns functions since the import is missing
const format = (date: Date, formatStr: string): string => {
  // Simplified format function - in production, use date-fns
  if (formatStr === 'MMM dd') {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const day = date.getDate().toString().padStart(2, '0');
    return `${month} ${day}`;
  } else if (formatStr === 'yyyy-ww') {
    const year = date.getFullYear();
    // Simple week calculation (not ISO week)
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
    const week = Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
    return `${year}-${week.toString().padStart(2, '0')}`;
  } else if (formatStr === 'yyyy-MM') {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${year}-${month}`;
  }
  return date.toISOString().split('T')[0];
};

const parseISO = (dateString: string): Date => {
  return new Date(dateString);
};

/**
 * Transform raw API data to PerformanceTrend
 */
export function transformRawData(rawData: any): PerformanceTrend {
  return {
    studentId: rawData.student_id || rawData.studentId,
    dataPoints: transformDataPoints(rawData.data_points || rawData.dataPoints || []),
    currentGPA: rawData.current_gpa || rawData.currentGPA,
    percentile: rawData.percentile,
    subjects: rawData.subjects ? rawData.subjects.map(transformSubject) : [],
    lastUpdated: rawData.last_updated || rawData.lastUpdated || new Date().toISOString(),
    projection: rawData.projection,
    metrics: rawData.metrics
  };
}

/**
 * Transform data points
 */
export function transformDataPoints(points: any[]): DataPoint[] {
  return points.map(point => ({
    date: normalizeDate(point.date || point.timestamp),
    gpa: normalizeGPA(point.gpa || point.score),
    percentile: point.percentile || point.rank,
    improvement: point.improvement || point.change,
    confidence: point.confidence,
    isPrediction: point.is_prediction || point.isPrediction || false,
    isInterpolated: point.is_interpolated || point.isInterpolated || false
  }));
}

/**
 * Transform subject data
 */
export function transformSubject(subject: any): SubjectData {
  return {
    id: subject.id || subject.subject_id,
    name: subject.name || subject.subject_name,
    category: subject.category || 'general',
    credits: subject.credits || subject.credit_hours || 3,
    currentGrade: subject.current_grade || subject.currentGrade || subject.grade || 0,
    previousGrade: subject.previous_grade || subject.previousGrade,
    classAverage: subject.class_average || subject.classAverage,
    rank: subject.rank || subject.student_rank,
    totalStudents: subject.total_students || subject.totalStudents,
    attendance: subject.attendance || subject.attendance_rate,
    completedAssignments: subject.completed_assignments || subject.completedAssignments,
    totalAssignments: subject.total_assignments || subject.totalAssignments,
    weakTopics: subject.weak_topics || subject.weakTopics || [],
    recommendation: subject.recommendation,
    trend: subject.trend || 0
  };
}

/**
 * Aggregate metrics from data points
 */
export function aggregateMetrics(dataPoints: DataPoint[]): any {
  if (!dataPoints || dataPoints.length === 0) {
    return {
      count: 0,
      average: 0,
      median: 0,
      min: 0,
      max: 0,
      stdDev: 0
    };
  }

  const gpas = dataPoints.map(d => d.gpa).filter(gpa => !isNaN(gpa));
  const sorted = [...gpas].sort((a, b) => a - b);
  
  const sum = gpas.reduce((acc, gpa) => acc + gpa, 0);
  const average = sum / gpas.length;
  const median = sorted[Math.floor(sorted.length / 2)];
  const min = sorted[0];
  const max = sorted[sorted.length - 1];
  
  const squaredDiffs = gpas.map(gpa => Math.pow(gpa - average, 2));
  const variance = squaredDiffs.reduce((acc, diff) => acc + diff, 0) / gpas.length;
  const stdDev = Math.sqrt(variance);

  return {
    count: gpas.length,
    average: Number(average.toFixed(3)),
    median: Number(median.toFixed(3)),
    min: Number(min.toFixed(3)),
    max: Number(max.toFixed(3)),
    stdDev: Number(stdDev.toFixed(3)),
    range: Number((max - min).toFixed(3)),
    firstQuartile: sorted[Math.floor(sorted.length * 0.25)],
    thirdQuartile: sorted[Math.floor(sorted.length * 0.75)]
  };
}

/**
 * Normalize date format
 */
export function normalizeDate(date: string | Date): string {
  try {
    if (typeof date === 'string') {
      // Try to parse as ISO string
      const parsed = parseISO(date);
      return parsed.toISOString();
    }
    return date.toISOString();
  } catch {
    return new Date().toISOString();
  }
}

/**
 * Normalize GPA to 4.0 scale
 */
export function normalizeGPA(gpa: number): number {
  if (gpa <= 4) return gpa;
  if (gpa <= 10) return (gpa / 10) * 4;
  if (gpa <= 100) return (gpa / 100) * 4;
  return 0;
}

/**
 * Transform to chart data
 */
/**
 * Transform to chart data
 */
export function transformToChartData(
  dataPoints: DataPoint[],
  metric: 'gpa' | 'percentile' | 'improvement' = 'gpa'
): any[] {
  return dataPoints.map(point => ({
    name: format(parseISO(point.date), 'MMM dd'),
    value: point[metric] || 0,
    ...point // This already includes the date property
  }));
}
/**
 * Group data by period
 */
export function groupByPeriod(
  dataPoints: DataPoint[],
  period: 'week' | 'month' | 'semester'
): Record<string, DataPoint[]> {
  const grouped: Record<string, DataPoint[]> = {};
  
  dataPoints.forEach(point => {
    const date = parseISO(point.date);
    let key: string;
    
    switch (period) {
      case 'week':
        key = format(date, 'yyyy-ww');
        break;
      case 'month':
        key = format(date, 'yyyy-MM');
        break;
      case 'semester':
        const month = date.getMonth();
        const year = date.getFullYear();
        key = month < 6 ? `${year}-spring` : `${year}-fall`;
        break;
      default:
        key = format(date, 'yyyy-MM-dd');
    }
    
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(point);
  });
  
  return grouped;
}

/**
 * Calculate period averages
 */
export function calculatePeriodAverages(
  dataPoints: DataPoint[],
  period: 'week' | 'month' | 'semester'
): any[] {
  const grouped = groupByPeriod(dataPoints, period);
  
  return Object.entries(grouped).map(([key, points]) => {
    const metrics = aggregateMetrics(points);
    return {
      period: key,
      average: metrics.average,
      min: metrics.min,
      max: metrics.max,
      count: metrics.count
    };
  });
}

/**
 * Flatten nested object
 */
export function flattenObject(obj: any, prefix = ''): Record<string, any> {
  const flattened: Record<string, any> = {};
  
  Object.keys(obj).forEach(key => {
    const value = obj[key];
    const newKey = prefix ? `${prefix}.${key}` : key;
    
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(flattened, flattenObject(value, newKey));
    } else {
      flattened[newKey] = value;
    }
  });
  
  return flattened;
}

/**
 * Convert to CSV
 */
export function convertToCSV(data: any[], columns?: string[]): string {
  if (data.length === 0) return '';
  
  const headers = columns || Object.keys(data[0]);
  const rows = data.map(row => 
    headers.map(header => {
      const value = row[header];
      return typeof value === 'string' && value.includes(',') 
        ? `"${value}"` 
        : value;
    }).join(',')
  );
  
  return [headers.join(','), ...rows].join('\n');
}

/**
 * Merge datasets
 */
export function mergeDatasets(
  primary: DataPoint[],
  secondary: DataPoint[]
): DataPoint[] {
  const merged = new Map<string, DataPoint>();
  
  primary.forEach(point => {
    merged.set(point.date, point);
  });
  
  secondary.forEach(point => {
    const existing = merged.get(point.date);
    if (existing) {
      merged.set(point.date, { ...existing, ...point });
    } else {
      merged.set(point.date, point);
    }
  });
  
  return Array.from(merged.values()).sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );
}

/**
 * Calculate moving average
 */
export function addMovingAverage(
  dataPoints: DataPoint[],
  window: number = 3
): DataPoint[] {
  return dataPoints.map((point, index) => {
    const start = Math.max(0, index - Math.floor(window / 2));
    const end = Math.min(dataPoints.length, index + Math.floor(window / 2) + 1);
    const subset = dataPoints.slice(start, end);
    const avgGPA = subset.reduce((sum, p) => sum + p.gpa, 0) / subset.length;
    
    return {
      ...point,
      movingAverage: Number(avgGPA.toFixed(3))
    };
  });
}

/**
 * Fill missing dates
 */
export function fillMissingDates(
  dataPoints: DataPoint[],
  interval: 'day' | 'week' = 'week'
): DataPoint[] {
  if (dataPoints.length < 2) return dataPoints;
  
  const filled: DataPoint[] = [];
  const sortedPoints = [...dataPoints].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  
  for (let i = 0; i < sortedPoints.length - 1; i++) {
    filled.push(sortedPoints[i]);
    
    const current = new Date(sortedPoints[i].date);
    const next = new Date(sortedPoints[i + 1].date);
    const daysDiff = Math.floor((next.getTime() - current.getTime()) / (1000 * 60 * 60 * 24));
    const step = interval === 'day' ? 1 : 7;
    
    if (daysDiff > step) {
      const steps = Math.floor(daysDiff / step);
      for (let j = 1; j < steps; j++) {
        const fillDate = new Date(current);
        fillDate.setDate(fillDate.getDate() + (j * step));
        
        const ratio = j / steps;
        filled.push({
          date: fillDate.toISOString(),
          gpa: sortedPoints[i].gpa + (sortedPoints[i + 1].gpa - sortedPoints[i].gpa) * ratio,
          isInterpolated: true
        });
      }
    }
  }
  
  filled.push(sortedPoints[sortedPoints.length - 1]);
  return filled;
}