// src/monitoring/performance.monitor.ts

export interface PerformanceMetric {
  transactionId: string;
  name: string;
  duration: number;
  startTime: number;
  endTime: number;
  metadata?: Record<string, any>;
}

export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private transactions: Map<string, { startTime: number; name: string; metadata?: any }>;
  private metrics: PerformanceMetric[] = [];
  private readonly MAX_METRICS = 1000;

  private constructor() {
    this.transactions = new Map();
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  startTransaction(name: string, metadata?: any): string {
    const id = `perf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.transactions.set(id, {
      startTime: performance.now(),
      name,
      metadata
    });
    return id;
  }

  endTransaction(id: string, additionalData?: any): void {
    const transaction = this.transactions.get(id);
    if (!transaction) return;

    const endTime = performance.now();
    const duration = endTime - transaction.startTime;
    
    const metric: PerformanceMetric = {
      transactionId: id,
      name: transaction.name,
      duration,
      startTime: transaction.startTime,
      endTime,
      metadata: { ...transaction.metadata, ...additionalData }
    };

    // Store metric
    this.metrics.push(metric);
    
    // Keep only recent metrics
    if (this.metrics.length > this.MAX_METRICS) {
      this.metrics = this.metrics.slice(-this.MAX_METRICS);
    }

    // Log performance data
    this.logPerformance(metric);

    this.transactions.delete(id);
  }

  private logPerformance(data: PerformanceMetric): void {
    // Use Vite environment variable instead of process.env
    if (import.meta.env.DEV) {
      console.log('Performance Metric:', {
        name: data.name,
        duration: `${data.duration.toFixed(2)}ms`,
        metadata: data.metadata
      });
    }

    // Send to analytics service
    this.sendToAnalytics(data);
  }

  private sendToAnalytics(data: PerformanceMetric): void {
    // Send to external analytics service if available
    if (typeof window !== 'undefined') {
      // Example: Google Analytics
      if ((window as any).gtag) {
        (window as any).gtag('event', 'performance', {
          event_category: 'Performance',
          event_label: data.name,
          value: Math.round(data.duration),
          custom_map: {
            dimension1: data.transactionId
          }
        });
      }

      // Custom analytics
      if ((window as any).analytics) {
        (window as any).analytics.track('Performance Metric', data);
      }
    }
  }

  async measureAsync<T>(
    name: string,
    fn: () => Promise<T>,
    metadata?: any
  ): Promise<T> {
    const id = this.startTransaction(name, metadata);
    try {
      const result = await fn();
      this.endTransaction(id, { success: true });
      return result;
    } catch (error) {
      this.endTransaction(id, { 
        success: false, 
        error: error instanceof Error ? error.message : String(error) 
      });
      throw error;
    }
  }

  measure<T>(
    name: string,
    fn: () => T,
    metadata?: any
  ): T {
    const id = this.startTransaction(name, metadata);
    try {
      const result = fn();
      this.endTransaction(id, { success: true });
      return result;
    } catch (error) {
      this.endTransaction(id, { 
        success: false, 
        error: error instanceof Error ? error.message : String(error) 
      });
      throw error;
    }
  }

  getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter(metric => metric.name === name);
  }

  getAverageDuration(name: string): number {
    const metrics = this.getMetricsByName(name);
    if (metrics.length === 0) return 0;
    
    const total = metrics.reduce((sum, metric) => sum + metric.duration, 0);
    return total / metrics.length;
  }

  clearMetrics(): void {
    this.metrics = [];
  }

  // Page load performance (simplified without navigation timing)
  trackPageLoad(): void {
    if (typeof window !== 'undefined' && 'performance' in window) {
      window.addEventListener('load', () => {
        // Use a simpler approach without navigation timing
        const loadTime = performance.now();
        this.logPerformance({
          transactionId: `page_load_${Date.now()}`,
          name: 'Page Load',
          duration: loadTime,
          startTime: 0,
          endTime: loadTime,
          metadata: {
            userAgent: navigator.userAgent,
            url: window.location.href
          }
        });
      });
    }
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();