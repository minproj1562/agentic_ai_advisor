// core/api/interceptors/auth.interceptor.ts
import type { AxiosRequestConfig } from 'axios';

export const authInterceptor = {
  onFulfilled: (config: AxiosRequestConfig): AxiosRequestConfig => {
    try {
      config.headers = config.headers ?? {};

      // Generate a request ID
      (config.headers as Record<string, string>)['X-Request-Id'] = cryptoRandomId();

      // Accept-Language header
      const lang = typeof navigator !== 'undefined' ? navigator.language : 'en-US';
      (config.headers as Record<string, string>)['Accept-Language'] = lang;

      // Authorization token
      const storedToken = typeof window !== 'undefined'
        ? localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
        : null;

      if (storedToken && !(config.headers as Record<string, string>)['Authorization']) {
        (config.headers as Record<string, string>)['Authorization'] = `Bearer ${storedToken}`;
      }
    } catch {
      // silently ignore
    }

    return config;
  },

  onRejected: (error: any) => Promise.reject(error)
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
