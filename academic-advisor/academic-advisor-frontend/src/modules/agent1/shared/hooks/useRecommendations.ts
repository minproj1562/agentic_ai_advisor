// modules/agent1/shared/hooks/useRecommendations.ts
import { useState, useEffect, useCallback, useMemo } from 'react';
import useSWR from 'swr';
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

interface Recommendation {
  id: string;
  type: 'subject' | 'study' | 'resource' | 'career';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  reasoning: string;
  impact: number;
  timeRequired: string;
  actionItems: string[];
  resources?: any[];
  applicableUntil?: string;
  confidence: number;
}

interface UseRecommendationsOptions {
  studentId: string;
  performanceData?: PerformanceTrend;
  subjectData?: SubjectData[];
  includeTypes?: string[];
  minPriority?: 'high' | 'medium' | 'low';
  limit?: number;
}

interface UseRecommendationsReturn {
  recommendations: Recommendation[];
  loading: boolean;
  error: Error | null;
  prioritized: Recommendation[];
  byType: Record<string, Recommendation[]>;
  acceptRecommendation: (id: string) => Promise<void>;
  dismissRecommendation: (id: string) => Promise<void>;
  refetch: () => Promise<void>;
}

export const useRecommendations = (
  options: UseRecommendationsOptions
): UseRecommendationsReturn => {
  const {
    studentId,
    performanceData,
    subjectData,
    includeTypes = ['subject', 'study', 'resource', 'career'],
    minPriority = 'low',
    limit = 20
  } = options;

  const [acceptedIds, setAcceptedIds] = useState<Set<string>>(new Set());
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  const fetcher = useCallback(async (url: string) => {
    const response = await apiService.post<Recommendation[]>(url, {
      studentId,
      performanceData,
      subjectData,
      includeTypes,
      minPriority,
      limit
    });
    return response.data;
  }, [studentId, performanceData, subjectData, includeTypes, minPriority, limit]);

  const {
    data: recommendations = [],
    error,
    mutate,
    isValidating
  } = useSWR(
    studentId ? `/api/recommendations/generate/${studentId}` : null,
    fetcher,
    {
      refreshInterval: 300000, // 5 minutes
      revalidateOnFocus: false,
      dedupingInterval: 60000
    }
  );

  /**
   * Filter out accepted/dismissed recommendations
   */
  const filteredRecommendations = useMemo(() => {
    return recommendations.filter((rec: Recommendation) => 
      !acceptedIds.has(rec.id) && !dismissedIds.has(rec.id)
    );
  }, [recommendations, acceptedIds, dismissedIds]);

  /**
   * Prioritized recommendations
   */
  const prioritized = useMemo(() => {
    const priorityOrder: Record<string, number> = { high: 0, medium: 1, low: 2 };
    
    return [...filteredRecommendations].sort((a: Recommendation, b: Recommendation) => {
      // First sort by priority
      const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (priorityDiff !== 0) return priorityDiff;
      
      // Then by impact
      return b.impact - a.impact;
    });
  }, [filteredRecommendations]);

  /**
   * Recommendations grouped by type
   */
  const byType = useMemo(() => {
    const grouped: Record<string, Recommendation[]> = {};
    
    filteredRecommendations.forEach((rec: Recommendation) => {
      if (!grouped[rec.type]) {
        grouped[rec.type] = [];
      }
      grouped[rec.type].push(rec);
    });
    
    return grouped;
  }, [filteredRecommendations]);

  /**
   * Accept a recommendation
   */
  const acceptRecommendation = useCallback(async (id: string) => {
    try {
      await apiService.post(`/api/recommendations/${id}/accept`, {
        studentId,
        timestamp: new Date().toISOString()
      });
      
      setAcceptedIds(prev => new Set(prev).add(id));
      
      // Track analytics
      trackRecommendationEvent('accept', id);
    } catch (error) {
      console.error('Failed to accept recommendation:', error);
      throw error;
    }
  }, [studentId]);

  /**
   * Dismiss a recommendation
   */
  const dismissRecommendation = useCallback(async (id: string) => {
    try {
      await apiService.post(`/api/recommendations/${id}/dismiss`, {
        studentId,
        timestamp: new Date().toISOString()
      });
      
      setDismissedIds(prev => new Set(prev).add(id));
      
      // Track analytics
      trackRecommendationEvent('dismiss', id);
    } catch (error) {
      console.error('Failed to dismiss recommendation:', error);
      throw error;
    }
  }, [studentId]);

  /**
   * Refetch recommendations
   */
  const refetch = useCallback(async () => {
    await mutate();
  }, [mutate]);

  /**
   * Load accepted/dismissed from localStorage
   */
  useEffect(() => {
    const loadSavedState = () => {
      try {
        const accepted = localStorage.getItem(`recommendations-accepted-${studentId}`);
        const dismissed = localStorage.getItem(`recommendations-dismissed-${studentId}`);
        
        if (accepted) {
          setAcceptedIds(new Set(JSON.parse(accepted)));
        }
        if (dismissed) {
          setDismissedIds(new Set(JSON.parse(dismissed)));
        }
      } catch (error) {
        console.error('Failed to load saved recommendation state:', error);
      }
    };

    if (studentId) {
      loadSavedState();
    }
  }, [studentId]);

  /**
   * Save to localStorage when state changes
   */
  useEffect(() => {
    try {
      if (studentId) {
        localStorage.setItem(
          `recommendations-accepted-${studentId}`,
          JSON.stringify(Array.from(acceptedIds))
        );
        localStorage.setItem(
          `recommendations-dismissed-${studentId}`,
          JSON.stringify(Array.from(dismissedIds))
        );
      }
    } catch (error) {
      console.error('Failed to save recommendation state:', error);
    }
  }, [studentId, acceptedIds, dismissedIds]);

  return {
    recommendations: filteredRecommendations,
    loading: !recommendations && !error,
    error: error as Error | null,
    prioritized,
    byType,
    acceptRecommendation,
    dismissRecommendation,
    refetch
  };
};

/**
 * Track recommendation events
 */
function trackRecommendationEvent(action: string, recommendationId: string): void {
  // Implement analytics tracking
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', 'recommendation_action', {
      action,
      recommendation_id: recommendationId
    });
  }
}