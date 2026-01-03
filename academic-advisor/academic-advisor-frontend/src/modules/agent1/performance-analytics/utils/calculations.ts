// modules/agent1/performance-analytics/utils/calculations.ts
import { DataPoint, TrendAnalysis, SubjectData, Anomaly, TrendPattern } from '../types/analytics.types';
import { CALCULATION_CONSTANTS } from '../constants/thresholds';

/**
 * Calculate trend metrics from performance data
 */
export function calculateTrendMetrics(
  data: DataPoint[],
  timeframeDays: number
): TrendAnalysis {
  // Add proper null checks at the start
  if (!data || !Array.isArray(data) || data.length === 0) {
    return getDefaultTrendAnalysis();
  }

  try {
    // Filter valid data points
    const validDataPoints = data.filter(dp => 
      dp && 
      typeof dp === 'object' && 
      dp.date && 
      typeof dp.date === 'string' &&
      typeof dp.gpa === 'number' &&
      !isNaN(dp.gpa)
    );

    if (validDataPoints.length < 2) {
      return getDefaultTrendAnalysis();
    }

    const filteredData = filterDataByTimeframe(validDataPoints, timeframeDays);
    const regression = linearRegression(filteredData);
    const statistics = calculateStatistics(filteredData);
    
    return {
      trend: determineTrend(regression.slope),
      slope: regression.slope,
      intercept: regression.intercept,
      r2Score: regression.r2,
      confidence: calculateConfidence(regression.r2, filteredData.length),
      currentGPA: statistics.current,
      projectedGPA: projectValue(regression, 1),
      gpaChange: statistics.percentageChange,
      percentile: statistics.percentile,
      percentileChange: statistics.percentileChange,
      improvementRate: regression.slope * 30, // Monthly rate
      dataPointsCount: filteredData.length,
      patterns: detectPatterns(filteredData),
      insights: generateInsights(regression, statistics),
      analysisDate: new Date().toISOString()
    };

  } catch (error) {
    console.error('Error in calculateTrendMetrics:', error);
    return getDefaultTrendAnalysis();
  }
}

/**
 * Add this helper function
 */
function getDefaultTrendAnalysis(): TrendAnalysis {
  return {
    trend: 'stable',
    slope: 0,
    intercept: 0,
    r2Score: 0,
    confidence: 0.5,
    patterns: [],
    insights: ['Insufficient data for analysis'],
    currentGPA: 0,
    projectedGPA: 0,
    gpaChange: 0,
    percentile: 50,
    percentileChange: 0,
    improvementRate: 0,
    dataPointsCount: 0,
    analysisDate: new Date().toISOString()
  };
}

/**
 * Detect patterns in data points
 */
export function detectPatterns(dataPoints: DataPoint[]): TrendPattern[] {
  if (!dataPoints || !Array.isArray(dataPoints) || dataPoints.length === 0) {
    return [];
  }

  const patterns: TrendPattern[] = [];
  
  try {
    // Filter out invalid data points with proper null checks
    const validDataPoints = dataPoints.filter(dp => 
      dp && 
      typeof dp === 'object' && 
      dp.date && 
      typeof dp.date === 'string' &&
      typeof dp.gpa === 'number' &&
      !isNaN(dp.gpa)
    );

    if (validDataPoints.length < 2) {
      return [];
    }

    // Sort by date to ensure chronological order
    const sortedPoints = [...validDataPoints].sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    // Detect acceleration pattern (safe version)
    const accelerationPattern = detectAccelerationPattern(sortedPoints);
    if (accelerationPattern) patterns.push(accelerationPattern);

    // Detect plateau pattern (safe version)  
    const plateauPattern = detectPlateauPattern(sortedPoints);
    if (plateauPattern) patterns.push(plateauPattern);

    // Detect seasonal pattern (safe version)
    const seasonalPattern = detectSeasonalPattern(sortedPoints);
    if (seasonalPattern) patterns.push(seasonalPattern);

    // Detect consecutive improvements pattern
    const consecutivePattern = detectConsecutivePattern(sortedPoints);
    if (consecutivePattern) patterns.push(consecutivePattern);

    // Detect volatility pattern
    const volatilityPattern = detectVolatilityPattern(sortedPoints);
    if (volatilityPattern) patterns.push(volatilityPattern);

  } catch (error) {
    console.error('Error in detectPatterns:', error);
    return [];
  }
  
  return patterns;
}

