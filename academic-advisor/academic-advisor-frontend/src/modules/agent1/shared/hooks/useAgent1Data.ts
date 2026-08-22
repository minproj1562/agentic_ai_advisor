// modules/agent1/shared/hooks/useAgent1Data.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService } from '../../../shared/services/api.service';
import { firebaseRealtime } from '../../../../core/integrations/firebase/realtime';

// Local types
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

const DEFAULT_DATA: Agent1Data = {
  performance: null,
  subjects: [],
  weaknesses: [],
  recommendations: [],
  insights: []
};

/**
 * Safely fetch from an API endpoint, returning a fallback on any error
 */
async function safeFetch<T>(url: string, fallback: T): Promise<T> {
  try {
    const response = await apiService.get(url);
    return response?.data ?? fallback;
  } catch {
    // Silently return fallback — endpoint may not exist
    return fallback;
  }
}

export const useAgent1Data = (options: UseAgent1DataOptions): UseAgent1DataReturn => {
  const {
    studentId,
    enableRealtime = false, // FIXED: Default to false — RTDB may not be set up
    autoFetch = true,
    refreshInterval
  } = options;

  const [data, setData] = useState<Agent1Data>(DEFAULT_DATA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const subscriptionsRef = useRef<Map<string, () => void>>(new Map());
  const refreshTimerRef = useRef<number | null>(null);
  const fetchedRef = useRef(false); // FIXED: Prevent double-fetch

  /**
   * Fetch all Agent 1 data — each endpoint fails independently
   */
  const fetchData = useCallback(async () => {
    if (!studentId) return;
    if (fetchedRef.current && !refreshInterval) return; // Prevent duplicate initial fetch

    setLoading(true);
    setError(null);
    fetchedRef.current = true;

    try {
      // Fetch all data in parallel — each call has its own fallback
      const [performance, subjects, weaknesses, recommendations, insights] = await Promise.all([
        safeFetch<any>(`/api/analytics/performance/${studentId}`, null),
        safeFetch<any[]>(`/api/analytics/subjects/${studentId}`, []),
        safeFetch<any[]>(`/api/analytics/weaknesses/${studentId}`, []),
        safeFetch<any[]>(`/api/recommendations/${studentId}`, []),
        safeFetch<any[]>(`/api/insights/${studentId}`, [])
      ]);

      setData({
        performance,
        subjects,
        weaknesses,
        recommendations,
        insights
      });
    } catch (err) {
      // This catch should rarely fire since safeFetch handles errors,
      // but we keep it as a safety net
      const error = err as Error;
      console.warn('Agent1Data: unexpected error during fetch:', error.message);
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [studentId, refreshInterval]);

  /**
   * Subscribe to realtime updates
   * FIXED: Returns a no-op if realtime is disabled or Firebase RTDB is unavailable
   */
  const subscribeToUpdates = useCallback(
    (channel: string, callback: (data: any) => void): (() => void) => {
      if (!enableRealtime || !studentId) {
        return () => {};
      }

      try {
        const fullChannel = `agent1/${studentId}/${channel}`;

        const unsubscribe = firebaseRealtime.subscribe(fullChannel, (snapshot: any) => {
          callback(snapshot);
        });

        subscriptionsRef.current.set(channel, unsubscribe);

        return () => {
          unsubscribe();
          subscriptionsRef.current.delete(channel);
        };
      } catch (err) {
        console.warn('Agent1Data: realtime subscription failed, RTDB may not be configured:', (err as Error).message);
        return () => {};
      }
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
    fetchedRef.current = false;
    setData(DEFAULT_DATA);
  }, []);

  /**
   * Setup realtime listeners — ONLY if enableRealtime is true
   */
  useEffect(() => {
    if (!enableRealtime || !studentId) return;

    const channels = ['performance', 'subjects', 'weaknesses', 'recommendations', 'insights'];

    channels.forEach(channel => {
      subscribeToUpdates(channel, (snapshot) => {
        if (snapshot) {
          setData(prev => ({
            ...prev,
            [channel]: snapshot
          }));
        }
      });
    });

    return () => {
      channels.forEach(channel => unsubscribe(channel));
    };
  }, [studentId, enableRealtime, subscribeToUpdates, unsubscribe]);

  /**
   * Auto-fetch on mount — only once
   */
  useEffect(() => {
    if (autoFetch && studentId && !fetchedRef.current) {
      fetchData();
    }
  }, [autoFetch, studentId, fetchData]);

  /**
   * Setup refresh interval
   */
  useEffect(() => {
    if (refreshInterval && studentId) {
      refreshTimerRef.current = window.setInterval(() => {
        fetchedRef.current = false; // Allow re-fetch
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
      subscriptionsRef.current.forEach(unsub => unsub());
      subscriptionsRef.current.clear();

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
    refetch: async () => {
      fetchedRef.current = false;
      await fetchData();
    },
    subscribeToUpdates,
    unsubscribe,
    updateData,
    clearCache
  };
};