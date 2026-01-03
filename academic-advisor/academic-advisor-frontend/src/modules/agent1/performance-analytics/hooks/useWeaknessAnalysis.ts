// modules/agent1/performance-analytics/hooks/useWeaknessAnalysis.ts
import { useState, useEffect, useCallback, useMemo } from 'react';
import useSWR from 'swr';
import { WeaknessAnalysis, WeakArea, ImprovementPlan } from '../types/analytics.types';
import { analyticsService } from '../services/analytics.service';
import { usePerformanceTrends } from './usePerformanceTrends';

// Add missing constants locally
const WEAKNESS_THRESHOLDS = {
  DEFAULT: 60,
  STRICT: 70,
  LENIENT: 50
} as const;

const IMPROVEMENT_STRATEGIES = {
  critical: {
    actions: [
      "Schedule immediate tutoring sessions",
      "Meet with professor during office hours", 
      "Form or join a study group",
      "Review fundamental concepts",
      "Complete all practice problems"
    ],
    resources: ["Tutoring Center", "Office Hours", "Study Groups", "Textbook Examples"],
    baseEffort: 10
  },
  high: {
    actions: [
      "Attend all classes and take detailed notes",
      "Complete assignments 2 days before deadline",
      "Review material weekly",
      "Practice with past exams"
    ],
    resources: ["Class Notes", "Assignment Solutions", "Past Exams"],
    baseEffort: 8
  },
  medium: {
    actions: [
      "Regular homework completion",
      "Weekly review sessions", 
      "Form study groups",
      "Seek clarification on difficult topics"
    ],
    resources: ["Homework Solutions", "Study Guides", "Online Resources"],
    baseEffort: 6
  },
  low: {
    actions: [
      "Maintain current study habits",
      "Occasional review sessions",
      "Complete all assignments on time"
    ],
    resources: ["Textbook", "Class Materials"],
    baseEffort: 4
  }
} as const;

interface UseWeaknessAnalysisOptions {
  threshold?: number;
  includeRecommendations?: boolean;
  includePeerComparison?: boolean;
  timeframe?: 'current' | 'semester' | 'year';
  priorityWeighting?: {
    credits: number;
    impact: number;
    difficulty: number;
  };
}

interface UseWeaknessAnalysisReturn {
  weaknesses: WeaknessAnalysis | null;
  loading: boolean;
  error: Error | null;
  prioritizedAreas: WeakArea[];
  improvementPlans: ImprovementPlan[];
  updateAnalysis: () => Promise<void>;
  getAreaDetails: (areaId: string) => WeakArea | null;
  trackImprovement: (areaId: string, progress: number) => Promise<void>;
}