// Safe version of detectAccelerationPattern
function detectAccelerationPattern(dataPoints: DataPoint[]): TrendPattern | null {
  if (dataPoints.length < 3) return null;
  
  try {
    const firstDerivative = [];
    for (let i = 1; i < dataPoints.length; i++) {
      if (dataPoints[i] && dataPoints[i-1]) {
        firstDerivative.push(dataPoints[i].gpa - dataPoints[i-1].gpa);
      }
    }
    
    const secondDerivative = [];
    for (let i = 1; i < firstDerivative.length; i++) {
      secondDerivative.push(firstDerivative[i] - firstDerivative[i-1]);
    }
    
    if (secondDerivative.length === 0) return null;
    
    const avgAcceleration = secondDerivative.reduce((a, b) => a + b, 0) / secondDerivative.length;
    
    if (Math.abs(avgAcceleration) > 0.01) {
      return {
        type: avgAcceleration > 0 ? 'accelerating' : 'decelerating',
        strength: Math.abs(avgAcceleration),
        description: `Performance is ${avgAcceleration > 0 ? 'accelerating' : 'decelerating'}`,
        startDate: dataPoints[0].date,
        endDate: dataPoints[dataPoints.length - 1].date
      };
    }
  } catch (error) {
    console.error('Error in detectAccelerationPattern:', error);
  }
  
  return null;
}

// Safe version of detectPlateauPattern  
function detectPlateauPattern(dataPoints: DataPoint[]): TrendPattern | null {
  if (dataPoints.length < 5) return null;
  
  try {
    const recentData = dataPoints.slice(-5);
    const gpas = recentData.map(d => d.gpa);
    const variance = calculateVariance(gpas);
    
    if (variance < 0.01) {
      return {
        type: 'plateau',
        strength: 1 - variance,
        description: 'Performance has plateaued',
        startDate: recentData[0].date,
        endDate: recentData[recentData.length - 1].date
      };
    }
  } catch (error) {
    console.error('Error in detectPlateauPattern:', error);
  }
  
  return null;
}

// Safe version of detectSeasonalPattern
function detectSeasonalPattern(dataPoints: DataPoint[]): TrendPattern | null {
  // Simplified implementation - you can enhance this later
  return null;
}

// Safe variance calculation
function calculateVariance(values: number[]): number {
  if (values.length === 0) return 0;
  
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
  return squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
}

// Detect consecutive improvements pattern
function detectConsecutivePattern(dataPoints: DataPoint[]): TrendPattern | null {
  if (dataPoints.length < 3) return null;
  
  try {
    let improvementStreak = 0;
    let maxStreak = 0;
    
    for (let i = 1; i < dataPoints.length; i++) {
      if (dataPoints[i] && dataPoints[i-1] && dataPoints[i].gpa > dataPoints[i-1].gpa) {
        improvementStreak++;
        maxStreak = Math.max(maxStreak, improvementStreak);
      } else {
        improvementStreak = 0;
      }
    }
    
    if (maxStreak >= 3) {
      return {
        type: 'consecutive_improvement',
        strength: maxStreak / dataPoints.length,
        description: `${maxStreak} consecutive improvements`,
        startDate: dataPoints[0].date,
        endDate: dataPoints[dataPoints.length - 1].date
      };
    }
  } catch (error) {
    console.error('Error in detectConsecutivePattern:', error);
  }
  
  return null;
}

// Detect volatility pattern
function detectVolatilityPattern(dataPoints: DataPoint[]): TrendPattern | null {
  if (dataPoints.length < 3) return null;
  
  try {
    const changes = [];
    for (let i = 1; i < dataPoints.length; i++) {
      if (dataPoints[i] && dataPoints[i-1]) {
        changes.push(Math.abs(dataPoints[i].gpa - dataPoints[i-1].gpa));
      }
    }
    
    if (changes.length === 0) return null;
    
    const avgChange = changes.reduce((a, b) => a + b, 0) / changes.length;
    if (avgChange > 0.2) {
      return {
        type: 'high_volatility',
        strength: avgChange,
        description: 'High volatility detected',
        startDate: dataPoints[0].date,
        endDate: dataPoints[dataPoints.length - 1].date
      };
    }
  } catch (error) {
    console.error('Error in detectVolatilityPattern:', error);
  }
  
  return null;
}

