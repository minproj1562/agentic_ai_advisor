// academic-advisor-frontend/src/services/student_analysis.service.ts
import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { auth } from '../services/firebase.config';

// Types
export interface StudentAnalysisRequest {
  skip?: number;
  limit?: number;
  department?: string;
  cgpaMin?: number;
  cgpaMax?: number;
  weaknessThreshold?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface StudentAnalysis {
  student_id: string;
  name: string;
  department: string;
  batch: number;
  current_semester: number;
  cgpa: number;
  sgpa_trend: number[];
  latest_sgpa: number;
  attendance: number;
  weaknesses: Weakness[];
  weakness_count: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  improvement_trend: 'improving' | 'stable' | 'declining';
  recommendations_pending: number;
  profile_completeness: number;
  last_updated: string;
  metadata: {
    total_credits: number;
    has_warnings: boolean;
    analysis_version: string;
  };
}

export interface Weakness {
  subject: string;
  topic?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  gap: number;
  priority: number;
}

export interface DetailedAnalysis extends StudentAnalysis {
  performance_data: {
    sgpa_trend: Array<{
      semester: number;
      sgpa: number;
      credits: number;
      year: string;
    }>;
    attendance_trend: Array<{
      semester: number;
      attendance: number;
      assignments: number;
    }>;
    grade_distribution: Record<string, number>;
    statistics: {
      mean_sgpa: number;
      std_sgpa: number;
      min_sgpa: number;
      max_sgpa: number;
      trend_direction: string;
    };
  };
  predictions: {
    next_semester_sgpa: number;
    expected_graduation_cgpa: number;
    failure_risk: string;
  };
  recommendations: string[];
}

export interface MLPredictionResponse {
  prediction_id: string;
  student_id: string;
  predictions: {
    next_semester_sgpa: number;
    expected_graduation_cgpa: number;
    failure_risk: string;
    confidence_interval?: [number, number];
    key_factors?: string[];
    improvement_recommendations?: string[];
  };
  model_metadata: {
    model_version: string;
    training_date: string;
    accuracy: number;
    features_used: string[];
  };
  timestamp: string;
}

export interface PredictionResult {
  predicted_sgpa: number;
  confidence: number;
  trend: string;
  risk_factors: Array<{
    factor: string;
    severity: string;
  }>;
  improvement_potential: {
    current: number;
    potential_max: number;
    time_to_achieve: string;
    focus_areas: string[];
  };
}

export interface RealtimeDashboard {
  faculty_id: string;
  students: StudentAnalysis[];
  summary: {
    total_students: number;
    at_risk_count: number;
    average_cgpa: number;
    department_performance: Record<string, number>;
    last_updated: string;
  };
  alerts: SystemAlert[];
}

export interface SystemAlert {
  id: string;
  type: 'risk_change' | 'performance_drop' | 'attendance_issue' | 'system';
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  student_id?: string;
  timestamp: string;
  acknowledged: boolean;
}

// Analytics Event Types
export interface AnalyticsEvent {
  event_name: string;
  event_data?: Record<string, any>;
  user_id?: string;
  timestamp: string;
  session_id?: string;
}

// Empty/Default data generators (no mock data - just empty structures)
const getEmptyStudentData = (studentId: string): DetailedAnalysis => {
  return {
    student_id: studentId,
    name: '',
    department: '',
    batch: 0,
    current_semester: 0,
    cgpa: 0,
    sgpa_trend: [],
    latest_sgpa: 0,
    attendance: 0,
    weaknesses: [],
    weakness_count: 0,
    risk_score: 0,
    risk_level: 'low',
    improvement_trend: 'stable',
    recommendations_pending: 0,
    profile_completeness: 0,
    last_updated: new Date().toISOString(),
    metadata: {
      total_credits: 0,
      has_warnings: false,
      analysis_version: '1.0'
    },
    performance_data: {
      sgpa_trend: [],
      attendance_trend: [],
      grade_distribution: {},
      statistics: {
        mean_sgpa: 0,
        std_sgpa: 0,
        min_sgpa: 0,
        max_sgpa: 0,
        trend_direction: 'stable'
      }
    },
    predictions: {
      next_semester_sgpa: 0,
      expected_graduation_cgpa: 0,
      failure_risk: 'unknown'
    },
    recommendations: []
  };
};

const getEmptyPredictionData = (studentId: string): MLPredictionResponse => {
  return {
    prediction_id: `pred_${studentId}_${Date.now()}`,
    student_id: studentId,
    predictions: {
      next_semester_sgpa: 0,
      expected_graduation_cgpa: 0,
      failure_risk: 'unknown',
      confidence_interval: [0, 0],
      key_factors: [],
      improvement_recommendations: []
    },
    model_metadata: {
      model_version: '1.0.0',
      training_date: new Date().toISOString(),
      accuracy: 0,
      features_used: []
    },
    timestamp: new Date().toISOString()
  };
};

// Helper function to convert performance data to AcademicRecord format
const convertToAcademicRecords = (performanceData: DetailedAnalysis['performance_data']): any[] => {
  if (!performanceData?.sgpa_trend) return [];

  return performanceData.sgpa_trend.map(semesterData => ({
    semester: semesterData.semester,
    sgpa: semesterData.sgpa,
    credits: semesterData.credits,
    year: semesterData.year,
    subjects: [],
    attendance: 0
  }));
};

// Helper function to adapt ML predictions to DetailedAnalysis format
const adaptMLPredictions = (mlPredictions: any): DetailedAnalysis['predictions'] => {
  if (!mlPredictions?.predictions) {
    return {
      next_semester_sgpa: 0,
      expected_graduation_cgpa: 0,
      failure_risk: 'unknown'
    };
  }

  const pred = mlPredictions.predictions;
  return {
    next_semester_sgpa: pred.next_semester_sgpa || 0,
    expected_graduation_cgpa: pred.expected_graduation_cgpa || 0,
    failure_risk: pred.failure_risk || 'unknown'
  };
};

// Simple EventEmitter implementation
class SimpleEventEmitter {
  private events: { [key: string]: Function[] } = {};

