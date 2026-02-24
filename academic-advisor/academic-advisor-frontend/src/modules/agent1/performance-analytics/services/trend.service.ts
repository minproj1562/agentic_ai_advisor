// modules/agent1/performance-analytics/services/trend.service.ts
import {
  PerformanceTrend,
  TrendAnalysis,
  DataPoint,
  TrendPattern,
  SeasonalPattern
} from '../types/analytics.types';
import { TREND_THRESHOLDS } from '../constants/thresholds';

class TrendService {
  private readonly MIN_DATA_POINTS = 5;
  private readonly SMOOTHING_WINDOW = 3;

  /**
   * Create a default/fallback TrendAnalysis when data is insufficient
   */
  private createDefaultAnalysis(data?: PerformanceTrend): TrendAnalysis {
    const currentGPA = data?.currentGPA ??
      (data?.dataPoints?.length ? data.dataPoints[data.dataPoints.length - 1].gpa : 0);

    return {
      trend: 'stable',
      slope: 0,
      intercept: currentGPA,
      r2Score: 0,
      confidence: 0,
      patterns: [],
      insights: ['Insufficient data for trend analysis. Add more semester results to enable predictions.'],
      currentGPA,
      projectedGPA: currentGPA,
      gpaChange: 0,
      percentile: data?.percentile ?? 50,
      percentileChange: 0,
      improvementRate: 0,
      dataPointsCount: data?.dataPoints?.length ?? 0,
      analysisDate: new Date().toISOString()
    };
  }

  /**
   * Analyze trends in performance data
   * Returns a default analysis instead of throwing when data is insufficient
   */
  async analyzeTrends(data: PerformanceTrend): Promise<TrendAnalysis> {
    try {
      // Guard: return default analysis if insufficient data (NO throw)
      if (!data?.dataPoints || data.dataPoints.length < this.MIN_DATA_POINTS) {
        console.warn(
          `Trend analysis: only ${data?.dataPoints?.length ?? 0} data points available, ` +
          `need ${this.MIN_DATA_POINTS}. Returning default analysis.`
        );
        return this.createDefaultAnalysis(data);
      }

      // Smooth data to reduce noise
      const smoothedData = this.smoothData(data.dataPoints);

      // Calculate trend metrics
      const trendMetrics = this.calculateTrendMetrics(smoothedData);

      // Detect patterns
      const patterns = this.detectPatterns(smoothedData);

      // Calculate confidence
      const confidence = this.calculateConfidence(smoothedData, trendMetrics);

      // Generate insights
      const insights = this.generateInsights(trendMetrics, patterns);

      return {
        trend: trendMetrics.direction,
        slope: trendMetrics.slope,
        intercept: trendMetrics.intercept,
        r2Score: trendMetrics.r2Score,
        confidence,
        patterns,
        insights,
        currentGPA: data.currentGPA || smoothedData[smoothedData.length - 1].gpa,
        projectedGPA: this.projectGPA(trendMetrics, 1),
        gpaChange: trendMetrics.percentageChange,
        percentile: data.percentile || 50,
        percentileChange: this.calculatePercentileChange(data),
        improvementRate: trendMetrics.improvementRate,
        dataPointsCount: data.dataPoints.length,
        analysisDate: new Date().toISOString()
      };
    } catch (error) {
      console.error('Trend analysis failed:', error);
      // Return default instead of re-throwing — prevents SWR infinite retry
      return this.createDefaultAnalysis(data);
    }
  }

  /**
   * Generate predictions based on trends
   * Returns empty array instead of throwing when data is insufficient
   */
  async generatePredictions(
    data: PerformanceTrend,
    timeRange: string
  ): Promise<DataPoint[]> {
    try {
      // Guard: return empty predictions if insufficient data
      if (!data?.dataPoints || data.dataPoints.length < this.MIN_DATA_POINTS) {
        console.warn(
          `Prediction generation: only ${data?.dataPoints?.length ?? 0} data points available, ` +
          `need ${this.MIN_DATA_POINTS}. Returning empty predictions.`
        );
        return [];
      }

      const trendAnalysis = await this.analyzeTrends(data);
      const predictions: DataPoint[] = [];

      const lastDate = new Date(data.dataPoints[data.dataPoints.length - 1].date);
      const daysToPredict = this.getHorizonDays(timeRange);
      const interval = Math.ceil(daysToPredict / 10); // 10 prediction points

      for (let i = 1; i <= 10; i++) {
        const daysAhead = i * interval;
        const predictedDate = new Date(lastDate);
        predictedDate.setDate(predictedDate.getDate() + daysAhead);

        const predictedGPA = this.projectGPA(
          trendAnalysis,
          daysAhead / 120 // Convert to semesters
        );

        predictions.push({
          date: predictedDate.toISOString(),
          gpa: Math.max(0, Math.min(4, predictedGPA)),
          percentile: this.projectPercentile(trendAnalysis, daysAhead),
          improvement: trendAnalysis.improvementRate * (i / 10),
          confidence: Math.max(0.5, 1 - (i * 0.05)),
          isPrediction: true
        });
      }

      return predictions;
    } catch (error) {
      console.error('Prediction generation failed:', error);
      // Return empty array instead of re-throwing
      return [];
    }
  }