/**
 * Detect anomalies in data points
 */
export function detectAnomalies(data: DataPoint[]): Anomaly[] {
  const anomalies: Anomaly[] = [];
  
  if (!data || !Array.isArray(data) || data.length < 3) return anomalies;

  try {
    // Filter valid data points
    const validData = data.filter(dp => 
      dp && 
      typeof dp === 'object' && 
      dp.date && 
      typeof dp.date === 'string' &&
      typeof dp.gpa === 'number' &&
      !isNaN(dp.gpa)
    );

    if (validData.length < 3) return anomalies;

    const smoothed = exponentialSmoothing(validData.map(d => d.gpa), 0.3);
    const stdDev = standardDeviation(validData.map(d => d.gpa));
    const mean = average(validData.map(d => d.gpa));
    
    for (let i = 0; i < validData.length; i++) {
      const actual = validData[i].gpa;
      const expected = smoothed[i];
      const zScore = stdDev !== 0 ? (actual - expected) / stdDev : 0;
      
      // Check for statistical anomaly (|z| > 2)
      if (Math.abs(zScore) > 2) {
        anomalies.push({
          date: validData[i].date,
          value: actual,
          expected,
          deviation: Math.abs(actual - expected),
          zScore,
          type: actual > expected ? 'positive' : 'negative',
          severity: Math.abs(zScore) > 3 ? 'high' : 'medium',
          description: generateAnomalyDescription(actual, expected, zScore, validData[i].date)
        });
      }
      
      // Check for sudden changes
      if (i > 0 && validData[i-1]) {
        const changeRate = validData[i-1].gpa !== 0 ? (actual - validData[i - 1].gpa) / validData[i - 1].gpa : 0;
        if (Math.abs(changeRate) > 0.2) {
          anomalies.push({
            date: validData[i].date,
            value: actual,
            expected: validData[i - 1].gpa,
            deviation: Math.abs(changeRate),
            type: 'sudden_change',
            severity: Math.abs(changeRate) > 0.3 ? 'high' : 'medium',
            description: `Sudden ${changeRate > 0 ? 'increase' : 'decrease'} of ${(Math.abs(changeRate) * 100).toFixed(1)}%`
          });
        }
      }
    }
  } catch (error) {
    console.error('Error in detectAnomalies:', error);
  }
  
  return anomalies;
}

/**
 * Calculate subject metrics
 */
export function calculateSubjectMetrics(subjects: SubjectData[]): any {
  if (!subjects || !Array.isArray(subjects)) {
    return getDefaultSubjectMetrics();
  }

  try {
    const validSubjects = subjects.filter(s => 
      s && 
      typeof s === 'object' && 
      typeof s.currentGrade === 'number' && 
      !isNaN(s.currentGrade) &&
      typeof s.credits === 'number' &&
      !isNaN(s.credits)
    );

    if (validSubjects.length === 0) {
      return getDefaultSubjectMetrics();
    }

    const grades = validSubjects.map(s => s.currentGrade);
    const credits = validSubjects.map(s => s.credits);
    
    const weightedGPA = calculateWeightedGPA(grades, credits);
    const previousGPA = calculatePreviousGPA(validSubjects);
    const gpaChange = previousGPA !== 0 ? ((weightedGPA - previousGPA) / previousGPA) * 100 : 0;
    
    return {
      overallGPA: weightedGPA,
      gpaChange,
      strongSubjects: validSubjects.filter(s => s.currentGrade >= 85).length,
      needsAttention: validSubjects.filter(s => s.currentGrade < 60).length,
      totalCredits: sum(credits),
      averageGrade: average(grades),
      medianGrade: median(grades),
      standardDeviation: standardDeviation(grades),
      distribution: calculateGradeDistribution(grades),
      trends: calculateSubjectTrends(validSubjects)
    };
  } catch (error) {
    console.error('Error in calculateSubjectMetrics:', error);
    return getDefaultSubjectMetrics();
  }
}

