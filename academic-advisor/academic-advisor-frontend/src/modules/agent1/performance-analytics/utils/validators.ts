// modules/agent1/performance-analytics/utils/validators.ts

import { DataPoint, PerformanceTrend } from '../types/analytics.types';

/**
 * Validate data point structure
 */
export function isValidDataPoint(point: any): point is DataPoint {
  return (
    point &&
    typeof point === 'object' &&
    typeof point.gpa === 'number' &&
    !isNaN(point.gpa) &&
    point.gpa >= 0 &&
    point.gpa <= 10 &&
    typeof point.date === 'string'
  );
}

/**
 * Validate performance trend structure
 */
export function isValidPerformanceTrend(trend: any): trend is PerformanceTrend {
  return (
    trend &&
    typeof trend === 'object' &&
    Array.isArray(trend.dataPoints) &&
    trend.dataPoints.every(isValidDataPoint)
  );
}

/**
 * Validate minimum data requirements
 */
export function hasMinimumData(dataPoints: DataPoint[], minRequired: number = 2): boolean {
  return Array.isArray(dataPoints) && dataPoints.length >= minRequired;
}

/**
 * Sanitize GPA value
 */
export function sanitizeGPA(value: any): number {
  const num = Number(value);
  if (isNaN(num)) return 0;
  return Math.max(0, Math.min(10, num));
}

export function validateAnalyticsData<T>(data: T): T {
  return data;
}

export function sanitizeInput(input: any): string {
  if (typeof input !== 'string') return '';
  return input.trim();
}

export function validatePredictionData<T>(data: T): T {
  return data;
}