  /**
   * Detect anomalies in performance data
   */
  detectAnomalies(dataPoints: DataPoint[]): any[] {
    if (!dataPoints || dataPoints.length < 2) return [];

    const anomalies = [];
    const smoothed = this.smoothData(dataPoints);
    const stdDev = this.calculateStdDev(smoothed.map(d => d.gpa));
    const mean = smoothed.reduce((sum, d) => sum + d.gpa, 0) / smoothed.length;

    for (let i = 1; i < dataPoints.length; i++) {
      const current = dataPoints[i].gpa;
      const expected = smoothed[i].gpa;
      const deviation = Math.abs(current - expected);

      if (deviation > 2 * stdDev) {
        anomalies.push({
          date: dataPoints[i].date,
          value: current,
          expected,
          deviation,
          type: current > expected ? 'positive' : 'negative',
          severity: deviation > 3 * stdDev ? 'high' : 'medium',
          description: this.generateAnomalyDescription(current, expected, dataPoints[i].date)
        });
      }

      const previousGpa = dataPoints[i - 1].gpa;
      if (previousGpa > 0) {
        const changeRate = Math.abs(current - previousGpa) / previousGpa;
        if (changeRate > 0.2) {
          anomalies.push({
            date: dataPoints[i].date,
            value: current,
            previous: previousGpa,
            changeRate,
            type: 'sudden_change',
            severity: changeRate > 0.3 ? 'high' : 'medium',
            description: `Sudden ${current > previousGpa ? 'increase' : 'decrease'} of ${(changeRate * 100).toFixed(1)}% detected`
          });
        }
      }
    }

    return anomalies;
  }

  /**
   * Calculate trend metrics
   */
  private calculateTrendMetrics(data: DataPoint[]): any {
    const n = data.length;
    const x = data.map((_, i) => i);
    const y = data.map(d => d.gpa);

    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);

    const denominator = n * sumX2 - sumX * sumX;
    const slope = denominator !== 0 ? (n * sumXY - sumX * sumY) / denominator : 0;
    const intercept = (sumY - slope * sumX) / n;

    const yMean = sumY / n;
    const ssTotal = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
    const ssRes = y.reduce((sum, yi, i) => {
      const predicted = slope * i + intercept;
      return sum + Math.pow(yi - predicted, 2);
    }, 0);
    const r2Score = ssTotal !== 0 ? 1 - (ssRes / ssTotal) : 0;

    let direction: 'improving' | 'declining' | 'stable';
    if (slope > TREND_THRESHOLDS.IMPROVEMENT) direction = 'improving';
    else if (slope < -TREND_THRESHOLDS.IMPROVEMENT) direction = 'declining';
    else direction = 'stable';

    const firstValue = y[0];
    const lastValue = y[n - 1];
    const percentageChange = firstValue !== 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

    const improvementRate = slope * 30;