function getDefaultSubjectMetrics(): any {
  return {
    overallGPA: 0,
    gpaChange: 0,
    strongSubjects: 0,
    needsAttention: 0,
    totalCredits: 0,
    averageGrade: 0,
    medianGrade: 0,
    standardDeviation: 0,
    distribution: { A: 0, B: 0, C: 0, D: 0, F: 0 },
    trends: { improving: 0, declining: 0, stable: 0 }
  };
}

/**
 * Identify weak areas in subjects
 */
export function identifyWeakAreas(subjects: SubjectData[]): string[] {
  if (!subjects || !Array.isArray(subjects)) return [];
  
  try {
    const threshold = CALCULATION_CONSTANTS.WEAKNESS_THRESHOLD;
    const classAvgThreshold = CALCULATION_CONSTANTS.CLASS_AVG_THRESHOLD;
    
    return subjects
      .filter(s => s && typeof s === 'object' && s.id)
      .filter(s => 
        s.currentGrade < threshold || 
        (s.classAverage && s.currentGrade < s.classAverage * classAvgThreshold)
      )
      .sort((a, b) => a.currentGrade - b.currentGrade)
      .map(s => s.id);
  } catch (error) {
    console.error('Error in identifyWeakAreas:', error);
    return [];
  }
}

/**
 * Interpolate missing data points
 */
export function interpolateData(data: DataPoint[]): DataPoint[] {
  if (!data || !Array.isArray(data) || data.length < 2) return data || [];
  
  try {
    const interpolated: DataPoint[] = [];
    
    for (let i = 0; i < data.length - 1; i++) {
      if (!data[i] || !data[i+1]) continue;
      
      interpolated.push(data[i]);
      
      const current = new Date(data[i].date);
      const next = new Date(data[i + 1].date);
      const daysDiff = Math.floor((next.getTime() - current.getTime()) / (1000 * 60 * 60 * 24));
      
      // If gap is more than 7 days, interpolate
      if (daysDiff > 7) {
        const points = Math.floor(daysDiff / 7) - 1;
        for (let j = 1; j <= points; j++) {
          const ratio = j / (points + 1);
          const interpolatedDate = new Date(current);
          interpolatedDate.setDate(interpolatedDate.getDate() + (j * 7));
          
          interpolated.push({
            date: interpolatedDate.toISOString(),
            gpa: lerp(data[i].gpa, data[i + 1].gpa, ratio),
            percentile: lerp(data[i].percentile || 50, data[i + 1].percentile || 50, ratio),
            improvement: lerp(data[i].improvement || 0, data[i + 1].improvement || 0, ratio),
            isInterpolated: true
          });
        }
      }
    }
    
    if (data.length > 0) {
      interpolated.push(data[data.length - 1]);
    }
    
    return interpolated;
  } catch (error) {
    console.error('Error in interpolateData:', error);
    return data || [];
  }
}

/**
 * Smooth data using exponential smoothing
 */
export function smoothData(data: DataPoint[], alpha: number = 0.3): DataPoint[] {
  if (!data || !Array.isArray(data)) return [];
  
  try {
    const validData = data.filter(dp => 
      dp && 
      typeof dp.gpa === 'number' && 
      !isNaN(dp.gpa)
    );

    if (validData.length === 0) return [];

    const smoothedGPA = exponentialSmoothing(validData.map(d => d.gpa), alpha);
    const smoothedPercentile = exponentialSmoothing(validData.map(d => d.percentile || 50), alpha);
    
    return validData.map((point, i) => ({
      ...point,
      gpa: smoothedGPA[i],
      percentile: smoothedPercentile[i],
      isSmoothed: true
    }));
  } catch (error) {
    console.error('Error in smoothData:', error);
    return data || [];
  }
}

/**
 * Calculate weighted GPA
 */
