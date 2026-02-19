// src/components/dashboard/EngineeringGuidance.tsx - COMPLETE FIXED VERSION
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, TrendingUp, Lightbulb, Target, ChevronRight, 
  ExternalLink, AlertCircle, CheckCircle, Brain, Sparkles, 
  GraduationCap, Award, Users, Eye, Bookmark, Play, Pause,
  RefreshCw, Download, Share2, MessageCircle, ThumbsUp,
  Clock, Calendar, Zap, TrendingDown, Minus, AlertTriangle
} from 'lucide-react';
import {
  usePerformanceMetrics,
  useElectiveRecommendations,
  useWeaknessAnalysis,
  useStudyResources,
  useBookmarkedResources,
  useToggleBookmark,
  useUpdateProgress,
  useTrackActivity
} from '../../hooks/useEngineeringGuidance';
import { cn } from '../../utils/cn';
import toast from 'react-hot-toast';

// ============== HELPER FUNCTIONS ==============

/**
 * Normalizes weakness data from various API formats
 */
const normalizeWeaknessData = (data: any): any[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (data.weaknesses && Array.isArray(data.weaknesses)) return data.weaknesses;
  if (data.subject || data.subjectCode) return [data];
  return [];
};

/**
 * Extracts metadata from weakness response
 */
const extractWeaknessMetadata = (data: any) => {
  const defaultMeta = {
    overallRiskScore: 0,
    totalWeaknesses: 0,
    criticalCount: 0,
    highCount: 0,
    mediumCount: 0,
    lowCount: 0,
    priorityAreas: [] as string[],
    keyInsights: [] as string[]
  };

  if (!data) return defaultMeta;
  
  if (typeof data === 'object' && !Array.isArray(data)) {
    return {
      overallRiskScore: data.overall_risk_score || data.overallRiskScore || 0,
      totalWeaknesses: data.total_weaknesses || data.totalWeaknesses || 0,
      criticalCount: data.critical_count || data.criticalCount || 0,
      highCount: data.high_count || data.highCount || 0,
      mediumCount: data.medium_count || data.mediumCount || 0,
      lowCount: data.low_count || data.lowCount || 0,
      priorityAreas: data.priority_areas || data.priorityAreas || [],
      keyInsights: data.key_insights || data.keyInsights || []
    };
  }
  
  if (Array.isArray(data)) {
    return {
      ...defaultMeta,
      totalWeaknesses: data.length,
      criticalCount: data.filter((w: any) => w.severity === 'critical').length,
      highCount: data.filter((w: any) => w.severity === 'high').length,
      mediumCount: data.filter((w: any) => w.severity === 'medium').length,
      lowCount: data.filter((w: any) => w.severity === 'low').length,
      priorityAreas: data.slice(0, 3).map((w: any) => w.subject || w.subjectName)
    };
  }
  
  return defaultMeta;
};

/**
 * Transforms weakness item to display format
 */
const transformWeaknessItem = (item: any, index: number): any => {
  if (item.subject && !item.topics) {
    return {
      id: item.id || `weakness-${index}`,
      subject: item.subject,
      subjectCode: item.subject_code || item.subjectCode || `SUBJ${index}`,
      semester: item.semester || 'Current',
      overallScore: item.current_score || item.currentScore || 50,
      targetScore: item.target_score || item.targetScore || 75,
      severity: item.severity || 'medium',
      confidence: item.confidence || 0.8,
      relatedTo: item.related_to || item.relatedTo || '',
      gapPercentage: item.gap_percentage || item.gapPercentage || 20,
      estimatedTime: item.estimated_improvement_time || item.estimatedTime || '4-6 weeks',
      topics: [
        {
          id: `topic-${index}-1`,
          name: item.topic || item.subject,
          currentScore: item.current_score || item.currentScore || 50,
          targetScore: item.target_score || item.targetScore || 75,
          severity: item.severity || 'medium',
          improvement: `+${item.gap_percentage || 20}%`,
          examWeight: '25%',
          resources: (item.recommended_resources || []).length || 3,
          timeEstimate: item.estimated_improvement_time || '2-3 hours',
          relatedTopics: []
        }
      ],
      improvementSuggestions: item.improvement_suggestions || item.improvementSuggestions || [],
      recommendedResources: item.recommended_resources || item.recommendedResources || [],
      impactOnInterest: item.impact_on_interest || item.impactOnInterest || null,
      impactOnElective: item.impact_on_elective || item.impactOnElective || null,
      impactOnCareer: item.impact_on_career || item.impactOnCareer || null,
      aiAnalysis: {
        rootCause: `Performance gap detected in ${item.subject}`,
        studyStrategy: item.improvement_suggestions?.[0] || 'Focus on fundamentals and practice regularly',
        estimatedImprovementTime: item.estimated_improvement_time || '4-6 weeks'
      }
    };
  }
  
  return {
    ...item,
    id: item.id || `weakness-${index}`,
    topics: item.topics || []
  };
};

/**
 * Normalizes resources data from various API formats
 */
const normalizeResourcesData = (data: any): any[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (data.resources && Array.isArray(data.resources)) return data.resources;
  if (data.recommended_resources && Array.isArray(data.recommended_resources)) return data.recommended_resources;
  if (data.data && Array.isArray(data.data)) return data.data;
  if (data.items && Array.isArray(data.items)) return data.items;
  
  if (typeof data === 'object' && !Array.isArray(data)) {
    const allResources: any[] = [];
    const categoryKeys = ['videos', 'courses', 'tutorials', 'books', 'practice', 'articles'];
    
    for (const key of categoryKeys) {
      if (data[key] && Array.isArray(data[key])) {
        allResources.push(...data[key].map((item: any) => ({ ...item, category: key })));
      }
    }
    
    if (allResources.length > 0) return allResources;
    
    Object.values(data).forEach((value) => {
      if (Array.isArray(value)) allResources.push(...value);
    });
    
    if (allResources.length > 0) return allResources;
    if (data.title || data.name || data.url) return [data];
  }
  
  return [];
};

/**
 * Transforms a resource item to ensure consistent structure
 */
