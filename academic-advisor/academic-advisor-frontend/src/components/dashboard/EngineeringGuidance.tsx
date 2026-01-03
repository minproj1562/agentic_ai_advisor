// src/components/dashboard/EngineeringGuidance.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, TrendingUp, Lightbulb, Target, ChevronRight, 
  ExternalLink, AlertCircle, CheckCircle, Brain, Sparkles, 
  GraduationCap, Award, Users, Eye, Bookmark, Play, Pause,
  RefreshCw, Download, Share2, MessageCircle, ThumbsUp,
  Clock, Calendar, Zap, TrendingDown, Minus
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

// ElectiveRecommender Component with Backend Integration
export const ElectiveRecommender: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = usePerformanceMetrics();
  const { data: recommendations, isLoading: recsLoading, refetch } = useElectiveRecommendations();
  const trackActivity = useTrackActivity();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
    toast.success('Recommendations updated!');
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
            {[1, 2, 3].map((i: number) => (
              <div key={i} className="h-32 bg-gray-100 rounded-xl"></div>
            ))}
          </div>
        </div>
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
              Personalized for {metrics?.studentInfo.year} • {metrics?.studentInfo.branch}
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
            <p className="text-lg font-bold text-purple-700">{metrics?.studentInfo.semester}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <AnimatePresence>
          {recommendations?.map((rec: any, index: number) => (
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
                    <span className="flex items-center gap-1">
                      👨‍🏫 {rec.instructor.name}
                    </span>
                    <span className="flex items-center gap-1">
                      ⭐ {rec.instructor.rating.toFixed(1)}
                    </span>
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
                {rec.tags.map((tag: string, idx: number) => (
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

              {/* Expanded Details */}
              <AnimatePresence>
                {expandedId === rec.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 pt-4 border-t border-purple-200"
                  >
                    <div className="space-y-4">
                      {/* Prerequisites */}
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

                      {/* Learning Outcomes */}
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

                      {/* Syllabus Preview */}
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

                      {/* Instructor Info */}
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
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

// WeaknessAnalyzer Component with Backend Integration
export const WeaknessAnalyzer: React.FC = () => {
  const { data: metrics } = usePerformanceMetrics();
  const { data: weaknesses, isLoading, refetch } = useWeaknessAnalysis();
  const trackActivity = useTrackActivity();
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  const getTrendIcon = (score: number, targetScore: number) => {
    if (score >= targetScore) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (score >= targetScore * 0.8) return <TrendingUp className="w-5 h-5 text-yellow-500" />;
    return <TrendingDown className="w-5 h-5 text-red-500" />;
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      high: 'bg-red-100 text-red-700 border-red-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      low: 'bg-green-100 text-green-700 border-green-200'
    };
    return colors[severity] || colors.low;
  };

  const handleStartLearning = (topicId: string) => {
    trackActivity.mutate({
      type: 'topic_completed',
      topicId
    });
    toast.success('Study plan generated! Check your resources.');
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2].map((i: number) => (
            <div key={i} className="h-48 bg-gray-100 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-3 rounded-xl">
            <AlertCircle className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI Weakness Analysis & Improvement Roadmap</h2>
            <p className="text-gray-500 text-sm">Personalized study plans based on performance data</p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
        >
          <RefreshCw className="w-5 h-5 text-purple-600" />
        </button>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-purple-600 font-medium mb-1">📊 Current Performance</p>
            <p className="text-2xl font-bold text-purple-700">CGPA: {metrics?.overallCGPA}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-purple-600 font-medium mb-1">🎯 Potential CGPA</p>
            <p className="text-2xl font-bold text-green-600">
              {(metrics?.overallCGPA! + 0.7).toFixed(1)}+ achievable
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">📈 Improvement</p>
            <p className="text-xl font-bold text-orange-600">+0.7 points</p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <AnimatePresence>
          {weaknesses?.map((weak: any, idx: number) => (
            <motion.div
              key={weak.subjectCode}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-gradient-to-r from-purple-50 to-white rounded-xl p-5 border border-purple-200"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <BookOpen size={20} className="text-purple-600" />
                    {weak.subject}
                  </h3>
                  <p className="text-sm text-gray-600">{weak.subjectCode} • {weak.semester}</p>
                </div>
                <div className="text-right">
                  <div className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-semibold mb-1">
                    Current: {weak.overallScore}%
                  </div>
                  <p className="text-xs text-gray-500">{weak.topics.length} topics need attention</p>
                </div>
              </div>

              {/* AI Analysis */}
              {weak.aiAnalysis && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-indigo-900 mb-2">AI Analysis</h4>
                      <p className="text-sm text-indigo-700 mb-2">
                        <strong>Root Cause:</strong> {weak.aiAnalysis.rootCause}
                      </p>
                      <p className="text-sm text-indigo-700 mb-2">
                        <strong>Strategy:</strong> {weak.aiAnalysis.studyStrategy}
                      </p>
                      <p className="text-xs text-indigo-600">
                        ⏱️ Estimated improvement time: {weak.aiAnalysis.estimatedImprovementTime}
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="space-y-3">
                {weak.topics.map((topic: any, tidx: number) => (
                  <div key={topic.id} className="bg-white rounded-lg p-4 border border-purple-100 hover:border-purple-300 transition-all">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3 flex-1">
                        <h4 className="font-semibold text-gray-800">{topic.name}</h4>
                        <span className={cn('px-3 py-1 rounded-full text-xs font-semibold border', getSeverityColor(topic.severity))}>
                          {topic.severity.toUpperCase()}
                        </span>
                        <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                          📝 Exam: {topic.examWeight}
                        </span>
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
                        <span>Current: {topic.currentScore}%</span>
                        <span>Target: {topic.targetScore}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5 relative overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${topic.currentScore}%` }}
                          transition={{ duration: 1, ease: "easeOut" }}
                          className="h-2.5 rounded-full bg-gradient-to-r from-purple-500 to-purple-600"
                        />
                        <div 
                          className="absolute top-0 h-2.5 w-0.5 bg-green-500"
                          style={{ left: `${topic.targetScore}%` }}
                        />
                      </div>
                    </div>

                    {/* Related Topics */}
                    {topic.relatedTopics && topic.relatedTopics.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-600 mb-1">Related Concepts:</p>
                        <div className="flex flex-wrap gap-1">
                          {topic.relatedTopics.map((rel: string, idx: number) => (
                            <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                              {rel}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
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
                        onClick={() => handleStartLearning(topic.id)}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
                      >
                        Start Learning <ChevronRight size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

// StudyResources Component with Backend Integration
export const StudyResources: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'recommended' | 'bookmarked'>('recommended');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const { data: metrics } = usePerformanceMetrics();
  const { data: resources, isLoading } = useStudyResources(
    activeTab === 'recommended' ? { type: selectedFilter !== 'all' ? selectedFilter : undefined } : undefined
  );
  const { data: bookmarked } = useBookmarkedResources();
  const toggleBookmark = useToggleBookmark();
  const updateProgress = useUpdateProgress();
  const trackActivity = useTrackActivity();

  const currentResources = activeTab === 'recommended' ? resources : bookmarked;

  const handleBookmark = async (resourceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    toggleBookmark.mutate(resourceId);
  };

  const handleAccessResource = (resource: any) => {
    trackActivity.mutate({
      type: 'resource_viewed',
      resourceId: resource.id
    });
    window.open(resource.url, '_blank');
  };

  const handleProgressUpdate = (resourceId: string, progress: number) => {
    updateProgress.mutate({ resourceId, progress });
  };

  const filters = ['all', 'video', 'tutorial', 'practice'];

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i: number) => (
            <div key={i} className="h-32 bg-gray-100 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-3 rounded-xl">
          <GraduationCap className="text-white" size={24} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Smart Study Resources</h2>
          <p className="text-gray-500 text-sm">
            AI-curated learning materials - {metrics?.studentInfo.semester}
          </p>
        </div>
      </div>

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
            🎯 AI Recommended ({resources?.length || 0})
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
            ⭐ Bookmarked ({bookmarked?.length || 0})
          </button>
        </div>

        <div className="flex gap-2">
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
        <AnimatePresence>
          {currentResources?.map((resource: any, index: number) => (
            <motion.div
              key={resource.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ delay: index * 0.05 }}
              className="bg-gradient-to-r from-purple-50 to-white rounded-xl p-5 border border-purple-200 hover:border-purple-400 transition-all hover:shadow-md"
            >
              <div className="flex items-start gap-4">
                {resource.thumbnailUrl ? (
                  <img
                    src={resource.thumbnailUrl}
                    alt={resource.title}
                    className="w-24 h-24 rounded-lg object-cover"
                  />
                ) : (
                  <div className="text-4xl">{resource.icon}</div>
                )}
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-bold text-gray-900">{resource.title}</h3>
                        <button
                          onClick={(e) => handleBookmark(resource.id, e)}
                          className={cn(
                            'p-1 rounded transition-colors',
                            resource.isBookmarked
                              ? 'text-yellow-500 hover:text-yellow-600'
                              : 'text-gray-400 hover:text-gray-600'
                          )}
                        >
                          <Bookmark className={cn('w-5 h-5', resource.isBookmarked && 'fill-current')} />
                        </button>
                      </div>
                      <div className="flex items-center gap-3 text-sm text-gray-600 mb-2 flex-wrap">
                        <span className="font-medium text-purple-600">{resource.type}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {resource.duration}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          ⭐ {resource.rating} ({resource.reviews.toLocaleString()})
                        </span>
                        <span>•</span>
                        <span className="text-purple-600 font-medium">{resource.difficulty}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-600 mb-2">
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
                      <div className="flex flex-wrap gap-2 mb-2">
                        {resource.tags.map((tag: string, idx: number) => (
                          <span key={idx} className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-medium">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {resource.aiReason && (
                    <div className="bg-purple-100 rounded-lg p-3 mb-3 flex items-start gap-2">
                      <Lightbulb size={16} className="text-purple-600 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-purple-800 font-medium">{resource.aiReason}</p>
                    </div>
                  )}

                  {/* Progress Bar */}
                  {resource.completionStatus > 0 && (
                    <div className="mb-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${resource.completionStatus}%` }}
                          className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <span>📺 {resource.provider} • {resource.platform}</span>
                      <span>•</span>
                      <span>Updated {resource.lastUpdated}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="p-2 hover:bg-purple-100 rounded-lg transition-colors">
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
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};