export function calculateWeightedGPA(grades: number[], credits: number[]): number {
  if (!grades || !credits || grades.length !== credits.length) {
    return 0;
  }

  try {
    const totalCredits = sum(credits);
    if (totalCredits === 0) return 0;
    
    const weightedSum = grades.reduce((sum, grade, i) => {
      const gradePoint = gradeToGPA(grade);
      return sum + (gradePoint * credits[i]);
    }, 0);
    
    return Number((weightedSum / totalCredits).toFixed(2));
  } catch (error) {
    console.error('Error in calculateWeightedGPA:', error);
    return 0;
  }
}

/**
 * Calculate prediction confidence
 */
export function calculateConfidence(r2Score: number, dataPoints: number): number {
  try {
    const r2Weight = 0.5;
    const dataWeight = 0.3;
    const recencyWeight = 0.2;
    
    const r2Confidence = Math.min(Math.max(r2Score, 0), 1) * r2Weight;
    const dataConfidence = Math.min(dataPoints / 20, 1) * dataWeight;
    const recencyConfidence = 0.8 * recencyWeight; // Simplified, would check actual recency
    
    return Math.min(r2Confidence + dataConfidence + recencyConfidence, 1);
  } catch (error) {
    console.error('Error in calculateConfidence:', error);
    return 0.5;
  }
}

/**
 * Linear regression calculation
 */
export function linearRegression(data: DataPoint[]): {
  slope: number;
  intercept: number;
  r2: number;
} {
  if (!data || data.length < 2) {
    return { slope: 0, intercept: 0, r2: 0 };
  }

  try {
    const n = data.length;
    const x = data.map((_, i) => i);
    const y = data.map(d => d.gpa);
    
    const sumX = sum(x);
    const sumY = sum(y);
    const sumXY = x.reduce((acc, xi, i) => acc + xi * y[i], 0);
    const sumX2 = x.reduce((acc, xi) => acc + xi * xi, 0);
    const sumY2 = y.reduce((acc, yi) => acc + yi * yi, 0);
    
    const denominator = (n * sumX2 - sumX * sumX);
    if (denominator === 0) {
      return { slope: 0, intercept: 0, r2: 0 };
    }
    
    const slope = (n * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / n;
    
    // Calculate R²
    const yMean = sumY / n;
    const ssTotal = y.reduce((acc, yi) => acc + Math.pow(yi - yMean, 2), 0);
    const ssRes = y.reduce((acc, yi, i) => {
      const predicted = slope * i + intercept;
      return acc + Math.pow(yi - predicted, 2);
    }, 0);
    const r2 = ssTotal === 0 ? 0 : 1 - (ssRes / ssTotal);
    
    return { slope, intercept, r2: isNaN(r2) ? 0 : Math.max(0, r2) };
  } catch (error) {
    console.error('Error in linearRegression:', error);
    return { slope: 0, intercept: 0, r2: 0 };
  }
}

/**
 * Polynomial regression
 */
export function polynomialRegression(
  data: DataPoint[],
  degree: number = 2
): {
  coefficients: number[];
  r2: number;
} {
  if (!data || data.length < 2) {
    return { coefficients: [], r2: 0 };
  }

  try {
    const n = data.length;
    const x = data.map((_, i) => i);
    const y = data.map(d => d.gpa);
    
    // Create Vandermonde matrix
    const X: number[][] = [];
    for (let i = 0; i < n; i++) {
      const row = [];
      for (let j = 0; j <= degree; j++) {
        row.push(Math.pow(x[i], j));
      }
      X.push(row);
    }
    
    // Solve using normal equation: (X'X)^-1 X'y
    const Xt = transpose(X);
    const XtX = matrixMultiply(Xt, X);
    const XtXInv = matrixInverse(XtX);
    const Xty = matrixVectorMultiply(Xt, y);
    const coefficients = matrixVectorMultiply(XtXInv, Xty);
    
    // Calculate R²
    const yMean = average(y);
    const predictions = x.map(xi => {
      return coefficients.reduce((sum, coef, j) => sum + coef * Math.pow(xi, j), 0);
    });
    
    const ssTotal = y.reduce((acc, yi) => acc + Math.pow(yi - yMean, 2), 0);
    const ssRes = y.reduce((acc, yi, i) => acc + Math.pow(yi - predictions[i], 2), 0);
    const r2 = ssTotal === 0 ? 0 : 1 - (ssRes / ssTotal);
    
    return { coefficients, r2: isNaN(r2) ? 0 : Math.max(0, r2) };
  } catch (error) {
    console.error('Error in polynomialRegression:', error);
    return { coefficients: [], r2: 0 };
  }
}

/**
 * Moving average calculation
 */
export function movingAverage(data: number[], window: number): number[] {
  if (!data || !Array.isArray(data) || data.length === 0) return [];
  
  try {
    const result: number[] = [];
    
    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - Math.floor(window / 2));
      const end = Math.min(data.length, i + Math.floor(window / 2) + 1);
      const subset = data.slice(start, end);
      result.push(average(subset));
    }
    
    return result;
  } catch (error) {
    console.error('Error in movingAverage:', error);
    return data || [];
  }
}

