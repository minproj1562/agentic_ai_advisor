// core/api/interceptors/error.interceptor.ts
import type { AxiosError } from 'axios';

interface InterceptorError {
  message: string;
  code: string;
  status: number;
  details?: any;
  original: any;
}

const STATUS_MESSAGES: Record<number, string> = {
  400: 'Bad request',
  401: 'Authentication required',
  403: 'You do not have permission to perform this action',
  404: 'Requested resource not found',
  409: 'Conflict - resource already exists',
  422: 'Unprocessable entity - validation failed',
  429: 'Too many requests - please slow down',
  500: 'Internal server error',
  502: 'Bad gateway',
  503: 'Service unavailable',
  504: 'Gateway timeout'
};

const STATUS_CODES: Record<number, string> = {
  401: 'AUTH_REQUIRED',
  403: 'PERMISSION_DENIED',
  404: 'NOT_FOUND',
  429: 'RATE_LIMITED'
};

export const errorInterceptor = {
  onRejected: (error: AxiosError): Promise<InterceptorError> => {
    // Network error
    if (error.code === 'ERR_NETWORK') {
      return Promise.reject({
        message: 'Network error - please check your connection',
        code: 'NETWORK_ERROR',
        status: 0,
        original: error
      });
    }

    // Timeout
    if (error.code === 'ECONNABORTED') {
      return Promise.reject({
        message: 'Request timed out - please try again',
        code: 'TIMEOUT',
        status: 0,
        original: error
      });
    }

    // Server response
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as Record<string, any> | undefined;

      const message = data?.message || STATUS_MESSAGES[status] || 'An unexpected error occurred';
      const code = data?.code || STATUS_CODES[status] || 'SERVER_ERROR';

      return Promise.reject({
        message,
        code,
        details: data?.details,
        status,
        original: error
      });
    }

    // Request made but no response
    if (error.request) {
      return Promise.reject({
        message: 'No response from server',
        code: 'NO_RESPONSE',
        status: 0,
        original: error
      });
    }

    // Unknown error
    return Promise.reject({
      message: error.message || 'Unknown error',
      code: 'UNKNOWN_ERROR',
      status: 0,
      original: error
    });
  }
};
