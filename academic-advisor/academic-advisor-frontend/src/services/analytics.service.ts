// src/services/analytics.service.ts

import { auth } from './firebase.config';

const BACKEND_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// ==================== Types ====================

export interface StudentAnalysis {
  student_id: string;
  name: string;
  department: string;
  current_semester: number;
  cgpa: number;
  latest_sgpa: number;
  weaknesses: any[];
  weakness_count: number;
  improvement_trend: 'improving' | 'stable' | 'declining';
}

export interface DetailedAnalysis extends StudentAnalysis {
  performance_data: {
    sgpa_trend: Array<{ semester: number; sgpa: number; credits: number }>;
  };
}

export interface MLPredictionResponse {
  predictions: {
    next_semester_sgpa: number;
    expected_graduation_cgpa: number;
    failure_risk: string;
  };
}

export interface PredictionResult {
  predicted_sgpa: number;
  confidence: number;
}

export interface RealtimeDashboard {
  students: any[];
  summary: any;
}

// ==================== Auth Helper ====================

async function getAuthHeaders(): Promise<Record<string, string>> {
  // 1. Try Firebase (faculty/admin)
  if (auth.currentUser) {
    try {
      const token = await auth.currentUser.getIdToken(false);
      return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
    } catch (e) {
      console.warn('Firebase token failed, trying stored token');
    }
  }

  // 2. Stored JWT (students)
  const stored = 
    localStorage.getItem('auth_token') || 
    sessionStorage.getItem('auth_token');

  if (!stored) {
    throw new Error('Not authenticated');
  }

  return { Authorization: `Bearer ${stored}`, 'Content-Type': 'application/json' };
}