/**
 * Exponential smoothing
 */
export function exponentialSmoothing(data: number[], alpha: number): number[] {
  if (!data || !Array.isArray(data) || data.length === 0) return [];
  
  try {
    const result: number[] = [data[0]];
    
    for (let i = 1; i < data.length; i++) {
      result.push(alpha * data[i] + (1 - alpha) * result[i - 1]);
    }
    
    return result;
  } catch (error) {
    console.error('Error in exponentialSmoothing:', error);
    return data || [];
  }
}

/**
 * Calculate standard deviation
 */
export function standardDeviation(data: number[]): number {
  if (!data || !Array.isArray(data) || data.length === 0) return 0;
  
  try {
    const mean = average(data);
    const squaredDiffs = data.map(x => Math.pow(x - mean, 2));
    const avgSquaredDiff = average(squaredDiffs);
    return Math.sqrt(avgSquaredDiff);
  } catch (error) {
    console.error('Error in standardDeviation:', error);
    return 0;
  }
}

/**
 * Calculate percentile rank
 */
export function percentileRank(value: number, data: number[]): number {
  if (!data || !Array.isArray(data) || data.length === 0) return 0;
  
  try {
    const sorted = [...data].sort((a, b) => a - b);
    const index = sorted.findIndex(v => v >= value);
    
    if (index === -1) return 100;
    if (index === 0) return 0;
    
    return (index / data.length) * 100;
  } catch (error) {
    console.error('Error in percentileRank:', error);
    return 50;
  }
}

/**
 * Detect outliers using IQR method
 */
export function detectOutliers(data: number[]): {
  outliers: number[];
  lowerBound: number;
  upperBound: number;
} {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return { outliers: [], lowerBound: 0, upperBound: 0 };
  }

  try {
    const sorted = [...data].sort((a, b) => a - b);
    const q1 = quantile(sorted, 0.25);
    const q3 = quantile(sorted, 0.75);
    const iqr = q3 - q1;
    
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;
    
    const outliers = data.filter(x => x < lowerBound || x > upperBound);
    
    return { outliers, lowerBound, upperBound };
  } catch (error) {
    console.error('Error in detectOutliers:', error);
    return { outliers: [], lowerBound: 0, upperBound: 0 };
  }
}

/**
 * Calculate correlation coefficient
 */
export function correlation(x: number[], y: number[]): number {
  if (!x || !y || !Array.isArray(x) || !Array.isArray(y) || x.length !== y.length) {
    return 0;
  }

  try {
    const n = x.length;
    const sumX = sum(x);
    const sumY = sum(y);
    const sumXY = x.reduce((acc, xi, i) => acc + xi * y[i], 0);
    const sumX2 = sum(x.map(xi => xi * xi));
    const sumY2 = sum(y.map(yi => yi * yi));
    
    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    
    return denominator === 0 ? 0 : numerator / denominator;
  } catch (error) {
    console.error('Error in correlation:', error);
    return 0;
  }
}

// Helper functions
function filterDataByTimeframe(data: DataPoint[], days: number): DataPoint[] {
  if (!data || !Array.isArray(data) || days <= 0) return data || [];
  
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return data.filter(d => new Date(d.date) >= cutoffDate);
  } catch (error) {
    console.error('Error in filterDataByTimeframe:', error);
    return data || [];
  }
}

