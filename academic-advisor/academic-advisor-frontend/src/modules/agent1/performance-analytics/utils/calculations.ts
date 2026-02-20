// modules/agent1/performance-analytics/utils/calculations.ts

import { DataPoint, TrendAnalysis, SubjectData } from '../types/analytics.types';

/**
 * Calculate trend metrics from data points
 */
export function calculateTrendMetrics(dataPoints: DataPoint[], timeRangeDays: number): TrendAnalysis {
  if (!dataPoints || dataPoints.length < 2) {
    return {
      trend: 'stable',
      slope: 0,
      intercept: 0,
      r2Score: 0,
      confidence: 0,
      patterns: [],
      insights: ['Insufficient data for trend analysis'],
      currentGPA: dataPoints?.[0]?.gpa || 0,
      projectedGPA: dataPoints?.[0]?.gpa || 0,
      gpaChange: 0,
      percentile: 50,
      percentileChange: 0,
      improvementRate: 0,
      dataPointsCount: dataPoints?.length || 0
    };
  }

  const n = dataPoints.length;
  const x = dataPoints.map((_, i) => i);
  const y = dataPoints.map(d => d.gpa);

  // Linear regression
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // R² score
  const yMean = sumY / n;
  const ssTotal = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
  const ssRes = y.reduce((sum, yi, i) => {
    const predicted = slope * i + intercept;
    return sum + Math.pow(yi - predicted, 2);
  }, 0);
  const r2Score = 1 - (ssRes / ssTotal);

  // Determine trend
  let trend: 'improving' | 'declining' | 'stable';
  if (slope > 0.05) trend = 'improving';
  else if (slope < -0.05) trend = 'declining';
  else trend = 'stable';

  const currentGPA = y[n - 1];
  const previousGPA = y[n - 2];
  const gpaChange = ((currentGPA - previousGPA) / previousGPA) * 100;

  return {
    trend,
    slope,
    intercept,
    r2Score,
    confidence: Math.min(r2Score, 1),
    patterns: [],
    insights: [`Performance is ${trend}`, `Change: ${gpaChange.toFixed(1)}%`],
    currentGPA,
    projectedGPA: slope * n + intercept,
    gpaChange,
    percentile: dataPoints[n - 1].percentile || 50,
    percentileChange: 0,
    improvementRate: slope * 30,
    dataPointsCount: n
  };
}

/**
 * Detect anomalies in data points
 */
export function detectAnomalies(dataPoints: DataPoint[]): any[] {
  if (!dataPoints || dataPoints.length < 3) return [];

  const anomalies: any[] = [];
  const values = dataPoints.map(d => d.gpa);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const stdDev = Math.sqrt(
    values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
  );

  dataPoints.forEach((point, i) => {
    const deviation = Math.abs(point.gpa - mean);
    if (deviation > 2 * stdDev) {
      anomalies.push({
        date: point.date,
        value: point.gpa,
        expected: mean,
        deviation,
        type: point.gpa > mean ? 'positive' : 'negative',
        severity: deviation > 3 * stdDev ? 'high' : 'medium',
        description: `Unusual ${point.gpa > mean ? 'high' : 'low'} performance detected`
      });
    }
  });

  return anomalies;
}

/**
 * Calculate subject-level metrics
 */
export function calculateSubjectMetrics(subjects: SubjectData[]) {
  if (!subjects || subjects.length === 0) {
    return null;
  }

  const totalCredits = subjects.reduce((sum, s) => sum + s.credits, 0);
  const weightedSum = subjects.reduce((sum, s) => sum + (s.currentGrade * s.credits), 0);
  const overallGPA = weightedSum / totalCredits;

  return {
    overallGPA,
    totalCredits,
    strongSubjects: subjects.filter(s => s.currentGrade >= 85).length,
    needsAttention: subjects.filter(s => s.currentGrade < 60).length,
    gpaChange: 0 // Would need historical data
  };
}

/**
 * Identify weak subject areas
 */
export function identifyWeakAreas(subjects: SubjectData[]): string[] {
  return subjects
    .filter(s => s.currentGrade < 60 || (s.classAverage && s.currentGrade < s.classAverage * 0.85))
    .map(s => s.id);
}