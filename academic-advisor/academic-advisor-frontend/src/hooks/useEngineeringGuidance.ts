// src/hooks/useEngineeringGuidance.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { engineeringService } from '../services/engineering.service';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

// ============== PERFORMANCE METRICS ==============

export const usePerformanceMetrics = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['performance-metrics', user?.uid],
    queryFn: () => engineeringService.getPerformanceMetrics(user!.uid),
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: true,
    retry: 2,
    retryDelay: 1000,
    // Provide placeholder data while loading
    placeholderData: {
      studentInfo: {
        uid: user?.uid || '',
        semester: '6',
        year: '3rd Year',
        branch: 'IT',
        roll_number: ''
      },
      subjects: [],
      overallCGPA: 0,
      semesterSGPA: 0,
      strongSubjects: [],
      weakSubjects: [],
      completedCredits: 0,
      totalCredits: 160,
      interests: [],
      careerGoals: [],
      skillsMatrix: {}
    }
  });
};

// ============== ELECTIVE RECOMMENDATIONS ==============

export const useElectiveRecommendations = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['elective-recommendations', user?.uid],
    queryFn: async () => {
      const result = await engineeringService.getElectiveRecommendations(user!.uid);
      // Ensure we always return an array
      if (Array.isArray(result)) return result;
      if (result && typeof result === 'object' && 'recommendations' in result) {
        return (result as any).recommendations || [];
      }
      return engineeringService.getDefaultElectives();
    },
    enabled: !!user?.uid,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    retry: 2,
    retryDelay: 1000,
    // Use default electives as placeholder
    placeholderData: engineeringService.getDefaultElectives()
  });
};

// ============== WEAKNESS ANALYSIS ==============

export const useWeaknessAnalysis = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['weakness-analysis', user?.uid],
    queryFn: () => engineeringService.getWeaknessAnalysis(user!.uid),
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
    retry: 2,
    retryDelay: 1000,
    // Provide empty weakness data as placeholder
    placeholderData: {
      weaknesses: [],
      overall_risk_score: 0,
      priority_areas: [],
      total_weaknesses: 0,
      critical_count: 0,
      high_count: 0,
      medium_count: 0,
      low_count: 0,
      key_insights: [],
      from_cache: false
    }
  });
};

// ============== STUDY RESOURCES ==============

export const useStudyResources = (filters?: {
  type?: string;
  difficulty?: string;
  topic?: string;
  subject?: string;
}) => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['study-resources', user?.uid, filters],
    queryFn: async () => {
      const result = await engineeringService.getStudyResources(user!.uid, filters);
      // Ensure we always return an array
      if (Array.isArray(result)) return result;
      if (result && typeof result === 'object' && 'resources' in result) {
        return (result as any).resources || [];
      }
      return engineeringService.getDefaultResources();
    },
    enabled: !!user?.uid,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    retry: 2,
    retryDelay: 1000,
    // Use default resources as placeholder
    placeholderData: engineeringService.getDefaultResources()
  });
};

// ============== BOOKMARKED RESOURCES ==============

export const useBookmarkedResources = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['bookmarked-resources', user?.uid],
    queryFn: async () => {
      const result = await engineeringService.getBookmarkedResources(user!.uid);
      return Array.isArray(result) ? result : [];
    },
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
    retry: 1,
    placeholderData: []
  });
};

// ============== TOGGLE BOOKMARK MUTATION ==============

export const useToggleBookmark = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (resourceId: string) => 
      engineeringService.toggleBookmark(user!.uid, resourceId),
    onMutate: async (resourceId) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['study-resources', user?.uid] });
      
      const previousResources = queryClient.getQueryData(['study-resources', user?.uid]);
      
      // Optimistically update the resource's bookmark status
      queryClient.setQueryData(['study-resources', user?.uid], (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((resource: any) => 
          resource.id === resourceId 
            ? { ...resource, isBookmarked: !resource.isBookmarked }
            : resource
        );
      });
      
      return { previousResources };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['study-resources', user?.uid] });
      queryClient.invalidateQueries({ queryKey: ['bookmarked-resources', user?.uid] });
      toast.success('Bookmark updated!');
    },
    onError: (err, resourceId, context) => {
      // Rollback on error
      if (context?.previousResources) {
        queryClient.setQueryData(['study-resources', user?.uid], context.previousResources);
      }
      toast.error('Failed to update bookmark');
    }
  });
};

