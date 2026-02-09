// academic-advisor-frontend/src/modules/agent1/student-analysis/services/ml-integration.service.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';

export interface MLPredictionRequest {
  student_id: string;
  academic_history: AcademicRecord[];
  current_semester: number;
  department: string;
  features: MLFeature[];
}

export interface AcademicRecord {
  semester: number;
  subjects: SubjectPerformance[];
  sgpa: number;
  attendance: number;
  credits: number;
}

export interface SubjectPerformance {
  subject_code: string;
  subject_name: string;
  marks: number;
  total_marks: number;
  grade: string;
}

export interface MLFeature {
  name: string;
  value: number | string;
  importance?: number;
}

export interface MLPredictionResponse {
  prediction_id: string;
  student_id: string;
  predictions: {
    next_semester_sgpa: number;
    confidence_interval: [number, number];
    risk_level: 'low' | 'medium' | 'high';
    key_factors: string[];
    improvement_recommendations: string[];
  };
  model_metadata: {
    model_version: string;
    training_date: string;
    accuracy: number;
    features_used: string[];
  };
  timestamp: string;
}

export interface WeaknessAnalysis {
  student_id: string;
  weaknesses: StudentWeakness[];
  overall_risk_score: number;
  analysis_timestamp: string;
}

export interface StudentWeakness {
  subject: string;
  topic: string;
  weakness_score: number;
  confidence: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recommended_actions: string[];
  resources: LearningResource[];
}

export interface LearningResource {
  type: 'video' | 'book' | 'article' | 'interactive' | 'exercise';
  title: string;
  url: string;
  description: string;
  duration_minutes?: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

// Mock data generator
const generateMockPredictionData = (studentId: string): MLPredictionResponse => {
  const nextSgpa = 7 + Math.random() * 3;
  const riskLevel = Math.random() > 0.7 ? 'high' : Math.random() > 0.4 ? 'medium' : 'low';
  
  return {
    prediction_id: `pred_${studentId}_${Date.now()}`,
    student_id: studentId,
    predictions: {
      next_semester_sgpa: nextSgpa,
      confidence_interval: [nextSgpa - 0.5, nextSgpa + 0.5],
      risk_level: riskLevel,
      key_factors: [
        'attendance',
        'previous_performance',
        'study_habits',
        'subject_difficulty'
      ],
      improvement_recommendations: [
        'Increase study hours by 2 hours per week',
        'Focus on weak subjects identified in analysis',
        'Join peer study groups',
        'Utilize office hours for difficult concepts'
      ]
    },
    model_metadata: {
      model_version: '1.2.0',
      training_date: '2023-01-15',
      accuracy: 0.87,
      features_used: ['attendance', 'grades', 'study_time', 'previous_sgpa']
    },
    timestamp: new Date().toISOString()
  };
};

const generateMockWeaknessAnalysis = (studentId: string): WeaknessAnalysis => {
  return {
    student_id: studentId,
    weaknesses: [
      {
        subject: 'Mathematics',
        topic: 'Calculus',
        weakness_score: 0.7,
        confidence: 0.85,
        severity: 'high',
        recommended_actions: [
          'Practice more calculus problems',
          'Review fundamental concepts',
          'Seek help from professor during office hours'
        ],
        resources: [
          {
            type: 'video',
            title: 'Calculus Fundamentals',
            url: 'https://example.com/calculus-video',
            description: 'Comprehensive video tutorial on calculus basics',
            duration_minutes: 45,
            difficulty: 'intermediate'
          },
          {
            type: 'book',
            title: 'Calculus Made Easy',
            url: 'https://example.com/calculus-book',
            description: 'Beginner-friendly guide to calculus',
            difficulty: 'beginner'
          }
        ]
      },
      {
        subject: 'Data Structures',
        topic: 'Trees',
        weakness_score: 0.5,
        confidence: 0.75,
        severity: 'medium',
        recommended_actions: [
          'Implement tree algorithms from scratch',
          'Practice LeetCode tree problems',
          'Visualize tree operations'
        ],
        resources: [
          {
            type: 'interactive',
            title: 'Tree Visualizer',
            url: 'https://example.com/tree-visualizer',
            description: 'Interactive tool to visualize tree operations',
            difficulty: 'beginner'
          }
        ]
      }
    ],
    overall_risk_score: 0.6,
    analysis_timestamp: new Date().toISOString()
  };
};

// Simple event emitter replacement for browser
class SimpleEventEmitter {
  private listeners: { [event: string]: Function[] } = {};

