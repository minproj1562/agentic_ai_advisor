// modules/agent1/performance-analytics/services/analytics.service.ts
import { apiService } from '../../../../modules/shared/services/api.service';
import { firebaseRealtime } from '../../../../core/integrations/firebase/realtime';
import { firebaseStorage } from '../../../../core/integrations/firebase/storage';
import {
  PerformanceTrend,
  TrendOptions,
  WeaknessAnalysis,
  SubjectData,
  AnalyticsConfig,
  DataPoint
} from '../types/analytics.types';
import { validateAnalyticsData, sanitizeInput } from '../utils/validators';
import { ANALYTICS_ENDPOINTS, CACHE_DURATION } from '../constants/thresholds';

// Add missing functions locally since data.transformers module is missing
const transformRawData = (rawData: any): any => {
  if (!rawData) return null;
  
  return {
    ...rawData,
    dataPoints: Array.isArray(rawData.dataPoints) ? rawData.dataPoints : [],
    subjects: Array.isArray(rawData.subjects) ? rawData.subjects : [],
    lastUpdated: rawData.lastUpdated || new Date().toISOString(),
    enriched: true
  };
};

const aggregateMetrics = (dataPoints: DataPoint[]): any => {
  if (!dataPoints || dataPoints.length === 0) {
    return {
      avg: 0,
      max: 0,
      min: 0,
      count: 0,
      sum: 0,
      stdDev: 0
    };
  }

  const gpas = dataPoints.map(d => d.gpa).filter(gpa => gpa !== null && gpa !== undefined);
  if (gpas.length === 0) {
    return {
      avg: 0,
      max: 0,
      min: 0,
      count: 0,
      sum: 0,
      stdDev: 0
    };
  }

  const sum = gpas.reduce((a, b) => a + b, 0);
  const avg = sum / gpas.length;
  const max = Math.max(...gpas);
  const min = Math.min(...gpas);
  
  // Calculate standard deviation
  const squaredDiffs = gpas.map(gpa => Math.pow(gpa - avg, 2));
  const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / gpas.length;
  const stdDev = Math.sqrt(avgSquaredDiff);

  return {
    avg: Number(avg.toFixed(3)),
    max: Number(max.toFixed(3)),
    min: Number(min.toFixed(3)),
    count: gpas.length,
    sum: Number(sum.toFixed(3)),
    stdDev: Number(stdDev.toFixed(3))
  };
};

class AnalyticsService {
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private listeners: Map<string, Set<Function>> = new Map();

