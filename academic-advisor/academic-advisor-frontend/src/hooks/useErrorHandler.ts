// src/hooks/useErrorHandler.ts
import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';

export interface ErrorState {
  message: string;
  code?: string;
  details?: any;
}

export const useErrorHandler = () => {
  const [error, setError] = useState<ErrorState | null>(null);

  const handleError = useCallback((error: Error | any, options?: {
    showToast?: boolean;
    toastMessage?: string;
    fallbackMessage?: string;
  }) => {
    const {
      showToast = true,
      toastMessage,
      fallbackMessage = 'An unexpected error occurred'
    } = options || {};

    // Extract error information
    const errorState: ErrorState = {
      message: error?.message || fallbackMessage,
      code: error?.code,
      details: error?.response?.data || error?.details
    };

    // Set error state
    setError(errorState);

    // Show toast notification if enabled
    if (showToast) {
      const message = toastMessage || errorState.message;
      if (errorState.code === 'NETWORK_ERROR') {
        toast.error('Network error. Please check your connection.');
      } else if (errorState.code === 'TIMEOUT') {
        toast.error('Request timeout. Please try again.');
      } else {
        toast.error(message);
      }
    }

    // Log error for debugging
    console.error('Error handled:', {
      message: errorState.message,
      code: errorState.code,
      details: errorState.details,
      originalError: error
    });

    return errorState;
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleAsyncError = useCallback(async <T>(
    promise: Promise<T>,
    options?: Parameters<typeof handleError>[1]
  ): Promise<T | null> => {
    try {
      const result = await promise;
      clearError();
      return result;
    } catch (error) {
      handleError(error, options);
      return null;
    }
  }, [handleError, clearError]);

  const hasError = useCallback((code?: string): boolean => {
    if (!error) return false;
    if (!code) return true;
    return error.code === code;
  }, [error]);

  return {
    error,
    handleError,
    clearError,
    handleAsyncError,
    hasError,
    isError: !!error
  };
};