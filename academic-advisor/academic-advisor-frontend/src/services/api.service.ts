// src/services/api.service.ts
import axios from 'axios';
import { auth } from './firebase.config';

const API_BASE_URL =
  import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api/v1`
    : 'http://localhost:8000/api/v1';

// ── Public endpoints that never need a token ──────────────────────────────────
const PUBLIC_ENDPOINTS = [
  '/auth/student/login',
  '/auth/faculty/login',
  '/auth/admin/login',
  '/health',
  '/faculty/approved-emails',
];

const isPublicEndpoint = (url: string): boolean =>
  PUBLIC_ENDPOINTS.some((pub) => url.includes(pub));

// ─────────────────────────────────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor ───────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  async (config) => {
    const url = config.url || '';

    // ✅ Skip token for public/auth endpoints
    if (isPublicEndpoint(url)) {
      console.log(`🔓 Public endpoint — no token needed: ${url}`);
      return config;
    }

    try {
      // 1. Firebase user (faculty/admin)
      const firebaseUser = auth.currentUser;
      if (firebaseUser) {
        const token = await firebaseUser.getIdToken(false);
        config.headers.Authorization = `Bearer ${token}`;
        return config;
      }

      // 2. Stored JWT (students)
      const stored =
        localStorage.getItem('auth_token') ||
        sessionStorage.getItem('auth_token');

      if (stored) {
        config.headers.Authorization = `Bearer ${stored}`;
        return config;
      }

      // 3. No token — warn but don't block the request
      console.warn(`⚠️ No token available for request: ${url}`);
    } catch (error) {
      console.warn('Auth token error in interceptor:', error);
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor ──────────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      // Don't clear tokens for verify-token (handled by AuthContext)
      // or public endpoints
      if (!isPublicEndpoint(url) && !url.includes('verify-token')) {
        console.error('401 — clearing stale token');
        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_token');
      }
    }
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
      console.error('❌ Backend unreachable or timeout:', error.config?.url);
    }
    return Promise.reject(error);
  },
);

export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const r = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return r.ok;
  } catch {
    return false;
  }
};

export default apiClient;