export const useWeaknessAnalysis = (
  studentId: string,
  options: UseWeaknessAnalysisOptions = {}
): UseWeaknessAnalysisReturn => {
  const {
    threshold = WEAKNESS_THRESHOLDS.DEFAULT,
    includeRecommendations = true,
    includePeerComparison = true,
    timeframe = 'semester',
    priorityWeighting = {
      credits: 0.3,
      impact: 0.5,
      difficulty: 0.2
    }
  } = options;

  const [improvementPlans, setImprovementPlans] = useState<ImprovementPlan[]>([]);
  const [trackedProgress, setTrackedProgress] = useState<Map<string, number>>(new Map());

  const { trends } = usePerformanceTrends(studentId);

  // Fetcher for weakness analysis
  const fetcher = useCallback(async (key: string) => {
    if (!trends) return null;

    try {
  // Mock implementation - replace with actual service call
  const analysis: WeaknessAnalysis = {
    weakAreas: trends.subjects?.filter((subject: any) => 
      subject.currentGrade < threshold
    ).map((subject: any, index: number) => {
      // Create a complete WeakArea object first
      const weakAreaData = {
        id: `weak-${subject.id}-${index}`,
        name: subject.name,
        currentScore: subject.currentGrade,
        targetScore: Math.min(subject.currentGrade + 15, 85),
        classAverage: subject.classAverage,
        credits: subject.credits,
        impactOnGPA: calculateGPAImpact(subject),
        difficulty: calculateDifficulty(subject),
        severity: calculateSeverityFromScore(subject.currentGrade),
        estimatedImprovementTime: '4-6 weeks',
        potentialImprovement: 15,
        subject: subject.name
      };
      
      // Now calculate priority using the complete data
      return {
        ...weakAreaData,
        priority: calculatePriorityScore(weakAreaData, priorityWeighting)
      };
    }) || [],
    overallWeaknessScore: calculateOverallWeaknessScore(trends, threshold),
    recommendations: [
      'Focus on subjects below passing threshold',
      'Utilize available academic resources',
      'Create structured study schedule'
    ],
    improvementPotential: 0.3,
    priorityOrder: trends.subjects?.filter((s: any) => s.currentGrade < threshold)
      .map((s: any) => s.id) || []
  };
      // Generate improvement plans
      if (includeRecommendations && analysis.weakAreas) {
        const plans = generateImprovementPlans(
          analysis.weakAreas,
          trends,
          priorityWeighting
        );
        setImprovementPlans(plans);
      }

      return analysis;
    } catch (error) {
      console.error('Weakness analysis failed:', error);
      throw error;
    }
  }, [studentId, trends, threshold, includeRecommendations, includePeerComparison, timeframe, priorityWeighting]);

  const {
    data: weaknesses,
    error,
    mutate,
    isValidating
  } = useSWR(
    trends ? `weakness-analysis-${studentId}-${JSON.stringify(options)}` : null,
    fetcher,
    {
      refreshInterval: 1800000, // 30 minutes
      revalidateOnFocus: true
    }
  );

  // Prioritize weak areas based on multiple factors
  const prioritizedAreas = useMemo(() => {
    if (!weaknesses?.weakAreas) return [];

    return [...weaknesses.weakAreas].sort((a, b) => {
      const scoreA = calculatePriorityScore(a, priorityWeighting);
      const scoreB = calculatePriorityScore(b, priorityWeighting);
      return scoreB - scoreA;
    });
  }, [weaknesses, priorityWeighting]);

  // Get details for a specific area
  const getAreaDetails = useCallback((areaId: string): WeakArea | null => {
    return weaknesses?.weakAreas?.find(area => area.id === areaId) || null;
  }, [weaknesses]);

  // Update analysis
  const updateAnalysis = useCallback(async () => {
    try {
      await mutate();
    } catch (error) {
      console.error('Failed to update weakness analysis:', error);
      throw error;
    }
  }, [mutate]);

  // Track improvement progress
  const trackImprovement = useCallback(async (areaId: string, progress: number) => {
    try {
      // Update local tracking
      setTrackedProgress(prev => new Map(prev).set(areaId, progress));

      // Mock implementation - replace with actual service call
      console.log('Tracking improvement:', { studentId, areaId, progress });

      // Trigger reanalysis if significant progress
      if (progress > 20) {
        await updateAnalysis();
      }
    } catch (error) {
      console.error('Failed to track improvement:', error);
      throw error;
    }
  }, [studentId, updateAnalysis]);

  // Auto-generate insights
  useEffect(() => {
    if (weaknesses && weaknesses.weakAreas.length > 0) {
      generateAutoInsights(weaknesses, trends);
    }
  }, [weaknesses, trends]);

  // FIXED: Return proper types to match the interface
  return {
    weaknesses: weaknesses || null, // Ensure it's never undefined
    loading: !weaknesses && !error,
    error,
    prioritizedAreas,
    improvementPlans,
    updateAnalysis,
    getAreaDetails,
    trackImprovement
  };
};

// Helper functions
function calculatePriorityScore(
  area: WeakArea,
  weighting: { credits: number; impact: number; difficulty: number }
): number {
  const creditScore = (area.credits || 0) * weighting.credits;
  const impactScore = (area.impactOnGPA || 0) * weighting.impact;
  const difficultyScore = (1 - (area.difficulty || 0.5)) * weighting.difficulty;
  
  return creditScore + impactScore + difficultyScore;
}

function generateImprovementPlans(
  weakAreas: WeakArea[],
  trends: any,
  priorityWeighting: any
): ImprovementPlan[] {
  const plans: ImprovementPlan[] = [];

  for (const area of weakAreas) {
    const strategy = selectImprovementStrategy(area, trends);
    
    plans.push({
      areaId: area.id,
      areaName: area.name,
      currentPerformance: area.currentScore,
      targetPerformance: calculateTarget(area),
      timeline: generateTimeline(area),
      strategies: strategy.actions,
      resources: strategy.resources,
      milestones: generateMilestones(area),
      estimatedEffort: strategy.effortHours,
      priority: calculatePriorityScore(area, priorityWeighting)
    });
  }

  return plans.sort((a, b) => b.priority - a.priority);
}