function determineTrend(slope: number): 'improving' | 'declining' | 'stable' {
  if (slope > 0.01) return 'improving';
  if (slope < -0.01) return 'declining';
  return 'stable';
}

function calculateStatistics(data: DataPoint[]): any {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return {
      current: 0,
      previous: 0,
      percentageChange: 0,
      average: 0,
      median: 0,
      stdDev: 0,
      percentile: 50,
      percentileChange: 0
    };
  }

  try {
    const gpas = data.map(d => d.gpa);
    const percentiles = data.map(d => d.percentile || 50);
    
    const current = gpas[gpas.length - 1];
    const previous = gpas[0];
    const percentageChange = previous !== 0 ? ((current - previous) / previous) * 100 : 0;
    
    return {
      current,
      previous,
      percentageChange,
      average: average(gpas),
      median: median(gpas),
      stdDev: standardDeviation(gpas),
      percentile: percentiles[percentiles.length - 1],
      percentileChange: percentiles[percentiles.length - 1] - percentiles[0]
    };
  } catch (error) {
    console.error('Error in calculateStatistics:', error);
    return {
      current: 0,
      previous: 0,
      percentageChange: 0,
      average: 0,
      median: 0,
      stdDev: 0,
      percentile: 50,
      percentileChange: 0
    };
  }
}

function projectValue(regression: any, periods: number): number {
  if (!regression || typeof regression.intercept !== 'number' || typeof regression.slope !== 'number') {
    return 0;
  }
  return regression.intercept + regression.slope * periods;
}

function generateInsights(regression: any, statistics: any): string[] {
  const insights: string[] = [];
  
  try {
    if (regression.slope > 0) {
      insights.push(`Improving at ${(regression.slope * 100).toFixed(2)}% per period`);
    } else if (regression.slope < 0) {
      insights.push(`Declining at ${Math.abs(regression.slope * 100).toFixed(2)}% per period`);
    }
    
    if (regression.r2 > 0.8) {
      insights.push('Strong trend reliability');
    } else if (regression.r2 < 0.5) {
      insights.push('Weak trend - high variability');
    }
    
    if (statistics.stdDev > 0.5) {
      insights.push('High performance variability');
    }
  } catch (error) {
    console.error('Error in generateInsights:', error);
    insights.push('Analysis completed with some limitations');
  }
  
  return insights.length > 0 ? insights : ['No significant patterns detected'];
}

function generateAnomalyDescription(
  actual: number,
  expected: number,
  zScore: number,
  date: string
): string {
  try {
    const formattedDate = new Date(date).toLocaleDateString();
    const difference = expected !== 0 ? ((actual - expected) / expected * 100).toFixed(1) : '0';
    
    if (zScore > 0) {
      return `Exceptional performance on ${formattedDate} - ${difference}% above expected`;
    } else {
      return `Significant drop on ${formattedDate} - ${Math.abs(Number(difference))}% below expected`;
    }
  } catch (error) {
    console.error('Error in generateAnomalyDescription:', error);
    return `Anomaly detected on ${date}`;
  }
}

function calculatePreviousGPA(subjects: SubjectData[]): number {
  if (!subjects || !Array.isArray(subjects)) return 0;
  
  try {
    const validSubjects = subjects.filter(s => 
      s && 
      typeof s.currentGrade === 'number' && 
      !isNaN(s.currentGrade)
    );
    
    if (validSubjects.length === 0) return 0;
    
    return validSubjects.reduce((sum, s) => sum + (s.previousGrade || s.currentGrade * 0.95), 0) / validSubjects.length;
  } catch (error) {
    console.error('Error in calculatePreviousGPA:', error);
    return 0;
  }
}

function calculateGradeDistribution(grades: number[]): any {
  if (!grades || !Array.isArray(grades)) {
    return { A: 0, B: 0, C: 0, D: 0, F: 0 };
  }

  try {
    return {
      A: grades.filter(g => g >= 90).length,
      B: grades.filter(g => g >= 80 && g < 90).length,
      C: grades.filter(g => g >= 70 && g < 80).length,
      D: grades.filter(g => g >= 60 && g < 70).length,
      F: grades.filter(g => g < 60).length
    };
  } catch (error) {
    console.error('Error in calculateGradeDistribution:', error);
    return { A: 0, B: 0, C: 0, D: 0, F: 0 };
  }
}