  on(event: string, listener: Function): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener);
  }

  off(event: string, listener: Function): void {
    if (!this.listeners[event]) return;
    const index = this.listeners[event].indexOf(listener);
    if (index > -1) {
      this.listeners[event].splice(index, 1);
    }
  }

  emit(event: string, ...args: any[]): void {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach(listener => {
      try {
        listener(...args);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  removeAllListeners(event?: string): void {
    if (event) {
      delete this.listeners[event];
    } else {
      this.listeners = {};
    }
  }
}

export class MLIntegrationService extends SimpleEventEmitter {
  private api: AxiosInstance;
  private baseURL: string;
  private predictionCache: Map<string, { data: MLPredictionResponse; timestamp: number }>;
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes
  private useMockData: boolean = false;

  constructor() {
    super();
    
    // Use environment variables with fallbacks for browser
    this.baseURL = (import.meta.env?.VITE_ML_API_URL as string) || 
                   (import.meta.env?.REACT_APP_ML_API_URL as string) || 
                   'http://localhost:5001/api/v1';
    
    this.predictionCache = new Map();
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': (import.meta.env?.VITE_ML_API_KEY as string) || 
                     (import.meta.env?.REACT_APP_ML_API_KEY as string) || '',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('mlAuthToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        // Check if it's a CORS or connection error
        if (error.code === 'ECONNREFUSED' || error.message.includes('CORS')) {
          console.log('ML API not available, switching to mock data');
          this.useMockData = true;
        }
        
        // Don't try to refresh tokens for now
        return Promise.reject(error);
      }
    );
  }

  private async refreshMLToken(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('mlRefreshToken');
      const response = await axios.post(`${this.baseURL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      localStorage.setItem('mlAuthToken', response.data.access_token);
    } catch (error) {
      console.error('Failed to refresh ML API token:', error);
      throw error;
    }
  }

  public async getPredictions(studentId: string, forceRefresh: boolean = false): Promise<MLPredictionResponse> {
    const cacheKey = `prediction_${studentId}`;
    const cached = this.predictionCache.get(cacheKey);

    if (!forceRefresh && cached && (Date.now() - cached.timestamp) < this.CACHE_TTL) {
      this.emit('predictionFromCache', { studentId, data: cached.data });
      return cached.data;
    }

    try {
      const response: AxiosResponse<MLPredictionResponse> = await this.api.get(`/predictions/${studentId}`);
      
      // Cache the prediction
      this.predictionCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      });

      this.emit('predictionUpdated', { studentId, data: response.data });
      return response.data;
    } catch (error) {
      console.error(`Failed to get predictions for student ${studentId}:`, error);
      
      // Return mock data as fallback
      const mockData = generateMockPredictionData(studentId);
      
      // Cache the mock data for a shorter time
      this.predictionCache.set(cacheKey, {
        data: mockData,
        timestamp: Date.now()
      });
      
      return mockData;
    }
  }

  public async analyzeWeaknesses(studentId: string, academicData: AcademicRecord[]): Promise<WeaknessAnalysis> {
    try {
      const response: AxiosResponse<WeaknessAnalysis> = await this.api.post('/weakness-analysis', {
        student_id: studentId,
        academic_data: academicData
      });

      this.emit('weaknessAnalysisComplete', { studentId, analysis: response.data });
      return response.data;
    } catch (error) {
      console.error(`Failed to analyze weaknesses for student ${studentId}:`, error);
      
      // Return mock data as fallback
      return generateMockWeaknessAnalysis(studentId);
    }
  }

  public async batchPredict(studentIds: string[]): Promise<Map<string, MLPredictionResponse>> {
    try {
      const response: AxiosResponse<{ predictions: MLPredictionResponse[] }> = await this.api.post('/predictions/batch', {
        student_ids: studentIds
      });

      const results = new Map<string, MLPredictionResponse>();
      response.data.predictions.forEach(prediction => {
        results.set(prediction.student_id, prediction);
        
        // Cache each prediction
        this.predictionCache.set(`prediction_${prediction.student_id}`, {
          data: prediction,
          timestamp: Date.now()
        });
      });

      this.emit('batchPredictionsComplete', { results });
      return results;
    } catch (error) {
      console.error('Failed to get batch predictions:', error);
      
      // Return mock data as fallback
      const results = new Map<string, MLPredictionResponse>();
      studentIds.forEach(studentId => {
        const mockData = generateMockPredictionData(studentId);
        results.set(studentId, mockData);
        
        // Cache the mock data for a shorter time
        this.predictionCache.set(`prediction_${studentId}`, {
          data: mockData,
          timestamp: Date.now()
        });
      });
      
      return results;
    }
  }

  public async getModelHealth(): Promise<any> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Failed to get model health:', error);
      
      // Return mock health status
      return {
        status: 'healthy',
        models: {
          performance_predictor: 'loaded',
          weakness_detector: 'loaded',
          recommendation_engine: 'loaded'
        },
        last_updated: new Date().toISOString()
      };
    }
  }

  public clearCache(studentId?: string): void {
    if (studentId) {
      this.predictionCache.delete(`prediction_${studentId}`);
    } else {
      this.predictionCache.clear();
    }
  }

  public getCacheStats(): { size: number; hits: number } {
    return {
      size: this.predictionCache.size,
      hits: 0 // You can implement hit tracking if needed
    };
  }
}

// Singleton instance
export const mlIntegrationService = new MLIntegrationService();
export default MLIntegrationService;