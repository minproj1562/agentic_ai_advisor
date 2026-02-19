// src/hooks/useEngineeringGuidance.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { engineeringService, InterestProfile } from '../services/engineering.service';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

// ============== STUDENT INTERESTS (NEW) ==============

/**
 * ✅ NEW: Hook to get student interests from the weakness service
 * This ensures we have interests for analysis even if performanceMetrics is empty
 */
export const useStudentInterests = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['student-interests', user?.uid],
    queryFn: async (): Promise<InterestProfile> => {
      if (!user?.uid) {
        return {
          student_id: '',
          interests: [],
          interest_levels: {},
          career_goals: [],
          preferred_electives: [],
          honours_minors_interest: [],
          skills: [],
          skill_levels: {}
        };
      }
      
      try {
        // First try to get the interest profile directly
        const profile = await engineeringService.getInterestProfile(user.uid);
        
        if (profile.interests?.length) {
          console.log('✅ Found interests in profile:', profile.interests);
          return profile;
        }
        
        // If no interests found, try syncing from other sources
        console.log('⚠️ No interests found, attempting sync...');
        const syncResult = await engineeringService.syncInterests(user.uid);
        
        if (syncResult.status === 'success' && syncResult.interests?.length) {
          console.log('✅ Synced interests:', syncResult.interests);
          return {
            student_id: user.uid,
            interests: syncResult.interests,
            interest_levels: {},
            career_goals: syncResult.career_goals || [],
            preferred_electives: [],
            honours_minors_interest: [],
            skills: [],
            skill_levels: {}
          };
        }
        
        console.log('⚠️ No interests found after sync');
        return {
          student_id: user.uid,
          interests: [],
          interest_levels: {},
          career_goals: [],
          preferred_electives: [],
          honours_minors_interest: [],
          skills: [],
          skill_levels: {}
        };
        
      } catch (error) {
        console.error('Error fetching interests:', error);
        return {
          student_id: user?.uid || '',
          interests: [],
          interest_levels: {},
          career_goals: [],
          preferred_electives: [],
          honours_minors_interest: [],
          skills: [],
          skill_levels: {}
        };
      }
    },
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 2,
    retryDelay: 1000
  });
};

// ============== PERFORMANCE METRICS ==============

export const usePerformanceMetrics = () => {
  const { user } = useAuth();
  const { data: interestsData } = useStudentInterests();
  
  return useQuery({
    queryKey: ['performance-metrics', user?.uid, interestsData?.interests?.join(',')],
    queryFn: async () => {
      const metrics = await engineeringService.getPerformanceMetrics(user!.uid);
      
      // ✅ MERGE interests from useStudentInterests if performanceMetrics has none
      if ((!metrics.interests || metrics.interests.length === 0) && interestsData?.interests?.length) {
        console.log('📝 Merging interests from interestsData into metrics');
        metrics.interests = interestsData.interests;
      }
      if ((!metrics.careerGoals || metrics.careerGoals.length === 0) && interestsData?.career_goals?.length) {
        metrics.careerGoals = interestsData.career_goals;
      }
      
      return metrics;
    },
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: true,
    retry: 2,
    retryDelay: 1000,
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
      interests: interestsData?.interests || [],
      careerGoals: interestsData?.career_goals || [],
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
    placeholderData: engineeringService.getDefaultElectives()
  });
};

// ============== WEAKNESS ANALYSIS (ENHANCED) ==============

/**
 * ✅ ENHANCED: Now uses interests from useStudentInterests as fallback
 * and calls the proper combined endpoint when we have parameters
 */
export const useWeaknessAnalysis = (params?: {
  interests?: string[];
  electives?: string[];
  honours?: string[];
}) => {
  const { user } = useAuth();
  const { data: interestsData } = useStudentInterests();
  
  // ✅ MERGE passed params with fetched interests
  const effectiveInterests = params?.interests?.length 
    ? params.interests 
    : (interestsData?.interests || []);
  
  const effectiveElectives = params?.electives?.length 
    ? params.electives 
    : (interestsData?.preferred_electives || []);
  
  const effectiveHonours = params?.honours?.length 
    ? params.honours 
    : (interestsData?.honours_minors_interest || []);
  
  return useQuery({
    queryKey: [
      'weakness-analysis',
      user?.uid,
      effectiveInterests.join(','),
      effectiveElectives.join(','),
      effectiveHonours.join(','),
    ],
    queryFn: async () => {
      console.log('🔍 Fetching weakness analysis with:', {
        interests: effectiveInterests,
        electives: effectiveElectives,
        honours: effectiveHonours
      });
      
      // If we have any parameters, use the combined endpoint
      if (
        effectiveInterests.length ||
        effectiveElectives.length ||
        effectiveHonours.length
      ) {
        return engineeringService.getCombinedWeaknessAnalysis(
          user!.uid,
          effectiveInterests.length ? effectiveInterests : undefined,
          effectiveElectives.length ? effectiveElectives : undefined,
          effectiveHonours.length ? effectiveHonours : undefined
        );
      }
      
      // Otherwise use the legacy endpoint which does combined analysis
      return engineeringService.getWeaknessAnalysis(user!.uid);
    },
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
    retry: 2,
    retryDelay: 1000,
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

// ============== SYNC INTERESTS MUTATION (NEW) ==============

/**
 * ✅ NEW: Hook to sync interests from all sources
 */
export const useSyncInterests = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (source?: 'profile' | 'performance' | 'all') => 
      source 
        ? engineeringService.forceSyncInterests(user!.uid, source)
        : engineeringService.syncInterests(user!.uid),
    onSuccess: (data) => {
      if (data.status === 'success' && data.interests?.length) {
        toast.success(`Synced ${data.interests.length} interests!`);
        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: ['student-interests', user?.uid] });
        queryClient.invalidateQueries({ queryKey: ['performance-metrics', user?.uid] });
        queryClient.invalidateQueries({ queryKey: ['weakness-analysis', user?.uid] });
      } else if (data.status === 'no_interests') {
        toast('No interests found. Please set your interests manually.', {
          icon: 'ℹ️'
        });
      }
    },
    onError: (error) => {
      console.error('Interest sync failed:', error);
      toast.error('Failed to sync interests');
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
      }),
      queryClient.prefetchQuery({
        queryKey: ['student-interests', user.uid],
        queryFn: () => engineeringService.getInterestProfile(user.uid),
        staleTime: 5 * 60 * 1000
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
        queryClient.invalidateQueries({ queryKey: ['student-interests', user.uid] }),
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
  useStudentInterests,
  usePerformanceMetrics,
  useElectiveRecommendations,
  useWeaknessAnalysis,
  useStudyResources,
  useBookmarkedResources,
  useToggleBookmark,
  useUpdateProgress,
  useTrackActivity,
  useSyncInterests,
  useSubjectResources,
  useResourcesByType,
  usePrefetchResources,
  useRefreshGuidanceData
};