// ============== UPDATE PROGRESS MUTATION ==============

export const useUpdateProgress = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ resourceId, progress }: { resourceId: string; progress: number }) =>
      engineeringService.updateResourceProgress(user!.uid, resourceId, progress),
    onMutate: async ({ resourceId, progress }) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['study-resources', user?.uid] });
      
      const previousResources = queryClient.getQueryData(['study-resources', user?.uid]);
      
      queryClient.setQueryData(['study-resources', user?.uid], (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((resource: any) => 
          resource.id === resourceId 
            ? { ...resource, completionStatus: progress }
            : resource
        );
      });
      
      return { previousResources };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['study-resources', user?.uid] });
      toast.success('Progress updated!');
    },
    onError: (err, variables, context) => {
      if (context?.previousResources) {
        queryClient.setQueryData(['study-resources', user?.uid], context.previousResources);
      }
      toast.error('Failed to update progress');
    }
  });
};

// ============== TRACK ACTIVITY MUTATION ==============

export const useTrackActivity = () => {
  const { user } = useAuth();
  
  return useMutation({
    mutationFn: (activityData: {
      type: 'resource_viewed' | 'topic_completed' | 'quiz_taken';
      resourceId?: string;
      topicId?: string;
      score?: number;
      timeSpent?: number;
    }) => engineeringService.trackActivity(user!.uid, activityData),
    // Silent failure - don't show errors for activity tracking
    onError: (error) => {
      console.warn('Activity tracking failed:', error);
    }
  });
};

// ============== ADDITIONAL UTILITY HOOKS ==============

/**
 * Hook to get resources for a specific subject
 */
export const useSubjectResources = (subject: string) => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['subject-resources', user?.uid, subject],
    queryFn: () => engineeringService.getStudyResources(user!.uid, { subject }),
    enabled: !!user?.uid && !!subject,
    staleTime: 10 * 60 * 1000,
    placeholderData: []
  });
};

/**
 * Hook to get resources by type
 */
export const useResourcesByType = (type: string) => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['resources-by-type', user?.uid, type],
    queryFn: () => engineeringService.getStudyResources(user!.uid, { type }),
    enabled: !!user?.uid && !!type,
    staleTime: 10 * 60 * 1000,
    placeholderData: []
  });
};

/**
 * Hook to prefetch resources (useful for preloading)
 */
export const usePrefetchResources = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const prefetch = async () => {
    if (!user?.uid) return;
    
    await Promise.all([
      queryClient.prefetchQuery({
        queryKey: ['study-resources', user.uid],
        queryFn: () => engineeringService.getStudyResources(user.uid),
        staleTime: 10 * 60 * 1000
      }),
      queryClient.prefetchQuery({
        queryKey: ['elective-recommendations', user.uid],
        queryFn: () => engineeringService.getElectiveRecommendations(user.uid),
        staleTime: 10 * 60 * 1000
      })
    ]);
  };
  
  return { prefetch };
};

/**
 * Hook to refresh all engineering guidance data
 */
export const useRefreshGuidanceData = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const refresh = async () => {
    if (!user?.uid) return;
    
    toast.loading('Refreshing data...', { id: 'refresh' });
    
    try {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['study-resources', user.uid] }),
        queryClient.invalidateQueries({ queryKey: ['elective-recommendations', user.uid] }),
        queryClient.invalidateQueries({ queryKey: ['weakness-analysis', user.uid] }),
        queryClient.invalidateQueries({ queryKey: ['performance-metrics', user.uid] }),
        queryClient.invalidateQueries({ queryKey: ['bookmarked-resources', user.uid] })
      ]);
      
      toast.success('Data refreshed!', { id: 'refresh' });
    } catch (error) {
      toast.error('Failed to refresh data', { id: 'refresh' });
    }
  };
  
  return { refresh };
};

// ============== DEFAULT EXPORT ==============

export default {
  usePerformanceMetrics,
  useElectiveRecommendations,
  useWeaknessAnalysis,
  useStudyResources,
  useBookmarkedResources,
  useToggleBookmark,
  useUpdateProgress,
  useTrackActivity,
  useSubjectResources,
  useResourcesByType,
  usePrefetchResources,
  useRefreshGuidanceData
};