const transformResourceItem = (item: any, index: number): any => {
  return {
    id: item.id || `resource-${index}`,
    title: item.title || item.name || 'Untitled Resource',
    type: item.type || item.category || 'resource',
    url: item.url || item.link || '#',
    duration: item.duration || item.time || 'N/A',
    rating: item.rating || 4.0,
    reviews: item.reviews || item.reviewCount || 0,
    difficulty: item.difficulty || item.level || 'Intermediate',
    language: item.language || 'English',
    examRelevance: item.examRelevance || item.exam_relevance || 'Relevant',
    completionStatus: item.completionStatus || item.completion_status || item.progress || 0,
    tags: item.tags || item.topics || [],
    provider: item.provider || item.source || 'Various',
    platform: item.platform || 'Online',
    lastUpdated: item.lastUpdated || item.last_updated || item.updated_at || 'Recently',
    thumbnailUrl: item.thumbnailUrl || item.thumbnail_url || item.thumbnail || null,
    icon: item.icon || '📚',
    aiReason: item.aiReason || item.ai_reason || item.reason || null,
    isBookmarked: item.isBookmarked || item.is_bookmarked || false,
    description: item.description || null,
    subject: item.subject || null
  };
};

/**
 * Normalizes elective recommendations data
 */
const normalizeElectiveData = (data: any): any[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (data.recommendations && Array.isArray(data.recommendations)) return data.recommendations;
  if (data.electives && Array.isArray(data.electives)) return data.electives;
  if (data.data && Array.isArray(data.data)) return data.data;
  return [];
};

/**
 * Transforms elective item to display format
 */
const transformElectiveItem = (item: any, index: number): any => {
  return {
    id: item.id || `elective-${index}`,
    title: item.title || item.name || item.elective_name || 'Unknown Elective',
    match: item.match || item.matchScore || item.match_score || 75,
    semester: item.semester || 'Upcoming',
    reason: item.reason || item.aiReason || item.ai_reason || 'Recommended based on your profile',
    credits: item.credits || 4,
    difficulty: item.difficulty || 'Intermediate',
    instructor: item.instructor || { name: 'TBA', rating: 4.0, expertise: [] },
    industryRelevance: item.industryRelevance || item.industry_relevance || 80,
    jobMarketDemand: item.jobMarketDemand || item.job_market_demand || 75,
    enrollmentCount: item.enrollmentCount || item.enrollment_count || 0,
    careerImpact: item.careerImpact || item.career_impact || 'Enhances career prospects',
    tags: item.tags || item.skills || [],
    prerequisites: item.prerequisites || [],
    learningOutcomes: item.learningOutcomes || item.learning_outcomes || [],
    syllabus: item.syllabus || item.topics || []
  };
};


// ============== ELECTIVE RECOMMENDER COMPONENT ==============

