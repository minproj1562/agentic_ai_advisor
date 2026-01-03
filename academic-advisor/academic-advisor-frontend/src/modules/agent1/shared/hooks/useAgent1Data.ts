// modules/agent1/shared/hooks/useAgent1Data.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { firebaseRealtime } from '../../../../core/integrations/firebase/realtime';
import { apiService } from '../../../shared/services/api.service';

// FIXED: Create local types since the import is missing
interface PerformanceTrend {
  studentId: string;
  dataPoints: Array<{
    date: string;
    gpa: number;
    percentile?: number;
    improvement?: number;
    confidence?: number;
  }>;
  currentGPA?: number;
  percentile?: number;
  subjects?: SubjectData[];
  lastUpdated?: string;
  projection?: any[];
}

interface SubjectData {
  id: string;
  name: string;
  category: string;
  credits: number;
  currentGrade: number;
  previousGrade?: number;
  classAverage?: number;
  rank?: number;
  totalStudents?: number;
  attendance?: number;
  completedAssignments?: number;
  totalAssignments?: number;
  weakTopics?: string[];
  recommendation?: string;
  trend: number;
}

interface UseAgent1DataOptions {
  studentId: string;
  enableRealtime?: boolean;
  autoFetch?: boolean;
  refreshInterval?: number;
}

interface Agent1Data {
  performance: PerformanceTrend | null;
  subjects: SubjectData[];
  weaknesses: any[];
  recommendations: any[];
  insights: any[];
}

interface UseAgent1DataReturn {
  data: Agent1Data;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  subscribeToUpdates: (channel: string, callback: (data: any) => void) => () => void;
  unsubscribe: (channel: string) => void;
  updateData: (updates: Partial<Agent1Data>) => void;
  clearCache: () => void;
}

export const useAgent1Data = (options: UseAgent1DataOptions): UseAgent1DataReturn => {
  const {
    studentId,
    enableRealtime = true,
    autoFetch = true,
    refreshInterval
  } = options;

  const [data, setData] = useState<Agent1Data>({
    performance: null,
    subjects: [],
    weaknesses: [],
    recommendations: [],
    insights: []
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const subscriptionsRef = useRef<Map<string, () => void>>(new Map());
  // FIXED: Use number type for browser setTimeout instead of NodeJS.Timeout
  const refreshTimerRef = useRef<number | null>(null);

  /**
   * Fetch all Agent 1 data
   */
  const fetchData = useCallback(async () => {
    if (!studentId) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [performance, subjects, weaknesses, recommendations, insights] = await Promise.all([
        apiService.get(`/api/analytics/performance/${studentId}`),
        apiService.get(`/api/analytics/subjects/${studentId}`),
        apiService.get(`/api/analytics/weaknesses/${studentId}`),
        apiService.get(`/api/recommendations/${studentId}`),
        apiService.get(`/api/insights/${studentId}`)
      ]);

      setData({
        performance: performance.data,
        subjects: subjects.data || [],
        weaknesses: weaknesses.data || [],
        recommendations: recommendations.data || [],
        insights: insights.data || []
      });
    } catch (err) {
      const error = err as Error;
      console.error('Failed to fetch Agent 1 data:', error);
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  /**
   * Subscribe to realtime updates
   */
  const subscribeToUpdates = useCallback(
    (channel: string, callback: (data: any) => void): (() => void) => {
      if (!enableRealtime) {
        return () => {};
      }

      const fullChannel = `agent1/${studentId}/${channel}`;
      
      const unsubscribe = firebaseRealtime.subscribe(fullChannel, (snapshot) => {
        callback(snapshot);
      });

      subscriptionsRef.current.set(channel, unsubscribe);

      return () => {
        unsubscribe();
        subscriptionsRef.current.delete(channel);
      };
    },
    [studentId, enableRealtime]
  );

  /**
   * Unsubscribe from a channel
   */
  const unsubscribe = useCallback((channel: string) => {
    const unsubscribeFn = subscriptionsRef.current.get(channel);
    if (unsubscribeFn) {
      unsubscribeFn();
      subscriptionsRef.current.delete(channel);
    }
  }, []);

  /**
   * Update data locally
   */
  const updateData = useCallback((updates: Partial<Agent1Data>) => {
    setData(prev => ({
      ...prev,
      ...updates
    }));
  }, []);

  /**
   * Clear cache
   */
  const clearCache = useCallback(() => {
    setData({
      performance: null,
      subjects: [],
      weaknesses: [],
      recommendations: [],
      insights: []
    });
  }, []);

  /**
   * Setup realtime listeners
   */
  useEffect(() => {
    if (!enableRealtime || !studentId) return;

    const channels = ['performance', 'subjects', 'weaknesses', 'recommendations', 'insights'];

    channels.forEach(channel => {
      subscribeToUpdates(channel, (snapshot) => {
        setData(prev => ({
          ...prev,
          [channel]: snapshot
        }));
      });
    });

    return () => {
      channels.forEach(channel => unsubscribe(channel));
    };
  }, [studentId, enableRealtime, subscribeToUpdates, unsubscribe]);

  /**
   * Auto-fetch on mount
   */
  useEffect(() => {
    if (autoFetch && studentId) {
      fetchData();
    }
  }, [autoFetch, studentId, fetchData]);

  /**
   * Setup refresh interval
   */
  useEffect(() => {
    if (refreshInterval && studentId) {
      // FIXED: Use window.setTimeout which returns number in browser
      refreshTimerRef.current = window.setInterval(() => {
        fetchData();
      }, refreshInterval);

      return () => {
        if (refreshTimerRef.current !== null) {
          clearInterval(refreshTimerRef.current);
          refreshTimerRef.current = null;
        }
      };
    }
  }, [refreshInterval, studentId, fetchData]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Unsubscribe from all channels
      subscriptionsRef.current.forEach(unsubscribe => unsubscribe());
      subscriptionsRef.current.clear();

      // Clear refresh timer
      if (refreshTimerRef.current !== null) {
        clearInterval(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    subscribeToUpdates,
    unsubscribe,
    updateData,
    clearCache
  };
};