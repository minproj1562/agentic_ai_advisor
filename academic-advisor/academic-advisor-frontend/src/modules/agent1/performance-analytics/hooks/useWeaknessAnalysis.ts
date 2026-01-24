// src/modules/agent1/performance-analytics/hooks/useWeaknessAnalysis.ts
import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  getWeaknessService, 
  WeaknessAnalysisResponse, 
  WeaknessSummary,
  AnalysisBasis,
  SeverityLevel 
} from '../../../../services/weakness.service';
import toast from 'react-hot-toast';

interface UseWeaknessAnalysisOptions {
  analysisBasis?: AnalysisBasis;
  autoLoad?: boolean;
  interests?: string[];
  electives?: string[];
  honours?: string[];
  includeResources?: boolean;
  includeStudyPlan?: boolean;
}

interface UseWeaknessAnalysisReturn {
  // Data
  weaknessData: WeaknessAnalysisResponse | null;
  summary: WeaknessSummary | null;
  
  // State
  loading: boolean;
  error: string | null;
  analyzing: boolean;
  
  // Methods
  analyzeByInterest: (interests?: string[]) => Promise<void>;
  analyzeByElectives: (electives?: string[]) => Promise<void>;
  analyzeByHonours: (honours?: string[]) => Promise<void>;
  analyzeByPerformance: () => Promise<void>;
  analyzeCombined: (interests?: string[], electives?: string[], honours?: string[]) => Promise<void>;
  refreshAnalysis: () => Promise<void>;
  loadSummary: () => Promise<void>;
  clearError: () => void;
}

export const useWeaknessAnalysis = (
  studentId: string,
  options: UseWeaknessAnalysisOptions = {}
): UseWeaknessAnalysisReturn => {
  const {
    analysisBasis = 'combined',
    autoLoad = true,
    interests = [],
    electives = [],
    honours = [],
    includeResources = true,
    includeStudyPlan = true
  } = options;

  const [weaknessData, setWeaknessData] = useState<WeaknessAnalysisResponse | null>(null);
  const [summary, setSummary] = useState<WeaknessSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const service = useMemo(() => getWeaknessService(), []);

  // Load cached data on mount
  useEffect(() => {
    if (autoLoad && studentId) {
      loadCachedData();
      loadSummary();
    }
  }, [studentId, autoLoad]);

  const loadCachedData = async () => {
    try {
      setLoading(true);
      setError(null);
      const cached = await service.getLatestAnalysis(studentId);
      if (cached) {
        setWeaknessData(cached as WeaknessAnalysisResponse);
      }
    } catch (err: any) {
      console.log('No cached analysis found');
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const summaryData = await service.getWeaknessSummary(studentId);
      setSummary(summaryData);
    } catch (err: any) {
      console.error('Failed to load summary:', err);
    }
  };

  const analyzeByInterest = useCallback(async (interestList?: string[]) => {
    try {
      setAnalyzing(true);
      setError(null);
      
      const interestsToUse = interestList || interests;
      
      const result = await service.getWeaknessByInterest(
        studentId,
        interestsToUse,
        includeResources,
        includeStudyPlan
      );
      
      setWeaknessData(result);
      await loadSummary();
      
      toast.success('Weakness analysis complete!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to analyze weaknesses by interest';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setAnalyzing(false);
    }
  }, [studentId, interests, includeResources, includeStudyPlan]);

  const analyzeByElectives = useCallback(async (electiveList?: string[]) => {
    try {
      setAnalyzing(true);
      setError(null);
      
      const electivesToUse = electiveList || electives;
      
      const result = await service.getWeaknessByElectives(
        studentId,
        electivesToUse,
        includeResources,
        includeStudyPlan
      );
      
      setWeaknessData(result);
      await loadSummary();
      
      toast.success('Elective readiness analysis complete!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to analyze weaknesses by electives';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setAnalyzing(false);
    }
  }, [studentId, electives, includeResources, includeStudyPlan]);

  const analyzeByHonours = useCallback(async (honoursList?: string[]) => {
    try {
      setAnalyzing(true);
      setError(null);
      
      const honoursToUse = honoursList || honours;
      
      const result = await service.getWeaknessByHonours(
        studentId,
        honoursToUse,
        includeResources,
        includeStudyPlan
      );
      
      setWeaknessData(result);
      await loadSummary();
      
      toast.success('Honours/Minors readiness analysis complete!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to analyze weaknesses by honours';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setAnalyzing(false);
    }
  }, [studentId, honours, includeResources, includeStudyPlan]);

  const analyzeByPerformance = useCallback(async () => {
    try {
      setAnalyzing(true);
      setError(null);
      
      const result = await service.getWeaknessByPerformance(
        studentId,
        includeResources,
        includeStudyPlan
      );
      
      setWeaknessData(result);
      await loadSummary();
      
      toast.success('Performance analysis complete!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to analyze performance weaknesses';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setAnalyzing(false);
    }
  }, [studentId, includeResources, includeStudyPlan]);

  const analyzeCombined = useCallback(async (
    interestList?: string[],
    electiveList?: string[],
    honoursList?: string[]
  ) => {
    try {
      setAnalyzing(true);
      setError(null);
      
      const result = await service.getCombinedAnalysis(
        studentId,
        interestList || interests,
        electiveList || electives,
        honoursList || honours,
        includeResources,
        includeStudyPlan
      );
      
      setWeaknessData(result);
      await loadSummary();
      
      toast.success('Comprehensive analysis complete!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to perform combined analysis';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setAnalyzing(false);
    }
  }, [studentId, interests, electives, honours, includeResources, includeStudyPlan]);

  const refreshAnalysis = useCallback(async () => {
    switch (analysisBasis) {
      case 'interest':
        await analyzeByInterest();
        break;
      case 'electives':
        await analyzeByElectives();
        break;
      case 'honours_minors':
        await analyzeByHonours();
        break;
      case 'performance':
        await analyzeByPerformance();
        break;
      case 'combined':
      default:
        await analyzeCombined();
        break;
    }
  }, [analysisBasis, analyzeByInterest, analyzeByElectives, analyzeByHonours, analyzeByPerformance, analyzeCombined]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    weaknessData,
    summary,
    loading,
    error,
    analyzing,
    analyzeByInterest,
    analyzeByElectives,
    analyzeByHonours,
    analyzeByPerformance,
    analyzeCombined,
    refreshAnalysis,
    loadSummary,
    clearError
  };
};

export default useWeaknessAnalysis;