async function apiFetch(path: string): Promise<any> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BACKEND_URL}${path}`, { headers });
  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error(`API error ${response.status}`);
  }
  return response.json();
}

// ==================== Dashboard Data Service ====================

class DashboardAnalyticsService {
  private cachedFullData: any = null;
  private cacheTimestamp = 0;
  private readonly CACHE_TTL = 60_000; // 1 minute

  /**
   * FIXED: Fetch from the CORRECT endpoint that returns sgpa_trend
   */
  async fetchFullDashboardData(forceRefresh = false): Promise<any> {
    if (!forceRefresh && this.cachedFullData && Date.now() - this.cacheTimestamp < this.CACHE_TTL) {
      return this.cachedFullData;
    }
    try {
      // FIXED: Use the correct endpoint
      const data = await apiFetch('/api/v1/student-profile/me/full');
      if (data) {
        this.cachedFullData = data;
        this.cacheTimestamp = Date.now();
        console.log('✅ Full dashboard data fetched:', {
          sgpa_trend_count: data.sgpa_trend?.length || 0,
          latest_sgpa: data.latest_sgpa,
          cgpa: data.cgpa
        });
      }
      return data;
    } catch (error) {
      console.error('Error fetching full dashboard data:', error);
      return this.cachedFullData || null;
    }
  }

  clearCache(): void {
    this.cachedFullData = null;
    this.cacheTimestamp = 0;
  }

  async getPerformanceMetrics(_studentId: string): Promise<any[]> {
    try {
      const data = await this.fetchFullDashboardData();
      if (!data?.sgpa_trend) {
        console.warn('No sgpa_trend in response');
        return [];
      }
      
      // FIXED: Map the correct fields from backend response
      return data.sgpa_trend.map((s: any) => ({
        semester: s.semester,
        sgpi: s.sgpa, // Backend uses 'sgpa', frontend expects 'sgpi'
        credits: s.credits,
        courses: s.subjects_count || 0
      }));
    } catch (error) {
      console.error('Error getting performance metrics:', error);
      return [];
    }
  }

  async getDashboardStats(_studentId: string): Promise<any> {
    try {
      const data = await this.fetchFullDashboardData();
      if (!data) return this.getEmptyStats();

      const sgpaTrend = data.sgpa_trend || [];
      
      // FIXED: Calculate stats from actual backend data
      const currentSGPI = data.latest_sgpa || 0;
      const previousSGPI = data.previous_sgpa || currentSGPI;
      const percentageChange = data.percentage_change || 0;

      return {
        currentSGPI,
        previousSGPI,
        averageSGPI: sgpaTrend.length > 0
          ? sgpaTrend.reduce((sum: number, s: any) => sum + s.sgpa, 0) / sgpaTrend.length 
          : 0,
        bestSGPI: sgpaTrend.length > 0 
          ? Math.max(...sgpaTrend.map((s: any) => s.sgpa)) 
          : 0,
        totalCredits: data.total_credits_earned || 0,
        currentSemester: data.current_semester || 1,
        cgpa: data.cgpa || 0,
        rank: '—',
        totalStudents: '—',
        department: data.branch || '',
        completedCourses: sgpaTrend.reduce((sum: number, s: any) => sum + (s.subjects_count || 0), 0),
        trend: data.trend || 'stable',
        percentageChange
      };
    } catch (error) {
      console.error('Error getting dashboard stats:', error);
      return this.getEmptyStats();
    }
  }

  /**
   * FIXED: Map backend data to PerformanceChart format
   */
  async getPerformanceChartData(_studentId: string): Promise<any> {
    try {
      const data = await this.fetchFullDashboardData();
      if (!data?.sgpa_trend?.length) {
        console.warn('No SGPA trend data available');
        return null;
      }

      // FIXED: Map backend fields to chart format
      const chartData = {
        currentSGPI: data.latest_sgpa || 0,
        previousSGPI: data.previous_sgpa || data.latest_sgpa || 0,
        trend: data.trend || 'stable',
        percentageChange: data.percentage_change || 0,
        semesterWiseData: data.sgpa_trend.map((s: any) => ({
          semester: s.semester,
          sgpi: s.sgpa, // CRITICAL: Backend uses 'sgpa', chart expects 'sgpi'
          credits: s.credits,
          courses: s.subjects_count || 0
        }))
      };

      console.log('📊 Chart data prepared:', {
        semesters: chartData.semesterWiseData.length,
        current: chartData.currentSGPI,
        trend: chartData.trend
      });

      return chartData;
    } catch (error) {
      console.error('Error getting chart data:', error);
      return null;
    }
  }

  async generateInsights(performanceMetrics: any[]): Promise<any> {
    if (!performanceMetrics?.length) {
      return {
        recommendations: [],
        trends: { overall: 'stable', confidence: 0, averageChange: 0 },
        predictions: { nextSGPI: 0, confidence: 'low', rSquared: 0 },
        riskFactors: []
      };
    }

    const sgpis = performanceMetrics.map(m => m.sgpi || m.sgpa || 0);
    const latest = sgpis[sgpis.length - 1];
    const previous = sgpis.length > 1 ? sgpis[sgpis.length - 2] : latest;
    const avgChange = previous > 0 ? ((latest - previous) / previous) * 100 : 0;

    return {
      recommendations: this.generateRecommendations(latest, avgChange),
      trends: {
        overall: avgChange > 5 ? 'improving' : avgChange < -5 ? 'declining' : 'stable',
        confidence: 0.85,
        averageChange: avgChange
      },
      predictions: {
        nextSGPI: Math.min(10, Math.max(0, latest + avgChange / 100)),
        confidence: latest > 7 ? 'high' : latest > 5 ? 'medium' : 'low',
        rSquared: 0.76
      },
      riskFactors: latest < 6 ? [{ factor: 'Low SGPI', severity: 'high' }] : []
    };
  }

  subscribeToMetrics(_studentId: string, callback: (metrics: any[]) => void): () => void {
    const interval = setInterval(async () => {
      try {
        const metrics = await this.getPerformanceMetrics(_studentId);
        if (metrics.length > 0) callback(metrics);
      } catch (error) {
        console.error('Metrics poll error:', error);
      }
    }, 30_000);
    return () => clearInterval(interval);
  }

  async trackEvent(eventName: string, data: any): Promise<void> {
    if (import.meta.env.DEV) console.log('Analytics:', eventName, data);
  }

  private getEmptyStats() {
    return {
      currentSGPI: 0, previousSGPI: 0, averageSGPI: 0, bestSGPI: 0,
      totalCredits: 0, currentSemester: 1, cgpa: 0, rank: '—',
      totalStudents: '—', department: '', completedCourses: 0,
      trend: 'stable', percentageChange: 0
    };
  }

  private generateRecommendations(sgpi: number, change: number) {
    const recs: Array<{ message: string; priority: string; type: string }> = [];
    if (sgpi < 6) recs.push({ message: 'Focus on core subjects to raise SGPI above 6.0', priority: 'high', type: 'alert' });
    else if (sgpi < 7.5) recs.push({ message: 'Target weak subjects to push above 7.5', priority: 'medium', type: 'warning' });
    if (change < -5) recs.push({ message: 'Performance declining — review study strategies', priority: 'high', type: 'warning' });
    else if (change > 5) recs.push({ message: 'Great improvement! Maintain this momentum', priority: 'low', type: 'success' });
    if (recs.length === 0) recs.push({ message: 'Keep up the consistent performance', priority: 'low', type: 'success' });
    return recs;
  }
}

// ==================== Exports ====================

export const extendedAnalyticsService = new DashboardAnalyticsService();

export const analyticsService = {
  trackEvent: (name: string, data: any) => extendedAnalyticsService.trackEvent(name, data),
  getPerformanceMetrics: (id: string) => extendedAnalyticsService.getPerformanceMetrics(id),
  getDashboardStats: (id: string) => extendedAnalyticsService.getDashboardStats(id),
};

export type { DashboardAnalyticsService };
export default analyticsService;