  on(event: string, listener: Function): void {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  emit(event: string, ...args: any[]): void {
    if (this.events[event]) {
      this.events[event].forEach(listener => {
        try {
          listener(...args);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  removeAllListeners(event?: string): void {
    if (event) {
      delete this.events[event];
    } else {
      this.events = {};
    }
  }
}

export class StudentAnalysisService extends SimpleEventEmitter {
  private api: AxiosInstance;
  private baseURL: string;
  private realtimeSubscriptions: Map<string, string>;
  private dataCache: Map<string, { data: any; timestamp: number }>;
  private analyticsQueue: AnalyticsEvent[] = [];
  private readonly CACHE_TTL = 2 * 60 * 1000; // 2 minutes
  private readonly ANALYTICS_BATCH_SIZE = 10;
  private readonly ANALYTICS_FLUSH_INTERVAL = 30000; // 30 seconds
  private analyticsFlushTimer: ReturnType<typeof setTimeout> | null = null;
  private sessionId: string;

  constructor() {
    super();
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    this.realtimeSubscriptions = new Map();
    this.dataCache = new Map();
    this.sessionId = this.generateSessionId();
    
    this.api = axios.create({
      baseURL: `${this.baseURL}/api/v1/student-analysis`,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.setupRealtimeListeners();
    this.startAnalyticsFlushTimer();
  }

  // ==================== ANALYTICS TRACKING METHODS ====================
  
  /**
   * Track an analytics event
   * @param eventName - Name of the event to track
   * @param eventData - Optional data associated with the event
   */
  public trackEvent(eventName: string, eventData?: Record<string, any>): void {
    try {
      const event: AnalyticsEvent = {
        event_name: eventName,
        event_data: eventData,
        user_id: auth.currentUser?.uid,
        timestamp: new Date().toISOString(),
        session_id: this.sessionId
      };

      // Add to queue
      this.analyticsQueue.push(event);

      // Log in development
      if (import.meta.env.DEV) {
        console.log(`[Analytics] ${eventName}:`, eventData);
      }

      // Flush if queue is full
      if (this.analyticsQueue.length >= this.ANALYTICS_BATCH_SIZE) {
        this.flushAnalytics();
      }

      // Emit event for any listeners
      this.emit('analyticsEvent', event);
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  /**
   * Track a page view event
   * @param pageName - Name of the page viewed
   * @param additionalData - Optional additional data
   */
  public trackPageView(pageName: string, additionalData?: Record<string, any>): void {
    this.trackEvent('page_view', {
      page: pageName,
      ...additionalData
    });
  }

  /**
   * Track a user action event
   * @param action - The action performed
   * @param category - Category of the action
   * @param label - Optional label for the action
   * @param value - Optional numeric value
   */
  public trackAction(action: string, category: string, label?: string, value?: number): void {
    this.trackEvent('user_action', {
      action,
      category,
      label,
      value
    });
  }

  /**
   * Track an error event
   * @param error - The error that occurred
   * @param context - Context where the error occurred
   */
  public trackError(error: Error | string, context?: string): void {
    this.trackEvent('error', {
      message: error instanceof Error ? error.message : error,
      stack: error instanceof Error ? error.stack : undefined,
      context
    });
  }

  /**
   * Track feature usage
   * @param featureName - Name of the feature used
   * @param details - Optional details about usage
   */
  public trackFeatureUsage(featureName: string, details?: Record<string, any>): void {
    this.trackEvent('feature_usage', {
      feature: featureName,
      ...details
    });
  }

  /**
   * Flush analytics events to the server
   */
  private async flushAnalytics(): Promise<void> {
    if (this.analyticsQueue.length === 0) return;

    const eventsToSend = [...this.analyticsQueue];
    this.analyticsQueue = [];

    try {
      await this.api.post('/analytics/batch', { events: eventsToSend });
    } catch (error) {
      // If failed, add events back to queue (at the front)
      this.analyticsQueue = [...eventsToSend, ...this.analyticsQueue];
      console.error('Failed to flush analytics:', error);
    }
  }

  /**
   * Start the analytics flush timer
   */
  private startAnalyticsFlushTimer(): void {
    if (this.analyticsFlushTimer) {
      clearInterval(this.analyticsFlushTimer);
    }

    this.analyticsFlushTimer = setInterval(() => {
      this.flushAnalytics();
    }, this.ANALYTICS_FLUSH_INTERVAL);
  }

  /**
   * Generate a unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // ==================== EXISTING METHODS ====================

  private setupInterceptors(): void {
    // Request interceptor
    this.api.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        try {
          // 1. Firebase user (faculty/admin)
          const currentUser = auth.currentUser;
          if (currentUser) {
            const token = await currentUser.getIdToken();
            if (token && config.headers) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          } else {
            // 2. Student JWT from localStorage
            const storedToken =
              localStorage.getItem('auth_token') ||
              sessionStorage.getItem('auth_token');
            if (storedToken && config.headers) {
              config.headers.Authorization = `Bearer ${storedToken}`;
            }
          }
        } catch (error) {
          console.error('Failed to get auth token:', error);
        }
        
        if (config.headers) {
          config.headers['X-Request-ID'] = this.generateRequestId();
        }
        
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        this.logApiCall(response.config, response);
        return response;
      },
      async (error) => {
        console.error('API Error:', error);
        this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private logApiCall(config: any, response: AxiosResponse): void {
    if (import.meta.env.DEV) {
      console.log('API Call:', {
        method: config.method,
        url: config.url,
        params: config.params,
        status: response.status,
      });
    }
  }

  private handleApiError(error: any): void {
    const errorMessage = error.response?.data?.detail || 'An unexpected error occurred';
    const errorCode = error.response?.status;
    
    window.dispatchEvent(new CustomEvent('api-error', {
      detail: { message: errorMessage, code: errorCode }
    }));
    
    this.trackError(errorMessage, 'api_call');
    this.logError(error);
  }

  private logError(error: any): void {
    if ((window as any).Sentry && import.meta.env.VITE_SENTRY_DSN) {
      (window as any).Sentry.captureException(error);
    }
  }

  private setupRealtimeListeners(): void {
    const realtimeService = realtimeSyncService as any;
    const mlService = mlIntegrationService as any;

    if (realtimeService.on) {
      realtimeService.on('dataUpdate', (update: any) => {
        this.handleRealtimeUpdate(update);
      });

      realtimeService.on('connectionStateChanged', (state: any) => {
        this.emit('realtimeConnectionState', state);
      });
    }

    if (mlService.on) {
      mlService.on('predictionUpdated', (data: any) => {
        this.emit('mlPredictionUpdated', data);
      });
    }
  }

  private handleRealtimeUpdate(update: any): void {
    const { path, data } = update;
    
    if (path.includes('students/')) {
      const studentId = path.split('/')[1];
      this.dataCache.set(`student_${studentId}`, {
        data,
        timestamp: Date.now()
      });
    }

    this.emit('realtimeData', { path, data });
  }

  public async getStudentsList(params: StudentAnalysisRequest): Promise<StudentAnalysis[]> {
    try {
      const response = await this.api.get<StudentAnalysis[]>('/list', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch students list:', error);
      return [];
    }
  }

  public async getStudentDetails(studentId: string): Promise<DetailedAnalysis> {
    const cacheKey = `student_${studentId}`;
    const cached = this.dataCache.get(cacheKey);

    if (cached && (Date.now() - cached.timestamp) < this.CACHE_TTL) {
      return cached.data;
    }

    try {
      const response = await this.api.get<DetailedAnalysis>(`/${studentId}`, {
        params: {
          include_predictions: true,
          include_recommendations: true,
          time_range: 'all',
        },
      });
      
      this.dataCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      });
      
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch details for student ${studentId}:`, error);
      
      // Return empty data structure instead of mock data
      const emptyData = getEmptyStudentData(studentId);
      
      this.dataCache.set(cacheKey, {
        data: emptyData,
        timestamp: Date.now()
      });
      
      return emptyData;
    }
  }

  public async getPredictions(studentId: string): Promise<MLPredictionResponse> {
    try {
      const response = await this.api.get(`/${studentId}/predictions`, {
        params: {
          include_confidence: true,
          time_horizon: 'next_semester',
        },
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch predictions for student ${studentId}:`, error);
      return getEmptyPredictionData(studentId);
    }
  }

  public async getRealtimeDashboard(facultyId: string): Promise<RealtimeDashboard> {
    try {
      const response: AxiosResponse<RealtimeDashboard> = await this.api.get('/dashboard/realtime', {
        params: { faculty_id: facultyId },
      });

      this.subscribeToFacultyUpdates(facultyId);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch realtime dashboard for faculty ${facultyId}:`, error);
      
      return {
        faculty_id: facultyId,
        students: [],
        summary: {
          total_students: 0,
          at_risk_count: 0,
          average_cgpa: 0,
          department_performance: {},
          last_updated: new Date().toISOString()
        },
        alerts: []
      };
    }
  }

  private subscribeToFacultyUpdates(facultyId: string): void {
    const subscriptionId = realtimeSyncService.subscribeToDepartmentUpdates(
      facultyId,
      (update: any) => {
        this.emit('facultyDashboardUpdate', { facultyId, update });
      }
    );

    this.realtimeSubscriptions.set(`faculty_${facultyId}`, subscriptionId);
  }

  public async getStudentWithRealtime(studentId: string): Promise<DetailedAnalysis> {
    const cacheKey = `student_${studentId}`;
    const cached = this.dataCache.get(cacheKey);

    if (cached && (Date.now() - cached.timestamp) < this.CACHE_TTL) {
      return cached.data;
    }

    try {
      const [studentData, mlPredictions] = await Promise.all([
        this.getStudentDetails(studentId),
        mlIntegrationService.getPredictions(studentId)
      ]);

      const adaptedPredictions = adaptMLPredictions(mlPredictions);

      const enhancedData: DetailedAnalysis = {
        ...studentData,
        predictions: adaptedPredictions
      };

      this.dataCache.set(cacheKey, {
        data: enhancedData,
        timestamp: Date.now()
      });

      this.subscribeToStudentUpdates(studentId);

      return enhancedData;
    } catch (error) {
      console.error(`Failed to get enhanced student data for ${studentId}:`, error);
      
      const emptyData = getEmptyStudentData(studentId);
      
      this.dataCache.set(cacheKey, {
        data: emptyData,
        timestamp: Date.now()
      });
      
      return emptyData;
    }
  }

  private subscribeToStudentUpdates(studentId: string): void {
    if (!this.realtimeSubscriptions.has(`student_${studentId}`)) {
      const subscriptionId = realtimeSyncService.subscribeToStudentUpdates(
        studentId,
        (update: any) => {
          this.handleStudentRealtimeUpdate(studentId, update);
        }
      );

      this.realtimeSubscriptions.set(`student_${studentId}`, subscriptionId);
    }
  }

  private handleStudentRealtimeUpdate(studentId: string, update: any): void {
    this.dataCache.set(`student_${studentId}`, {
      data: update.data,
      timestamp: Date.now()
    });

    this.emit('studentDataUpdated', { studentId, data: update.data });
  }

  public async triggerAdvancedAnalysis(studentId: string): Promise<{ analysis_id: string; status: string }> {
    try {
      const studentData = await this.getStudentDetails(studentId);
      const academicRecords = convertToAcademicRecords(studentData.performance_data);

      const [weaknessAnalysis, prediction] = await Promise.all([
        mlIntegrationService.analyzeWeaknesses(studentId, academicRecords),
        mlIntegrationService.getPredictions(studentId, true)
      ]);

      const response = await this.api.post(`/${studentId}/advanced-analysis`, {
        weakness_analysis: weaknessAnalysis,
        prediction: prediction,
        timestamp: new Date().toISOString()
      });

      this.emit('advancedAnalysisComplete', { studentId, result: response.data });
      this.trackEvent('advanced_analysis_triggered', { studentId });
      return response.data;
    } catch (error) {
      console.error(`Failed to trigger advanced analysis for ${studentId}:`, error);
      
      return {
        analysis_id: `analysis_${studentId}_${Date.now()}`,
        status: 'failed'
      };
    }
  }

  public async exportToExcel(students: StudentAnalysis[]): Promise<void> {
    try {
      const response = await this.api.post('/export/excel', { students }, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `students_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      this.trackEvent('export_excel', { count: students.length });
    } catch (error) {
      console.error('Failed to export to Excel:', error);
      throw error;
    }
  }

  public async bulkAnalyze(studentIds: string[]): Promise<any> {
    try {
      const response = await this.api.post('/bulk-analyze', { student_ids: studentIds });
      this.trackEvent('bulk_analyze', { count: studentIds.length });
      return response.data;
    } catch (error) {
      console.error('Failed to bulk analyze:', error);
      throw error;
    }
  }

  public async sendBulkEmail(studentIds: string[]): Promise<any> {
    try {
      const response = await this.api.post('/bulk-email', { student_ids: studentIds });
      this.trackEvent('bulk_email_sent', { count: studentIds.length });
      return response.data;
    } catch (error) {
      console.error('Failed to send bulk email:', error);
      throw error;
    }
  }

  public async generateBulkReport(studentIds: string[]): Promise<any> {
    try {
      const response = await this.api.post('/bulk-report', { student_ids: studentIds });
      this.trackEvent('bulk_report_generated', { count: studentIds.length });
      return response.data;
    } catch (error) {
      console.error('Failed to generate bulk report:', error);
      throw error;
    }
  }

  public getRealtimeSubscriptions(): string[] {
    return Array.from(this.realtimeSubscriptions.keys());
  }

  public unsubscribeFromStudent(studentId: string): void {
    const subscriptionId = this.realtimeSubscriptions.get(`student_${studentId}`);
    if (subscriptionId) {
      realtimeSyncService.unsubscribe(subscriptionId);
      this.realtimeSubscriptions.delete(`student_${studentId}`);
    }
  }

  public clearCache(studentId?: string): void {
    if (studentId) {
      this.dataCache.delete(`student_${studentId}`);
    } else {
      this.dataCache.clear();
    }
    const mlService = mlIntegrationService as any;
    if (mlService.clearCache) {
      mlService.clearCache(studentId);
    }
  }

  public getServiceStats(): any {
    const mlService = mlIntegrationService as any;
    const realtimeService = realtimeSyncService as any;
    
    return {
      cacheSize: this.dataCache.size,
      realtimeSubscriptions: this.realtimeSubscriptions.size,
      analyticsQueueSize: this.analyticsQueue.length,
      sessionId: this.sessionId,
      mlServiceStats: mlService.getCacheStats ? mlService.getCacheStats() : {},
      realtimeStats: realtimeService.getSubscriptionStats ? realtimeService.getSubscriptionStats() : {}
    };
  }

  public destroy(): void {
    // Flush remaining analytics
    this.flushAnalytics();
    
    // Clear the flush timer
    if (this.analyticsFlushTimer) {
      clearInterval(this.analyticsFlushTimer);
      this.analyticsFlushTimer = null;
    }

    // Cleanup all real-time subscriptions
    this.realtimeSubscriptions.forEach((subscriptionId) => {
      realtimeSyncService.unsubscribe(subscriptionId);
    });
    this.realtimeSubscriptions.clear();
    
    // Remove all event listeners
    this.removeAllListeners();
  }

  public async triggerWeaknessAnalysis(
    studentId: string,
    forceRefresh: boolean = false
  ): Promise<{ status: string; job_id?: string }> {
    try {
      const response = await this.api.post(`/${studentId}/weakness-analysis`, null, {
        params: { force_refresh: forceRefresh },
      });
      this.trackEvent('weakness_analysis_triggered', { studentId, forceRefresh });
      return response.data;
    } catch (error) {
      console.error(`Failed to trigger weakness analysis for ${studentId}:`, error);
      
      return {
        status: 'failed',
        job_id: undefined
      };
    }
  }

  public async getAnalysisStatus(studentId: string): Promise<{
    status: string;
    progress?: number;
    result?: any;
  }> {
    try {
      const response = await this.api.get(`/${studentId}/analysis-status`);
      return response.data;
    } catch (error) {
      console.error(`Failed to get analysis status for ${studentId}:`, error);
      
      return {
        status: 'unknown',
        progress: 0
      };
    }
  }
}

// Service stubs for imported services
const mlIntegrationService = {
  getPredictions: (studentId: string, forceRefresh?: boolean) => Promise.resolve(getEmptyPredictionData(studentId)),
  analyzeWeaknesses: (studentId: string, records: any) => Promise.resolve({ weaknesses: [] }),
};

const realtimeSyncService = {
  subscribeToDepartmentUpdates: (facultyId: string, callback: Function) => `sub_${facultyId}`,
  subscribeToStudentUpdates: (studentId: string, callback: Function) => `sub_${studentId}`,
  unsubscribe: (subscriptionId: string) => { /* unsubscribe logic */ },
};

// Singleton instance
let serviceInstance: StudentAnalysisService | null = null;

export const getStudentAnalysisService = (): StudentAnalysisService => {
  if (!serviceInstance) {
    serviceInstance = new StudentAnalysisService();
  }
  return serviceInstance;
};

// Create a default instance for direct import usage
export const studentAnalysisService = getStudentAnalysisService();

export default StudentAnalysisService;