    return {
      slope,
      intercept,
      r2Score,
      direction,
      percentageChange,
      improvementRate
    };
  }

  /**
   * Detect patterns in data
   */
  private detectPatterns(data: DataPoint[]): TrendPattern[] {
    const patterns: TrendPattern[] = [];

    const seasonalPattern = this.detectSeasonalPattern(data);
    if (seasonalPattern) patterns.push(seasonalPattern);

    const cyclicalPattern = this.detectCyclicalPattern(data);
    if (cyclicalPattern) patterns.push(cyclicalPattern);

    const accelerationPattern = this.detectAcceleration(data);
    if (accelerationPattern) patterns.push(accelerationPattern);

    const plateauPattern = this.detectPlateau(data);
    if (plateauPattern) patterns.push(plateauPattern);

    return patterns;
  }

  /**
   * Smooth data using moving average
   */
  private smoothData(data: DataPoint[]): DataPoint[] {
    if (!data || data.length === 0) return [];

    const smoothed: DataPoint[] = [];
    const window = this.SMOOTHING_WINDOW;

    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - Math.floor(window / 2));
      const end = Math.min(data.length, i + Math.floor(window / 2) + 1);
      const subset = data.slice(start, end);

      const avgGPA = subset.reduce((sum, d) => sum + d.gpa, 0) / subset.length;
      const avgPercentile = subset.reduce((sum, d) => sum + (d.percentile || 0), 0) / subset.length;

      smoothed.push({
        ...data[i],
        gpa: avgGPA,
        percentile: avgPercentile
      });
    }

    return smoothed;
  }

  /**
   * Calculate confidence in trend analysis
   */
  private calculateConfidence(data: DataPoint[], metrics: any): number {
    let confidence = 0;

    confidence += (metrics.r2Score || 0) * 0.4;

    const dataQuality = Math.min(data.length / 20, 1);
    confidence += dataQuality * 0.2;

    const consistency = this.calculateConsistency(data);
    confidence += consistency * 0.2;

    const recency = this.calculateRecency(data);
    confidence += recency * 0.2;

    return Math.min(confidence, 1);
  }

  /**
   * Generate insights from trends
   */
  private generateInsights(metrics: any, patterns: TrendPattern[]): string[] {
    const insights: string[] = [];

    if (metrics.direction === 'improving') {
      insights.push(`Performance improving at ${(metrics.improvementRate * 100).toFixed(1)}% per month`);
    } else if (metrics.direction === 'declining') {
      insights.push(`Performance declining - immediate intervention recommended`);
    } else {
      insights.push('Performance is stable');
    }

    patterns.forEach(pattern => {
      insights.push(pattern.description);
    });

    if (metrics.r2Score > 0.8) {
      insights.push('High confidence in trend prediction');
    } else if (metrics.r2Score < 0.5) {
      insights.push('Performance is highly variable - predictions less certain');
    }

    return insights;
  }

  // Helper methods
  private projectGPA(analysis: any, semestersAhead: number): number {
    return (analysis.intercept || 0) + ((analysis.slope || 0) * semestersAhead * 120);
  }

  private projectPercentile(analysis: any, daysAhead: number): number {
    return Math.min(100, Math.max(0,
      (analysis.percentile || 50) + ((analysis.percentileChange || 0) * daysAhead / 30)
    ));
  }

  private calculatePercentileChange(data: PerformanceTrend): number {
    if (!data.dataPoints || data.dataPoints.length < 2) return 0;

    const first = data.dataPoints[0].percentile || 50;
    const last = data.dataPoints[data.dataPoints.length - 1].percentile || 50;

    return last - first;
  }

  private getHorizonDays(timeRange: string): number {
    const horizons: { [key: string]: number } = {
      '1m': 30,
      '3m': 90,
      '6m': 180,
      '1y': 365
    };
    return horizons[timeRange] || 90;
  }

  private calculateStdDev(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    const avgSquaredDiff = squaredDiffs.reduce((sum, v) => sum + v, 0) / values.length;
    return Math.sqrt(avgSquaredDiff);
  }

  private generateAnomalyDescription(actual: number, expected: number, date: string): string {
    const diff = actual - expected;
    const formattedDate = new Date(date).toLocaleDateString();

    if (diff > 0) {
      return `Unusually high performance on ${formattedDate} - ${expected !== 0 ? (diff * 100 / expected).toFixed(1) : '0'}% above expected`;
    } else {
      return `Performance drop on ${formattedDate} - ${expected !== 0 ? Math.abs(diff * 100 / expected).toFixed(1) : '0'}% below expected`;
    }
  }

  private detectSeasonalPattern(data: DataPoint[]): TrendPattern | null {
    return null;
  }

  private detectCyclicalPattern(data: DataPoint[]): TrendPattern | null {
    return null;
  }

  private detectAcceleration(data: DataPoint[]): TrendPattern | null {
    if (data.length < 3) return null;

    const firstDerivative = [];
    for (let i = 1; i < data.length; i++) {
      firstDerivative.push(data[i].gpa - data[i - 1].gpa);
    }

    const secondDerivative = [];
    for (let i = 1; i < firstDerivative.length; i++) {
      secondDerivative.push(firstDerivative[i] - firstDerivative[i - 1]);
    }

    if (secondDerivative.length === 0) return null;

    const avgAcceleration = secondDerivative.reduce((a, b) => a + b, 0) / secondDerivative.length;

    if (Math.abs(avgAcceleration) > 0.01) {
      return {
        type: avgAcceleration > 0 ? 'accelerating' : 'decelerating',
        strength: Math.abs(avgAcceleration),
        description: `Performance is ${avgAcceleration > 0 ? 'accelerating' : 'decelerating'}`,
        startDate: data[0].date,
        endDate: data[data.length - 1].date
      };
    }

    return null;
  }

  private detectPlateau(data: DataPoint[]): TrendPattern | null {
    if (data.length < 5) return null;

    const recentData = data.slice(-5);
    const variance = this.calculateVariance(recentData.map(d => d.gpa));

    if (variance < 0.01) {
      return {
        type: 'plateau',
        strength: 1 - variance,
        description: 'Performance has plateaued - consider new strategies',
        startDate: recentData[0].date,
        endDate: recentData[recentData.length - 1].date
      };
    }

    return null;
  }

  private calculateConsistency(data: DataPoint[]): number {
    if (data.length < 2) return 1;

    let consistencyScore = 1;
    for (let i = 1; i < data.length; i++) {
      const change = Math.abs(data[i].gpa - data[i - 1].gpa);
      if (change > 0.5) consistencyScore -= 0.1;
    }

    return Math.max(0, consistencyScore);
  }

  private calculateRecency(data: DataPoint[]): number {
    if (data.length === 0) return 0;

    const lastDate = new Date(data[data.length - 1].date);
    const daysSince = (Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24);

    if (daysSince < 7) return 1;
    if (daysSince < 30) return 0.8;
    if (daysSince < 90) return 0.5;
    return 0.2;
  }

  private calculateVariance(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return squaredDiffs.reduce((sum, v) => sum + v, 0) / values.length;
  }
}

export const trendService = new TrendService();