function calculateSubjectTrends(subjects: SubjectData[]): any {
  if (!subjects || !Array.isArray(subjects)) {
    return { improving: 0, declining: 0, stable: 0 };
  }

  try {
    return {
      improving: subjects.filter(s => (s.trend || 0) > 0).length,
      declining: subjects.filter(s => (s.trend || 0) < 0).length,
      stable: subjects.filter(s => (s.trend || 0) === 0).length
    };
  } catch (error) {
    console.error('Error in calculateSubjectTrends:', error);
    return { improving: 0, declining: 0, stable: 0 };
  }
}

function gradeToGPA(grade: number): number {
  if (grade >= 90) return 4.0;
  if (grade >= 80) return 3.0;
  if (grade >= 70) return 2.0;
  if (grade >= 60) return 1.0;
  return 0.0;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function sum(arr: number[]): number {
  if (!arr || !Array.isArray(arr)) return 0;
  return arr.reduce((a, b) => a + b, 0);
}

function average(arr: number[]): number {
  if (!arr || !Array.isArray(arr) || arr.length === 0) return 0;
  return sum(arr) / arr.length;
}

function median(arr: number[]): number {
  if (!arr || !Array.isArray(arr) || arr.length === 0) return 0;
  
  try {
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];
  } catch (error) {
    console.error('Error in median:', error);
    return 0;
  }
}

function quantile(sorted: number[], q: number): number {
  if (!sorted || !Array.isArray(sorted) || sorted.length === 0) return 0;
  
  try {
    const pos = (sorted.length - 1) * q;
    const base = Math.floor(pos);
    const rest = pos - base;
    
    if (sorted[base + 1] !== undefined) {
      return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
    } else {
      return sorted[base];
    }
  } catch (error) {
    console.error('Error in quantile:', error);
    return 0;
  }
}

function transpose(matrix: number[][]): number[][] {
  if (!matrix || !Array.isArray(matrix) || matrix.length === 0) return [];
  
  try {
    return matrix[0].map((_, i) => matrix.map(row => row[i]));
  } catch (error) {
    console.error('Error in transpose:', error);
    return [];
  }
}

function matrixMultiply(a: number[][], b: number[][]): number[][] {
  if (!a || !b || !Array.isArray(a) || !Array.isArray(b) || a.length === 0 || b.length === 0) return [];
  
  try {
    const result: number[][] = [];
    for (let i = 0; i < a.length; i++) {
      result[i] = [];
      for (let j = 0; j < b[0].length; j++) {
        let sum = 0;
        for (let k = 0; k < b.length; k++) {
          sum += a[i][k] * b[k][j];
        }
        result[i][j] = sum;
      }
    }
    return result;
  } catch (error) {
    console.error('Error in matrixMultiply:', error);
    return [];
  }
}

function matrixVectorMultiply(matrix: number[][], vector: number[]): number[] {
  if (!matrix || !vector || !Array.isArray(matrix) || !Array.isArray(vector) || matrix.length === 0) return [];
  
  try {
    return matrix.map(row => 
      row.reduce((sum, val, i) => sum + val * vector[i], 0)
    );
  } catch (error) {
    console.error('Error in matrixVectorMultiply:', error);
    return [];
  }
}

function matrixInverse(matrix: number[][]): number[][] {
  if (!matrix || !Array.isArray(matrix) || matrix.length === 0) return [];
  
  try {
    const n = matrix.length;
    
    if (n === 2) {
      const det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
      if (det === 0) return matrix; // Return original if singular
      
      return [
        [matrix[1][1] / det, -matrix[0][1] / det],
        [-matrix[1][0] / det, matrix[0][0] / det]
      ];
    }
    
    // For larger matrices, return identity matrix as placeholder
    return matrix.map((row, i) => row.map((_, j) => i === j ? 1 : 0));
  } catch (error) {
    console.error('Error in matrixInverse:', error);
    return [];
  }
}