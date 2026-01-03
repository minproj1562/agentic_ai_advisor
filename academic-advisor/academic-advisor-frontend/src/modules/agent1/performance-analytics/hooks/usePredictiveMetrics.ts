// modules/agent1/performance-analytics/hooks/usePredictiveMetrics.ts
import { useState, useEffect, useCallback, useMemo } from 'react';
import useSWR from 'swr';
import { PredictiveMetrics, PredictionConfig, TimeSeriesData } from '../types/analytics.types';
import { predictionService } from '../services/prediction.service';
import { usePerformanceTrends } from './usePerformanceTrends';
import { CACHE_KEYS, REFRESH_INTERVALS } from '../constants/thresholds';

// Add missing constants locally
const PREDICTION_MODELS = {
  LINEAR: 'linear',
  POLYNOMIAL: 'polynomial', 
  EXPONENTIAL: 'exponential',
  ML: 'ml'
} as const;

const CONFIDENCE_THRESHOLDS = {
  LOW: 0.6,
  DEFAULT: 0.8,
  HIGH: 0.95
} as const;

interface UsePredictiveMetricsOptions {
  modelType?: 'linear' | 'polynomial' | 'exponential' | 'ml';
  horizonDays?: number;
  confidenceLevel?: number;
  includeSeasonality?: boolean;
  includeExternalFactors?: boolean;
  customFeatures?: string[];
}

interface UsePredictiveMetricsReturn {
  predictions: PredictiveMetrics | null;
  loading: boolean;
  error: Error | null;
  confidence: number;
  updatePrediction: (config: Partial<PredictionConfig>) => Promise<void>;
  scenarios: ScenarioAnalysis[];
  recommendations: PredictionRecommendation[];
}

interface ScenarioAnalysis {
  name: string;
  probability: number;
  impact: 'positive' | 'negative' | 'neutral';
  projectedGPA: number;
  requiredActions: string[];
}

interface PredictionRecommendation {
  priority: 'high' | 'medium' | 'low';
  action: string;
  expectedImprovement: number;
  timeframe: string;
}

export const usePredictiveMetrics = (
  studentId: string,
  options: UsePredictiveMetricsOptions = {}
): UsePredictiveMetricsReturn => {
  const {
    modelType = 'ml',
    horizonDays = 90,
    confidenceLevel = CONFIDENCE_THRESHOLDS.DEFAULT,
    includeSeasonality = true,
    includeExternalFactors = true,
    customFeatures = []
  } = options;

  const [localPredictions, setLocalPredictions] = useState<PredictiveMetrics | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioAnalysis[]>([]);
  const [recommendations, setRecommendations] = useState<PredictionRecommendation[]>([]);

  const { trends } = usePerformanceTrends(studentId, {
    enablePrediction: false // We'll handle predictions here
  });

  // Fetcher for predictions
  const fetcher = useCallback(async (key: string) => {
    if (!trends || !trends.dataPoints) {
      throw new Error('No historical data available for predictions');
    }

    try {
      // Prepare prediction configuration
      const config: PredictionConfig = {
        modelType,
        horizonDays,
        confidenceLevel,
        includeSeasonality,
        includeExternalFactors,
        customFeatures,
        historicalData: trends.dataPoints
      };

      // Generate predictions
      const predictions = await predictionService.generatePredictions(config);

      // Generate scenario analysis
      const scenarioResults = generateScenarios(predictions, trends);
      setScenarios(scenarioResults);

      // Generate recommendations
      const recs = generateRecommendations(predictions, trends);
      setRecommendations(recs);

      return predictions;
    } catch (error) {
      console.error('Prediction generation failed:', error);
      throw error;
    }
  }, [trends, modelType, horizonDays, confidenceLevel, includeSeasonality, includeExternalFactors, customFeatures]);

  // SWR for prediction data
  const {
    data: predictions,
    error,
    mutate,
    isValidating
  } = useSWR(
    trends ? `predictions-${studentId}-${JSON.stringify(options)}` : null,
    fetcher,
    {
      refreshInterval: 3600000, // Refresh every hour
      revalidateOnFocus: false,
      dedupingInterval: 300000 // 5 minutes
    }
  );

  // Calculate confidence score
  const confidence = useMemo(() => {
    if (!predictions) return 0;

    const factors = {
      dataQuality: calculateDataQuality(trends),
      modelAccuracy: predictions.modelAccuracy || 0,
      dataPoints: Math.min(trends?.dataPoints?.length || 0, 100) / 100,
      recentness: calculateRecentness(predictions.generatedAt)
    };

    return Object.values(factors).reduce((acc, val) => acc + val, 0) / Object.keys(factors).length;
  }, [predictions, trends]);

  // Update prediction with new configuration
  const updatePrediction = useCallback(async (config: Partial<PredictionConfig>) => {
    try {
      const updatedConfig = {
        modelType,
        horizonDays,
        confidenceLevel,
        includeSeasonality,
        includeExternalFactors,
        customFeatures,
        ...config,
        historicalData: trends?.dataPoints || []
      };

      const newPredictions = await predictionService.generatePredictions(updatedConfig);
      setLocalPredictions(newPredictions);
      await mutate(newPredictions, false);
    } catch (error) {
      console.error('Failed to update predictions:', error);
      throw error;
    }
  }, [trends, modelType, horizonDays, confidenceLevel, includeSeasonality, includeExternalFactors, customFeatures, mutate]);

  // Advanced prediction features
  useEffect(() => {
    if (predictions && modelType === 'ml') {
      // Enable ML-specific features
      enhancePredictionsWithML(predictions, trends);
    }
  }, [predictions, modelType, trends]);

  return {
    predictions: predictions || localPredictions,
    loading: !predictions && !error,
    error,
    confidence,
    updatePrediction,
    scenarios,
    recommendations
  };
};

