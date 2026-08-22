// modules/shared/services/api.service.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { authInterceptor } from '../../../core/api/interceptors/auth.interceptor';
import { errorInterceptor } from '../../../core/api/interceptors/error.interceptor';

interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

interface ApiError {
  message: string;
  code: string;
  details?: any;
  status?: number;
}

class ApiService {
  private axiosInstance: AxiosInstance;
  private pendingRequests: Map<string, AbortController>;
  private cache: Map<string, { data: any; timestamp: number }>;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  constructor() {
    // Use Vite environment variables for browser
    const baseURL = (import.meta.env?.VITE_API_BASE_URL as string) || 
                   (import.meta.env?.REACT_APP_API_BASE_URL as string) || 
                   '/api';

    this.axiosInstance = axios.create({
      baseURL: baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.pendingRequests = new Map();
    this.cache = new Map();

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      // FIXED: Properly typed interceptor functions
      (config: InternalAxiosRequestConfig) => {
        if (authInterceptor.onFulfilled) {
          return (authInterceptor.onFulfilled(config) as unknown) as InternalAxiosRequestConfig;
        }
        return config;
      },
      (error: any) => {
        if (authInterceptor.onRejected) {
          return authInterceptor.onRejected(error);
        }
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error: any) => {
        if (errorInterceptor.onRejected) {
          return errorInterceptor.onRejected(error);
        }
        return Promise.reject(error);
      }
    );

    // Add request deduplication
    this.axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      const requestKey = this.generateRequestKey(config);
      
      // Cancel duplicate requests
      if (this.pendingRequests.has(requestKey)) {
        const controller = this.pendingRequests.get(requestKey);
        controller?.abort();
      }

      // Create new abort controller
      const controller = new AbortController();
      config.signal = controller.signal;
      this.pendingRequests.set(requestKey, controller);

      return config;
    });

    // Clean up after response
    this.axiosInstance.interceptors.response.use(
      (response) => {
        const requestKey = this.generateRequestKey(response.config);
        this.pendingRequests.delete(requestKey);
        return response;
      },
      (error) => {
        if (error.config) {
          const requestKey = this.generateRequestKey(error.config);
          this.pendingRequests.delete(requestKey);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Generate unique request key for deduplication
   */
  private generateRequestKey(config: AxiosRequestConfig): string {
    return `${config.method}-${config.url}-${JSON.stringify(config.params)}`;
  }

  /**
   * Check cache for data
   */
  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const isExpired = Date.now() - cached.timestamp > this.CACHE_DURATION;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return cached.data as T;
  }

  /**
   * Set cache
   */
  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * Clear cache
   */
  public clearCache(pattern?: string): void {
    if (pattern) {
      Array.from(this.cache.keys())
        .filter(key => key.includes(pattern))
        .forEach(key => this.cache.delete(key));
    } else {
      this.cache.clear();
    }
  }

  /**
   * GET request
   */
  async get<T = any>(
    url: string,
    config?: AxiosRequestConfig & { useCache?: boolean }
  ): Promise<ApiResponse<T>> {
    try {
      const cacheKey = `GET-${url}-${JSON.stringify(config?.params)}`;
      
      // Check cache if enabled
      if (config?.useCache !== false) {
        const cached = this.getFromCache<T>(cacheKey);
        if (cached) {
          return {
            data: cached,
            success: true,
            timestamp: new Date().toISOString()
          };
        }
      }

      const response: AxiosResponse<T> = await this.axiosInstance.get(url, config);
      
      // Cache successful response
      if (config?.useCache !== false) {
        this.setCache(cacheKey, response.data);
      }

      return {
        data: response.data,
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * POST request
   */
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.axiosInstance.post(url, data, config);
      
      // Invalidate related cache
      this.clearCache(url);

      return {
        data: response.data,
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * PUT request
   */
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.axiosInstance.put(url, data, config);
      
      // Invalidate related cache
      this.clearCache(url);

      return {
        data: response.data,
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * PATCH request
   */
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.axiosInstance.patch(url, data, config);
      
      // Invalidate related cache
      this.clearCache(url);

      return {
        data: response.data,
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * DELETE request
   */
  async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.axiosInstance.delete(url, config);
      
      // Invalidate related cache
      this.clearCache(url);

      return {
        data: response.data,
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * Upload file
   */
  async upload<T = any>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response: AxiosResponse<T> = await this.axiosInstance.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      });

      return {
        data: response.data,
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * Download file
   */
  async download(
    url: string,
    filename: string,
    onProgress?: (progress: number) => void
  ): Promise<void> {
    try {
      const response = await this.axiosInstance.get(url, {
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      });

      // Create download link
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * Batch requests
   */
  async batch<T = any>(
    requests: Array<() => Promise<ApiResponse<any>>>
  ): Promise<ApiResponse<T[]>> {
    try {
      const results = await Promise.all(requests.map(request => request()));
      
      return {
        data: results.map(r => r.data) as T[],
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw this.handleError(error as AxiosError);
    }
  }

  /**
   * Retry request
   */
  async retry<T = any>(
    request: () => Promise<ApiResponse<T>>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<ApiResponse<T>> {
    let lastError: Error;

    for (let i = 0; i < maxRetries; i++) {
      try {
        return await request();
      } catch (error) {
        lastError = error as Error;
        
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
        }
      }
    }

    throw lastError!;
  }

  /**
   * Handle API errors
   */
  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error
      // FIXED: Properly access error response data
      const responseData = error.response.data as any;
      return {
        message: responseData?.message || 'Request failed',
        code: responseData?.code || 'SERVER_ERROR',
        details: responseData?.details,
        status: error.response.status
      };
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'Network error - please check your connection',
        code: 'NETWORK_ERROR'
      };
    } else {
      // Error setting up request
      return {
        message: error.message || 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR'
      };
    }
  }

  /**
   * Set auth token
   */
  setAuthToken(token: string): void {
    this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Remove auth token
   */
  removeAuthToken(): void {
    delete this.axiosInstance.defaults.headers.common['Authorization'];
  }

  /**
   * Get instance for custom configuration
   */
  getInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

export const apiService = new ApiService();