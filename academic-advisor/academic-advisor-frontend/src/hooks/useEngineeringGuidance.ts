// src/hooks/useEngineeringGuidance.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { engineeringService } from '../services/engineering.service';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

export const usePerformanceMetrics = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['performance-metrics', user?.uid],
    queryFn: () => engineeringService.getPerformanceMetrics(user!.uid),
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (replaced cacheTime)
    refetchOnWindowFocus: true,
  });
};

export const useElectiveRecommendations = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['elective-recommendations', user?.uid],
    queryFn: () => engineeringService.getElectiveRecommendations(user!.uid),
    enabled: !!user?.uid,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000, // replaced cacheTime
  });
};

export const useWeaknessAnalysis = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['weakness-analysis', user?.uid],
    queryFn: () => engineeringService.getWeaknessAnalysis(user!.uid),
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
  });
};

export const useStudyResources = (filters?: any) => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['study-resources', user?.uid, filters],
    queryFn: () => engineeringService.getStudyResources(user!.uid, filters),
    enabled: !!user?.uid,
    staleTime: 10 * 60 * 1000,
  });
};

export const useBookmarkedResources = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['bookmarked-resources', user?.uid],
    queryFn: () => engineeringService.getBookmarkedResources(user!.uid),
    enabled: !!user?.uid,
  });
};

export const useToggleBookmark = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (resourceId: string) => 
      engineeringService.toggleBookmark(user!.uid, resourceId),
    onSuccess: () => {
      // Fixed query invalidation for TanStack Query v5
      queryClient.invalidateQueries({ 
        queryKey: ['study-resources', user?.uid] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['bookmarked-resources', user?.uid] 
      });
      toast.success('Bookmark updated');
    },
    onError: () => {
      toast.error('Failed to update bookmark');
    }
  });
};

export const useUpdateProgress = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ resourceId, progress }: { resourceId: string; progress: number }) =>
      engineeringService.updateResourceProgress(user!.uid, resourceId, progress),
    onSuccess: () => {
      queryClient.invalidateQueries({ 
        queryKey: ['study-resources', user?.uid] 
      });
    }
  });
};

export const useTrackActivity = () => {
  const { user } = useAuth();
  
  return useMutation({
    mutationFn: (activityData: any) =>
      engineeringService.trackActivity(user!.uid, activityData),
  });
};