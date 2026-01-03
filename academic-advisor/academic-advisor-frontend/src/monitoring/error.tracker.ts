// src/monitoring/error.tracker.ts

export interface ErrorContext {
  userId?: string;
  context?: string;
  component?: string;
  [key: string]: any;
}

export interface TrackedError {
  id: string;
  error: Error;
  context: ErrorContext;
  timestamp: Date;
  stack?: string;
}

export class ErrorTracker {
  private static instance: ErrorTracker;
  private errors: TrackedError[] = [];
  private readonly MAX_ERRORS = 1000;

  private constructor() {}

  static getInstance(): ErrorTracker {
    if (!ErrorTracker.instance) {
      ErrorTracker.instance = new ErrorTracker();
    }
    return ErrorTracker.instance;
  }

  captureError(error: Error, context?: ErrorContext): string {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const errorEntry: TrackedError = {
      id: errorId,
      error,
      context: context || {},
      timestamp: new Date(),
      stack: error.stack
    };

    // Store error
    this.errors.push(errorEntry);
    
    // Keep only recent errors
    if (this.errors.length > this.MAX_ERRORS) {
      this.errors = this.errors.slice(-this.MAX_ERRORS);
    }
    
    // Log to console in development
    if (import.meta.env.DEV) {
      console.error('Error captured:', {
        id: errorId,
        message: error.message,
        context: errorEntry.context,
        stack: error.stack
      });
    }

    // Send to monitoring service
    this.sendToMonitoringService(errorEntry);

    return errorId;
  }

  captureException(exception: unknown, context?: ErrorContext): string {
    const error = exception instanceof Error ? exception : new Error(String(exception));
    return this.captureError(error, context);
  }

  private sendToMonitoringService(errorEntry: TrackedError): void {
    // Implement integration with external services
    
    // Sentry
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(errorEntry.error, {
        extra: errorEntry.context,
        tags: {
          errorId: errorEntry.id
        }
      });
    }

    // LogRocket
    if (typeof window !== 'undefined' && (window as any).LogRocket) {
      (window as any).LogRocket.captureException(errorEntry.error, {
        extra: errorEntry.context
      });
    }

    // Custom backend API
    this.sendToBackend(errorEntry);
  }

  private async sendToBackend(errorEntry: TrackedError): Promise<void> {
    try {
      // Only send in production or if explicitly enabled
      if (!import.meta.env.PROD) return;

      await fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: errorEntry.id,
          message: errorEntry.error.message,
          stack: errorEntry.stack,
          context: errorEntry.context,
          timestamp: errorEntry.timestamp.toISOString(),
          url: typeof window !== 'undefined' ? window.location.href : '',
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : ''
        })
      });
    } catch (error) {
      // Silently fail - we don't want error tracking to cause errors
      if (import.meta.env.DEV) {
        console.warn('Failed to send error to backend:', error);
      }
    }
  }

  // React error boundary helper (for use in React components)
  captureReactError(error: Error, errorInfo: { componentStack?: string }): string {
    return this.captureError(error, {
      context: 'react_error_boundary',
      componentStack: errorInfo.componentStack
    });
  }

  // Network error tracking
  captureNetworkError(url: string, status: number, responseText?: string): string {
    const error = new Error(`Network request failed: ${url} (${status})`);
    return this.captureError(error, {
      context: 'network_error',
      url,
      status,
      responseText: responseText?.substring(0, 500) // Limit size
    });
  }

  getErrors(): TrackedError[] {
    return [...this.errors];
  }

  getErrorById(id: string): TrackedError | undefined {
    return this.errors.find(error => error.id === id);
  }

  getErrorsByContext(context: string): TrackedError[] {
    return this.errors.filter(error => error.context.context === context);
  }

  clearErrors(): void {
    this.errors = [];
  }

  // Error statistics
  getErrorStats(): {
    total: number;
    byContext: Record<string, number>;
    last24Hours: number;
  } {
    const now = Date.now();
    const twentyFourHoursAgo = now - (24 * 60 * 60 * 1000);

    const byContext: Record<string, number> = {};
    let last24Hours = 0;

    this.errors.forEach(error => {
      // Count by context
      const context = error.context.context || 'unknown';
      byContext[context] = (byContext[context] || 0) + 1;

      // Count last 24 hours
      if (error.timestamp.getTime() > twentyFourHoursAgo) {
        last24Hours++;
      }
    });

    return {
      total: this.errors.length,
      byContext,
      last24Hours
    };
  }

  // Set user context for all future errors
  setUserContext(userId: string, userData?: any): void {
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.setUser({ id: userId, ...userData });
    }
  }

  // Clear user context
  clearUserContext(): void {
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.setUser(null);
    }
  }
}

// Export singleton instance
export const errorTracker = ErrorTracker.getInstance();