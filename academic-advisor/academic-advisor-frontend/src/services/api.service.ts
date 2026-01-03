// src/services/api.service.ts
import axios from 'axios';
import { auth } from './firebase.config'; // Import auth instance

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with better error handling
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      // Get current user from Firebase auth
      const user = auth.currentUser;
      if (user) {
        const token = await user.getIdToken();
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.warn('No authenticated user found or token error:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('Backend server is not running');
      // You can show a user-friendly message or switch to demo mode
    }
    return Promise.reject(error);
  }
);

// Helper function to check if backend is running
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:8000/health');
    return response.ok;
  } catch (error) {
    console.warn('Backend server not running');
    return false;
  }
};

export default apiClient;