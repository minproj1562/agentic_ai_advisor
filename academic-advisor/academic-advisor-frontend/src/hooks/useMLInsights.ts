// src/hooks/useMLInsights.ts
import { useState, useEffect, useCallback } from 'react';
import {
  mlService,
  PredictionResponse,
  WeaknessAnalysisResponse,
  StudentAcademicData,
  SubjectScore
} from '../services/ml.service';
import { useAuth } from '../contexts/AuthContext';

interface UseMLInsightsProps {
  academicData: StudentAcademicData | null;
  historicalScores: Array<{ semester: number; gpa: number; credits: number }>;
  currentSemester: number;
  subjectScores?: SubjectScore[];
  skills?: string[];
  interests?: string[];
  projects?: string[];
}

export const useMLInsights = ({
  academicData,
  historicalScores,
  currentSemester,
  subjectScores = [],
  skills = [],
  interests = [],
  projects = []
}: UseMLInsightsProps) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [weaknessAnalysis, setWeaknessAnalysis] = useState<WeaknessAnalysisResponse | null>(null);
const [careerPredictions, setCareerPredictions] = useState<any>(null);
  const fetchPredictions = useCallback(async () => {
    if (!user?.uid || !academicData) return null;

    try {
      const response = await mlService.getPredictions(
        user.uid,
        academicData,
        historicalScores,
        currentSemester
      );
      setPredictions(response);
      return response;
    } catch (err) {
      console.error('Error fetching predictions:', err);
      throw err;
    }
  }, [user?.uid, academicData, historicalScores, currentSemester]);

  const fetchWeaknessAnalysis = useCallback(async () => {
    if (!user?.uid || subjectScores.length === 0 || !academicData) return null;

    try {
      const response = await mlService.analyzeWeaknesses(
        user.uid,
        subjectScores,
        academicData.current_cgpa
      );
      setWeaknessAnalysis(response);
      return response;
    } catch (err) {
      console.error('Error analyzing weaknesses:', err);
      throw err;
    }
  }, [user?.uid, subjectScores, academicData]);

  const fetchCareerPredictions = useCallback(async () => {
    if (!user?.uid || !academicData) return null;

    try {
      const response = await mlService.predictCareer(
        user.uid,
        skills,
        interests,
        academicData.current_cgpa,
        projects
      );
      setCareerPredictions(response);
      return response;
    } catch (err) {
      console.error('Error predicting careers:', err);
      throw err;
    }
  }, [user?.uid, skills, interests, academicData, projects]);

  const fetchAllInsights = useCallback(async () => {
    if (!academicData) {
      setError('Academic data not available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchPredictions(),
        fetchWeaknessAnalysis(),
        fetchCareerPredictions()
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ML insights');
    } finally {
      setLoading(false);
    }
  }, [fetchPredictions, fetchWeaknessAnalysis, fetchCareerPredictions, academicData]);

  // Auto-fetch when data changes
  useEffect(() => {
    if (academicData && user?.uid) {
      fetchAllInsights();
    }
  }, [academicData, user?.uid]);

  return {
    loading,
    error,
    predictions,
    weaknessAnalysis,
    careerPredictions,
    refetch: fetchAllInsights,
    fetchPredictions,
    fetchWeaknessAnalysis,
    fetchCareerPredictions
  };
};