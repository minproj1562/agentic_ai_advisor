// modules/agent1/performance-analytics/hooks/usePerformanceTrends.ts
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
  const { subscribeToUpdates, unsubscribe } = useAgent1Data({ studentId });

  // Stable serialized key for trendOptions to prevent SWR key churn
  const trendOptionsKey = useRef(JSON.stringify(trendOptions));
  useEffect(() => {
    trendOptionsKey.current = JSON.stringify(trendOptions);
  }, [JSON.stringify(trendOptions)]);

  // SWR configuration — disable retry on error to prevent infinite loops
  const swrConfig: SWRConfiguration = {
    refreshInterval: cacheTime,
    revalidateOnFocus: false, // Prevent refetch on tab focus
    revalidateOnReconnect: true,
    shouldRetryOnError: false, // FIXED: Disable automatic retry to prevent infinite loops
    errorRetryCount: 0, // FIXED: No retries
    dedupingInterval: 10000, // FIXED: Increased dedup interval to 10s
    onError: (error) => {
      console.warn('Performance trends error:', error?.message || error);
      onError?.(error);
    },
    onSuccess: (data) => {
      if (data) {
        setLocalData(data);
        onSuccess?.(data);
      }
    }
  };

  // Fetch function for SWR — never throws, always returns data or null
  const fetcher = useCallback(async (_key: string): Promise<PerformanceTrend | null> => {
    try {
      // Fetch base performance data
      const performanceData = await analyticsService.getPerformanceTrends(
        studentId,
        trendOptions
      );

      // If no data returned, return null gracefully
      if (!performanceData) {
        console.warn('No performance data returned for student:', studentId);
        return null;
      }

      // Add predictions if enabled and there's enough data
      // trendService.generatePredictions now returns [] on insufficient data instead of throwing
      if (enablePrediction && performanceData?.dataPoints?.length > 0) {
        const predictions = await trendService.generatePredictions(
          performanceData,
          trendOptions.timeRange || '3m'
        );
        performanceData.projection = predictions;
      }

      // Calculate trend analysis — now returns default analysis instead of throwing
      const trendAnalysis = await trendService.analyzeTrends(performanceData);
      setAnalysis(trendAnalysis);

      return performanceData;
    } catch (error) {
      console.warn('Failed to fetch performance trends:', (error as Error)?.message || error);
      // Return null instead of throwing — prevents SWR from retrying
      return null;
    }
  }, [studentId, enablePrediction]); // FIXED: removed trendOptions from deps (use ref instead)

  // SWR hook — key is null when no studentId, preventing fetch
  const {
    data,
    error,
    mutate,
    isValidating
  } = useSWR(
    studentId ? `${CACHE_KEYS.PERFORMANCE_TRENDS}-${studentId}-${trendOptionsKey.current}` : null,
    fetcher,
    swrConfig
  );

  // Realtime subscription — only subscribe once per studentId
  useEffect(() => {
    if (!enableRealtime || !studentId) return;

    let cancelled = false;

    const unsubscribeFunc = subscribeToUpdates(
      `performance/${studentId}`,
      async (update: any) => {
        if (cancelled || !update?.data) return;

        const mergedData = {
          ...localData,
          ...update.data,
          lastUpdated: new Date().toISOString()
        };

        setLocalData(mergedData);
        await mutate(mergedData, false);

        if (mergedData?.dataPoints?.length > 0) {
          const newAnalysis = await trendService.analyzeTrends(mergedData);
          if (!cancelled) {
            setAnalysis(newAnalysis);
          }
        }
      }
    );

    return () => {
      cancelled = true;
      unsubscribeFunc();
    };
    // FIXED: removed localData from deps to prevent re-subscription loops
  }, [enableRealtime, studentId, mutate, subscribeToUpdates]);

  // Update trend function
  const updateTrend = useCallback(async (data: Partial<PerformanceTrend>): Promise<void> => {
    try {
      const updatedData = await analyticsService.updatePerformanceTrend(
        studentId,
        data
      );

      setLocalData(updatedData);
      await mutate(updatedData, false);
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
      console.warn('Failed to refetch:', error);
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
    loading: !data && !error && !!studentId,
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

  const factors = {
    completeness: data.dataPoints.filter(d => d.gpa !== null && d.gpa !== undefined).length / data.dataPoints.length,
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