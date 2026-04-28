// core/api/interceptors/auth.interceptor.ts
import type { AxiosRequestConfig } from 'axios';
import { auth } from '../../../services/firebase.config';

export const authInterceptor = {
  onFulfilled: async (config: AxiosRequestConfig): Promise<AxiosRequestConfig> => {
    try {
      config.headers = config.headers ?? {};

      // Generate a request ID
      (config.headers as Record<string, string>)['X-Request-Id'] = cryptoRandomId();

      // Accept-Language header
      const lang = typeof navigator !== 'undefined' ? navigator.language : 'en-US';
      (config.headers as Record<string, string>)['Accept-Language'] = lang;

      // ✅ FIX: Get fresh token from Firebase if user is logged in
      if (typeof window !== 'undefined' && auth.currentUser) {
        try {
          const freshToken = await auth.currentUser.getIdToken(false); // false = use cached if valid
          (config.headers as Record<string, string>)['Authorization'] = `Bearer ${freshToken}`;
          
          // Update storage with fresh token
          const userRole = localStorage.getItem('user_role') || sessionStorage.getItem('user_role');
          const storage = localStorage.getItem('auth_token') ? localStorage : sessionStorage;
          storage.setItem('auth_token', freshToken);
          
          return config;
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
          // Fall through to stored token
        }
      }

      // Fallback: Use stored token
      const storedToken = typeof window !== 'undefined'
        ? localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
        : null;

      if (storedToken && !(config.headers as Record<string, string>)['Authorization']) {
        (config.headers as Record<string, string>)['Authorization'] = `Bearer ${storedToken}`;
      }
    } catch (err) {
      console.error('Auth interceptor error:', err);
    }

    return config;
  },

  onRejected: (error: any) => {
    // ✅ Handle 401 errors by clearing auth state
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      sessionStorage.removeItem('auth_token');
      localStorage.removeItem('user_role');
      sessionStorage.removeItem('user_role');
      
      // Redirect to login if not already there
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
};

function cryptoRandomId(): string {
  try {
    if (typeof window !== 'undefined' && window.crypto?.getRandomValues) {
      const arr = new Uint8Array(16);
      window.crypto.getRandomValues(arr);
      return Array.from(arr, b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch {}

  // fallback
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}