// Helper functions - FIXED: Removed async from non-async functions
function generateScenarios(
  predictions: PredictiveMetrics,
  trends: any
): ScenarioAnalysis[] {
  const scenarios: ScenarioAnalysis[] = [
    {
      name: 'Best Case Scenario',
      probability: calculateScenarioProbability(predictions, 'best'),
      impact: 'positive',
      projectedGPA: predictions.bestCase?.gpa || 4.0,
      requiredActions: [
        'Maintain current study schedule',
        'Complete all assignments on time',
        'Attend all classes',
        'Seek help for difficult topics early'
      ]
    },
    {
      name: 'Most Likely Scenario',
      probability: calculateScenarioProbability(predictions, 'likely'),
      impact: 'neutral',
      projectedGPA: predictions.mostLikely?.gpa || trends?.currentGPA || 3.0,
      requiredActions: [
        'Continue current efforts',
        'Focus on weak subjects',
        'Maintain consistent study habits'
      ]
    },
    {
      name: 'Worst Case Scenario',
      probability: calculateScenarioProbability(predictions, 'worst'),
      impact: 'negative',
      projectedGPA: predictions.worstCase?.gpa || 2.0,
      requiredActions: [
        'Immediate intervention required',
        'Schedule tutoring sessions',
        'Review study methods',
        'Consider reducing course load'
      ]
    }
  ];

  return scenarios;
}

function generateRecommendations(
  predictions: PredictiveMetrics,
  trends: any
): PredictionRecommendation[] {
  const recommendations: PredictionRecommendation[] = [];

  // Analyze prediction trends
  if (predictions.trend === 'declining') {
    recommendations.push({
      priority: 'high',
      action: 'Schedule immediate academic counseling',
      expectedImprovement: 0.3,
      timeframe: 'Within 1 week'
    });

    recommendations.push({
      priority: 'high',
      action: 'Identify and address weak subjects',
      expectedImprovement: 0.5,
      timeframe: 'Next 2 weeks'
    });
  }

  if (predictions.weakAreas && predictions.weakAreas.length > 0) {
    predictions.weakAreas.forEach((area: any) => {
      recommendations.push({
        priority: 'medium',
        action: `Focus on improving ${area.subject}`,
        expectedImprovement: area.potentialImprovement || 0.2,
        timeframe: 'Next month'
      });
    });
  }

  // Add study recommendations - FIXED: Added null check
  if (predictions.studyHoursNeeded && predictions.studyHoursNeeded > (trends?.currentStudyHours || 0)) {
    recommendations.push({
      priority: 'medium',
      action: `Increase study hours to ${predictions.studyHoursNeeded} per week`,
      expectedImprovement: 0.4,
      timeframe: 'Starting immediately'
    });
  }

  return recommendations.sort((a, b) => {
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });
}

function calculateScenarioProbability(predictions: PredictiveMetrics, scenario: 'best' | 'likely' | 'worst'): number {
  // Implement probability calculation based on confidence intervals
  const baseProb = {
    best: 0.15,
    likely: 0.70,
    worst: 0.15
  };

  // Adjust based on prediction confidence - FIXED: Proper indexing
  const confidenceAdjustment = predictions.confidence || 0.5;
  return baseProb[scenario] * confidenceAdjustment;
}

function calculateDataQuality(trends: any): number {
  if (!trends || !trends.dataPoints) return 0;
  
  const factors = {
    quantity: Math.min(trends.dataPoints.length / 50, 1),
    completeness: trends.dataPoints.filter((d: any) => d.gpa !== null).length / trends.dataPoints.length,
    recency: trends.lastUpdated ? calculateRecentness(trends.lastUpdated) : 0
  };
  
  return Object.values(factors).reduce((acc, val) => acc + val, 0) / Object.keys(factors).length;
}

function calculateRecentness(date: string): number {
  const daysOld = (Date.now() - new Date(date).getTime()) / (1000 * 60 * 60 * 24);
  return Math.max(0, 1 - (daysOld / 30));
}

function enhancePredictionsWithML(predictions: PredictiveMetrics, trends: any): void {
  // Implement ML-specific enhancements
  // This could include feature importance, model explanations, etc.
  console.log('Enhancing predictions with ML features');
}