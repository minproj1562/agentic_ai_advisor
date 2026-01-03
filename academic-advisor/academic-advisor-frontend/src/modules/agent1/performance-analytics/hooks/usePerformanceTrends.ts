// modules/agent1/performance-analytics/hooks/usePerformanceTrends.ts
import { useState, useEffect, useCallback, useMemo } from 'react';
import useSWR, { SWRConfiguration } from 'swr';
import { PerformanceTrend, TrendOptions, TrendAnalysis } from '../types/analytics.types';
import { analyticsService } from '../services/analytics.service';
import { trendService } from '../services/trend.service';
import { useAgent1Data } from '../../shared/hooks/useAgent1Data';
import { CACHE_KEYS, REFRESH_INTERVALS } from '../constants/thresholds';

interface UsePerformanceTrendsOptions extends TrendOptions {
  enableRealtime?: boolean;
  enablePrediction?: boolean;
  cacheTime?: number;
  onError?: (error: Error) => void;
  onSuccess?: (data: PerformanceTrend) => void;
}

interface UsePerformanceTrendsReturn {
  trends: PerformanceTrend | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  isValidating: boolean;
  analysis: TrendAnalysis | null;
  updateTrend: (data: Partial<PerformanceTrend>) => Promise<void>;
}

export const usePerformanceTrends = (
  studentId: string,
  options: UsePerformanceTrendsOptions = {}
): UsePerformanceTrendsReturn => {
  const {
    enableRealtime = true,
    enablePrediction = true,
    cacheTime = REFRESH_INTERVALS.PERFORMANCE_DATA,
    onError,
    onSuccess,
    ...trendOptions
  } = options;

  const [localData, setLocalData] = useState<PerformanceTrend | null>(null);
  const [analysis, setAnalysis] = useState<TrendAnalysis | null>(null);
  // FIXED: Added studentId parameter to useAgent1Data hook
   const { subscribeToUpdates, unsubscribe } = useAgent1Data({ studentId });

  // SWR configuration
  const swrConfig: SWRConfiguration = {
    refreshInterval: cacheTime,
    revalidateOnFocus: true,
    revalidateOnReconnect: true,
    shouldRetryOnError: true,
    errorRetryCount: 3,
    errorRetryInterval: 5000,
    dedupingInterval: 2000,
    onError: (error) => {
      console.error('Performance trends error:', error);
      onError?.(error);
    },
    onSuccess: (data) => {
      setLocalData(data);
      onSuccess?.(data);
    }
  };

  // Fetch function for SWR
  const fetcher = useCallback(async (key: string) => {
    try {
      // Fetch base performance data
      const performanceData = await analyticsService.getPerformanceTrends(
        studentId,
        trendOptions
      );

      // Add predictions if enabled
      if (enablePrediction && performanceData) {
        const predictions = await trendService.generatePredictions(
          performanceData,
          trendOptions.timeRange || '3m'
        );
        performanceData.projection = predictions;
      }

      // Calculate trend analysis
      const trendAnalysis = await trendService.analyzeTrends(performanceData);
      setAnalysis(trendAnalysis);

      return performanceData;
    } catch (error) {
      console.error('Failed to fetch performance trends:', error);
      throw error;
    }
  }, [studentId, trendOptions, enablePrediction]);

  // SWR hook for data fetching
  const {
    data,
    error,
    mutate,
    isValidating
  } = useSWR(
    studentId ? `${CACHE_KEYS.PERFORMANCE_TRENDS}-${studentId}-${JSON.stringify(trendOptions)}` : null,
    fetcher,
    swrConfig
  );

  // Realtime subscription
  useEffect(() => {
    if (!enableRealtime || !studentId) return;

    const unsubscribeFunc = subscribeToUpdates(
      `performance/${studentId}`,
      async (update: any) => {
        // Validate update
        if (!update || !update.data) return;

        // Merge with existing data
        const mergedData = {
          ...localData,
          ...update.data,
          lastUpdated: new Date().toISOString()
        };

        setLocalData(mergedData);
        
        // Trigger revalidation
        await mutate(mergedData, false);

        // Recalculate analysis
        if (mergedData) {
          const newAnalysis = await trendService.analyzeTrends(mergedData);
          setAnalysis(newAnalysis);
        }
      }
    );

    return () => {
      unsubscribeFunc();
    };
  }, [enableRealtime, studentId, localData, mutate, subscribeToUpdates]);

  // Update trend function
  // FIXED: Changed return type from Promise<PerformanceTrend> to Promise<void>
  const updateTrend = useCallback(async (data: Partial<PerformanceTrend>): Promise<void> => {
    try {
      const updatedData = await analyticsService.updatePerformanceTrend(
        studentId,
        data
      );
      
      // Update local state
      setLocalData(updatedData);
      
      // Trigger revalidation
      await mutate(updatedData, false);
      
      // FIXED: Don't return the data since the return type expects Promise<void>
    } catch (error) {
      console.error('Failed to update trend:', error);
      throw error;
    }
  }, [studentId, mutate]);

  // Refetch function
  const refetch = useCallback(async () => {
    try {
      await mutate();
    } catch (error) {
      console.error('Failed to refetch:', error);
      throw error;
    }
  }, [mutate]);

  // Process and enrich data
  const processedTrends = useMemo(() => {
    if (!data) return null;

    return {
      ...data,
      enriched: true,
      processedAt: new Date().toISOString(),
      dataQuality: calculateDataQuality(data),
      insights: generateInsights(data, analysis)
    };
  }, [data, analysis]);

  return {
    trends: processedTrends || localData,
    loading: !data && !error,
    error,
    refetch,
    isValidating,
    analysis,
    updateTrend
  };
};