  /**
   * Get performance trends for a student
   */
  async getPerformanceTrends(
    studentId: string,
    options: TrendOptions = {}
  ): Promise<PerformanceTrend> {
    try {
      const cacheKey = `trends-${studentId}-${JSON.stringify(options)}`;
      const cached = this.getFromCache(cacheKey);
      
      if (cached) {
        return cached;
      }

      // Mock implementation - replace with actual API call
      console.log('Fetching performance trends for student:', studentId, options);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock response data
      const mockData: PerformanceTrend = {
        studentId,
        dataPoints: [
          { date: '2024-01-01T00:00:00Z', gpa: 3.2, percentile: 65 },
          { date: '2024-02-01T00:00:00Z', gpa: 3.4, percentile: 70 },
          { date: '2024-03-01T00:00:00Z', gpa: 3.6, percentile: 78 },
          { date: '2024-04-01T00:00:00Z', gpa: 3.5, percentile: 75 },
          { date: '2024-05-01T00:00:00Z', gpa: 3.7, percentile: 82 },
          { date: '2024-06-01T00:00:00Z', gpa: 3.8, percentile: 85 }
        ],
        currentGPA: 3.8,
        percentile: 85,
        subjects: [
          {
            id: 'math-101',
            name: 'Mathematics',
            category: 'core',
            credits: 4,
            currentGrade: 88,
            previousGrade: 85,
            classAverage: 76,
            trend: 3.5
          },
          {
            id: 'phys-101',
            name: 'Physics',
            category: 'core',
            credits: 4,
            currentGrade: 82,
            previousGrade: 78,
            classAverage: 72,
            trend: 4.0
          },
          {
            id: 'chem-101',
            name: 'Chemistry',
            category: 'core',
            credits: 3,
            currentGrade: 75,
            previousGrade: 80,
            classAverage: 71,
            trend: -5.0
          }
        ],
        lastUpdated: new Date().toISOString()
      };

      // Transform and validate data
      const transformedData = transformRawData(mockData);
      const validatedData = validateAnalyticsData(transformedData);

      // Enrich with additional metrics
      const finalData: PerformanceTrend = {
        ...validatedData,
        metrics: aggregateMetrics(validatedData.dataPoints),
        lastUpdated: new Date().toISOString()
      };

      // Cache the result
      this.setCache(cacheKey, finalData);

      return finalData;
    } catch (error) {
      console.error('Failed to fetch performance trends:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Update performance trend
   */
  async updatePerformanceTrend(
    studentId: string,
    data: Partial<PerformanceTrend>
  ): Promise<PerformanceTrend> {
    try {
      // Mock implementation - replace with actual API call
      console.log('Updating performance trend for student:', studentId, data);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 300));

      // Get current data and merge with updates
      const currentData = await this.getPerformanceTrends(studentId);
      const updatedData = { 
        ...currentData, 
        ...data, 
        lastUpdated: new Date().toISOString() 
      };

      // Invalidate cache
      this.invalidateCache(`trends-${studentId}`);

      // Notify listeners
      this.notifyListeners(`performance-${studentId}`, updatedData);

      return updatedData;
    } catch (error) {
      console.error('Failed to update performance trend:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Analyze weaknesses
   */
  async analyzeWeaknesses(config: {
    studentId: string;
    performanceData: PerformanceTrend;
    threshold: number;
    includeRecommendations: boolean;
    includePeerComparison: boolean;
    timeframe: string;
  }): Promise<WeaknessAnalysis> {
    try {
      // Mock implementation - replace with actual API call
      console.log('Analyzing weaknesses for student:', config.studentId);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 400));

      const weakAreas = config.performanceData.subjects?.filter((subject: any) => 
        subject.currentGrade < config.threshold
      ).map((subject: any, index: number) => ({
        id: `weak-${subject.id}-${index}`,
        name: subject.name,
        currentScore: subject.currentGrade,
        targetScore: Math.min(subject.currentGrade + 15, 85),
        classAverage: subject.classAverage,
        credits: subject.credits,
        impactOnGPA: this.calculateGPAImpact(subject),
        difficulty: this.calculateDifficulty(subject),
        severity: this.calculateSeverity(subject.currentGrade),
        priority: this.calculatePriority(subject),
        estimatedImprovementTime: this.estimateImprovementTime(subject),
        potentialImprovement: 15,
        subject: subject.name
      })) || [];

      const analysis: WeaknessAnalysis = {
        weakAreas,
        overallWeaknessScore: this.calculateOverallWeaknessScore(config.performanceData, config.threshold),
        recommendations: [
          'Focus on subjects below passing threshold',
          'Utilize available academic resources',
          'Create structured study schedule'
        ],
        improvementPotential: weakAreas.length > 0 ? 0.3 : 0,
        priorityOrder: weakAreas.map(area => area.id)
      };

      return analysis;
    } catch (error) {
      console.error('Failed to analyze weaknesses:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get subject performance data
   */
  async getSubjectPerformance(
    studentId: string,
    semesterId?: string
  ): Promise<SubjectData[]> {
    try {
      // Mock implementation - replace with actual API call
      console.log('Fetching subject performance for student:', studentId, semesterId);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 400));

      const trends = await this.getPerformanceTrends(studentId);
      
      // Enrich with additional data
      const enrichedData = await Promise.all(
        (trends.subjects || []).map(async (subject: any) => ({
          ...subject,
          trend: await this.calculateSubjectTrend(subject.id, studentId),
          weakTopics: await this.identifyWeakTopics(subject),
          recommendation: await this.generateSubjectRecommendation(subject)
        }))
      );

      return enrichedData;
    } catch (error) {
      console.error('Failed to fetch subject performance:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Track improvement progress
   */
  async trackImprovement(data: {
    studentId: string;
    areaId: string;
    progress: number;
    timestamp: string;
  }): Promise<void> {
    try {
      // Mock implementation - replace with actual API call
      console.log('Tracking improvement:', data);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 200));

      // Mock Firebase update
      console.log('Updating Firebase with improvement data');

    } catch (error) {
      console.error('Failed to track improvement:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Generate performance report
   */
  async generateReport(
    studentId: string,
    type: 'summary' | 'detailed' | 'comparative'
  ): Promise<string> {
    try {
      // Mock implementation - replace with actual API call
      console.log('Generating report for student:', studentId, type);
      
      // Simulate report generation delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock report URL
      return `https://reports.example.com/${studentId}/${type}-${Date.now()}.pdf`;
    } catch (error) {
      console.error('Failed to generate report:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Subscribe to performance updates
   */
  subscribeToUpdates(
    channel: string,
    callback: (data: any) => void
  ): () => void {
    if (!this.listeners.has(channel)) {
      this.listeners.set(channel, new Set());
    }

    this.listeners.get(channel)!.add(callback);

    // Mock Firebase subscription
    console.log('Subscribed to channel:', channel);

    return () => {
      this.listeners.get(channel)?.delete(callback);
      console.log('Unsubscribed from channel:', channel);
    };
  }

  // Private helper methods
  private calculateGPAImpact(subject: any): number {
    const grade = subject.currentGrade || 0;
    if (grade < 60) return 0.8;
    if (grade < 70) return 0.6;
    if (grade < 80) return 0.4;
    return 0.2;
  }

  private calculateDifficulty(subject: any): number {
    // Mock difficulty calculation
    const classAvg = subject.classAverage || 70;
    const studentGrade = subject.currentGrade || 0;
    const gap = classAvg - studentGrade;
    return Math.min(Math.max(gap / 30, 0.1), 0.9);
  }

  private calculateSeverity(score: number): 'low' | 'medium' | 'high' | 'critical' {
    if (score < 40) return 'critical';
    if (score < 55) return 'high';
    if (score < 70) return 'medium';
    return 'low';
  }

  private calculatePriority(subject: any): number {
    return (subject.credits || 0) * (100 - (subject.currentGrade || 0)) / 100;
  }

  private estimateImprovementTime(subject: any): string {
    const current = subject.currentGrade || 0;
    const target = Math.min(current + 15, 85);
    const gap = target - current;
    
    if (gap > 30) return '3-4 months';
    if (gap > 20) return '2-3 months';
    if (gap > 10) return '1-2 months';
    return '2-4 weeks';
  }

  private calculateOverallWeaknessScore(trends: PerformanceTrend, threshold: number): number {
    if (!trends.subjects || trends.subjects.length === 0) return 0;
    
    const weakSubjects = trends.subjects.filter((s: any) => s.currentGrade < threshold);
    const totalImpact = weakSubjects.reduce((sum: number, subject: any) => {
      return sum + (subject.credits || 0) * this.calculateGPAImpact(subject);
    }, 0);
    
    return Math.min(totalImpact / trends.subjects.length, 1);
  }

  private async calculateSubjectTrend(
    subjectId: string,
    studentId: string
  ): Promise<number> {
    // Mock trend calculation
    return Math.random() * 10 - 5; // Random trend between -5 and +5
  }

  private async identifyWeakTopics(subject: SubjectData): Promise<string[]> {
    // Mock weak topics identification
    const topics = ['Algebra', 'Calculus', 'Statistics', 'Geometry'];
    return topics.slice(0, Math.floor(Math.random() * 3) + 1);
  }

  private async generateSubjectRecommendation(subject: SubjectData): Promise<string> {
    // Mock recommendation generation
    const recommendations = [
      'Focus on completing all assignments on time',
      'Attend office hours for difficult topics',
      'Form a study group with classmates',
      'Review fundamental concepts regularly'
    ];
    return recommendations[Math.floor(Math.random() * recommendations.length)];
  }

  private getFromCache(key: string): any {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const isExpired = Date.now() - cached.timestamp > (CACHE_DURATION as any).MEDIUM || 1800000;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  private invalidateCache(pattern: string): void {
    Array.from(this.cache.keys())
      .filter(key => key.includes(pattern))
      .forEach(key => this.cache.delete(key));
  }

  private notifyListeners(channel: string, data: any): void {
    this.listeners.get(channel)?.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Listener callback error:', error);
      }
    });
  }

  private handleError(error: any): Error {
    if (error.response) {
      return new Error(error.response.data?.message || 'API request failed');
    }
    if (error.request) {
      return new Error('Network error - please check your connection');
    }
    return error instanceof Error ? error : new Error('An unexpected error occurred');
  }
}

export const analyticsService = new AnalyticsService();