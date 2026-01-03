// src/services/engineering.service.ts
import axios from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000';

// Axios instance with auth
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests (simplified approach)
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await auth.currentUser?.getIdToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (err) {
      console.warn('Failed to get auth token:', err);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Define your interfaces (you need to add these based on your existing types)
export interface StudentPerformanceMetrics {
  // Add your interface properties here
  [key: string]: any;
}

export interface ElectiveRecommendation {
  // Add your interface properties here
  [key: string]: any;
}

export interface WeaknessAnalysis {
  // Add your interface properties here
  [key: string]: any;
}

export interface StudyResource {
  // Add your interface properties here
  [key: string]: any;
}

// API Functions
export const engineeringService = {
  async getPerformanceMetrics(userId: string): Promise<StudentPerformanceMetrics> {
    const response = await apiClient.get(`/students/${userId}/performance`);
    return response.data;
  },

  async getElectiveRecommendations(userId: string): Promise<ElectiveRecommendation[]> {
    const response = await apiClient.get(`/students/${userId}/electives/recommendations`);
    return response.data;
  },

  async getWeaknessAnalysis(userId: string): Promise<WeaknessAnalysis[]> {
    const response = await apiClient.get(`/students/${userId}/weaknesses`);
    return response.data;
  },

  async getStudyResources(userId: string, filters?: { type?: string; difficulty?: string; topic?: string; }): Promise<StudyResource[]> {
    const response = await apiClient.get(`/students/${userId}/resources`, { params: filters });
    return response.data;
  },

  async getBookmarkedResources(userId: string): Promise<StudyResource[]> {
    const response = await apiClient.get(`/students/${userId}/resources/bookmarked`);
    return response.data;
  },

  async toggleBookmark(userId: string, resourceId: string): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/students/${userId}/resources/${resourceId}/bookmark`);
    return response.data;
  },

  async updateResourceProgress(userId: string, resourceId: string, progress: number): Promise<{ success: boolean }> {
    const response = await apiClient.put(`/students/${userId}/resources/${resourceId}/progress`, { progress });
    return response.data;
  },

  async getStudyPlan(userId: string, topicId: string): Promise<any> {
    const response = await apiClient.post(`/students/${userId}/study-plan`, { topicId });
    return response.data;
  },

  async trackActivity(userId: string, activityData: {
    type: 'resource_viewed' | 'topic_completed' | 'quiz_taken';
    resourceId?: string;
    topicId?: string;
    score?: number;
    timeSpent?: number;
  }): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/students/${userId}/activity`, activityData);
    return response.data;
  }
};