// Helper functions
function calculateDataQuality(data: PerformanceTrend): number {
  if (!data.dataPoints || data.dataPoints.length === 0) return 0;
  
  // FIXED: Added null check for lastUpdated
  const factors = {
    completeness: data.dataPoints.filter(d => d.gpa !== null).length / data.dataPoints.length,
    recency: isDataRecent(data.lastUpdated || '') ? 1 : 0.5,
    consistency: checkDataConsistency(data.dataPoints),
    coverage: data.subjects ? Math.min(data.subjects.length / 10, 1) : 0.5
  };
  
  return Object.values(factors).reduce((acc, val) => acc + val, 0) / Object.keys(factors).length;
}

function isDataRecent(lastUpdated: string): boolean {
  if (!lastUpdated) return false;
  
  const lastUpdate = new Date(lastUpdated);
  const daysSinceUpdate = (Date.now() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24);
  return daysSinceUpdate < 7;
}

function checkDataConsistency(dataPoints: any[]): number {
  if (dataPoints.length < 2) return 1;
  
  let consistencyScore = 1;
  for (let i = 1; i < dataPoints.length; i++) {
    const diff = Math.abs((dataPoints[i].gpa || 0) - (dataPoints[i - 1].gpa || 0));
    if (diff > 1) consistencyScore -= 0.1;
  }
  
  return Math.max(0, consistencyScore);
}

function generateInsights(data: PerformanceTrend, analysis: TrendAnalysis | null): string[] {
  const insights: string[] = [];
  
  if (analysis) {
    if (analysis.trend === 'improving') {
      insights.push(`Your performance is improving with ${(analysis.confidence * 100).toFixed(0)}% confidence`);
    } else if (analysis.trend === 'declining') {
      insights.push(`Performance decline detected - consider seeking academic support`);
    }
    
    if (analysis.projectedGPA && analysis.currentGPA && analysis.projectedGPA > analysis.currentGPA) {
      insights.push(`Expected GPA improvement to ${analysis.projectedGPA.toFixed(2)} next semester`);
    }
  }
  
  if (data.subjects) {
    const weakSubjects = data.subjects.filter(s => s.currentGrade < 60);
    if (weakSubjects.length > 0) {
      insights.push(`${weakSubjects.length} subjects need immediate attention`);
    }
  }
  
  return insights;
}