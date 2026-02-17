// src/components/dashboard/ReadinessAnalysis.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle, AlertTriangle, XCircle, Clock, TrendingUp,
  BookOpen, Award, Target, ChevronDown, ChevronUp, Loader2,
  RefreshCw, Info, Zap, Calendar, ArrowRight, AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import {
  getWeaknessService,
  ReadinessResponse,
  ReadinessWeakness
} from '../../services/weakness.service';

// ==================== Props ====================

interface ReadinessAnalysisProps {
  studentId?: string;
  interests?: string[];
  electives?: string[];
  honours?: string[];
  compact?: boolean;
  onAnalysisComplete?: (data: ReadinessResponse) => void;
}

// ==================== Helpers ====================

const getLevelConfig = (level: string) => {
  const configs: Record<string, {
    color: string;
    bg: string;
    icon: React.ReactNode;
    label: string;
  }> = {
    excellent: {
      color: 'text-green-600',
      bg: 'bg-green-50',
      icon: <CheckCircle className="w-6 h-6" />,
      label: 'Excellent',
    },
    good: {
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      icon: <CheckCircle className="w-6 h-6" />,
      label: 'Good',
    },
    moderate: {
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
      icon: <AlertTriangle className="w-6 h-6" />,
      label: 'Moderate',
    },
    low: {
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      icon: <AlertTriangle className="w-6 h-6" />,
      label: 'Low',
    },
    not_ready: {
      color: 'text-red-600',
      bg: 'bg-red-50',
      icon: <XCircle className="w-6 h-6" />,
      label: 'Not Ready',
    },
  };
  return configs[level] || configs.moderate;
};

const getRecTypeConfig = (type: string) => {
  const configs: Record<string, {
    color: string;
    bg: string;
    border: string;
  }> = {
    proceed: {
      color: 'text-green-700',
      bg: 'bg-green-100',
      border: 'border-green-300',
    },
    proceed_with_caution: {
      color: 'text-blue-700',
      bg: 'bg-blue-100',
      border: 'border-blue-300',
    },
    improve_first: {
      color: 'text-orange-700',
      bg: 'bg-orange-100',
      border: 'border-orange-300',
    },
    do_not_proceed: {
      color: 'text-red-700',
      bg: 'bg-red-100',
      border: 'border-red-300',
    },
  };
  return configs[type] || configs.improve_first;
};

const getSeverityBadge = (severity: string) => {
  const styles: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 border-red-300',
    high: 'bg-orange-100 text-orange-700 border-orange-300',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    low: 'bg-green-100 text-green-700 border-green-300',
  };
  return styles[severity] || styles.medium;
};

// ==================== Component ====================