export const ElectiveRecommender: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = usePerformanceMetrics();
  const { data: rawRecommendations, isLoading: recsLoading, refetch, error } = useElectiveRecommendations();
  const trackActivity = useTrackActivity();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const recommendations = useMemo(() => {
    const normalized = normalizeElectiveData(rawRecommendations);
    return normalized.map((item, index) => transformElectiveItem(item, index));
  }, [rawRecommendations]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
      toast.success('Recommendations updated!');
    } catch (err) {
      toast.error('Failed to update recommendations');
    } finally {
      setRefreshing(false);
    }
  };

  const handleViewSyllabus = (elective: any) => {
    setExpandedId(expandedId === elective.id ? null : elective.id);
    trackActivity.mutate({
      type: 'resource_viewed',
      resourceId: elective.id
    });
  };

  if (metricsLoading || recsLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-100 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-red-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-red-500" size={24} />
          <h2 className="text-xl font-bold text-gray-900">Error Loading Recommendations</h2>
        </div>
        <p className="text-gray-600 mb-4">Unable to load elective recommendations. Please try again.</p>
        <button
          onClick={handleRefresh}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-3 rounded-xl">
            <Sparkles className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI-Powered Elective Recommendations</h2>
            <p className="text-gray-500 text-sm">
              Personalized for {metrics?.studentInfo?.year || 'Current Year'} • {metrics?.studentInfo?.branch || 'Your Branch'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
            title="Refresh recommendations"
          >
            <RefreshCw className={cn('w-5 h-5 text-purple-600', refreshing && 'animate-spin')} />
          </button>
          <div className="bg-purple-50 border border-purple-200 rounded-lg px-4 py-2">
            <p className="text-xs text-purple-600 font-medium">Current Semester</p>
            <p className="text-lg font-bold text-purple-700">{metrics?.studentInfo?.semester || 'N/A'}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <AnimatePresence>
          {recommendations.map((rec, index) => (
            <motion.div
              key={rec.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gradient-to-r from-purple-50 to-white rounded-xl p-5 border border-purple-200 hover:border-purple-400 transition-all hover:shadow-md"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <h3 className="text-lg font-bold text-gray-900">{rec.title}</h3>
                    <div className="bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      {rec.match}% Match
                    </div>
                    <div className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold">
                      {rec.semester}
                    </div>
                    {rec.jobMarketDemand > 80 && (
                      <div className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs font-semibold">
                        🔥 High Demand
                      </div>
                    )}
                  </div>
                  <p className="text-purple-700 text-sm flex items-center gap-2 mb-3">
                    <Brain size={16} />
                    {rec.reason}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-gray-600 mb-3 flex-wrap">
                    <span>👨‍🏫 {rec.instructor?.name || 'TBA'}</span>
                    <span>⭐ {rec.instructor?.rating?.toFixed(1) || 'N/A'}</span>
                    <span>📚 {rec.credits} Credits</span>
                    <span>📈 Industry: {rec.industryRelevance}%</span>
                    <span>👥 {rec.enrollmentCount} enrolled</span>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-3">
                    <p className="text-xs text-blue-700 font-medium">
                      💼 Career Impact: {rec.careerImpact}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mb-3">
                {rec.tags?.slice(0, 5).map((tag: string, idx: number) => (
                  <span key={idx} className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs font-medium">
                    {tag}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-purple-100">
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Target size={14} className="text-purple-500" />
                    {rec.difficulty}
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle size={14} className="text-green-500" />
                    Prerequisites Met
                  </span>
                </div>
                <button 
                  onClick={() => handleViewSyllabus(rec)}
                  className="text-purple-600 hover:text-purple-700 font-semibold text-sm flex items-center gap-1 hover:gap-2 transition-all"
                >
                  {expandedId === rec.id ? 'Hide' : 'View'} Details <ChevronRight size={16} />
                </button>
              </div>

              <AnimatePresence>
                {expandedId === rec.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 pt-4 border-t border-purple-200"
                  >
                    <div className="space-y-4">
                      {rec.prerequisites?.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            Prerequisites
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {rec.prerequisites.map((prereq: string, idx: number) => (
                              <span key={idx} className="px-3 py-1 bg-green-50 text-green-700 rounded-lg text-sm">
                                {prereq}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {rec.learningOutcomes?.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                            <Target className="w-4 h-4 text-blue-500" />
                            Learning Outcomes
                          </h4>
                          <ul className="space-y-1">
                            {rec.learningOutcomes.map((outcome: string, idx: number) => (
                              <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                                <ChevronRight className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                                {outcome}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {rec.syllabus?.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-orange-500" />
                            Syllabus Topics
                          </h4>
                          <div className="grid grid-cols-2 gap-2">
                            {rec.syllabus.slice(0, 6).map((topic: string, idx: number) => (
                              <span key={idx} className="px-3 py-2 bg-gray-50 text-gray-700 rounded-lg text-sm">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {rec.instructor?.expertise?.length > 0 && (
                        <div className="bg-indigo-50 rounded-lg p-4">
                          <h4 className="font-semibold text-gray-900 mb-2">Instructor Expertise</h4>
                          <div className="flex flex-wrap gap-2">
                            {rec.instructor.expertise.map((exp: string, idx: number) => (
                              <span key={idx} className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs">
                                {exp}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </AnimatePresence>

        {recommendations.length === 0 && (
          <div className="text-center py-12 bg-purple-50 rounded-xl">
            <Sparkles className="w-12 h-12 text-purple-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Recommendations Yet</h3>
            <p className="text-gray-600">Set your interests to get personalized elective recommendations.</p>
          </div>
        )}
      </div>
    </div>
  );
};


// ============== CONTEXT FOR SHARING SELECTED TOPIC ==============

interface LearningContextType {
  selectedTopic: string | null;
  selectedSubject: string | null;
  setSelectedTopic: (topic: string | null, subject: string | null) => void;
}

const LearningContext = React.createContext<LearningContextType>({
  selectedTopic: null,
  selectedSubject: null,
  setSelectedTopic: () => {}
});

export const useLearningContext = () => React.useContext(LearningContext);
// ============== WEAKNESS ANALYZER COMPONENT ==============
// Replace the entire WeaknessAnalyzer component with this:

interface WeaknessAnalyzerProps {
  onStartLearning?: (topicId: string, subject: string) => void;
  interests?: string[];
  electives?: string[];
}

export const WeaknessAnalyzer: React.FC<WeaknessAnalyzerProps> = ({ 
  onStartLearning,
  interests: propInterests,
  electives: propElectives
}) => {
  const { data: metrics } = usePerformanceMetrics();
  
  // Props > metrics fallback for interests
  const interests = useMemo(() => {
    if (propInterests && propInterests.length > 0) return propInterests;
    if (metrics?.interests && metrics.interests.length > 0) return metrics.interests;
    return [];
  }, [propInterests, metrics?.interests]);

  const electives = useMemo(() => {
    if (propElectives && propElectives.length > 0) return propElectives;
    return [];
  }, [propElectives]);

  const analysisParams = useMemo(() => {
    const params: { interests?: string[]; electives?: string[] } = {};
    if (interests.length > 0) params.interests = interests;
    if (electives.length > 0) params.electives = electives;
    return Object.keys(params).length > 0 ? params : undefined;
  }, [interests, electives]);

  // ===== Source 1: Existing hook-based weakness analysis =====
  const { data: rawWeaknessData, isLoading: hookLoading, refetch: hookRefetch, error: hookError } = useWeaknessAnalysis(analysisParams);

  // ===== Source 2: Academic Recommendations API (same as AcademicInsights) =====
  const [academicData, setAcademicData] = useState<any>(null);
  const [academicLoading, setAcademicLoading] = useState(true);
  const [academicError, setAcademicError] = useState<string | null>(null);
  const [needsSetup, setNeedsSetup] = useState(false);

  const trackActivity = useTrackActivity();

  // Fetch academic recommendations (same API as AcademicInsights)
  const fetchAcademicWeaknesses = useCallback(async () => {
    try {
      setAcademicLoading(true);
      setAcademicError(null);
      setNeedsSetup(false);

      const { mlService } = await import('../../services/ml.service');
      const data = await mlService.getAcademicRecommendations();
      setAcademicData(data);
      console.log('✅ WeaknessAnalyzer: Academic recommendations loaded', {
        weaknesses: data.weaknesses?.length || 0,
        actions: data.curriculum_recommendations?.immediate_actions?.length || 0,
        focus: data.curriculum_recommendations?.focus_areas?.length || 0
      });
    } catch (err: any) {
      console.error('WeaknessAnalyzer: Error fetching academic recommendations:', err);
      if (err.message?.includes('profile') || err.message?.includes('not found') || err.response?.status === 404) {
        setNeedsSetup(true);
      } else {
        setAcademicError(err.message || 'Failed to load academic analysis');
      }
    } finally {
      setAcademicLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAcademicWeaknesses();

    const handleUpdate = () => fetchAcademicWeaknesses();
    window.addEventListener('academicDataUpdated', handleUpdate);
    window.addEventListener('profileSaved', handleUpdate);
    return () => {
      window.removeEventListener('academicDataUpdated', handleUpdate);
      window.removeEventListener('profileSaved', handleUpdate);
    };
  }, [fetchAcademicWeaknesses]);

  // ===== Merge both data sources =====
  const hookWeaknesses = useMemo(() => {
    const normalized = normalizeWeaknessData(rawWeaknessData);
    return normalized.map((item, index) => transformWeaknessItem(item, index));
  }, [rawWeaknessData]);

  const hookMetadata = useMemo(() => {
    return extractWeaknessMetadata(rawWeaknessData);
  }, [rawWeaknessData]);

  // Academic weaknesses from AcademicInsights API
  const academicWeaknesses = useMemo(() => {
    if (!academicData?.weaknesses) return [];
    return academicData.weaknesses;
  }, [academicData]);

  const immediateActions = useMemo(() => {
    return academicData?.curriculum_recommendations?.immediate_actions || [];
  }, [academicData]);

  const focusAreas = useMemo(() => {
    return academicData?.curriculum_recommendations?.focus_areas || [];
  }, [academicData]);

  const studentInfo = useMemo(() => {
    return academicData?.student_info || null;
  }, [academicData]);

  // Merge: deduplicate by subject name, prefer academic data (richer)
  const mergedWeaknesses = useMemo(() => {
    const seenSubjects = new Set<string>();
    const merged: any[] = [];

    // First: add all academic weaknesses (richer data, same source as AcademicInsights)
    academicWeaknesses.forEach((aw: any, index: number) => {
      const key = (aw.subject || '').toLowerCase().trim();
      if (key && !seenSubjects.has(key)) {
        seenSubjects.add(key);
        merged.push({
          id: `academic-weakness-${index}`,
          subject: aw.subject,
          subjectCode: aw.subject_code || `AW${index}`,
          semester: 'Current',
          overallScore: aw.average_score || 0,
          targetScore: (aw.average_score || 0) + (aw.gap || 20),
          severity: aw.severity || 'medium',
          confidence: aw.confidence || 0.8,
          gapPercentage: aw.gap || 0,
          estimatedTime: aw.improvement_plan?.timeline || '4-6 weeks',
          source: 'academic', // tag so we know where it came from
          topics: aw.topics?.length > 0
            ? aw.topics.map((t: string, tidx: number) => ({
                id: `aw-topic-${index}-${tidx}`,
                name: t,
                currentScore: aw.average_score || 0,
                targetScore: (aw.average_score || 0) + (aw.gap || 20),
                severity: aw.severity || 'medium',
                improvement: `+${aw.gap || 20}%`,
                examWeight: '—',
                resources: aw.resources?.length || 2,
                timeEstimate: aw.improvement_plan?.timeline || '2-3 hours',
                relatedTopics: []
              }))
            : [{
                id: `aw-topic-${index}-0`,
                name: aw.subject,
                currentScore: aw.average_score || 0,
                targetScore: (aw.average_score || 0) + (aw.gap || 20),
                severity: aw.severity || 'medium',
                improvement: `+${aw.gap || 20}%`,
                examWeight: '—',
                resources: 2,
                timeEstimate: '2-3 hours',
                relatedTopics: []
              }],
          improvementSuggestions: aw.improvement_plan?.steps || [],
          recommendedResources: (aw.resources || []).map((r: any) =>
            typeof r === 'string' ? { title: r, url: '#', platform: 'Online' } : r
          ),
          impactOnInterest: interests.some(i =>
            (aw.subject || '').toLowerCase().includes(i.toLowerCase())
          )
            ? `Directly related to your interest in "${interests.find(i => (aw.subject || '').toLowerCase().includes(i.toLowerCase()))}"`
            : null,
          impactOnElective: null,
          impactOnCareer: null,
          aiAnalysis: {
            rootCause: `Performance gap of ${aw.gap?.toFixed(1) || 0}% detected in ${aw.subject}`,
            studyStrategy: aw.improvement_plan?.steps?.[0] || 'Focus on fundamentals and practice regularly',
            estimatedImprovementTime: aw.improvement_plan?.timeline || '4-6 weeks'
          }
        });
      }
    });

    // Then: add hook-based weaknesses that aren't already present
    hookWeaknesses.forEach((hw: any) => {
      const key = (hw.subject || '').toLowerCase().trim();
      if (key && !seenSubjects.has(key)) {
        seenSubjects.add(key);
        merged.push({ ...hw, source: 'hook' });
      }
    });

    return merged;
  }, [academicWeaknesses, hookWeaknesses, interests]);

  // Severity counts from merged data
  const severityCounts = useMemo(() => ({
    critical: mergedWeaknesses.filter(w => w.severity === 'critical').length,
    high: mergedWeaknesses.filter(w => w.severity === 'high').length,
    medium: mergedWeaknesses.filter(w => w.severity === 'medium').length,
    low: mergedWeaknesses.filter(w => w.severity === 'low').length
  }), [mergedWeaknesses]);

  const overallRiskScore = useMemo(() => {
    if (hookMetadata.overallRiskScore > 0) return hookMetadata.overallRiskScore;
    // Compute from merged weaknesses
    if (mergedWeaknesses.length === 0) return 0;
    const severityWeights: Record<string, number> = { critical: 25, high: 15, medium: 8, low: 3 };
    return Math.min(100, mergedWeaknesses.reduce((sum, w) =>
      sum + (severityWeights[w.severity] || 5), 0
    ));
  }, [hookMetadata, mergedWeaknesses]);

  const averageGap = useMemo(() => {
    if (mergedWeaknesses.length === 0) return 0;
    return mergedWeaknesses.reduce((sum, w) => sum + (w.gapPercentage || 0), 0) / mergedWeaknesses.length;
  }, [mergedWeaknesses]);

  // Combined loading state
  const isLoading = hookLoading && academicLoading;
  const hasAnyData = mergedWeaknesses.length > 0 || immediateActions.length > 0 || focusAreas.length > 0;

  // ===== Helpers =====
  const getTrendIcon = (score: number, targetScore: number) => {
    if (score >= targetScore) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (score >= targetScore * 0.8) return <TrendingUp className="w-5 h-5 text-yellow-500" />;
    return <TrendingDown className="w-5 h-5 text-red-500" />;
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-700 border-red-200',
      high: 'bg-orange-100 text-orange-700 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      low: 'bg-green-100 text-green-700 border-green-200'
    };
    return colors[severity?.toLowerCase()] || colors.medium;
  };

  const getRiskColor = (score: number) => {
    if (score >= 75) return 'text-red-600 bg-red-50';
    if (score >= 50) return 'text-orange-600 bg-orange-50';
    if (score >= 25) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const handleStartLearning = (topicId: string, subject: string) => {
    trackActivity.mutate({ type: 'topic_completed', topicId });
    if (onStartLearning) onStartLearning(topicId, subject);
    toast.success(`📚 Study plan for "${subject}" created! Scroll down to Resources.`, {
      duration: 4000,
      icon: '🎯'
    });
  };

  const handleRefresh = async () => {
    try {
      await Promise.all([
        hookRefetch(),
        fetchAcademicWeaknesses()
      ]);
      toast.success('Weakness analysis refreshed!');
    } catch (err) {
      toast.error('Failed to refresh analysis');
    }
  };

  // ===== Loading =====
  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="h-24 bg-purple-100 rounded-xl"></div>
          {[1, 2].map(i => (
            <div key={i} className="h-48 bg-gray-100 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  // ===== Needs Setup =====
  if (needsSetup && !hasAnyData) {
    return (
      <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-2xl p-8">
        <div className="flex flex-col items-center text-center">
          <div className="p-4 bg-yellow-100 rounded-full mb-4">
            <GraduationCap className="w-10 h-10 text-yellow-600" />
          </div>
          <h3 className="text-xl font-semibold text-yellow-900 mb-2">Academic Profile Required</h3>
          <p className="text-yellow-700 mb-6 max-w-md">
            Add your academic details and semester scores to unlock AI-powered weakness analysis and improvement recommendations.
          </p>
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('navigateToAcademic'))}
            className="px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors flex items-center gap-2"
          >
            <GraduationCap className="w-5 h-5" />
            Setup Academic Profile
          </button>
        </div>
      </div>
    );
  }

  // ===== Error =====
  if (hookError && academicError && !hasAnyData) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-red-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-red-500" size={24} />
          <h2 className="text-xl font-bold text-gray-900">Error Loading Analysis</h2>
        </div>
        <p className="text-gray-600 mb-4">Unable to load weakness analysis. Please try again.</p>
        <button onClick={handleRefresh} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg">
          Retry
        </button>
      </div>
    );
  }

  // ==================== MAIN RENDER ====================
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-orange-500 to-red-600 p-3 rounded-xl">
            <AlertCircle className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI Weakness Analysis & Improvement Roadmap</h2>
            <p className="text-gray-500 text-sm">
              {interests.length > 0
                ? `Based on your interests: ${interests.slice(0, 3).join(', ')}${interests.length > 3 ? '...' : ''}`
                : 'Personalized analysis based on your academic performance'}
              {studentInfo && (
                <span className="ml-2 text-purple-600 font-medium">
                  • CGPA: {studentInfo.cgpa?.toFixed(2)} • {studentInfo.branch} Sem {studentInfo.semester}
                </span>
              )}
            </p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
          title="Refresh analysis"
        >
          <RefreshCw className="w-5 h-5 text-purple-600" />
        </button>
      </div>

      {/* ===== Severity Summary Cards ===== */}
      {mergedWeaknesses.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-orange-50 border border-purple-200 rounded-xl p-4 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className={cn('rounded-lg p-3 text-center', getRiskColor(overallRiskScore))}>
              <p className="text-xs font-medium mb-1">Risk Score</p>
              <p className="text-2xl font-bold">{overallRiskScore.toFixed(0)}%</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center border">
              <p className="text-xs text-gray-600 font-medium mb-1">Total</p>
              <p className="text-2xl font-bold text-gray-900">{mergedWeaknesses.length}</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center border border-red-100">
              <p className="text-xs text-red-600 font-medium mb-1">Critical</p>
              <p className="text-2xl font-bold text-red-700">{severityCounts.critical}</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-3 text-center border border-orange-100">
              <p className="text-xs text-orange-600 font-medium mb-1">High</p>
              <p className="text-2xl font-bold text-orange-700">{severityCounts.high}</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3 text-center border border-yellow-100">
              <p className="text-xs text-yellow-600 font-medium mb-1">Medium</p>
              <p className="text-2xl font-bold text-yellow-700">{severityCounts.medium}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center border border-green-100">
              <p className="text-xs text-green-600 font-medium mb-1">Avg Gap</p>
              <p className="text-2xl font-bold text-green-700">{averageGap.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}

      {/* ===== Immediate Actions (from Academic Recommendations) ===== */}
      {immediateActions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-red-500" />
            Immediate Actions Required
          </h3>
          <div className="space-y-2">
            {immediateActions.map((action: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  'p-4 rounded-lg border-l-4',
                  action.priority === 'critical'
                    ? 'border-red-500 bg-red-50'
                    : action.priority === 'high'
                    ? 'border-orange-500 bg-orange-50'
                    : 'border-yellow-500 bg-yellow-50'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{action.action}</p>
                    {action.reason && (
                      <p className="text-sm text-gray-600 mt-1">{action.reason}</p>
                    )}
                    {action.subjects && action.subjects.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {action.subjects.map((subj: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-white/70 rounded text-xs font-medium text-gray-700 border">
                            {subj}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className={cn(
                    'text-xs font-bold uppercase px-2 py-1 rounded ml-3',
                    action.priority === 'critical' ? 'bg-red-200 text-red-800'
                      : action.priority === 'high' ? 'bg-orange-200 text-orange-800'
                      : 'bg-yellow-200 text-yellow-800'
                  )}>
                    {action.priority}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ===== Priority Areas ===== */}
      {hookMetadata.priorityAreas.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            Priority Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {hookMetadata.priorityAreas.map((area: string, idx: number) => (
              <span key={idx} className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm font-medium">
                {area}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ===== Key Insights ===== */}
      {hookMetadata.keyInsights.length > 0 && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-6">
          <h3 className="text-sm font-semibold text-indigo-900 mb-2 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-indigo-500" />
            Key Insights
          </h3>
          <ul className="space-y-2">
            {hookMetadata.keyInsights.map((insight: string, idx: number) => (
              <li key={idx} className="text-sm text-indigo-700 flex items-start gap-2">
                <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ===== Performance Summary ===== */}
      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="text-sm text-purple-600 font-medium mb-1">📊 Current Performance</p>
            <p className="text-2xl font-bold text-purple-700">
              CGPA: {studentInfo?.cgpa?.toFixed(2) || metrics?.overallCGPA || 'N/A'}
            </p>
          </div>
          {(studentInfo?.cgpa || metrics?.overallCGPA) && (
            <>
              <div className="text-right">
                <p className="text-sm text-purple-600 font-medium mb-1">🎯 Potential CGPA</p>
                <p className="text-2xl font-bold text-green-600">
                  {(((studentInfo?.cgpa || metrics?.overallCGPA || 7) as number) + 0.7).toFixed(1)}+ achievable
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">📈 Total Weaknesses</p>
                <p className="text-xl font-bold text-orange-600">{mergedWeaknesses.length} subjects</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ===== Merged Weakness List ===== */}
      <div className="space-y-6">
        <AnimatePresence>
          {mergedWeaknesses.map((weak, idx) => (
            <motion.div
              key={weak.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-gradient-to-r from-purple-50 to-white rounded-xl p-5 border border-purple-200"
            >
              {/* Source badge */}
              {weak.source === 'academic' && (
                <div className="flex items-center gap-2 mb-3">
                  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-semibold flex items-center gap-1">
                    <Brain className="w-3 h-3" />
                    From Academic Analysis
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <BookOpen size={20} className="text-purple-600" />
                    {weak.subject}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {weak.subjectCode} {weak.semester && `• ${weak.semester}`}
                    {weak.relatedTo && (
                      <span className="ml-2 text-purple-600">• {weak.relatedTo}</span>
                    )}
                  </p>
                </div>
                <div className="text-right">
                  <div className={cn(
                    'px-3 py-1 rounded-full text-sm font-semibold mb-1 border',
                    getSeverityColor(weak.severity)
                  )}>
                    {weak.severity?.toUpperCase()} — {weak.overallScore?.toFixed?.(1) || weak.overallScore}%
                  </div>
                  <p className="text-xs text-gray-500">
                    Gap: {weak.gapPercentage?.toFixed?.(1) || weak.gapPercentage}%
                  </p>
                </div>
              </div>

              {/* Impact Information */}
              {(weak.impactOnInterest || weak.impactOnElective || weak.impactOnCareer) && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-blue-700">
                    <strong>💡 Impact:</strong> {weak.impactOnInterest || weak.impactOnElective || weak.impactOnCareer}
                  </p>
                </div>
              )}

              {/* AI Analysis */}
              {weak.aiAnalysis && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-indigo-900 mb-2">AI Analysis</h4>
                      <p className="text-sm text-indigo-700 mb-1">
                        <strong>Root Cause:</strong> {weak.aiAnalysis.rootCause}
                      </p>
                      <p className="text-sm text-indigo-700 mb-1">
                        <strong>Strategy:</strong> {weak.aiAnalysis.studyStrategy}
                      </p>
                      <p className="text-xs text-indigo-600">
                        ⏱️ Estimated improvement: {weak.aiAnalysis.estimatedImprovementTime}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Improvement Suggestions */}
              {weak.improvementSuggestions?.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500" />
                    Improvement Steps
                  </h4>
                  <ul className="space-y-1">
                    {weak.improvementSuggestions.slice(0, 5).map((suggestion: string, sidx: number) => (
                      <li key={sidx} className="text-sm text-gray-600 flex items-start gap-2">
                        <div className="mt-1 w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-xs flex items-center justify-center font-bold flex-shrink-0">
                          {sidx + 1}
                        </div>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Topics */}
              <div className="space-y-3">
                {weak.topics?.map((topic: any, tidx: number) => (
                  <div key={topic.id || tidx} className="bg-white rounded-lg p-4 border border-purple-100 hover:border-purple-300 transition-all">
                    <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                      <div className="flex items-center gap-3 flex-1 flex-wrap">
                        <h4 className="font-semibold text-gray-800">{topic.name}</h4>
                        <span className={cn('px-3 py-1 rounded-full text-xs font-semibold border', getSeverityColor(topic.severity))}>
                          {topic.severity?.toUpperCase()}
                        </span>
                        {topic.examWeight && topic.examWeight !== '—' && (
                          <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                            📝 Exam: {topic.examWeight}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {getTrendIcon(topic.currentScore, topic.targetScore)}
                        <div className="text-green-600 font-bold text-sm flex items-center gap-1">
                          <TrendingUp size={16} />
                          {topic.improvement}
                        </div>
                      </div>
                    </div>

                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Current: {topic.currentScore?.toFixed?.(1) || topic.currentScore}%</span>
                        <span>Target: {topic.targetScore?.toFixed?.(1) || topic.targetScore}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5 relative overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(topic.currentScore, 100)}%` }}
                          transition={{ duration: 1, ease: 'easeOut' }}
                          className="h-2.5 rounded-full bg-gradient-to-r from-purple-500 to-purple-600"
                        />
                        <div
                          className="absolute top-0 h-2.5 w-0.5 bg-green-500"
                          style={{ left: `${Math.min(topic.targetScore, 100)}%` }}
                        />
                      </div>
                    </div>

                    {topic.relatedTopics?.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-600 mb-1">Related Concepts:</p>
                        <div className="flex flex-wrap gap-1">
                          {topic.relatedTopics.map((rel: string, ridx: number) => (
                            <span key={ridx} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                              {rel}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <BookOpen className="w-4 h-4" />
                          {topic.resources} resources
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {topic.timeEstimate}
                        </span>
                      </div>
                      <button
                        onClick={() => handleStartLearning(topic.id, weak.subject)}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
                      >
                        Start Learning <ChevronRight size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Recommended Resources */}
              {weak.recommendedResources?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-purple-100">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-purple-500" />
                    Recommended Resources
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {weak.recommendedResources.slice(0, 3).map((resource: any, ridx: number) => (
                      <a
                        key={ridx}
                        href={resource.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-3 py-2 bg-white border border-purple-200 rounded-lg hover:border-purple-400 hover:shadow-sm transition-all text-sm"
                      >
                        <span className="text-gray-900">{resource.title}</span>
                        {resource.platform && (
                          <span className="text-xs text-gray-500">({resource.platform})</span>
                        )}
                        <ExternalLink className="w-3 h-3 text-purple-500" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty State */}
        {mergedWeaknesses.length === 0 && (
          <div className="text-center py-12 bg-green-50 rounded-xl border border-green-200">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-green-800 mb-2">
              {interests.length > 0 ? 'Great Performance for Your Interests!' : 'Excellent Performance!'}
            </h3>
            <p className="text-green-700">
              {interests.length > 0
                ? `No significant weaknesses detected for your interests (${interests.slice(0, 2).join(', ')}). Keep up the great work!`
                : 'No significant weaknesses detected. Keep up the great work!'}
            </p>
            {interests.length === 0 && (
              <p className="text-sm text-green-600 mt-2">
                Tip: Set your interests to get analysis based on your career goals.
              </p>
            )}
          </div>
        )}
      </div>

      {/* ===== Strong Areas (from Academic Recommendations) ===== */}
      {focusAreas.length > 0 && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-xl p-5">
          <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            Your Strong Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {focusAreas.map((area: any, index: number) => (
              <span key={index} className="px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                ⭐ {area.area} ({area.average_score?.toFixed(0) || 0}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ===== AI Tips ===== */}
      {mergedWeaknesses.length > 0 && (
        <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-5">
          <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            AI Improvement Tips
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {severityCounts.critical > 0 && (
              <div className="flex items-start gap-3 bg-white rounded-lg p-3 border">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {severityCounts.critical} critical subject{severityCounts.critical > 1 ? 's' : ''} need daily attention
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Dedicate at least 1 hour daily to each critical subject</p>
                </div>
              </div>
            )}
            {severityCounts.high > 0 && (
              <div className="flex items-start gap-3 bg-white rounded-lg p-3 border">
                <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {severityCounts.high} high priority subject{severityCounts.high > 1 ? 's' : ''} need regular practice
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Solve previous year papers and practice problems</p>
                </div>
              </div>
            )}
            <div className="flex items-start gap-3 bg-white rounded-lg p-3 border">
              <Target className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">
                  Average gap: {averageGap.toFixed(1)}% across {mergedWeaknesses.length} subjects
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Closing this gap could improve your CGPA by ~{(averageGap * 0.05).toFixed(2)} points
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 bg-white rounded-lg p-3 border">
              <BookOpen className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Use active recall & spaced repetition</p>
                <p className="text-xs text-gray-500 mt-1">Most effective study techniques for closing knowledge gaps</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============== STUDY RESOURCES COMPONENT ==============

interface StudyResourcesProps {
  selectedSubject?: string | null;
  highlightNew?: boolean;
}

export const StudyResources: React.FC<StudyResourcesProps> = ({ 
  selectedSubject = null,
  highlightNew = false 
}) => {
  const [activeTab, setActiveTab] = useState<'recommended' | 'bookmarked'>('recommended');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const { data: metrics } = usePerformanceMetrics();
  const { data: rawResources, isLoading, error, refetch } = useStudyResources(
    activeTab === 'recommended' ? { type: selectedFilter !== 'all' ? selectedFilter : undefined } : undefined
  );
  const { data: rawBookmarked } = useBookmarkedResources();
  const toggleBookmark = useToggleBookmark();
  const updateProgress = useUpdateProgress();
  const trackActivity = useTrackActivity();

  // Normalize resources data
  const resources = useMemo(() => {
    const normalized = normalizeResourcesData(rawResources);
    return normalized.map((item, index) => transformResourceItem(item, index));
  }, [rawResources]);

  const bookmarked = useMemo(() => {
    const normalized = normalizeResourcesData(rawBookmarked);
    return normalized.map((item, index) => transformResourceItem(item, index));
  }, [rawBookmarked]);

  // Get current resources with filtering
  const currentResources = useMemo(() => {
    let data = activeTab === 'recommended' ? resources : bookmarked;
    
    // Filter by type if not 'all'
    if (selectedFilter !== 'all' && activeTab === 'recommended') {
      data = data.filter((r) => 
        r.type?.toLowerCase() === selectedFilter.toLowerCase() ||
        r.category?.toLowerCase() === selectedFilter.toLowerCase()
      );
    }
    
    // If a subject is selected, prioritize resources for that subject
    if (selectedSubject) {
      const subjectLower = selectedSubject.toLowerCase();
      data = data.sort((a, b) => {
        const aMatch = (a.subject?.toLowerCase().includes(subjectLower) || 
                       a.title?.toLowerCase().includes(subjectLower) ||
                       a.tags?.some((t: string) => t.toLowerCase().includes(subjectLower))) ? 1 : 0;
        const bMatch = (b.subject?.toLowerCase().includes(subjectLower) || 
                       b.title?.toLowerCase().includes(subjectLower) ||
                       b.tags?.some((t: string) => t.toLowerCase().includes(subjectLower))) ? 1 : 0;
        return bMatch - aMatch;
      });
    }
    
    return data;
  }, [activeTab, resources, bookmarked, selectedFilter, selectedSubject]);

  // Refetch when subject changes
  useEffect(() => {
    if (selectedSubject) {
      refetch();
    }
  }, [selectedSubject, refetch]);

  const handleBookmark = async (resourceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      toggleBookmark.mutate(resourceId);
      toast.success('Bookmark updated!');
    } catch (err) {
      toast.error('Failed to update bookmark');
    }
  };

  const handleAccessResource = (resource: any) => {
    trackActivity.mutate({
      type: 'resource_viewed',
      resourceId: resource.id
    });
    if (resource.url && resource.url !== '#') {
      window.open(resource.url, '_blank');
    } else {
      toast.error('Resource URL not available');
    }
  };

  const filters = ['all', 'video', 'tutorial', 'practice', 'course'];

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-red-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-red-500" size={24} />
          <h2 className="text-xl font-bold text-gray-900">Error Loading Resources</h2>
        </div>
        <p className="text-gray-600">Unable to load study resources. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className={cn(
      "bg-white rounded-2xl shadow-lg border p-6 transition-all",
      highlightNew ? "border-purple-400 ring-2 ring-purple-200" : "border-purple-100"
    )}>
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-3 rounded-xl">
          <GraduationCap className="text-white" size={24} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Smart Study Resources</h2>
          <p className="text-gray-500 text-sm">
            {selectedSubject ? (
              <span className="text-purple-600 font-medium">
                📚 Showing resources for: {selectedSubject}
              </span>
            ) : (
              `AI-curated learning materials - ${metrics?.studentInfo?.semester || 'Current Semester'}`
            )}
          </p>
        </div>
        {selectedSubject && (
          <button
            onClick={() => window.location.reload()}
            className="ml-auto text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
          >
            <RefreshCw className="w-4 h-4" />
            Show All
          </button>
        )}
      </div>

      {/* Selected Subject Banner */}
      {selectedSubject && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-purple-100 border border-purple-300 rounded-lg p-3 mb-4 flex items-center gap-2"
        >
          <Sparkles className="w-5 h-5 text-purple-600" />
          <span className="text-purple-800 font-medium">
            Personalized resources for "{selectedSubject}" based on your weakness analysis
          </span>
        </motion.div>
      )}

      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('recommended')}
            className={cn(
              'px-4 py-2 rounded-lg font-semibold transition-all',
              activeTab === 'recommended'
                ? 'bg-purple-600 text-white shadow-lg'
                : 'bg-purple-50 text-purple-600 hover:bg-purple-100'
            )}
          >
            🎯 AI Recommended ({resources.length})
          </button>
          <button
            onClick={() => setActiveTab('bookmarked')}
            className={cn(
              'px-4 py-2 rounded-lg font-semibold transition-all',
              activeTab === 'bookmarked'
                ? 'bg-purple-600 text-white shadow-lg'
                : 'bg-purple-50 text-purple-600 hover:bg-purple-100'
            )}
          >
            ⭐ Bookmarked ({bookmarked.length})
          </button>
        </div>

        <div className="flex gap-2 flex-wrap">
          {filters.map((filter) => (
            <button
              key={filter}
              onClick={() => setSelectedFilter(filter)}
              className={cn(
                'px-3 py-1 rounded-lg text-sm font-medium transition-all',
                selectedFilter === filter
                  ? 'bg-purple-100 text-purple-700 border border-purple-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <AnimatePresence mode="wait">
          {currentResources.length > 0 ? (
            currentResources.map((resource, index) => {
              // Check if this resource matches the selected subject
              const isMatchingSubject = selectedSubject && (
                resource.subject?.toLowerCase().includes(selectedSubject.toLowerCase()) ||
                resource.title?.toLowerCase().includes(selectedSubject.toLowerCase()) ||
                resource.tags?.some((t: string) => t.toLowerCase().includes(selectedSubject.toLowerCase()))
              );

              return (
                <motion.div
                  key={resource.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "bg-gradient-to-r from-purple-50 to-white rounded-xl p-5 border transition-all hover:shadow-md",
                    isMatchingSubject 
                      ? "border-purple-400 ring-2 ring-purple-100" 
                      : "border-purple-200 hover:border-purple-400"
                  )}
                >
                  {isMatchingSubject && (
                    <div className="flex items-center gap-2 mb-3">
                      <span className="bg-purple-600 text-white px-2 py-1 rounded text-xs font-semibold flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        Recommended for your weakness
                      </span>
                    </div>
                  )}

                  <div className="flex items-start gap-4">
                    {resource.thumbnailUrl ? (
                      <img
                        src={resource.thumbnailUrl}
                        alt={resource.title}
                        className="w-24 h-24 rounded-lg object-cover flex-shrink-0"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="text-4xl w-24 h-24 flex items-center justify-center bg-purple-100 rounded-lg flex-shrink-0">
                        {resource.icon}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <h3 className="text-lg font-bold text-gray-900 truncate">{resource.title}</h3>
                            <button
                              onClick={(e) => handleBookmark(resource.id, e)}
                              className={cn(
                                'p-1 rounded transition-colors flex-shrink-0',
                                resource.isBookmarked
                                  ? 'text-yellow-500 hover:text-yellow-600'
                                  : 'text-gray-400 hover:text-gray-600'
                              )}
                            >
                              <Bookmark className={cn('w-5 h-5', resource.isBookmarked && 'fill-current')} />
                            </button>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-gray-600 mb-2 flex-wrap">
                            <span className="font-medium text-purple-600 capitalize">{resource.type}</span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {resource.duration}
                            </span>
                            <span>•</span>
                            <span>
                              ⭐ {typeof resource.rating === 'number' ? resource.rating.toFixed(1) : resource.rating}
                            </span>
                            <span>•</span>
                            <span className="text-purple-600 font-medium">{resource.difficulty}</span>
                          </div>
                          
                          {resource.description && (
                            <p className="text-sm text-gray-600 mb-2 line-clamp-2">{resource.description}</p>
                          )}
                          
                          <div className="flex items-center gap-3 text-xs text-gray-600 mb-2 flex-wrap">
                            <span className="bg-green-100 text-green-700 px-2 py-1 rounded font-medium">
                              🗣️ {resource.language}
                            </span>
                            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded font-medium">
                              📝 {resource.examRelevance}
                            </span>
                            {resource.completionStatus > 0 && (
                              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded font-medium">
                                {resource.completionStatus}% Complete
                              </span>
                            )}
                          </div>
                          
                          {resource.tags?.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {resource.tags.slice(0, 5).map((tag: string, idx: number) => (
                                <span key={idx} className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-medium">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {resource.aiReason && (
                        <div className="bg-purple-100 rounded-lg p-3 mb-3 flex items-start gap-2">
                          <Lightbulb size={16} className="text-purple-600 mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-purple-800 font-medium">{resource.aiReason}</p>
                        </div>
                      )}

                      {resource.completionStatus > 0 && (
                        <div className="mb-3">
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>Progress</span>
                            <span>{resource.completionStatus}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${resource.completionStatus}%` }}
                              transition={{ duration: 0.5 }}
                              className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-3 text-sm text-gray-500">
                          <span>📺 {resource.provider} • {resource.platform}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button 
                            className="p-2 hover:bg-purple-100 rounded-lg transition-colors"
                            title="Share resource"
                          >
                            <Share2 className="w-4 h-4 text-purple-600" />
                          </button>
                          <button
                            onClick={() => handleAccessResource(resource)}
                            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
                          >
                            Access Now <ExternalLink size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12 bg-purple-50 rounded-xl"
            >
              <GraduationCap className="w-12 h-12 text-purple-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {activeTab === 'bookmarked' ? 'No Bookmarked Resources' : 'No Resources Found'}
              </h3>
              <p className="text-gray-600 mb-4">
                {activeTab === 'bookmarked' 
                  ? 'Bookmark resources to access them quickly later.'
                  : selectedFilter !== 'all'
                    ? `No ${selectedFilter} resources found. Try a different filter.`
                    : 'Resources will appear based on your interests and weaknesses.'}
              </p>
              {selectedFilter !== 'all' && (
                <button
                  onClick={() => setSelectedFilter('all')}
                  className="text-purple-600 hover:text-purple-700 font-medium"
                >
                  Show all resources
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};


// ============== COMBINED ENGINEERING GUIDANCE COMPONENT ==============

export const EngineeringGuidance: React.FC = () => {
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [highlightResources, setHighlightResources] = useState(false);
  const resourcesRef = React.useRef<HTMLDivElement>(null);

  const handleStartLearning = useCallback((topicId: string, subject: string) => {
    setSelectedSubject(subject);
    setHighlightResources(true);
    
    // Scroll to resources section
    setTimeout(() => {
      resourcesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);

    // Remove highlight after 3 seconds
    setTimeout(() => {
      setHighlightResources(false);
    }, 3000);
  }, []);

  return (
    <div className="space-y-8">
      {/* Elective Recommendations */}
      <ElectiveRecommender />
      
      {/* Weakness Analysis */}
      <WeaknessAnalyzer onStartLearning={handleStartLearning} />
      
      {/* Study Resources */}
      <div ref={resourcesRef}>
        <StudyResources 
          selectedSubject={selectedSubject} 
          highlightNew={highlightResources}
        />
      </div>
    </div>
  );
};


// ============== EXPORTS ==============

export default EngineeringGuidance;