// FIXED: Added proper type definitions for severity keys
type SeverityLevel = keyof typeof IMPROVEMENT_STRATEGIES;

// Add this interface definition
interface StrategyConfig {
  actions: readonly string[];
  resources: readonly string[];
  baseEffort: number;
}

// FIXED: Using proper interface
function selectImprovementStrategy(area: WeakArea, trends: any): any {
  // Select strategy based on weakness type and severity
  const severity = calculateSeverity(area) as SeverityLevel;
  const strategies: StrategyConfig = IMPROVEMENT_STRATEGIES[severity] as StrategyConfig;
  
  // FIXED: No type assertion needed now
  const applicableActions = strategies.actions.filter((action: string) => 
    isApplicable(action, area)
  );
  
  return {
    actions: applicableActions,
    resources: strategies.resources,
    effortHours: strategies.baseEffort * (area.difficulty || 1)
  };
}

function calculateTarget(area: WeakArea): number {
  const current = area.currentScore || 0;
  const classAvg = area.classAverage || 70;
  
  // Set realistic target based on current performance
  if (current < 50) return Math.min(current + 20, 70);
  if (current < 70) return Math.min(current + 15, 85);
  return Math.min(current + 10, 95);
}

function generateTimeline(area: WeakArea): string {
  const improvement = calculateTarget(area) - (area.currentScore || 0);
  
  if (improvement > 30) return '3-4 months';
  if (improvement > 20) return '2-3 months';
  if (improvement > 10) return '1-2 months';
  return '2-4 weeks';
}

function generateMilestones(area: WeakArea): any[] {
  const target = calculateTarget(area);
  const current = area.currentScore || 0;
  const increment = (target - current) / 4;
  
  return [
    {
      week: 2,
      target: current + increment,
      description: 'Foundation strengthening'
    },
    {
      week: 4,
      target: current + (increment * 2),
      description: 'Concept mastery'
    },
    {
      week: 6,
      target: current + (increment * 3),
      description: 'Practice and application'
    },
    {
      week: 8,
      target: target,
      description: 'Target achievement'
    }
  ];
}

function calculateSeverity(area: WeakArea): SeverityLevel {
  const score = area.currentScore || 0;
  if (score < 40) return 'critical';
  if (score < 55) return 'high';
  if (score < 70) return 'medium';
  return 'low';
}

function isApplicable(action: string, area: WeakArea): boolean {
  // Check if action is applicable to the specific weakness
  // This would contain more complex logic in production
  return true;
}

function generateAutoInsights(weaknesses: WeaknessAnalysis, trends: any): void {
  // Generate automatic insights based on weakness patterns
  console.log('Generating insights for weaknesses:', weaknesses);
}

// Additional helper functions for mock implementation
function calculateGPAImpact(subject: any): number {
  const grade = subject.currentGrade || 0;
  if (grade < 60) return 0.8;
  if (grade < 70) return 0.6;
  if (grade < 80) return 0.4;
  return 0.2;
}

function calculateDifficulty(subject: any): number {
  // Mock difficulty calculation
  const classAvg = subject.classAverage || 70;
  const studentGrade = subject.currentGrade || 0;
  const gap = classAvg - studentGrade;
  return Math.min(Math.max(gap / 30, 0.1), 0.9);
}

function calculateSeverityFromScore(score: number): 'low' | 'medium' | 'high' | 'critical' {
  if (score < 40) return 'critical';
  if (score < 55) return 'high';
  if (score < 70) return 'medium';
  return 'low';
}

function calculateOverallWeaknessScore(trends: any, threshold: number): number {
  if (!trends.subjects || trends.subjects.length === 0) return 0;
  
  const weakSubjects = trends.subjects.filter((s: any) => s.currentGrade < threshold);
  const totalImpact = weakSubjects.reduce((sum: number, subject: any) => {
    return sum + (subject.credits || 0) * calculateGPAImpact(subject);
  }, 0);
  
  return Math.min(totalImpact / trends.subjects.length, 1);
}