export const ReadinessAnalysis: React.FC<ReadinessAnalysisProps> = ({
  studentId,
  interests = [],
  electives = [],
  honours = [],
  compact = false,
  onAnalysisComplete,
}) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ReadinessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['overview', 'weaknesses'])
  );
  const [selectedTab, setSelectedTab] = useState<
    'overview' | 'weaknesses' | 'plan'
  >('overview');

  const effectiveStudentId = studentId || user?.uid || '';

  // ==================== Fetch ====================

  const fetchReadiness = async () => {
    if (!effectiveStudentId) {
      setError('No student ID available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const service = getWeaknessService();
      const result = await service.getReadiness(
        effectiveStudentId,
        interests.length > 0 ? interests : undefined,
        electives.length > 0 ? electives : undefined,
        honours.length > 0 ? honours : undefined
      );
      setData(result);
      onAnalysisComplete?.(result);
    } catch (e: any) {
      console.error('Readiness fetch error:', e);
      setError(e.message || 'Failed to fetch readiness analysis');
      toast.error('Failed to load readiness analysis');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchReadiness();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveStudentId]);

  // Re-fetch when selections change
  useEffect(() => {
    if (
      effectiveStudentId &&
      (interests.length > 0 || electives.length > 0 || honours.length > 0)
    ) {
      fetchReadiness();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interests.join(','), electives.join(','), honours.join(',')]);

  // ==================== Toggle ====================

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  };

  // ==================== Loading ====================

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-8 flex flex-col items-center justify-center min-h-[300px]">
        <Loader2 className="w-10 h-10 animate-spin text-purple-600 mb-4" />
        <p className="text-gray-600">Analyzing your academic readiness...</p>
        <p className="text-sm text-gray-400 mt-1">
          This evaluates your preparation for selected goals
        </p>
      </div>
    );
  }

  // ==================== Error ====================

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-8">
        <div className="flex items-center gap-3 text-red-600 mb-4">
          <AlertCircle className="w-6 h-6" />
          <h3 className="font-semibold">Analysis Error</h3>
        </div>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchReadiness}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Retry Analysis
        </button>
      </div>
    );
  }

  // ==================== No Data ====================

  if (!data) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
        <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="font-semibold text-gray-700 mb-2">No Readiness Data</h3>
        <p className="text-gray-500 mb-4">
          Select your interests, electives, or honours to analyze readiness.
        </p>
        <button
          onClick={fetchReadiness}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Run Analysis
        </button>
      </div>
    );
  }

  // ==================== Computed ====================

  const levelConfig = getLevelConfig(data.readiness_level);
  const recConfig = getRecTypeConfig(data.recommendation_type);
  const weaknesses: ReadinessWeakness[] = data.weaknesses || [];
  const criticalCount = weaknesses.filter((w) => w.severity === 'critical').length;
  const highCount = weaknesses.filter((w) => w.severity === 'high').length;
  const studyPlan = data.study_plan || null;

  // ==================== Compact ====================

  if (compact) {
    return (
      <div className={`rounded-xl p-4 border ${levelConfig.bg}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={levelConfig.color}>{levelConfig.icon}</div>
            <div>
              <p className="font-semibold text-gray-800">
                Readiness: {data.overall_readiness_score.toFixed(0)}%
              </p>
              <p className="text-sm text-gray-600">{levelConfig.label}</p>
            </div>
          </div>
          <div className="text-right">
            {data.has_critical_weakness && (
              <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
                {criticalCount} Critical
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ==================== Full Render ====================

  return (
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold mb-1">Academic Readiness Analysis</h2>
            <p className="text-purple-100 text-sm">
              Based on your selected interests, electives, and honours
            </p>
          </div>
          <button
            onClick={fetchReadiness}
            className="px-3 py-2 bg-white/20 rounded-lg hover:bg-white/30 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {/* Score Circle */}
        <div className="mt-6 flex items-center gap-6">
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                fill="none"
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="8"
              />
              <circle
                cx="48"
                cy="48"
                r="40"
                fill="none"
                stroke="white"
                strokeWidth="8"
                strokeDasharray={`${(data.overall_readiness_score / 100) * 251.2} 251.2`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl font-bold">
                {data.overall_readiness_score.toFixed(0)}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-lg font-semibold">{levelConfig.label} Readiness</p>
            <p className="text-purple-200 text-sm mt-1">
              {data.primary_recommendation}
            </p>
          </div>
        </div>
      </div>

      {/* Category Scores */}
      <div className="grid grid-cols-3 gap-px bg-gray-200">
        {[
          {
            label: 'Interest',
            score: data.interest_readiness,
            icon: <Zap className="w-4 h-4" />,
          },
          {
            label: 'Elective',
            score: data.elective_readiness,
            icon: <BookOpen className="w-4 h-4" />,
          },
          {
            label: 'Honours',
            score: data.honours_readiness,
            icon: <Award className="w-4 h-4" />,
          },
        ].map((cat) => (
          <div key={cat.label} className="bg-white p-4 text-center">
            <div className="flex items-center justify-center gap-2 text-gray-500 mb-1">
              {cat.icon}
              <span className="text-sm">{cat.label}</span>
            </div>
            <p className="text-2xl font-bold text-gray-800">
              {(cat.score ?? 0).toFixed(0)}%
            </p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b flex">
        {(['overview', 'weaknesses', 'plan'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${
              selectedTab === tab
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'overview' && 'Overview'}
            {tab === 'weaknesses' && `Weaknesses (${weaknesses.length})`}
            {tab === 'plan' && 'Study Plan'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-6">
        <AnimatePresence mode="wait">
          {/* ===== Overview ===== */}
          {selectedTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {/* Recommendation */}
              <div
                className={`p-4 rounded-lg border ${recConfig.bg} ${recConfig.border}`}
              >
                <h4 className={`font-semibold ${recConfig.color} mb-2`}>
                  Recommendation:{' '}
                  {data.recommendation_type.replace(/_/g, ' ').toUpperCase()}
                </h4>
                <p className={`text-sm ${recConfig.color}`}>
                  {data.primary_recommendation}
                </p>
              </div>

              {/* Action Items */}
              {data.detailed_recommendations &&
                data.detailed_recommendations.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">
                      Action Items
                    </h4>
                    <ul className="space-y-2">
                      {data.detailed_recommendations.map((rec, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-gray-700"
                        >
                          <ArrowRight className="w-4 h-4 mt-1 text-purple-500 flex-shrink-0" />
                          <span className="text-sm">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-red-600">
                    {criticalCount}
                  </p>
                  <p className="text-xs text-gray-500">Critical</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-orange-600">
                    {highCount}
                  </p>
                  <p className="text-xs text-gray-500">High Priority</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {data.subjects_to_focus?.length || 0}
                  </p>
                  <p className="text-xs text-gray-500">Focus Areas</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <p className="text-lg font-bold text-purple-600">
                    {data.estimated_preparation_time || 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500">Est. Time</p>
                </div>
              </div>

              {/* Focus Subjects */}
              {data.subjects_to_focus &&
                data.subjects_to_focus.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">
                      Subjects to Focus On
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {data.subjects_to_focus.map((subj, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                        >
                          {subj}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              {/* First Semester */}
              {data.is_first_semester && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-800">
                      First Semester Student
                    </p>
                    <p className="text-sm text-blue-700">
                      Some subjects haven't been taken yet — this is expected.
                    </p>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* ===== Weaknesses ===== */}
          {selectedTab === 'weaknesses' && (
            <motion.div
              key="weaknesses"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {weaknesses.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                  <p className="text-gray-600">
                    No significant weaknesses detected!
                  </p>
                </div>
              ) : (
                weaknesses.map((w, i) => {
                  const currentScore = w.current_score ?? 0;
                  const targetScore = w.target_score ?? 60;
                  const gapValue = w.gap ?? targetScore - currentScore;
                  const progressPercent =
                    targetScore > 0
                      ? Math.min((currentScore / targetScore) * 100, 100)
                      : 0;

                  return (
                    <div
                      key={w.id || `weakness-${i}`}
                      className="border rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleSection(`weakness-${i}`)}
                        className="w-full p-4 flex items-center justify-between hover:bg-gray-50"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityBadge(
                              w.severity
                            )}`}
                          >
                            {w.severity.toUpperCase()}
                          </span>
                          <div className="text-left">
                            <p className="font-medium text-gray-800">
                              {w.subject}
                            </p>
                            <p className="text-sm text-gray-500">
                              Score: {currentScore.toFixed(0)}% → Target:{' '}
                              {targetScore.toFixed(0)}%
                            </p>
                          </div>
                        </div>
                        {expandedSections.has(`weakness-${i}`) ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </button>

                      <AnimatePresence>
                        {expandedSections.has(`weakness-${i}`) && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t bg-gray-50 p-4"
                          >
                            <div className="space-y-3">
                              {/* Progress bar */}
                              <div>
                                <div className="flex justify-between text-xs text-gray-500 mb-1">
                                  <span>
                                    Current: {currentScore.toFixed(0)}%
                                  </span>
                                  <span>
                                    Target: {targetScore.toFixed(0)}%
                                  </span>
                                </div>
                                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-gradient-to-r from-red-500 to-yellow-500 rounded-full"
                                    style={{
                                      width: `${progressPercent}%`,
                                    }}
                                  />
                                </div>
                              </div>

                              {/* Gap */}
                              <p className="text-sm text-gray-600">
                                <strong>Gap:</strong>{' '}
                                {gapValue.toFixed(1)}% improvement needed
                              </p>

                              {/* Linked goals */}
                              {w.linked_goals &&
                                w.linked_goals.length > 0 && (
                                  <div>
                                    <p className="text-sm font-medium text-gray-700 mb-1">
                                      Affects:
                                    </p>
                                    <div className="flex flex-wrap gap-1">
                                      {w.linked_goals.map((g, gi) => (
                                        <span
                                          key={gi}
                                          className="px-2 py-0.5 bg-white border rounded text-xs"
                                        >
                                          {g}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                              {/* Suggestions */}
                              {w.suggestions &&
                                w.suggestions.length > 0 && (
                                  <div>
                                    <p className="text-sm font-medium text-gray-700 mb-1">
                                      Suggestions:
                                    </p>
                                    <ul className="text-sm text-gray-600 space-y-1">
                                      {w.suggestions
                                        .slice(0, 3)
                                        .map((s, si) => (
                                          <li
                                            key={si}
                                            className="flex items-start gap-2"
                                          >
                                            <span className="text-purple-500">
                                              •
                                            </span>
                                            {s}
                                          </li>
                                        ))}
                                    </ul>
                                  </div>
                                )}

                              {/* Estimated time */}
                              <p className="text-sm text-gray-500 flex items-center gap-1">
                                <Clock className="w-4 h-4" />
                                Estimated: {w.estimated_hours || 10} hours to
                                improve
                              </p>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })
              )}
            </motion.div>
          )}

          {/* ===== Study Plan ===== */}
          {selectedTab === 'plan' && (
            <motion.div
              key="plan"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {studyPlan && Object.keys(studyPlan).length > 0 ? (
                <>
                  {/* Plan Header */}
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg">
                    <div>
                      <h4 className="font-semibold text-purple-800">
                        Personalized Study Plan
                      </h4>
                      <p className="text-sm text-purple-600">
                        Duration: {studyPlan.duration || '—'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-purple-700">
                        {studyPlan.weekly_hours || '15-20'}
                      </p>
                      <p className="text-xs text-purple-500">hours/week</p>
                    </div>
                  </div>

                  {/* Focus Areas */}
                  {studyPlan.focus_areas &&
                    studyPlan.focus_areas.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                          <Target className="w-4 h-4" /> Focus Areas
                        </h5>
                        <div className="space-y-2">
                          {studyPlan.focus_areas.map((area, i) => (
                            <div
                              key={i}
                              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                            >
                              <div className="flex items-center gap-3">
                                <span className="w-6 h-6 rounded-full bg-purple-600 text-white flex items-center justify-center text-sm font-bold">
                                  {area.priority || i + 1}
                                </span>
                                <div>
                                  <p className="font-medium text-gray-800">
                                    {area.subject}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    {area.current_score.toFixed(0)}% →{' '}
                                    {area.target_score.toFixed(0)}%
                                  </p>
                                </div>
                              </div>
                              <span className="text-sm text-purple-600 font-medium">
                                {area.weekly_hours} hrs/week
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Phases */}
                  {studyPlan.phases && studyPlan.phases.length > 0 && (
                    <div>
                      <h5 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <Calendar className="w-4 h-4" /> Phases
                      </h5>
                      <div className="space-y-3">
                        {studyPlan.phases.map((phase, i) => (
                          <div
                            key={i}
                            className="border-l-4 border-purple-500 pl-4 py-2"
                          >
                            <p className="font-medium text-gray-800">
                              {phase.name}{' '}
                              <span className="text-gray-500 text-sm">
                                ({phase.weeks})
                              </span>
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                              Focus:{' '}
                              {Array.isArray(phase.focus)
                                ? phase.focus.join(', ')
                                : phase.focus}
                            </p>
                            {phase.goals && phase.goals.length > 0 && (
                              <ul className="text-sm text-gray-500 mt-1">
                                {phase.goals.map((g, gi) => (
                                  <li key={gi}>• {g}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Milestones */}
                  {studyPlan.milestones &&
                    studyPlan.milestones.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                          <TrendingUp className="w-4 h-4" /> Milestones
                        </h5>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {studyPlan.milestones.map((m, i) => (
                            <div
                              key={i}
                              className="p-3 bg-green-50 rounded-lg border border-green-200 text-center"
                            >
                              <p className="text-lg font-bold text-green-700">
                                Week {m.week}
                              </p>
                              <p className="text-xs text-green-600 mt-1">
                                {m.target}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                </>
              ) : (
                <div className="text-center py-8">
                  <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">
                    No study plan available yet.
                  </p>
                  <p className="text-sm text-gray-400">
                    Run a full analysis to generate a personalized plan.
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="border-t p-4 bg-gray-50 text-center text-xs text-gray-500">
        Analysis performed at{' '}
        {new Date(data.analysis_timestamp).toLocaleString()}
      </div>
    </div>
  );
};

export default ReadinessAnalysis;